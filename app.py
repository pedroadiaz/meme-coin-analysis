import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from src.services.meme_coin_analyzer import MemeCoinAnalyzer
from src.utils import validate_contract_address
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Meme Coin Analysis Dashboard",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Meme Coin Analysis Dashboard")
st.markdown("Analyze social sentiment and on-chain metrics for any meme coin")

@st.cache_resource
def get_analyzer():
    return MemeCoinAnalyzer()

def display_twitter_metrics(sentiment_analysis):
    if not sentiment_analysis:
        st.warning("No Twitter data available")
        return
    
    metrics = sentiment_analysis.get('metrics', {})
    tweets_df = sentiment_analysis.get('tweets')
    influencers = sentiment_analysis.get('influencers')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Positive Tweets", metrics.get('positive_count', 0))
        positive_engagement = metrics.get('engagement_by_sentiment', {}).get('positive', {})
        st.metric("Avg Views (Positive)", f"{positive_engagement.get('avg_views', 0):,.0f}")
        st.metric("Avg Retweets (Positive)", f"{positive_engagement.get('avg_retweets', 0):,.0f}")
    
    with col2:
        st.metric("Negative Tweets", metrics.get('negative_count', 0))
        negative_engagement = metrics.get('engagement_by_sentiment', {}).get('negative', {})
        st.metric("Avg Views (Negative)", f"{negative_engagement.get('avg_views', 0):,.0f}")
        st.metric("Avg Retweets (Negative)", f"{negative_engagement.get('avg_retweets', 0):,.0f}")
    
    with col3:
        st.metric("Neutral Tweets", metrics.get('neutral_count', 0))
        total_tweets = metrics.get('total_tweets', 0)
        if total_tweets > 0:
            sentiment_score = ((metrics.get('positive_count', 0) - metrics.get('negative_count', 0)) / total_tweets * 100)
        else:
            sentiment_score = 0
        st.metric("Sentiment Score", f"{sentiment_score:+.1f}%")
    
    if influencers is not None and not influencers.empty:
        st.subheader("Top Influencers")
        st.dataframe(
            influencers[['username', 'followers', 'text', 'sentiment', 'views', 'retweets']].head(10),
            use_container_width=True
        )
    
    if tweets_df is not None and not tweets_df.empty:
        st.subheader("Recent Tweets")
        st.dataframe(
            tweets_df[['created_at', 'username', 'text', 'sentiment', 'views', 'retweets', 'followers']].head(20),
            use_container_width=True
        )

def display_coin_metrics(coin_data, risk_assessment):
    if not coin_data:
        st.warning("Unable to fetch coin data")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Market Cap", f"${coin_data.get('market_cap', 'N/A'):,}" if coin_data.get('market_cap') != 'N/A' else 'N/A')
        st.metric("Price", f"${coin_data.get('price', 'N/A')}" if coin_data.get('price') != 'N/A' else 'N/A')
        st.metric("24h Volume", f"${coin_data.get('volume_24h', 'N/A'):,}" if coin_data.get('volume_24h') != 'N/A' else 'N/A')
        st.metric("Liquidity", f"${coin_data.get('liquidity', 'N/A'):,}" if coin_data.get('liquidity') != 'N/A' else 'N/A')
    
    with col2:
        st.metric("Insider Holdings", f"{coin_data.get('insider_holdings', 'N/A')}%")
        st.metric("Sniper Holdings", f"{coin_data.get('sniper_holdings', 'N/A')}%")
        st.metric("Bundlers", coin_data.get('bundlers', 'N/A'))
        lp_status = "✅ Burned" if coin_data.get('lp_burned') else "❌ Not Burned"
        st.metric("LP Status", lp_status)
    
    if risk_assessment:
        st.subheader(f"Risk Assessment: {risk_assessment['color']} {risk_assessment['level']}")
        st.metric("Risk Score", f"{risk_assessment['score']}/100")
        if risk_assessment.get('factors'):
            st.write("Risk Factors:")
            for factor in risk_assessment['factors']:
                st.write(f"• {factor}")
    
    if 'holders' in coin_data:
        st.subheader("Holder Distribution")
        holders_df = pd.DataFrame(coin_data['holders'])
        st.dataframe(holders_df, use_container_width=True)

