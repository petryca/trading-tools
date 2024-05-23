#!/usr/bin/env python3

import sys
from binance.exceptions import BinanceAPIException, BinanceRequestException

def print_help():
    print("Usage: analize.py <arg1> <arg2>")
    print("Description: This script performs technical analysis on cryptocurrency trading pairs using RSI, MACD, and Bollinger Bands indicators.")

if '-h' in sys.argv or '--help' in sys.argv:
    print_help()
    sys.exit(0)

try:
    import requests
    import pandas as pd
    import ta

    def get_klines(symbol, interval):
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval
        }
        response = requests.get(url, params=params)
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['close'] = df['close'].astype(float)

        return df

    def calculate_indicators(df):
        # Calculate RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=7).rsi()

        # Calculate MACD
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        # Calculate Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_high'] = bollinger.bollinger_hband()
        df['bb_low'] = bollinger.bollinger_lband()
        df['bb_middle'] = bollinger.bollinger_mavg()

        return df

    def analyze_data(df):
        # Analyze RSI
        if df['rsi'].iloc[-1] > 80:
            rsi_signal = "SHORT"
        elif df['rsi'].iloc[-1] < 20:
            rsi_signal = "LONG"
        else:
            rsi_signal = "NEUTRAL"

        # Analyze MACD
        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
            macd_signal = "LONG"
        elif df['macd'].iloc[-1] < df['macd_signal'].iloc[-1]:
            macd_signal = "SHORT"
        else:
            macd_signal = "NEUTRAL"

        # Analyze Bollinger Bands
        if df['close'].iloc[-1] > df['bb_high'].iloc[-1]:
            bb_signal = "SHORT"
        elif df['close'].iloc[-1] < df['bb_low'].iloc[-1]:
            bb_signal = "LONG"
        else:
            bb_signal = "NEUTRAL"

        return {
            'RSI': rsi_signal,
            'MACD': macd_signal,
            'Bollinger Bands': bb_signal
        }

    def main(symbol, interval):
        df = get_klines(symbol, interval)
        df = calculate_indicators(df)
        signals = analyze_data(df)

        # Print the latest data and signals
        print("Latest Data:")
        print(df.tail(1).T)

        print("\nSignals:")
        for indicator, signal in signals.items():
            print(f"{indicator}: {signal}")

    if __name__ == "__main__":
        if len(sys.argv) != 3:
            print("Usage: python analize.py <trading-pair> <interval>")
            print("Example: python analize.py SOLBTC 1d")
        else:
            symbol = sys.argv[1].upper()
            interval = sys.argv[2]
            main(symbol, interval)

except BinanceAPIException as e:
    print(f"Binance API Exception: {e}")
except BinanceRequestException as e:
    print(f"Binance Request Exception: {e}")
except IndexError:
    print("Error: Missing command line arguments.")
    print_help()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
