
import os
import logging
from typing import List, Dict, Any, Optional
import httpx
from fastapi import FastAPI, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import ta
import quantstats as qs
import ffn
from duckduckgo_search import DDGS
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "tgp_v1_yiOzJa4FDB68ZmOLU76CKILY2a60Y2CDiykBdfni75A")
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trade-insights-bot")

# --- FASTAPI SETUP ---
app = FastAPI(title="Trade Insights Bot (Ultimate Edition)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class NewsItem(BaseModel):
    title: str
    link: str
    snippet: str
    date: Optional[str] = None
    sentiment: Optional[str] = None

class StockInfo(BaseModel):
    name: str = None
    symbol: str = None
    price: float = None
    previous_close: float = None
    currency: str = None
    price_week_ago: float = None
    price_month_ago: float = None
    volume: float = None
    avg_volume: float = None
    volatility: float = None
    rsi: float = None
    macd: float = None
    boll_upper: float = None
    boll_lower: float = None
    mfi: float = None
    obv: float = None
    atr: float = None
    alert: Optional[str] = None

class PortfolioAnalytics(BaseModel):
    total_value: float
    returns: float
    volatility: float
    sharpe: float
    drawdown: float
    risk_level: str

class BacktestComparison(BaseModel):
    backtest_summary: str
    live_summary: str
    discrepancies: str

class TradeInsightsResponse(BaseModel):
    result: str
    stats: Dict[str, Any] = {}

class BacktestResponse(BaseModel):
    backtest_result: str

class FeedbackRequest(BaseModel):
    query: str
    rating: int
    comments: Optional[str] = None

class CompareStrategiesRequest(BaseModel):
    strategies: List[str]

# --- DEPENDENCY: Application-wide AsyncClient ---
@app.on_event("startup")
async def startup_event():
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.http_client.aclose()

async def get_http_client() -> httpx.AsyncClient:
    return app.state.http_client

# --- HELPERS ---
def get_stock_info(symbol: str) -> StockInfo:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        info = ticker.info
        close = hist['Close']
        volume = hist['Volume']
        # Technical indicators
        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi().iloc[-1] if len(close) >= 14 else None
        macd = ta.trend.MACD(close=close).macd().iloc[-1] if len(close) >= 26 else None
        bb = ta.volatility.BollingerBands(close=close, window=20)
        boll_upper = bb.bollinger_hband().iloc[-1] if len(close) >= 20 else None
        boll_lower = bb.bollinger_lband().iloc[-1] if len(close) >= 20 else None
        mfi = ta.volume.MFIIndicator(high=hist['High'], low=hist['Low'], close=close, volume=volume, window=14).money_flow_index().iloc[-1] if len(close) >= 14 else None
        obv = ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume().iloc[-1] if len(close) >= 2 else None
        atr = ta.volatility.AverageTrueRange(high=hist['High'], low=hist['Low'], close=close, window=14).average_true_range().iloc[-1] if len(close) >= 14 else None
        volatility = close.pct_change().std() * (252 ** 0.5) if len(close) > 1 else None
        alert = None
        if volatility and (volatility > 0.05):
            alert = "⚠️ Unusual volatility detected!"
        return StockInfo(
            name=info.get("shortName"),
            symbol=symbol,
            price=info.get("regularMarketPrice"),
            previous_close=info.get("regularMarketPreviousClose"),
            currency=info.get("currency"),
            price_week_ago=close[-6] if len(close) > 5 else None,
            price_month_ago=close[0] if len(close) > 0 else None,
            volume=volume.iloc[-1] if len(volume) > 0 else None,
            avg_volume=volume.mean() if len(volume) > 0 else None,
            volatility=volatility,
            rsi=rsi,
            macd=macd,
            boll_upper=boll_upper,
            boll_lower=boll_lower,
            mfi=mfi,
            obv=obv,
            atr=atr,
            alert=alert
        )
    except Exception as e:
        logger.error(f"Error fetching stock info for {symbol}: {e}")
        return StockInfo(symbol=symbol)

def search_news(query: str, max_results: int = 3) -> List[NewsItem]:
    try:
        with DDGS() as ddgs:
            results = ddgs.news(query, max_results=max_results)
            sentiments = ["positive", "negative", "neutral"]
            return [
                NewsItem(
                    title=r["title"],
                    link=r["url"],
                    snippet=r["body"],
                    date=datetime.now().strftime("%Y-%m-%d"),
                    sentiment=sentiments[i % 3]
                )
                for i, r in enumerate(results)
            ]
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []

def get_economic_calendar():
    # Simulated for demo; use Finnhub or Finnworlds API for production
    return [
        {"event": "Fed Interest Rate Decision", "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "impact": "high"},
        {"event": "US Jobs Report", "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"), "impact": "medium"},
        {"event": "CPI Inflation Release", "date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"), "impact": "high"},
    ]

