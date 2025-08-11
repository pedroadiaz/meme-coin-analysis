from typing import Dict, Optional, Any
import pandas as pd
from ..twitter_analyzer import TwitterAnalyzer
from ..sentiment_analyzer import SentimentAnalyzer
from ..coin_data_scraper import CoinDataScraper
from ..utils import calculate_risk_score

class MemeCoinAnalyzer:
    def __init__(self):
        self.twitter_analyzer = TwitterAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.coin_scraper = CoinDataScraper()
    
    def analyze_coin(self, contract_address: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        results = {
            'contract_address': contract_address,
            'symbol': symbol,
            'twitter_data': None,
            'sentiment_analysis': None,
            'coin_metrics': None,
            'risk_assessment': None,
            'error': None
        }
        
        try:
            twitter_data = self.fetch_twitter_data(contract_address, symbol)
            results['twitter_data'] = twitter_data
            
            if twitter_data is not None and not twitter_data.empty:
                sentiment_analysis = self.analyze_sentiment(twitter_data)
                results['sentiment_analysis'] = sentiment_analysis
            
            coin_metrics = self.fetch_coin_metrics(contract_address)
            results['coin_metrics'] = coin_metrics
            
            if coin_metrics:
                risk_assessment = self.assess_risk(coin_metrics)
                results['risk_assessment'] = risk_assessment
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def fetch_twitter_data(self, contract_address: str, symbol: Optional[str] = None) -> pd.DataFrame:
        return self.twitter_analyzer.search_tweets(contract_address, symbol)
    
    def analyze_sentiment(self, tweets_df: pd.DataFrame) -> Dict[str, Any]:
        if tweets_df.empty:
            return {}
        
        analyzed_df = self.sentiment_analyzer.analyze_tweets(tweets_df)
        
        metrics = self.sentiment_analyzer.get_aggregate_metrics(analyzed_df)
        
        influencers = self.sentiment_analyzer.identify_influencers(analyzed_df)
        
        timeline = self.sentiment_analyzer.get_sentiment_timeline(analyzed_df)
        
        return {
            'tweets': analyzed_df,
            'metrics': metrics,
            'influencers': influencers,
            'timeline': timeline
        }
    
    def fetch_coin_metrics(self, contract_address: str) -> Dict[str, Any]:
        return self.coin_scraper.get_coin_data(contract_address)
    
    def assess_risk(self, coin_data: Dict[str, Any]) -> Dict[str, Any]:
        return calculate_risk_score(coin_data)
    
    def get_summary_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        stats = {
            'has_twitter_data': False,
            'total_tweets': 0,
            'sentiment_score': 0,
            'positive_ratio': 0,
            'market_cap': 'N/A',
            'risk_level': 'Unknown',
            'top_influencer': None
        }
        
        if results.get('sentiment_analysis'):
            metrics = results['sentiment_analysis'].get('metrics', {})
            stats['has_twitter_data'] = True
            stats['total_tweets'] = metrics.get('total_tweets', 0)
            stats['sentiment_score'] = metrics.get('average_sentiment', 0)
            
            if stats['total_tweets'] > 0:
                positive = metrics.get('positive_count', 0)
                stats['positive_ratio'] = positive / stats['total_tweets']
            
            influencers = results['sentiment_analysis'].get('influencers')
            if influencers is not None and not influencers.empty:
                top = influencers.iloc[0]
                stats['top_influencer'] = {
                    'username': top['username'],
                    'followers': top['followers']
                }
        
        if results.get('coin_metrics'):
            stats['market_cap'] = results['coin_metrics'].get('market_cap', 'N/A')
        
        if results.get('risk_assessment'):
            stats['risk_level'] = results['risk_assessment'].get('level', 'Unknown')
        
        return stats
    
    def cleanup(self):
        if hasattr(self.coin_scraper, 'close'):
            self.coin_scraper.close()