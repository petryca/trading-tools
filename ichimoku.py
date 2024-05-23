#!/usr/bin/env python3

import sys
import requests
import pandas as pd
from ta.trend import IchimokuIndicator
from ta.volatility import AverageTrueRange
import numpy as np

def fetch_data(trading_pair, interval):
    url = f'https://api.binance.com/api/v3/klines?symbol={trading_pair}&interval={interval}&limit=1000'
    response = requests.get(url)
    data = response.json()
    
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_asset_volume', 'number_of_trades', 
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def apply_ichimoku(df, window1, window2, window3):
    ichimoku = IchimokuIndicator(
        high=df['high'],
        low=df['low'],
        window1=window1,
        window2=window2,
        window3=window3
    )
    
    df['tenkan_sen'] = ichimoku.ichimoku_conversion_line()
    df['kijun_sen'] = ichimoku.ichimoku_base_line()
    df['senkou_span_a'] = ichimoku.ichimoku_a()
    df['senkou_span_b'] = ichimoku.ichimoku_b()
    df['chikou_span'] = df['close'].shift(-window2)
    
    return df

def analyze_ichimoku(df):
    latest = df.iloc[-1]
    prior = df.iloc[-2]
    
    # Basic Ichimoku analysis
    if latest['close'] > latest['senkou_span_a'] and latest['close'] > latest['senkou_span_b']:
        if latest['tenkan_sen'] > latest['kijun_sen'] and prior['tenkan_sen'] <= prior['kijun_sen']:
            return "LONG"
    elif latest['close'] < latest['senkou_span_a'] and latest['close'] < latest['senkou_span_b']:
        if latest['tenkan_sen'] < latest['kijun_sen'] and prior['tenkan_sen'] >= prior['kijun_sen']:
            return "SHORT"
    
    return "NEUTRAL"

def compute_target_and_stop(signal, latest_close, atr):
    if signal == "LONG":
        target = latest_close + 2 * atr
        stop_loss = latest_close - atr
    elif signal == "SHORT":
        target = latest_close - 2 * atr
        stop_loss = latest_close + atr
    else:
        target = None
        stop_loss = None
    return target, stop_loss

def main():
    if len(sys.argv) not in [3, 6]:
        print("Usage: python ichimoku.py <trading-pair> <time-span> [<window1> <window2> <window3>]")
        return

    trading_pair = sys.argv[1].upper()
    time_span = sys.argv[2]

    if len(sys.argv) == 6:
        window1 = int(sys.argv[3])
        window2 = int(sys.argv[4])
        window3 = int(sys.argv[5])
    else:
        window1 = 9
        window2 = 18
        window3 = 24

    df = fetch_data(trading_pair, time_span)
    df = apply_ichimoku(df, window1, window2, window3)
    
    # Calculate ATR for target and stop-loss levels
    atr_indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
    df['atr'] = atr_indicator.average_true_range()
    
    signal = analyze_ichimoku(df)
    latest_close = df.iloc[-1]['close']
    latest_atr = df.iloc[-1]['atr']
    
    # Debugging statements
    print(f"Latest close price: {latest_close}")
    print(f"Latest ATR: {latest_atr}")
    
    target, stop_loss = compute_target_and_stop(signal, latest_close, latest_atr)
    
    if target and stop_loss:
        target_percent = ((target - latest_close) / latest_close) * 100
        stop_loss_percent = ((stop_loss - latest_close) / latest_close) * 100
    else:
        target_percent = None
        stop_loss_percent = None

    print(f"Trading Signal for {trading_pair} on {time_span} timeframe: {signal}")
    if signal in ["LONG", "SHORT"]:
        print(f"Target: {target:.8f} ({target_percent:.2f}%)")
        print(f"Stop Loss: {stop_loss:.8f} ({stop_loss_percent:.2f}%)")

if __name__ == "__main__":
    main()