def display_visualizations(sentiment_analysis):
    if not sentiment_analysis or sentiment_analysis.get('tweets') is None or sentiment_analysis.get('tweets').empty:
        st.info("No data available for visualization")
        return
    
    tweets_df = sentiment_analysis['tweets']
    
    col1, col2 = st.columns(2)
    
    with col1:
        sentiment_counts = tweets_df['sentiment'].value_counts()
        fig_pie = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Sentiment Distribution",
            color_discrete_map={'positive': '#00cc44', 'negative': '#ff3333', 'neutral': '#808080'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        sentiment_by_influence = tweets_df.groupby('sentiment').agg({
            'followers': 'sum',
            'views': 'sum',
            'retweets': 'sum'
        }).reset_index()
        
        fig_bar = px.bar(
            sentiment_by_influence,
            x='sentiment',
            y=['followers', 'views', 'retweets'],
            title="Engagement by Sentiment",
            barmode='group'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    timeline = sentiment_analysis.get('timeline')
    if timeline is not None and not timeline.empty:
        fig_timeline = go.Figure()
        for sentiment in timeline.columns:
            color = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}.get(sentiment, 'blue')
            fig_timeline.add_trace(go.Scatter(
                x=timeline.index,
                y=timeline[sentiment],
                mode='lines',
                name=sentiment.capitalize(),
                line=dict(color=color)
            ))
        
        fig_timeline.update_layout(
            title="Sentiment Timeline",
            xaxis_title="Time",
            yaxis_title="Number of Tweets",
            hovermode='x unified'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

def main():
    analyzer = get_analyzer()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        contract_address = st.text_input(
            "Enter Meme Coin Contract Address:",
            placeholder="0x...",
            help="Enter the contract address of the meme coin you want to analyze"
        )
    
    with col2:
        symbol = st.text_input(
            "Token Symbol (optional):",
            placeholder="PEPE, SHIB, etc.",
            help="Enter the token symbol for better Twitter search results"
        )
    
    if st.button("🔍 Analyze", type="primary"):
        if not contract_address:
            st.error("Please enter a contract address")
            return
        
        if not validate_contract_address(contract_address):
            st.error("Invalid contract address format. CA length is: " + str(len(contract_address)))
            return
        
        with st.spinner("Fetching and analyzing data..."):
            results = analyzer.analyze_coin(contract_address, symbol)
            
            if results.get('error'):
                st.error(f"Analysis error: {results['error']}")
                return
            
            tab1, tab2, tab3 = st.tabs(["📊 Twitter Analysis", "💹 Coin Metrics", "📈 Visualizations"])
            
            with tab1:
                st.subheader("Twitter Sentiment Analysis")
                display_twitter_metrics(results.get('sentiment_analysis'))
            
            with tab2:
                st.subheader("On-Chain Metrics")
                display_coin_metrics(
                    results.get('coin_metrics'),
                    results.get('risk_assessment')
                )
            
            with tab3:
                st.subheader("Data Visualizations")
                display_visualizations(results.get('sentiment_analysis'))

with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This dashboard analyzes meme coins by:
    - Searching Twitter for mentions
    - Analyzing sentiment of tweets
    - Fetching on-chain metrics
    - Visualizing engagement data
    
    **Requirements:**
    - Valid contract address
    - TwitterAPI.io API key (.env file)
    """)
    
    st.header("⚙️ Settings")
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache cleared!")
    
    st.header("📊 Data Sources")
    st.markdown("""
    - **Twitter**: TwitterAPI.io
    - **DexScreener**: Token metrics
    - **On-chain**: Direct blockchain data
    """)
    
    api_status = "✅ Connected" if os.getenv('TWITTERAPI_IO_KEY') else "❌ Not configured"
    st.markdown(f"**API Status**: {api_status}")

if __name__ == "__main__":
    main()