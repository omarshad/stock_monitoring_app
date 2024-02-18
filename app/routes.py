from app import app
from flask import render_template, request
import ta
import os
from app.stock_functions import fetch_data, calculate_technical_indicators, plot_stock_data
from datetime import datetime, timedelta
import pandas as pd

@app.route("/", methods=["GET", "POST"])
def index():
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)
    
    default_start_date = one_year_ago.strftime("%Y-%m-%d")
    default_end_date = today.strftime("%Y-%m-%d")
    
    if request.method == "POST":
        asset = request.form.get("asset", "AAPL")
        start_date = request.form.get("start_date", default_start_date)
        end_date = request.form.get("end_date", default_end_date)

        asset_data = fetch_data(asset, start_date, end_date)
        asset_data = calculate_technical_indicators(asset_data)
        plot_json = plot_stock_data(asset_data, asset)
    else:
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
        if not df.empty:
            processed_df = calculate_technical_indicators(df)
            dates = processed_df.index.strftime('%Y-%m-%d').tolist()
            prices = processed_df['c'].tolist()
            stock_data.append({
                "symbol": stock,
                "dates": dates,
                "prices": prices,
                "latest_data": processed_df.iloc[-1].to_dict()
            })

    return render_template("monitor.html", stock_data=stock_data, start_date=start_date, end_date=end_date)