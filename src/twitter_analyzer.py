import pandas as pd
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
from .twitter_api_io import TwitterAPIio
from .x_api_v2 import XAPIv2

class TwitterAnalyzer:
    def __init__(self):
        self.x_api = XAPIv2()
        self.twitter_api_io = TwitterAPIio()
    
    def search_tweets(self, contract_address: str, symbol: Optional[str] = None, max_results: int = 500) -> pd.DataFrame:
        # Try X API v2 first
        print("Attempting to use X API v2...")
        result = self.x_api.search_tweets(contract_address, symbol, max_results)
        
        if result is not None and not result.empty:
            print(f"Successfully fetched {len(result)} tweets using X API v2")
            return result
        elif result is not None and result.empty:
            print("X API v2 returned no results")
            return result
        else:
            # Fall back to TwitterAPI.io
            print("X API v2 unavailable or rate limited. Falling back to TwitterAPI.io...")
            return self.twitter_api_io.search_tweets(contract_address, symbol, max_results)
    
    def search_advanced(self, query: str, filters: Optional[Dict] = None) -> pd.DataFrame:
        # For advanced search, use TwitterAPI.io directly as X API v2 would need different implementation
        return self.twitter_api_io.search_tweets_advanced(query, filters)
    
    def get_trending_topics(self, location_id: int = 1) -> List[Dict]:
        return self.twitter_api_io.get_trending_topics(location_id)