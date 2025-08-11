import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.twitter_api_io import TwitterAPIio

class TokenDiscovery:
    def __init__(self):
        self.twitter_client = TwitterAPIio()
        self.dexscreener_base = "https://api.dexscreener.com/latest"
        self.moralis_api_key = os.getenv('MORALIS_API_KEY')
        self.moralis_base = "https://solana-gateway.moralis.io"
        
    def get_new_tokens(self, minutes_old: int = 3) -> List[Dict]:
        """Get tokens that are less than X minutes old from multiple sources"""
        all_tokens = []
        
        # Get from Moralis API (Pump.fun and other exchanges)
        if self.moralis_api_key:
            moralis_tokens = self._get_moralis_new_tokens(minutes_old)
            all_tokens.extend(moralis_tokens)
        else:
            print("Moralis API key not configured, skipping Moralis data")
        
        # Optionally still try DexScreener as backup
        # dexscreener_tokens = self._get_dexscreener_new_tokens(minutes_old)
        # all_tokens.extend(dexscreener_tokens)
        
        # Remove duplicates based on contract address
        seen = set()
        unique_tokens = []
        duplicate_count = 0
        
        for token in all_tokens:
            ca = token.get('contract_address')
            
            # Skip tokens without contract address
            if not ca:
                print(f"Skipping token {token.get('symbol', 'Unknown')} - no contract address")
                continue
                
            if ca not in seen:
                seen.add(ca)
                unique_tokens.append(token)
            else:
                duplicate_count += 1
                print(f"Duplicate CA found: {token.get('symbol')} - {ca[:10]}...")
        
        if duplicate_count > 0:
            print(f"Removed {duplicate_count} duplicate tokens")
        
        print(f"Found {len(unique_tokens)} unique tokens")
        return unique_tokens
    
    def _get_moralis_new_tokens(self, minutes_old: int) -> List[Dict]:
        """Fetch new tokens from Moralis API (Pump.fun exchange)"""
        tokens = []
        
        try:
            # Moralis endpoint for new tokens by exchange
            url = f"{self.moralis_base}/token/mainnet/exchange/pumpfun/new"
            
            headers = {
                'X-API-Key': self.moralis_api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'limit': 100  # Get up to 100 newest tokens
            }
            
            print(f"Fetching new tokens from Moralis API (Pump.fun)")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Moralis returns tokens in a result array
                token_list = data.get('result', []) if isinstance(data, dict) else data
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
                
                for token in token_list:
                    # Parse creation time - Moralis uses ISO format
                    created_at_str = token.get('createdAt') or token.get('created_at')
                    
                    if created_at_str:
                        try:
                            # Parse ISO format datetime
                            if 'T' in created_at_str:
                                created_datetime = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            else:
                                created_datetime = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
                                created_datetime = created_datetime.replace(tzinfo=timezone.utc)
                            
                            # Check if token is within our time window
                            if created_datetime >= cutoff_time:
                                # Extract token data and ensure numeric values
                                def safe_float(value, default=0):
                                    try:
                                        return float(value) if value else default
                                    except (ValueError, TypeError):
                                        return default
                                
                                # Get contract address - Moralis might use 'mint' for Solana tokens
                                contract_addr = token.get('mint') or token.get('address') or token.get('tokenAddress')
                                
                                print(f"Token {token.get('symbol')}: CA = {contract_addr}")
                                
                                tokens.append({
                                    'contract_address': contract_addr,
                                    'symbol': token.get('symbol', 'Unknown'),
                                    'name': token.get('name', 'Unknown'),
                                    'chain': 'solana',
                                    'created_at': created_datetime,
                                    'liquidity': safe_float(token.get('liquidity')),
                                    'market_cap': safe_float(token.get('marketCap') or token.get('market_cap')),
                                    'price': str(token.get('price', '0')),
                                    'volume_24h': safe_float(token.get('volume24h') or token.get('volume')),
                                    'price_change_24h': safe_float(token.get('priceChange24h')),
                                    'source': 'moralis_pumpfun',
                                    'decimals': safe_float(token.get('decimals'), 9),
                                    'total_supply': safe_float(token.get('totalSupply') or token.get('total_supply')),
                                    'exchange': 'pumpfun',
                                    'description': token.get('description', ''),
                                    'image': token.get('image') or token.get('logo', ''),
                                    'twitter': token.get('twitter', ''),
                                    'telegram': token.get('telegram', ''),
                                    'website': token.get('website', '')
                                })
                                
                                print(f"Found new token: {token.get('symbol')} created at {created_datetime}")
                            
                        except Exception as e:
                            print(f"Error parsing token datetime: {e}")
                            # Still add the token if we can't parse the date
                            def safe_float(value, default=0):
                                try:
                                    return float(value) if value else default
                                except (ValueError, TypeError):
                                    return default
                            
                            contract_addr = token.get('mint') or token.get('address') or token.get('tokenAddress')
                            print(f"Token {token.get('symbol')} (no date): CA = {contract_addr}")
                            
                            tokens.append({
                                'contract_address': contract_addr,
                                'symbol': token.get('symbol', 'Unknown'),
                                'name': token.get('name', 'Unknown'),
                                'chain': 'solana',
                                'created_at': datetime.now(timezone.utc),
                                'liquidity': safe_float(token.get('liquidity')),
                                'market_cap': safe_float(token.get('marketCap') or token.get('market_cap')),
                                'price': str(token.get('price', '0')),
                                'volume_24h': safe_float(token.get('volume24h') or token.get('volume')),
                                'price_change_24h': safe_float(token.get('priceChange24h')),
                                'source': 'moralis_pumpfun',
                                'exchange': 'pumpfun'
                            })
                
                print(f"Found {len(tokens)} new tokens from Moralis")
                
            elif response.status_code == 401:
                print("Invalid Moralis API key")
            elif response.status_code == 429:
                print("Moralis API rate limit exceeded")
            else:
                print(f"Moralis API error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Error fetching from Moralis: {e}")
        
        return tokens
    
    def _get_dexscreener_new_tokens(self, minutes_old: int) -> List[Dict]:
        """Fetch new Solana tokens from DexScreener"""
        tokens = []
        
        try:
            # First try to get Solana-specific tokens from the profiles endpoint
            url = f"https://api.dexscreener.com/token-profiles/latest/v1"
            print(f"Fetching from: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process only Solana token profiles
                for profile in data:
                    chain_id = profile.get('chainId')
                    token_address = profile.get('tokenAddress')
                    
                    # Only process Solana tokens
                    if chain_id == 'solana' and token_address:
                        # Now fetch the token pairs for this specific token
                        token_url = f"{self.dexscreener_base}/dex/tokens/{token_address}"
                        print(f"Fetching token data: {token_url}")
                        
                        try:
                            token_response = requests.get(token_url, timeout=5)
                            
                            if token_response.status_code == 200:
                                token_data = token_response.json()
                                pairs = token_data.get('pairs', [])
                                
                                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
                                
                                for pair in pairs:
                                    # Check if token is new enough
                                    created_at = pair.get('pairCreatedAt')
                                    if created_at:
                                        try:
                                            # DexScreener uses milliseconds timestamp
                                            created_datetime = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                                            
                                            if created_datetime >= cutoff_time:
                                                base_token = pair.get('baseToken', {})
                                                
                                                # Map chainId to chain name
                                                chain_map = {
                                                    'ethereum': 'ethereum',
                                                    'bsc': 'bsc', 
                                                    'polygon': 'polygon',
                                                    'arbitrum': 'arbitrum',
                                                    'optimism': 'optimism',
                                                    'base': 'base',
                                                    'solana': 'solana'
                                                }
                                                
                                                tokens.append({
                                                    'contract_address': base_token.get('address', ''),
                                                    'symbol': base_token.get('symbol', 'Unknown'),
                                                    'name': base_token.get('name', 'Unknown'),
                                                    'chain': chain_id,
                                                    'created_at': created_datetime,
                                                    'liquidity': pair.get('liquidity', {}).get('usd', 0),
                                                    'market_cap': pair.get('fdv', 0),
                                                    'price': pair.get('priceUsd', '0'),
                                                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                                                    'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                                                    'source': 'dexscreener',
                                                    'pair_address': pair.get('pairAddress', ''),
                                                    'dex': pair.get('dexId', ''),
                                                    'url': pair.get('url', '')
                                                })
                                                break  # Only need one pair per token
                                        except Exception as e:
                                            print(f"Error processing pair: {e}")
                                            continue
                            
                            time.sleep(0.1)  # Rate limiting between token fetches
                            
                        except Exception as e:
                            print(f"Error fetching token {token_address}: {e}")
                            continue
            else:
                print(f"Error fetching latest tokens: {response.status_code}")
            
            # Alternative: Search for recent Solana tokens directly
            print("Trying alternative: searching recent Solana pairs")
            search_url = f"{self.dexscreener_base}/dex/search"
            params = {'q': 'chain:solana'}
            
            search_response = requests.get(search_url, params=params, timeout=5)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                pairs = search_data.get('pairs', [])
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
                
                # Sort by creation time and process newest first
                sorted_pairs = sorted(pairs, key=lambda x: x.get('pairCreatedAt', 0), reverse=True)
                
                for pair in sorted_pairs[:50]:  # Check first 50 pairs
                    # Only process Solana pairs
                    if pair.get('chainId') != 'solana':
                        continue
                        
                    created_at = pair.get('pairCreatedAt')
                    if created_at:
                        try:
                            created_datetime = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
                            
                            if created_datetime >= cutoff_time:
                                base_token = pair.get('baseToken', {})
                                tokens.append({
                                    'contract_address': base_token.get('address', ''),
                                    'symbol': base_token.get('symbol', 'Unknown'),
                                    'name': base_token.get('name', 'Unknown'),
                                    'chain': 'solana',
                                    'created_at': created_datetime,
                                    'liquidity': pair.get('liquidity', {}).get('usd', 0),
                                    'market_cap': pair.get('fdv', 0),
                                    'price': pair.get('priceUsd', '0'),
                                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                                    'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                                    'source': 'dexscreener',
                                    'pair_address': pair.get('pairAddress', ''),
                                    'dex': pair.get('dexId', ''),
                                    'url': pair.get('url', '')
                                })
                            else:
                                # Since pairs are sorted by creation time, we can stop here
                                break
                        except:
                            continue
                    
        except Exception as e:
            print(f"Error in DexScreener fetch: {e}")
        
        return tokens
    
    def _get_pump_fun_tokens(self, minutes_old: int) -> List[Dict]:
        """Fetch new tokens from Pump.fun"""
        tokens = []
        
        try:
            # Pump.fun API endpoint
            url = "https://frontend-api.pump.fun/coins"
            params = {
                'offset': 0,
                'limit': 50,
                'sort': 'created',
                'order': 'desc'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
                
                for coin in data:
                    created_at_str = coin.get('created_timestamp')
                    if created_at_str:
                        try:
                            created_datetime = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            
                            if created_datetime >= cutoff_time:
                                tokens.append({
                                    'contract_address': coin.get('mint', ''),
                                    'symbol': coin.get('symbol', 'Unknown'),
                                    'name': coin.get('name', 'Unknown'),
                                    'chain': 'solana',
                                    'created_at': created_datetime,
                                    'liquidity': coin.get('usd_market_cap', 0) * 0.1,  # Estimate
                                    'market_cap': coin.get('usd_market_cap', 0),
                                    'price': '0',  # Not provided
                                    'volume_24h': coin.get('volume', 0),
                                    'price_change_24h': 0,
                                    'source': 'pump.fun',
                                    'description': coin.get('description', ''),
                                    'twitter': coin.get('twitter', ''),
                                    'telegram': coin.get('telegram', ''),
                                    'website': coin.get('website', '')
                                })
                        except:
                            continue
                            
        except Exception as e:
            print(f"Error fetching from Pump.fun: {e}")
        
        return tokens
    
    def check_twitter_mentions(self, tokens: List[Dict], max_workers: int = 5) -> List[Dict]:
        """Check Twitter mentions for a list of tokens using parallel processing"""
        
        def check_single_token(token):
            # Initialize default values at the start
            token.setdefault('twitter_mentions', 0)
            token.setdefault('twitter_data', pd.DataFrame())
            token.setdefault('total_views', 0)
            token.setdefault('total_likes', 0)
            token.setdefault('total_retweets', 0)
            token.setdefault('avg_followers', 0)
            token.setdefault('max_followers', 0)
            token.setdefault('top_influencer', None)
            
            try:
                # Safely get contract address and symbol
                contract_address = token.get('contract_address', '')
                symbol = token.get('symbol', 'Unknown')
                
                # Only show first 10 chars of CA for logging
                ca_preview = contract_address[:10] + '...' if len(contract_address) > 10 else contract_address
                
                print(f"Checking Twitter for {symbol}: CA={ca_preview} and ${symbol}")
                
                tweets = self.twitter_client.search_tweets(
                    contract_address=contract_address,
                    symbol=symbol,  # Will search for $SYMBOL only
                    max_results=100  # Limit for initial scan
                )
                
                # Ensure tweets is always a DataFrame, never None
                if tweets is None:
                    tweets = pd.DataFrame()
                
                if not tweets.empty:
                    token['twitter_mentions'] = len(tweets)
                    token['twitter_data'] = tweets
                    
                    # Calculate engagement metrics safely
                    token['total_views'] = tweets['views'].sum() if 'views' in tweets.columns else 0
                    token['total_likes'] = tweets['likes'].sum() if 'likes' in tweets.columns else 0
                    token['total_retweets'] = tweets['retweets'].sum() if 'retweets' in tweets.columns else 0
                    token['avg_followers'] = tweets['followers'].mean() if 'followers' in tweets.columns else 0
                    token['max_followers'] = tweets['followers'].max() if 'followers' in tweets.columns else 0
                    
                    # Get top influencer safely
                    if len(tweets) > 0 and 'followers' in tweets.columns:
                        try:
                            top_tweet = tweets.nlargest(1, 'followers').iloc[0]
                            token['top_influencer'] = {
                                'username': top_tweet.get('username', 'Unknown'),
                                'followers': top_tweet.get('followers', 0),
                                'text': str(top_tweet.get('text', ''))[:100]  # First 100 chars
                            }
                        except:
                            token['top_influencer'] = None
                    else:
                        token['top_influencer'] = None
                else:
                    # No tweets found
                    token['twitter_mentions'] = 0
                    token['twitter_data'] = pd.DataFrame()
                    token['total_views'] = 0
                    token['total_likes'] = 0
                    token['total_retweets'] = 0
                    token['avg_followers'] = 0
                    token['max_followers'] = 0
                    token['top_influencer'] = None
                    
            except Exception as e:
                print(f"Error checking Twitter for {token.get('symbol', 'Unknown')}: {e}")
                # Set default values on error
                token['twitter_mentions'] = 0
                token['twitter_data'] = pd.DataFrame()
                token['total_views'] = 0
                token['total_likes'] = 0
                token['total_retweets'] = 0
                token['avg_followers'] = 0
                token['max_followers'] = 0
                token['top_influencer'] = None
            
            return token
        
        # Use ThreadPoolExecutor for parallel processing
        tokens_with_mentions = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_token = {executor.submit(check_single_token, token): token for token in tokens}
            
            for future in as_completed(future_to_token):
                try:
                    result = future.result(timeout=10)
                    tokens_with_mentions.append(result)
                except Exception as e:
                    # If future fails, still add the token with default values
                    token = future_to_token[future]
                    print(f"Error processing {token.get('symbol', 'Unknown')}: {e}")
                    
                    # Ensure all required fields are present with defaults
                    token['twitter_mentions'] = 0
                    token['twitter_data'] = pd.DataFrame()
                    token['total_views'] = 0
                    token['total_likes'] = 0
                    token['total_retweets'] = 0
                    token['avg_followers'] = 0
                    token['max_followers'] = 0
                    token['top_influencer'] = None
                    
                    tokens_with_mentions.append(token)
        
        return tokens_with_mentions
    
    def discover_trending_tokens(self, minutes_old: int = 3, min_mentions: int = 1) -> pd.DataFrame:
        """Main method to discover and rank new tokens by Twitter mentions"""
        
        print(f"Fetching tokens less than {minutes_old} minutes old...")
        new_tokens = self.get_new_tokens(minutes_old)
        print(f"Found {len(new_tokens)} new tokens")
        
        if not new_tokens:
            return pd.DataFrame()
        
        print("Checking Twitter mentions...")
        tokens_with_mentions = self.check_twitter_mentions(new_tokens)
        
        # Filter out tokens with no mentions if specified
        if min_mentions > 0:
            tokens_with_mentions = [t for t in tokens_with_mentions if t.get('twitter_mentions', 0) >= min_mentions]
        
        if not tokens_with_mentions:
            print("No tokens with Twitter mentions found")
            return pd.DataFrame()
        
        # Convert to DataFrame and sort by mentions
        df = pd.DataFrame(tokens_with_mentions)
        
        # Calculate a trending score (combination of mentions and engagement)
        df['trending_score'] = (
            df['twitter_mentions'] * 10 +
            df.get('total_views', 0) / 1000 +
            df.get('total_likes', 0) * 2 +
            df.get('total_retweets', 0) * 3 +
            df.get('max_followers', 0) / 10000
        )
        
        # Sort by trending score
        df = df.sort_values('trending_score', ascending=False)
        
        print(f"Found {len(df)} tokens with Twitter activity")
        
        return df
    
    def get_mock_trending_tokens(self) -> pd.DataFrame:
        """Return mock data for testing when APIs are not available"""
        mock_tokens = [
            {
                'contract_address': '0x1234567890abcdef1234567890abcdef12345678',
                'symbol': 'MOON',
                'name': 'Moon Coin',
                'chain': 'ethereum',
                'created_at': datetime.now(timezone.utc) - timedelta(minutes=2),
                'liquidity': 50000,
                'market_cap': 100000,
                'price': '0.0001',
                'volume_24h': 25000,
                'twitter_mentions': 45,
                'total_views': 125000,
                'total_likes': 890,
                'total_retweets': 234,
                'trending_score': 1500,
                'top_influencer': {
                    'username': 'cryptowhale',
                    'followers': 50000,
                    'text': 'New gem alert! $MOON just launched...'
                }
            },
            {
                'contract_address': '0xabcdef1234567890abcdef1234567890abcdef12',
                'symbol': 'ROCKET',
                'name': 'Rocket Token',
                'chain': 'bsc',
                'created_at': datetime.now(timezone.utc) - timedelta(minutes=1),
                'liquidity': 75000,
                'market_cap': 150000,
                'price': '0.0002',
                'volume_24h': 40000,
                'twitter_mentions': 32,
                'total_views': 89000,
                'total_likes': 567,
                'total_retweets': 123,
                'trending_score': 980,
                'top_influencer': {
                    'username': 'defiking',
                    'followers': 25000,
                    'text': '$ROCKET taking off! Early gem...'
                }
            },
            {
                'contract_address': 'FAbEFG2tRQYPPN66C1qfcECNHh5dJkwp9odxFHMdBAGS',
                'symbol': 'PEPE2',
                'name': 'Pepe 2.0',
                'chain': 'solana',
                'created_at': datetime.now(timezone.utc) - timedelta(seconds=90),
                'liquidity': 25000,
                'market_cap': 50000,
                'price': '0.00005',
                'volume_24h': 15000,
                'twitter_mentions': 18,
                'total_views': 45000,
                'total_likes': 234,
                'total_retweets': 67,
                'trending_score': 450,
                'top_influencer': {
                    'username': 'solanamaxis',
                    'followers': 15000,
                    'text': 'PEPE2 on Solana pump.fun...'
                }
            }
        ]
        
        return pd.DataFrame(mock_tokens)