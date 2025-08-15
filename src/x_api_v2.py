import tweepy
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
import time
import json

class XAPIv2:
    def __init__(self):
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if bearer_token:
            self.client = tweepy.Client(bearer_token=bearer_token)
        else:
            self.client = None
        
        self.rate_limit_file = 'rate_limits.json'
        self.daily_search_limit = 500  # Adjust based on your API tier
        self.load_rate_limits()
    
    def load_rate_limits(self):
        if os.path.exists(self.rate_limit_file):
            try:
                with open(self.rate_limit_file, 'r') as f:
                    data = json.load(f)
                    saved_date = datetime.fromisoformat(data.get('date', ''))
                    if saved_date.date() == datetime.now().date():
                        self.searches_today = data.get('searches', 0)
                    else:
                        self.searches_today = 0
            except:
                self.searches_today = 0
        else:
            self.searches_today = 0
    
    def save_rate_limits(self):
        data = {
            'date': datetime.now().isoformat(),
            'searches': self.searches_today
        }
        with open(self.rate_limit_file, 'w') as f:
            json.dump(data, f)
    
    def can_search(self) -> bool:
        return self.searches_today < self.daily_search_limit
    
    def increment_search_count(self):
        self.searches_today += 1
        self.save_rate_limits()
    
    def search_tweets(self, contract_address: str, symbol: Optional[str] = None, max_results: int = 100) -> Optional[pd.DataFrame]:
        if not self.client or not self.can_search():
            return None
        
        try:
            query_parts = []
            
            if contract_address:
                query_parts.append(contract_address)
            
            if symbol:
                query_parts.append(f"${symbol}")
            
            if not query_parts:
                return pd.DataFrame()
            
            query = " OR ".join(query_parts)
            query += " -is:retweet"  # Exclude retweets
            
            tweets_data = []
            
            # Search recent tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit is 100 per request
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang'],
                user_fields=['username', 'verified', 'public_metrics'],
                expansions=['author_id']
            )
            
            self.increment_search_count()
            
            if response.data:
                users = {user.id: user for user in response.includes.get('users', [])} if response.includes else {}
                
                for tweet in response.data:
                    author = users.get(tweet.author_id, None)
                    metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                    
                    tweet_info = {
                        'tweet_id': tweet.id,
                        'created_at': tweet.created_at,
                        'text': tweet.text,
                        'author_id': tweet.author_id,
                        'username': author.username if author else 'Unknown',
                        'followers': author.public_metrics.get('followers_count', 0) if author and hasattr(author, 'public_metrics') else 0,
                        'following': author.public_metrics.get('following_count', 0) if author and hasattr(author, 'public_metrics') else 0,
                        'verified': author.verified if author and hasattr(author, 'verified') else False,
                        'retweets': metrics.get('retweet_count', 0),
                        'likes': metrics.get('like_count', 0),
                        'replies': metrics.get('reply_count', 0),
                        'views': metrics.get('impression_count', 0),
                        'lang': tweet.lang if hasattr(tweet, 'lang') else 'en'
                    }
                    
                    tweets_data.append(tweet_info)
            
            if tweets_data:
                df = pd.DataFrame(tweets_data)
                return df.sort_values('created_at', ascending=False)
            else:
                return pd.DataFrame()
                
        except tweepy.TooManyRequests:
            print("Rate limit reached for X API v2")
            self.searches_today = self.daily_search_limit
            self.save_rate_limits()
            return None
        except Exception as e:
            print(f"Error with X API v2: {e}")
            return None