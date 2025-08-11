from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from src.services.meme_coin_analyzer import MemeCoinAnalyzer
from src.utils import validate_contract_address
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Meme Coin Analysis API",
    description="API for analyzing meme coins through Twitter sentiment and on-chain metrics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = MemeCoinAnalyzer()

class AnalysisRequest(BaseModel):
    contract_address: str
    symbol: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "name": "Meme Coin Analysis API",
        "version": "1.0.0",
        "status": "running",
        "api_configured": bool(os.getenv('TWITTERAPI_IO_KEY'))
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_coin(request: AnalysisRequest):
    try:
        if not validate_contract_address(request.contract_address):
            raise HTTPException(status_code=400, detail="Invalid contract address format")
        
        results = analyzer.analyze_coin(request.contract_address, request.symbol)
        
        if results.get('error'):
            return AnalysisResponse(
                success=False,
                error=results['error']
            )
        
        summary = analyzer.get_summary_stats(results)
        
        response_data = {
            'contract_address': request.contract_address,
            'symbol': request.symbol,
            'summary': summary,
            'twitter_analysis': {
                'metrics': results['sentiment_analysis'].get('metrics') if results.get('sentiment_analysis') else None,
                'top_influencers': results['sentiment_analysis']['influencers'].head(5).to_dict('records') if results.get('sentiment_analysis') and not results['sentiment_analysis']['influencers'].empty else [],
                'recent_tweets': results['sentiment_analysis']['tweets'].head(10).to_dict('records') if results.get('sentiment_analysis') and not results['sentiment_analysis']['tweets'].empty else []
            } if results.get('sentiment_analysis') else None,
            'coin_metrics': results.get('coin_metrics'),
            'risk_assessment': results.get('risk_assessment')
        }
        
        return AnalysisResponse(
            success=True,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=str(e)
        )

@app.get("/twitter/search")
async def search_twitter(query: str, limit: int = 50):
    try:
        tweets = analyzer.twitter_analyzer.api_client.search_tweets(query, None, limit)
        
        if tweets.empty:
            return {
                "success": True,
                "count": 0,
                "tweets": []
            }
        
        return {
            "success": True,
            "count": len(tweets),
            "tweets": tweets.to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/coin/{contract_address}")
async def get_coin_data(contract_address: str):
    try:
        if not validate_contract_address(contract_address):
            raise HTTPException(status_code=400, detail="Invalid contract address format")
        
        coin_data = analyzer.fetch_coin_metrics(contract_address)
        
        if not coin_data:
            raise HTTPException(status_code=404, detail="Coin data not found")
        
        risk_assessment = analyzer.assess_risk(coin_data)
        
        return {
            "success": True,
            "data": {
                "metrics": coin_data,
                "risk": risk_assessment
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api_key_configured": bool(os.getenv('TWITTERAPI_IO_KEY'))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)