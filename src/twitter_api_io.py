import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
import time

class TwitterAPIio:
    def __init__(self):
        self.api_key = os.getenv('TWITTERAPI_IO_KEY')
        self.base_url = "https://api.twitterapi.io/twitter"
        self.headers = {
            'X-API-Key': self.api_key if self.api_key else '',
            'Content-Type': 'application/json'
        }
    
    def search_tweets(self, contract_address: str, symbol: Optional[str] = None, max_results: int = 500) -> pd.DataFrame:
        try:
            if not self.api_key:
                print("TwitterAPI.io API key not configured. Using mock data.")
                return self._get_mock_data()
            
            query_parts = []
            
            if contract_address:
                query_parts.append(contract_address)
            
            # Only search for symbol with $ prefix to avoid common words
            if symbol:
                query_parts.append(f"${symbol}")
            
            if not query_parts:
                return pd.DataFrame()
        except Exception as e:
            print(f"Error building query: {e}")
            return pd.DataFrame()
        
        query = " OR ".join(query_parts)
        
        try:
            endpoint = f"{self.base_url}/tweet/advanced_search"
            all_tweets_data = []
            next_cursor = None
            page_count = 0
            max_pages = 10  # Limit to prevent infinite loops
            
            while page_count < max_pages:
                params = {
                    'query': query,
                    'queryType': 'Latest'
                }
                
                # Add cursor for pagination if we have one
                if next_cursor:
                    params['cursor'] = next_cursor
                
                response = requests.get(endpoint, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get('tweets', [])
                    
                    # If no tweets, break
                    if not tweets:
                        break
                    
                    print(f"Page {page_count + 1}: Fetched {len(tweets)} tweets")
                    
                    # Process tweets
                    for tweet in tweets:
                        author = tweet.get('author', {})
                        
                        # Parse the createdAt date string
                        created_at_str = tweet.get('createdAt', '')
                        try:
                            created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                        except:
                            created_at = datetime.now()
                        
                        tweet_info = {
                            'tweet_id': tweet.get('id'),
                            'created_at': created_at,
                            'text': tweet.get('text', ''),
                            'author_id': author.get('id'),
                            'username': author.get('userName', 'Unknown'),
                            'followers': author.get('followers', 0),
                            'following': author.get('following', 0),
                            'verified': author.get('isVerified', False) or author.get('isBlueVerified', False),
                            'retweets': tweet.get('retweetCount', 0),
                            'likes': tweet.get('likeCount', 0),
                            'replies': tweet.get('replyCount', 0),
                            'views': tweet.get('viewCount', 0),
                            'lang': tweet.get('lang', 'en')
                        }
                        
                        all_tweets_data.append(tweet_info)
                    
                    # Check if we've reached the max results
                    if len(all_tweets_data) >= max_results:
                        print(f"Reached max results limit ({max_results})")
                        break
                    
                    # Check for next page
                    has_next_page = data.get('has_next_page', False)
                    next_cursor = data.get('next_cursor')
                    
                    if not has_next_page or not next_cursor:
                        print("No more pages available")
                        break
                    
                    page_count += 1
                    time.sleep(0.5)  # Small delay to avoid rate limiting
                
                else:
                    print(f"Error fetching page {page_count + 1}: {response.status_code}")
                    break
            
            if all_tweets_data:
                df = pd.DataFrame(all_tweets_data)
                print(f"Total tweets fetched: {len(df)}")
                return df.sort_values('created_at', ascending=False)
            else:
                print("No tweets found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            # Always return a DataFrame, never None
            try:
                return self._get_mock_data()
            except:
                return pd.DataFrame()
    
    def search_tweets_advanced(self, query: str, filters: Optional[Dict] = None) -> pd.DataFrame:
        if not self.api_key:
            return self._get_mock_data()
        
        try:
            endpoint = f"{self.base_url}/tweet/advanced_search"
            
            params = {
                'query': query,
                'max_results': 100
            }
            
            if filters:
                if 'from_date' in filters:
                    params['start_time'] = filters['from_date']
                if 'to_date' in filters:
                    params['end_time'] = filters['to_date']
                if 'min_likes' in filters:
                    params['min_likes'] = filters['min_likes']
                if 'min_retweets' in filters:
                    params['min_retweets'] = filters['min_retweets']
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tweets = data.get('tweets', [])
                
                tweets_data = []
                for tweet in tweets:
                    author = tweet.get('author', {})
                    
                    # Parse the createdAt date string
                    created_at_str = tweet.get('createdAt', '')
                    try:
                        created_at = datetime.strptime(created_at_str, '%a %b %d %H:%M:%S %z %Y')
                    except:
                        created_at = datetime.now()
                    
                    tweet_info = {
                        'tweet_id': tweet.get('id'),
                        'created_at': created_at,
                        'text': tweet.get('text', ''),
                        'author_id': author.get('id'),
                        'username': author.get('userName', 'Unknown'),
                        'followers': author.get('followers', 0),
                        'following': author.get('following', 0),
                        'verified': author.get('isVerified', False) or author.get('isBlueVerified', False),
                        'retweets': tweet.get('retweetCount', 0),
                        'likes': tweet.get('likeCount', 0),
                        'replies': tweet.get('replyCount', 0),
                        'views': tweet.get('viewCount', 0),
                        'lang': tweet.get('lang', 'en')
                    }
                    
                    tweets_data.append(tweet_info)
                
                df = pd.DataFrame(tweets_data)
                return df.sort_values('created_at', ascending=False)
            
            else:
                return self._get_mock_data()
                
        except Exception as e:
            print(f"Error in advanced search: {e}")
            return self._get_mock_data()
    
    def get_trending_topics(self, location_id: int = 1) -> List[Dict]:
        if not self.api_key:
            return []
        
        try:
            endpoint = f"{self.base_url}/trends/place"
            params = {'id': location_id}
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                trends = data[0].get('trends', []) if data else []
                return trends[:10]
            
            return []
            
        except Exception as e:
            print(f"Error fetching trends: {e}")
            return []
    
    def _get_mock_data(self) -> pd.DataFrame:
        mock_tweets = [
            {
                'tweet_id': '1',
                'created_at': datetime.now() - timedelta(hours=1),
                'text': 'Just bought some of this new meme coin! To the moon! 🚀',
                'author_id': 'user1',
                'username': 'cryptotrader1',
                'followers': 5432,
                'following': 234,
                'verified': False,
                'retweets': 45,
                'likes': 123,
                'replies': 12,
                'views': 8934,
                'lang': 'en'
            },
            {
                'tweet_id': '2',
                'created_at': datetime.now() - timedelta(hours=2),
                'text': 'This coin is definitely a scam, be careful everyone!',
                'author_id': 'user2',
                'username': 'defiexpert',
                'followers': 12543,
                'following': 543,
                'verified': True,
                'retweets': 234,
                'likes': 456,
                'replies': 89,
                'views': 45632,
                'lang': 'en'
            },
            {
                'tweet_id': '3',
                'created_at': datetime.now() - timedelta(hours=3),
                'text': 'Interesting tokenomics on this one. Worth keeping an eye on.',
                'author_id': 'user3',
                'username': 'tokenanalyst',
                'followers': 8932,
                'following': 123,
                'verified': False,
                'retweets': 67,
                'likes': 234,
                'replies': 23,
                'views': 12456,
                'lang': 'en'
            },
            {
                'tweet_id': '4',
                'created_at': datetime.now() - timedelta(hours=4),
                'text': 'HODL gang where you at? This is going to explode! 💎🙌',
                'author_id': 'user4',
                'username': 'memecoinlord',
                'followers': 23456,
                'following': 876,
                'verified': False,
                'retweets': 567,
                'likes': 1234,
                'replies': 234,
                'views': 87654,
                'lang': 'en'
            },
            {
                'tweet_id': '5',
                'created_at': datetime.now() - timedelta(hours=5),
                'text': 'Rug pull alert! Dev wallets hold 40% of supply.',
                'author_id': 'user5',
                'username': 'chainalysis',
                'followers': 45678,
                'following': 234,
                'verified': True,
                'retweets': 890,
                'likes': 2345,
                'replies': 456,
                'views': 234567,
                'lang': 'en'
            },
            {
                'tweet_id': '6',
                'created_at': datetime.now() - timedelta(hours=6),
                'text': 'Bullish on this project! Great community and solid roadmap.',
                'author_id': 'user6',
                'username': 'altcoinhunter',
                'followers': 18234,
                'following': 456,
                'verified': False,
                'retweets': 234,
                'likes': 678,
                'replies': 45,
                'views': 56789,
                'lang': 'en'
            },
            {
                'tweet_id': '7',
                'created_at': datetime.now() - timedelta(hours=7),
                'text': 'Stay away from this token. Classic pump and dump scheme.',
                'author_id': 'user7',
                'username': 'cryptodetective',
                'followers': 34567,
                'following': 123,
                'verified': True,
                'retweets': 456,
                'likes': 890,
                'replies': 123,
                'views': 123456,
                'lang': 'en'
            },
            {
                'tweet_id': '8',
                'created_at': datetime.now() - timedelta(hours=8),
                'text': 'Loading my bags here. Risk/reward looks good.',
                'author_id': 'user8',
                'username': 'degen_trader',
                'followers': 9876,
                'following': 567,
                'verified': False,
                'retweets': 123,
                'likes': 345,
                'replies': 34,
                'views': 34567,
                'lang': 'en'
            }
        ]
        
        return pd.DataFrame(mock_tweets)