import requests
import pandas as pd
import plotly.graph_objs as go
import ta
from datetime import datetime, timedelta

# Assuming the API_KEY is hardcoded in this script or imported from a secure config
API_KEY = 'uwb46Tke491slxFdIOfkDxoghia2X0X9'

def fetch_data(symbol, start_date, end_date):
    """
    Fetch stock data for a given symbol within a specified date range.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["results"])
        df["t"] = pd.to_datetime(df["t"], unit="ms")
        df.set_index("t", inplace=True)
        return df
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_technical_indicators(df):
    """
    Calculate various technical indicators for the provided DataFrame.
    """
    if not df.empty:
        df['MA50'] = ta.trend.sma_indicator(df['c'], window=50)
        df['MA200'] = ta.trend.sma_indicator(df['c'], window=200)
        df['RSI'] = ta.momentum.rsi(df['c'], window=14)
        macd = ta.trend.MACD(df['c'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        bollinger = ta.volatility.BollingerBands(df['c'])
        df['Bollinger_High'] = bollinger.bollinger_hband()
        df['Bollinger_Low'] = bollinger.bollinger_lband()
        df['Signal'] = 'Hold'
        buy_signals = (df['MA50'] > df['MA200']) & (df['MA50'].shift(1) <= df['MA200'].shift(1))
        sell_signals = (df['MA50'] < df['MA200']) & (df['MA50'].shift(1) >= df['MA200'].shift(1))
        df.loc[buy_signals, 'Signal'] = 'Buy'
        df.loc[sell_signals, 'Signal'] = 'Sell'
        
    return df

def plot_stock_data(df, asset):
    """
    Generate a Plotly plot from the stock data DataFrame.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["c"], mode="lines", name=f"{asset} Close"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], mode="lines", name="MA50", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], mode="lines", name="MA200", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI", line=dict(color='green')))
    fig.update_layout(title=f"{asset} Stock Data Plot", xaxis_title="Date", yaxis_title="Value")
    return fig.to_json()
