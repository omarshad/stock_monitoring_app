from flask import Flask, render_template, request
import requests
import pandas as pd
import plotly.graph_objs as go
import ta
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='./')
session = requests.Session()

# Set default API key with a fallback
API_KEY = os.getenv('POLYGON_API_KEY', 'uwb46Tke491slxFdIOfkDxoghia2X0X9')

# Modularize API call
def fetch_data(symbol, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["results"])
        df["t"] = pd.to_datetime(df["t"], unit="ms")
        df.set_index("t", inplace=True)
        return df
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

# Modular technical indicators
def calculate_technical_indicators(df):
    if not df.empty:
        # Existing indicators
        df['MA50'] = ta.trend.sma_indicator(df['c'], window=50)
        df['MA200'] = ta.trend.sma_indicator(df['c'], window=200)
        df['RSI'] = ta.momentum.rsi(df['c'], window=14)

        # MACD
        macd = ta.trend.MACD(df['c'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()

        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['c'])
        df['Bollinger_High'] = bollinger.bollinger_hband()
        df['Bollinger_Low'] = bollinger.bollinger_lband()

        # Signals
        df['Signal'] = 'Hold'
        buy_signals = (df['MA50'] > df['MA200']) & (df['MA50'].shift(1) <= df['MA200'].shift(1))
        sell_signals = (df['MA50'] < df['MA200']) & (df['MA50'].shift(1) >= df['MA200'].shift(1))
        df.loc[buy_signals, 'Signal'] = 'Buy'
        df.loc[sell_signals, 'Signal'] = 'Sell'
    return df


# Modular plot function
def plot_stock_data(df, asset):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["c"], mode="lines", name=f"{asset} Close"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], mode="lines", name="MA50", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], mode="lines", name="MA200", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI", line=dict(color='green')))
    fig.update_layout(title=f"{asset} Stock Data Plot", xaxis_title="Date", yaxis_title="Value")
    return fig.to_json()

@app.route("/", methods=["GET", "POST"])
def index():
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)
    
    default_start_date = one_year_ago.strftime("%Y-%m-%d")
    default_end_date = today.strftime("%Y-%m-%d")
    
    if request.method == "POST":
        asset = request.form.get("asset", "AAPL")  # Default to AAPL if not provided
        start_date = request.form.get("start_date", default_start_date)
        end_date = request.form.get("end_date", default_end_date)

        asset_data = fetch_data(asset, start_date, end_date)
        asset_data = calculate_technical_indicators(asset_data)
        plot_json = plot_stock_data(asset_data, asset)
    else:
        # Pre-populate with default data
        asset = "AAPL"
        asset_data = fetch_data(asset, default_start_date, default_end_date)
        asset_data = calculate_technical_indicators(asset_data)
        plot_json = plot_stock_data(asset_data, asset)

    return render_template("index.html", plot_json=plot_json, start_date=default_start_date, end_date=default_end_date)

@app.route("/monitor", methods=["GET", "POST"])
def monitor():
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)

    default_start_date = one_year_ago.strftime("%Y-%m-%d")
    default_end_date = today.strftime("%Y-%m-%d")

    if request.method == "POST":
        stock_input = request.form.get('stock', 'AAPL,MSFT,GOOGL')
        stocks = [stock.strip().upper() for stock in stock_input.split(',')]
        start_date = request.form.get('start_date', default_start_date)
        end_date = request.form.get('end_date', default_end_date)
    else:
        stocks = ["AAPL", "MSFT", "GOOGL"]
        start_date = default_start_date
        end_date = default_end_date

    stock_data = []
    for stock in stocks:
        df = fetch_data(stock, start_date, end_date)
        df = calculate_technical_indicators(df) if not df.empty else pd.DataFrame()
        if not df.empty:
            dates = df.index.strftime('%Y-%m-%d').tolist()
            prices = df['c'].tolist()
            latest_data = df.iloc[-1]
            stock_data.append({
                "symbol": stock,
                "dates": dates,
                "prices": prices,
                "latest_price": latest_data['c'],
                "MA50": latest_data['MA50'],
                "MA200": latest_data['MA200'],
                "RSI": latest_data['RSI'],
                "Signal": latest_data['Signal'],
                "MACD": latest_data['MACD'],
                "Bollinger_High": latest_data['Bollinger_High'],
                "Bollinger_Low": latest_data['Bollinger_Low']
            })
        else:
            # Handle case where no data is returned
            stock_data.append({
                "symbol": stock,
                "dates": [],
                "prices": [],
                "latest_price": "N/A",
                "MA50": "N/A",
                "MA200": "N/A",
                "RSI": "N/A",
                "Signal": "N/A",
                "MACD": "N/A",
                "Bollinger_High": "N/A",
                "Bollinger_Low": "N/A"
            })

    return render_template("monitor.html", stock_data=stock_data, start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    app.run(debug=True)