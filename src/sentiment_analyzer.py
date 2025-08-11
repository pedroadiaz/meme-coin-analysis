import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
from typing import Dict, List

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        self.crypto_lexicon = {
            'moon': 3.0,
            'mooning': 3.0,
            'hodl': 2.0,
            'bullish': 2.5,
            'pump': 2.0,
            'gem': 2.0,
            'rocket': 2.0,
            '🚀': 2.0,
            '💎': 1.5,
            '🙌': 1.5,
            'buy': 1.5,
            'long': 1.5,
            'undervalued': 2.0,
            'breakout': 2.0,
            'rug': -3.0,
            'rugpull': -3.0,
            'scam': -3.0,
            'dump': -2.5,
            'bearish': -2.5,
            'crash': -2.5,
            'sell': -1.5,
            'short': -1.5,
            'overvalued': -2.0,
            'ponzi': -3.0,
            'fake': -2.5,
            'warning': -2.0,
            'careful': -1.5,
            'avoid': -2.0
        }
        
        for word, score in self.crypto_lexicon.items():
            self.vader.lexicon[word] = score
    
    def analyze_tweets(self, tweets_df: pd.DataFrame) -> pd.DataFrame:
        if tweets_df.empty:
            return tweets_df
        
        tweets_df = tweets_df.copy()
        
        sentiments = []
        sentiment_scores = []
        
        for text in tweets_df['text']:
            sentiment, score = self._analyze_text(text)
            sentiments.append(sentiment)
            sentiment_scores.append(score)
        
        tweets_df['sentiment'] = sentiments
        tweets_df['sentiment_score'] = sentiment_scores
        
        return tweets_df
    
    def _analyze_text(self, text: str) -> tuple:
        text_cleaned = self._clean_text(text)
        
        vader_scores = self.vader.polarity_scores(text_cleaned)
        compound_score = vader_scores['compound']
        
        try:
            blob = TextBlob(text_cleaned)
            blob_polarity = blob.sentiment.polarity
        except:
            blob_polarity = 0
        
        combined_score = (compound_score * 0.7 + blob_polarity * 0.3)
        
        if combined_score >= 0.1:
            sentiment = 'positive'
        elif combined_score <= -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return sentiment, combined_score
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        text = re.sub(r'@\w+', '', text)
        
        text = re.sub(r'#(\w+)', r'\1', text)
        
        text = re.sub(r'\$([A-Z]+)', r'\1', text)
        
        return text.strip()
    
    def get_aggregate_metrics(self, tweets_df: pd.DataFrame) -> Dict:
        if tweets_df.empty:
            return {
                'total_tweets': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_sentiment': 0,
                'sentiment_distribution': {},
                'engagement_by_sentiment': {}
            }
        
        if 'sentiment' not in tweets_df.columns:
            tweets_df = self.analyze_tweets(tweets_df)
        
        sentiment_counts = tweets_df['sentiment'].value_counts().to_dict()
        
        engagement_by_sentiment = {}
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_tweets = tweets_df[tweets_df['sentiment'] == sentiment]
            if not sentiment_tweets.empty:
                engagement_by_sentiment[sentiment] = {
                    'avg_views': sentiment_tweets['views'].mean(),
                    'avg_retweets': sentiment_tweets['retweets'].mean(),
                    'avg_likes': sentiment_tweets['likes'].mean(),
                    'total_reach': sentiment_tweets['followers'].sum(),
                    'avg_followers': sentiment_tweets['followers'].mean()
                }
            else:
                engagement_by_sentiment[sentiment] = {
                    'avg_views': 0,
                    'avg_retweets': 0,
                    'avg_likes': 0,
                    'total_reach': 0,
                    'avg_followers': 0
                }
        
        return {
            'total_tweets': len(tweets_df),
            'positive_count': sentiment_counts.get('positive', 0),
            'negative_count': sentiment_counts.get('negative', 0),
            'neutral_count': sentiment_counts.get('neutral', 0),
            'average_sentiment': tweets_df['sentiment_score'].mean() if 'sentiment_score' in tweets_df.columns else 0,
            'sentiment_distribution': sentiment_counts,
            'engagement_by_sentiment': engagement_by_sentiment
        }
    
    def identify_influencers(self, tweets_df: pd.DataFrame, min_followers: int = 10000) -> pd.DataFrame:
        if tweets_df.empty:
            return pd.DataFrame()
        
        influencers = tweets_df[tweets_df['followers'] >= min_followers].copy()
        
        if not influencers.empty:
            influencers['influence_score'] = (
                influencers['followers'] * 0.4 +
                influencers['views'] * 0.3 +
                influencers['retweets'] * 0.2 +
                influencers['likes'] * 0.1
            )
            
            return influencers.sort_values('influence_score', ascending=False)
        
        return pd.DataFrame()
    
    def get_sentiment_timeline(self, tweets_df: pd.DataFrame, interval: str = '1H') -> pd.DataFrame:
        if tweets_df.empty or 'created_at' not in tweets_df.columns:
            return pd.DataFrame()
        
        tweets_df = tweets_df.copy()
        tweets_df['created_at'] = pd.to_datetime(tweets_df['created_at'])
        
        timeline = tweets_df.set_index('created_at').resample(interval)['sentiment'].value_counts().unstack(fill_value=0)
        
        return timeline