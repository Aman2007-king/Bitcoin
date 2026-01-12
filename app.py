import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# --- WEB APP UI SETUP ---
st.set_page_config(page_title="TradeGoing AI", layout="wide")
st.title("📈 TradeGoing: AI Strategy Backtester")
st.sidebar.header("Strategy Settings")

# User Inputs in the Sidebar
ticker = st.sidebar.text_input("Crypto/Stock Ticker", value="BTC-USD")
short_ma = st.sidebar.slider("Short Moving Average", 5, 20, 7)
long_ma = st.sidebar.slider("Long Moving Average", 21, 100, 30)
stop_loss = st.sidebar.slider("Stop Loss %", 1, 15, 5) / 100
slippage = 0.0005 # 0.05% fixed

# --- FUNCTIONS ---
@st.cache_data # This keeps the app fast by saving data in memory
def get_data(symbol):
    data = yf.download(symbol, period="1y", interval="1d")
    df = data[['Close']].copy()
    df.columns = ['Price']
    return df.dropna()

def run_backtest(df, s_ma, l_ma, sl_pct):
    # Signals
    df['S_MA'] = df['Price'].rolling(window=s_ma).mean()
    df['L_MA'] = df['Price'].rolling(window=l_ma).mean()
    df['Signal'] = np.where(df['S_MA'] > df['L_MA'], 1, 0)
    df['Action'] = df['Signal'].shift(1).fillna(0)
    
    # Simulation
    cash, btc, entry_p = 100000, 0, 0
    history = []

    for i, row in df.iterrows():
        curr_p = row['Price']
        if btc > 0: # Check Exit
            if curr_p < entry_p * (1 - sl_pct) or row['Action'] == 0:
                cash = (btc * curr_p) * (0.999) # Fee + Slippage
                btc, entry_p = 0, 0
        elif row['Action'] == 1: # Check Entry
            btc = (cash * 0.999) / curr_p
            entry_p, cash = curr_p, 0
    
    final_v = cash + (btc * df.iloc[-1]['Price'])
    return final_v, df

# --- EXECUTION ---
try:
    data_df = get_data(ticker)
    final_value, result_df = run_backtest(data_df, short_ma, long_ma, stop_loss)

    # Display Metrics
    col1, col2 = st.columns(2)
    col1.metric("Final Portfolio", f"${final_value:,.2f}")
    col2.metric("Total Return", f"{((final_value - 100000)/100000)*100:.2f}%")

    # Charting
    st.subheader(f"{ticker} Strategy Chart")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=result_df.index, y=result_df['Price'], name="Price"))
    fig.add_trace(go.Scatter(x=result_df.index, y=result_df['S_MA'], name=f"{short_ma} Day MA"))
    fig.add_trace(go.Scatter(x=result_df.index, y=result_df['L_MA'], name=f"{long_ma} Day MA"))
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error fetching data for {ticker}. Check the symbol name!")