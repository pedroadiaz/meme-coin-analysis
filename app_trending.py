import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone
from src.token_discovery import TokenDiscovery
from src.services.meme_coin_analyzer import MemeCoinAnalyzer
from src.utils import validate_contract_address, format_number, get_time_ago
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Trending Token Discovery",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Trending Token Discovery")
st.markdown("Discover new tokens with Twitter buzz - Updated every refresh")

@st.cache_resource
def get_discovery_service():
    return TokenDiscovery()

@st.cache_resource
def get_analyzer():
    return MemeCoinAnalyzer()

def display_token_card(token):
    """Display a single token card with key metrics"""
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.markdown(f"### {token.get('symbol', 'Unknown')} - {token.get('name', 'Unknown')}")
            st.caption(f"Chain: {token.get('chain', 'Unknown').title()} | {get_time_ago(token.get('created_at'))}")
            
            # Show top influencer if available
            if 'top_influencer' in token and token['top_influencer']:
                influencer = token['top_influencer']
                st.markdown(f"💬 **Top mention:** @{influencer['username']} ({format_number(influencer['followers'])} followers)")
                st.caption(f"_{influencer['text']}_")
        
        with col2:
            st.metric("🐦 Mentions", token.get('twitter_mentions', 0))
            st.metric("👁 Total Views", format_number(token.get('total_views', 0)))
        
        with col3:
            st.metric("💰 Market Cap", f"${format_number(token.get('market_cap', 0))}")
            st.metric("💧 Liquidity", f"${format_number(token.get('liquidity', 0))}")
        
        with col4:
            st.metric("❤️ Likes", format_number(token.get('total_likes', 0)))
            st.metric("🔄 Retweets", format_number(token.get('total_retweets', 0)))
        
        with col5:
            st.metric("📊 Volume 24h", f"${format_number(token.get('volume_24h', 0))}")
            if st.button("Analyze", key=f"analyze_{token.get('contract_address')}", type="primary"):
                st.session_state['selected_token'] = token
                st.session_state['show_analysis'] = True
                st.rerun()
        
        st.divider()

