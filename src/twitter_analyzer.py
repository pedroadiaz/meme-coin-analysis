import pandas as pd
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional
from .twitter_api_io import TwitterAPIio

class TwitterAnalyzer:
    def __init__(self):
        self.api_client = TwitterAPIio()
    
    def search_tweets(self, contract_address: str, symbol: Optional[str] = None, max_results: int = 500) -> pd.DataFrame:
        return self.api_client.search_tweets(contract_address, symbol, max_results)
    
    def search_advanced(self, query: str, filters: Optional[Dict] = None) -> pd.DataFrame:
        return self.api_client.search_tweets_advanced(query, filters)
    
    def get_trending_topics(self, location_id: int = 1) -> List[Dict]:
        return self.api_client.get_trending_topics(location_id)