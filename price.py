#!/usr/bin/env python3

import os
import argparse
from binance.client import Client
from keys import API_KEY, API_SECRET

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)

def get_current_price(symbol):
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"An error occurred while fetching the price: {e}")
        return None

def calculate_breakeven_price(current_price, trade):
    fee_rate = 0.001  # 0.1% trading fee per trade
    if trade == 'BUY':
        # Breakeven price when selling the bought asset
        breakeven_price = current_price * (1 + 2 * fee_rate)
    else:
        # Breakeven price when buying back the sold asset
        breakeven_price = current_price / (1 + 2 * fee_rate)
    return breakeven_price

def main(symbol, trade):
    trade = trade.upper()

    if trade not in ['BUY', 'SELL']:
        print("Invalid trade type. Please enter either 'BUY' or 'SELL'.")
        return

    current_price = get_current_price(symbol)

    if current_price is None:
        print("Failed to get the current price.")
        return

    breakeven_price = calculate_breakeven_price(current_price, trade)
    quote_asset = symbol[-4:]  # Assuming the trading pair format is always like "BTCUSDT"

    print(f"The current market price of {symbol} is: {current_price:.6f} {quote_asset}")
    if trade == 'BUY':
        print(f"The breakeven price to cover 2x 0.1% trading fees if SOLD is: {breakeven_price:.6f} {quote_asset}")
    else:
        print(f"The breakeven price to cover 2x 0.1% trading fees if BOUGHT back is: {breakeven_price:.6f} {quote_asset}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance price and breakeven calculation script")
    parser.add_argument('symbol', type=str, help='Trading pair symbol (e.g., BTCUSDT)')
    parser.add_argument('trade', type=str, help='Trade type (BUY or SELL)')

    args = parser.parse_args()

    main(args.symbol, args.trade)