def display_detailed_analysis(token, analyzer):
    """Display detailed analysis for a selected token"""
    st.markdown(f"## 📊 Detailed Analysis: {token.get('symbol')} ({token.get('name')})")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Contract: `{token.get('contract_address')}`")
    with col2:
        if st.button("← Back to List", type="secondary"):
            st.session_state['show_analysis'] = False
            st.rerun()
    
    with st.spinner("Performing detailed analysis..."):
        # Use the existing analyzer
        results = analyzer.analyze_coin(
            token.get('contract_address'),
            token.get('symbol')
        )
        
        if results.get('error'):
            st.error(f"Analysis error: {results['error']}")
            return
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Twitter Analysis", "💹 Token Metrics", "📈 Visualizations", "📋 Raw Data"])
        
        with tab1:
            if results.get('sentiment_analysis'):
                sentiment_data = results['sentiment_analysis']
                metrics = sentiment_data.get('metrics', {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Tweets", metrics.get('total_tweets', 0))
                with col2:
                    st.metric("Positive", metrics.get('positive_count', 0))
                with col3:
                    st.metric("Negative", metrics.get('negative_count', 0))
                with col4:
                    st.metric("Neutral", metrics.get('neutral_count', 0))
                
                # Show recent tweets if available
                if 'tweets' in sentiment_data and not sentiment_data['tweets'].empty:
                    st.subheader("Recent Tweets")
                    tweets_display = sentiment_data['tweets'][['created_at', 'username', 'text', 'sentiment', 'followers', 'views']].head(10)
                    st.dataframe(tweets_display, use_container_width=True)
            else:
                st.info("No Twitter data available")
        
        with tab2:
            st.subheader("Token Information")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Chain", token.get('chain', 'Unknown').title())
                st.metric("Market Cap", f"${format_number(token.get('market_cap', 0))}")
                st.metric("Liquidity", f"${format_number(token.get('liquidity', 0))}")
                st.metric("Price", token.get('price', 'N/A'))
            
            with col2:
                st.metric("Volume 24h", f"${format_number(token.get('volume_24h', 0))}")
                st.metric("Price Change 24h", f"{token.get('price_change_24h', 0):.2f}%")
                st.metric("Source", token.get('source', 'Unknown'))
                st.metric("DEX", token.get('dex', 'Unknown'))
            
            # Show coin metrics if available
            if results.get('coin_metrics'):
                st.subheader("On-Chain Metrics")
                coin_metrics = results['coin_metrics']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Insider Holdings", f"{coin_metrics.get('insider_holdings', 'N/A')}%")
                    st.metric("Sniper Holdings", f"{coin_metrics.get('sniper_holdings', 'N/A')}%")
                
                with col2:
                    st.metric("Bundlers", coin_metrics.get('bundlers', 'N/A'))
                    lp_status = "✅ Burned" if coin_metrics.get('lp_burned') else "❌ Not Burned"
                    st.metric("LP Status", lp_status)
        
        with tab3:
            if results.get('sentiment_analysis') and 'tweets' in results['sentiment_analysis']:
                tweets_df = results['sentiment_analysis']['tweets']
                
                if not tweets_df.empty:
                    # Sentiment distribution
                    sentiment_counts = tweets_df['sentiment'].value_counts()
                    fig_pie = px.pie(
                        values=sentiment_counts.values,
                        names=sentiment_counts.index,
                        title="Sentiment Distribution",
                        color_discrete_map={'positive': '#00cc44', 'negative': '#ff3333', 'neutral': '#808080'}
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Engagement over time
                    tweets_df['created_at'] = pd.to_datetime(tweets_df['created_at'])
                    timeline = tweets_df.set_index('created_at').resample('15min').size()
                    
                    fig_timeline = px.line(
                        x=timeline.index,
                        y=timeline.values,
                        title="Tweet Activity Timeline",
                        labels={'x': 'Time', 'y': 'Number of Tweets'}
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
        
        with tab4:
            st.json(token)

def main():
    discovery = get_discovery_service()
    analyzer = get_analyzer()
    
    # Initialize session state
    if 'tokens_df' not in st.session_state:
        st.session_state['tokens_df'] = pd.DataFrame()
    if 'show_analysis' not in st.session_state:
        st.session_state['show_analysis'] = False
    if 'last_refresh' not in st.session_state:
        st.session_state['last_refresh'] = None
    
    # Check if we should show detailed analysis
    if st.session_state.get('show_analysis') and st.session_state.get('selected_token'):
        display_detailed_analysis(st.session_state['selected_token'], analyzer)
        return
    
    # Main controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        minutes_old = st.number_input(
            "Max age (minutes)",
            min_value=1,
            max_value=60,
            value=3,
            help="Find tokens created within the last X minutes"
        )
    
    with col2:
        min_mentions = st.number_input(
            "Min mentions",
            min_value=0,
            max_value=100,
            value=1,
            help="Minimum Twitter mentions required"
        )
    
    with col3:
        use_mock = st.checkbox(
            "Use mock data",
            value=not bool(os.getenv('TWITTERAPI_IO_KEY')),
            help="Use mock data for testing"
        )
    
    with col4:
        col4_1, col4_2 = st.columns(2)
        with col4_1:
            if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
                with st.spinner("Discovering trending tokens..."):
                    if use_mock:
                        st.session_state['tokens_df'] = discovery.get_mock_trending_tokens()
                    else:
                        st.session_state['tokens_df'] = discovery.discover_trending_tokens(
                            minutes_old=minutes_old,
                            min_mentions=min_mentions
                        )
                    st.session_state['last_refresh'] = datetime.now(timezone.utc)
                    st.success(f"Found {len(st.session_state['tokens_df'])} trending tokens!")
        
        with col4_2:
            if st.session_state.get('last_refresh'):
                st.caption(f"Last refresh: {get_time_ago(st.session_state['last_refresh'])}")
    
    # Display tokens
    if not st.session_state['tokens_df'].empty:
        st.markdown("---")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Tokens", len(st.session_state['tokens_df']))
        with col2:
            total_mentions = st.session_state['tokens_df']['twitter_mentions'].sum()
            st.metric("Total Mentions", total_mentions)
        with col3:
            avg_mentions = st.session_state['tokens_df']['twitter_mentions'].mean()
            st.metric("Avg Mentions", f"{avg_mentions:.1f}")
        with col4:
            total_volume = st.session_state['tokens_df']['volume_24h'].sum()
            st.metric("Total Volume", f"${format_number(total_volume)}")
        
        st.markdown("---")
        st.subheader("🏆 Trending Tokens (Ranked by Twitter Activity)")
        
        # Display each token as a card
        for _, token in st.session_state['tokens_df'].iterrows():
            display_token_card(token.to_dict())
    
    else:
        st.info("👆 Click 'Refresh Data' to discover trending tokens")
        
        # Show instructions
        with st.expander("ℹ️ How it works"):
            st.markdown("""
            1. **Token Discovery**: Scans DexScreener and Pump.fun for new token launches
            2. **Twitter Analysis**: Checks each token for Twitter mentions
            3. **Ranking**: Sorts tokens by engagement (mentions, views, retweets)
            4. **Deep Dive**: Click 'Analyze' on any token for detailed analysis
            
            **Tips:**
            - Lower the "Max age" to find only the newest launches
            - Increase "Min mentions" to filter for tokens with more buzz
            - Refresh regularly to catch new opportunities
            """)

# Sidebar
with st.sidebar:
    st.header("🔥 Trending Tokens")
    st.markdown("""
    Discover new token launches with social momentum.
    
    **Data Sources:**
    - Moralis API (Pump.fun)
    - Twitter/X API
    
    **Metrics Tracked:**
    - Twitter mentions
    - Engagement (views, likes, RT)
    - Influencer activity
    - Market data
    """)
    
    st.divider()
    
    twitter_status = "✅ Connected" if os.getenv('TWITTERAPI_IO_KEY') else "❌ Not configured"
    moralis_status = "✅ Connected" if os.getenv('MORALIS_API_KEY') else "❌ Not configured"
    st.markdown(f"**Twitter API**: {twitter_status}")
    st.markdown(f"**Moralis API**: {moralis_status}")
    
    st.divider()
    
    st.caption("💡 Pro tip: Tokens with high Twitter activity in the first few minutes often see rapid price movement")

if __name__ == "__main__":
    main()