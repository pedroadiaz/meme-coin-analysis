# Meme Coin Analysis Dashboard

A modular application for analyzing meme coins through Twitter sentiment analysis and on-chain metrics. Available as both a Streamlit dashboard and FastAPI backend.

## Features

- **Twitter Analysis**: Search for coin mentions by contract address or symbol
- **Sentiment Analysis**: Classify tweets as positive, negative, or neutral with crypto-specific lexicon
- **Engagement Metrics**: Track views, retweets, and follower counts
- **On-Chain Data**: Market cap, liquidity, insider holdings, LP burn status
- **Risk Assessment**: Automated risk scoring based on multiple factors
- **Data Visualization**: Interactive charts and metrics dashboard
- **Modular Architecture**: Separated business logic for easy framework switching

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd meme-coin-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up TwitterAPI.io credentials:
```bash
cp .env.example .env
# Edit .env with your TwitterAPI.io key
```

## Usage

### Single Token Analysis
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

### Trending Token Discovery
```bash
streamlit run app_trending.py
```
Opens at `http://localhost:8501`

### FastAPI Server
```bash
python api_server.py
# or
uvicorn api_server:app --reload
```
API available at `http://localhost:8000`
Documentation at `http://localhost:8000/docs`

## TwitterAPI.io Setup

1. Get an API key from [TwitterAPI.io](https://twitterapi.io)
2. Add to `.env` file:
   - TWITTERAPI_IO_KEY=your_key_here

## How It Works

1. **Input**: Enter a meme coin contract address (e.g., `0x...`)
2. **Twitter Search**: Searches for mentions of the contract or token symbol
3. **Sentiment Analysis**: Uses VADER and TextBlob for crypto-specific sentiment
4. **Web Scraping**: Fetches on-chain data from DexScreener
5. **Risk Analysis**: Calculates risk score based on:
   - Insider holdings percentage
   - Sniper wallet activity
   - Bundler presence
   - LP burn status

## Mock Data

The application includes mock data for testing without API credentials:
- Twitter data: Sample tweets with various sentiments
- Coin data: Example metrics and holdings

## Technologies Used

- **Streamlit**: Web application framework
- **Tweepy**: Twitter API integration
- **VADER Sentiment**: Sentiment analysis
- **BeautifulSoup/Selenium**: Web scraping
- **Plotly**: Data visualization
- **Pandas**: Data manipulation

## Risk Indicators

- 🟢 **Low Risk**: Score < 40
- 🟡 **Medium Risk**: Score 40-70
- 🔴 **High Risk**: Score > 70

## Note

This tool is for educational and research purposes only. Always do your own research before making investment decisions.