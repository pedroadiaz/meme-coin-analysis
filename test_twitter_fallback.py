#!/usr/bin/env python3
"""
Test script to verify X API v2 with TwitterAPI.io fallback functionality
"""

from src.twitter_analyzer import TwitterAnalyzer
import os
from dotenv import load_dotenv

def test_fallback():
    # Load environment variables
    load_dotenv()
    
    print("=" * 60)
    print("Testing Twitter API Fallback Mechanism")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = TwitterAnalyzer()
    
    # Test search with a sample contract address
    test_contract = "0x1234567890abcdef"  # Example contract
    test_symbol = "TEST"
    
    print(f"\nSearching for contract: {test_contract}")
    print(f"Symbol: {test_symbol}")
    print("-" * 40)
    
    # Perform search (will try X API v2 first, then fallback to TwitterAPI.io)
    results = analyzer.search_tweets(test_contract, test_symbol, max_results=10)
    
    if not results.empty:
        print(f"\n✓ Successfully retrieved {len(results)} tweets")
        print("\nFirst 3 tweets:")
        for idx, row in results.head(3).iterrows():
            print(f"\n  Tweet {idx + 1}:")
            print(f"    User: @{row['username']}")
            print(f"    Text: {row['text'][:100]}...")
            print(f"    Likes: {row['likes']} | Retweets: {row['retweets']}")
    else:
        print("\n✗ No tweets found")
    
    # Check rate limit status
    print("\n" + "=" * 60)
    print("Rate Limit Status:")
    print("-" * 40)
    
    if hasattr(analyzer.x_api, 'searches_today'):
        print(f"X API v2 searches today: {analyzer.x_api.searches_today}/{analyzer.x_api.daily_search_limit}")
        if analyzer.x_api.searches_today >= analyzer.x_api.daily_search_limit:
            print("  ⚠️  Daily limit reached - using TwitterAPI.io fallback")
        else:
            print("  ✓ X API v2 available")
    
    # Check API configurations
    print("\n" + "=" * 60)
    print("API Configuration Status:")
    print("-" * 40)
    
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    twitterapi_key = os.getenv('TWITTERAPI_IO_KEY')
    
    if bearer_token and bearer_token != 'your_twitter_bearer_token_here':
        print("✓ X API v2 Bearer Token: Configured")
    else:
        print("✗ X API v2 Bearer Token: Not configured (will use TwitterAPI.io)")
    
    if twitterapi_key:
        print("✓ TwitterAPI.io Key: Configured")
    else:
        print("✗ TwitterAPI.io Key: Not configured")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_fallback()