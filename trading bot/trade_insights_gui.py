import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Trade Insights Bot", layout="wide")
st.title("🚀 Next-Gen Trade Insights Bot")

# --- Watchlist & Portfolio ---
st.sidebar.header("Watchlist & Portfolio")
tickers = st.sidebar.text_input("Enter tickers (comma separated)", "BTC-USD, AAPL, TSLA").split(",")
tickers = [t.strip().upper() for t in tickers if t.strip()]
indicators = st.sidebar.multiselect("Technical Indicators", ["RSI", "MACD", "Bollinger Bands"], default=["RSI", "MACD"])

st.sidebar.header("Portfolio Holdings")
portfolio = {}
for t in tickers:
    qty = st.sidebar.number_input(f"{t} shares/coins", min_value=0, value=0)
    if qty > 0:
        portfolio[t] = qty

# --- Economic Calendar ---
st.sidebar.header("Economic Calendar")
if st.sidebar.button("Show Upcoming Events"):
    econ_events = requests.get("http://localhost:8000/").json().get("message", "Error")
    st.sidebar.write(econ_events)

# --- Trade Insights ---
st.subheader("Trade Insights")
query = st.text_area("Enter your trade insights query:", "Analyze my watchlist and provide actionable insights.")
if st.button("Get Insights"):
    with st.spinner("Fetching insights..."):
        resp = requests.post("http://localhost:8000/trade-insights", json={
            "query": query,
            "tickers": tickers,
            "indicators": indicators
        })
        if resp.status_code == 200:
            data = resp.json()
            st.markdown(data["result"])
            st.json(data["stats"])
        else:
            st.error(resp.text)

# --- Portfolio Analytics ---
st.subheader("Portfolio Analytics")
if st.button("Analyze Portfolio"):
    with st.spinner("Analyzing..."):
        resp = requests.post("http://localhost:8000/portfolio-analytics", json={
            "holdings": portfolio,
            "indicators": indicators
        })
        if resp.status_code == 200:
            data = resp.json()
            st.write(data)
        else:
            st.error(resp.text)

# --- Backtest ---
st.subheader("Strategy Backtest")
strategy = st.text_area("Describe your backtest strategy:", "Backtest a simple moving average crossover on BTC-USD for the last 2 years.")
if st.button("Run Backtest"):
    with st.spinner("Running backtest..."):
        resp = requests.post("http://localhost:8000/backtest", json={"strategy": strategy})
        if resp.status_code == 200:
            st.markdown(resp.json()["backtest_result"])
        else:
            st.error(resp.text)

# --- Compare Strategies ---
st.subheader("Compare Strategies")
strategies = st.text_area("Enter strategies to compare (one per line):", "SMA crossover on BTC-USD\nRSI strategy on AAPL").split("\n")
if st.button("Compare"):
    with st.spinner("Comparing..."):
        resp = requests.post("http://localhost:8000/compare-strategies", json={"strategies": strategies})
        if resp.status_code == 200:
            st.markdown(resp.json()["comparison"])
        else:
            st.error(resp.text)

# --- Sentiment History Chart ---
st.subheader("Sentiment History")
sentiment_topic = st.text_input("News topic for sentiment history", "BTC NASDAQ market")
if st.button("Show Sentiment History"):
    resp = requests.get(f"http://localhost:8000/sentiment-history?news_topic={sentiment_topic}")
    if resp.status_code == 200:
        hist = resp.json()["history"]
        df = pd.DataFrame(hist)
        st.line_chart(df.set_index("date")["sentiment"].replace({"positive": 1, "neutral": 0, "negative": -1}))
    else:
        st.error(resp.text)

# --- User Feedback ---
st.subheader("User Feedback")
feedback_query = st.text_input("What did you ask the bot?", "")
rating = st.slider("How helpful was the answer?", 1, 5, 3)
comments = st.text_area("Additional comments (optional):", "")
if st.button("Submit Feedback"):
    resp = requests.post("http://localhost:8000/feedback", json={
        "query": feedback_query,
        "rating": rating,
        "comments": comments
    })
    if resp.status_code == 200:
        st.success("Thank you for your feedback!")
    else:
        st.error(resp.text)