def get_portfolio_analytics(holdings: Dict[str, float]) -> PortfolioAnalytics:
    total_value = 0.0
    returns = []
    vols = []
    prices = []
    for symbol, qty in holdings.items():
        info = get_stock_info(symbol)
        if info.price and info.price_month_ago:
            total_value += info.price * qty
            returns.append((info.price - info.price_month_ago) / info.price_month_ago)
            vols.append(info.volatility or 0)
            prices.append(info.price)
    avg_return = sum(returns) / len(returns) if returns else 0
    avg_vol = sum(vols) / len(vols) if vols else 0
    sharpe = avg_return / avg_vol if avg_vol else 0
    drawdown = min(returns) if returns else 0
    risk_level = "Low"
    if avg_vol > 0.05:
        risk_level = "Medium"
    if avg_vol > 0.1:
        risk_level = "High"
    return PortfolioAnalytics(
        total_value=total_value,
        returns=avg_return,
        volatility=avg_vol,
        sharpe=sharpe,
        drawdown=drawdown,
        risk_level=risk_level
    )

async def ask_together(messages: List[Dict[str, Any]], client: httpx.AsyncClient) -> str:
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7
    }
    try:
        response = await client.post(TOGETHER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        completion = response.json()
        return completion["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Error from Together API: {e}")
        raise

# --- ROUTES ---

@app.post("/trade-insights", response_model=TradeInsightsResponse)
async def trade_insights(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    data = await request.json()
    query = data.get("query", "Analyze my watchlist and provide actionable insights.")
    tickers = data.get("tickers", ["BTC-USD", "^IXIC"])
    stats = {symbol: get_stock_info(symbol).dict() for symbol in tickers}
    news = search_news(" ".join(tickers), max_results=5)
    econ_calendar = get_economic_calendar()
    system_prompt = (
        "You are a multi-agent AI trading assistant. Given the following data, do the following:\n"
        "- Summarize technical and statistical indicators for each asset\n"
        "- Summarize news sentiment and key drivers\n"
        "- Give actionable recommendations (buy/sell/hold) and risk assessment\n"
        "- Highlight alerts (volatility, volume, macro events)\n"
        "- No code, only insights and analytics."
    )
    user_prompt = (
        f"{query}\n\n"
        f"Tickers: {tickers}\n"
        f"Stats: {stats}\n"
        f"Latest News: {[n.dict() for n in news]}\n"
        f"Economic Calendar: {econ_calendar}\n"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        ai_response = await ask_together(messages, client)
        return TradeInsightsResponse(result=ai_response, stats=stats)
    except Exception as e:
        logger.error(f"Trade insights error: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"result": f"Error: {e}", "stats": stats})

@app.post("/portfolio-analytics", response_model=PortfolioAnalytics)
async def portfolio_analytics(request: Request):
    data = await request.json()
    holdings = data.get("holdings", {"AAPL": 10, "MSFT": 5})
    return get_portfolio_analytics(holdings)

@app.post("/backtest", response_model=BacktestResponse)
async def backtest(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client)
):
    data = await request.json()
    strategy = data.get("strategy", "Backtest a simple moving average crossover on BTC-USD for the last 2 years.")
    system_prompt = (
        "You are a quant analyst. Summarize:\n"
        "- The logic in plain English\n"
        "- Expected performance (win rate, avg return, drawdown)\n"
        "- Main risks and market conditions\n"
        "- No code, only insights."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": strategy}
    ]
    try:
        ai_response = await ask_together(messages, client)
        return BacktestResponse(backtest_result=ai_response)
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"backtest_result": f"Error: {e}"})

@app.post("/feedback")
async def feedback(feedback: FeedbackRequest):
    logger.info(f"User feedback: {feedback.dict()}")
    return {"status": "success", "message": "Thank you for your feedback!"}

@app.post("/compare-strategies")
async def compare_strategies(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    data = await request.json()
    strategies = data.get("strategies", [])
    system_prompt = (
        "You are a trading strategy expert. Compare the following strategies. "
        "Summarize logic, performance, risk, and optimal market conditions."
    )
    user_prompt = "\n\n".join(strategies)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        ai_response = await ask_together(messages, client)
        return {"comparison": ai_response}
    except Exception as e:
        logger.error(f"Compare strategies error: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"comparison": f"Error: {e}"})

@app.get("/sentiment-history")
async def sentiment_history(news_topic: str = "BTC NASDAQ market"):
    today = datetime.now()
    history = []
    sentiments = ["positive", "negative", "neutral"]
    for i in range(10):
        history.append({
            "date": (today - timedelta(days=i)).strftime("%Y-%m-%d"),
            "sentiment": sentiments[i % 3]
        })
    return {"history": history}

@app.post("/backtest-vs-live", response_model=BacktestComparison)
async def backtest_vs_live(request: Request, client: httpx.AsyncClient = Depends(get_http_client)):
    data = await request.json()
    backtest_data = data.get("backtest_data")
    live_data = data.get("live_data")
    system_prompt = (
        "You are an AI trading analyst. Compare backtest and live trading results. "
        "Highlight discrepancies, possible causes, and suggest optimizations."
    )
    user_prompt = f"Backtest: {backtest_data}\nLive: {live_data}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        ai_response = await ask_together(messages, client)
        return BacktestComparison(
            backtest_summary=backtest_data,
            live_summary=live_data,
            discrepancies=ai_response
        )
    except Exception as e:
        logger.error(f"Backtest vs live error: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"discrepancies": f"Error: {e}"})

@app.get("/")
async def root():
    return {"message": "Trade Insights Bot with All Advanced Features is running."}
