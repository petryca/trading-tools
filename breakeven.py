#!/usr/bin/env python3

import sys
from binance.client import Client
from decimal import Decimal, ROUND_DOWN, getcontext
from datetime import datetime, timedelta, timezone
from keys import API_KEY, API_SECRET

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)

# Set decimal precision high enough for financial calculations
getcontext().prec = 8

TRADING_FEE_PERCENT = Decimal('0.001')  # 0.1% trading fee

def get_last_trade(symbol):
    """Get the last trade of a specific trading pair symbol."""
    trades = client.get_my_trades(symbol=symbol, limit=1)
    if trades:
        return trades[0]
    return None

def calculate_breakeven_price(last_trade, current_price):
    """Calculate the breakeven price incorporating the trading fee."""
    last_trade_price = Decimal(last_trade['price'])
    last_trade_qty = Decimal(last_trade['qty'])
    last_trade_side = last_trade['isBuyer']

    if last_trade_side:
        # Last trade was a BUY
        cost_basis = last_trade_price * last_trade_qty
        cost_basis += cost_basis * TRADING_FEE_PERCENT  # Add buy fee
        breakeven_price = (cost_basis / last_trade_qty) / (1 - TRADING_FEE_PERCENT)
    else:
        # Last trade was a SELL
        revenue_basis = last_trade_price * last_trade_qty
        revenue_basis -= revenue_basis * TRADING_FEE_PERCENT  # Subtract sell fee
        breakeven_price = (revenue_basis / last_trade_qty) / (1 + TRADING_FEE_PERCENT)

    return breakeven_price

def format_timedelta(delta):
    """Format a timedelta object into a string with days, hours, minutes, and seconds."""
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

def main():
    if len(sys.argv) != 2:
        print("Usage: python breakeven.py <symbol>")
        sys.exit(1)

    symbol = sys.argv[1].upper()

    # Get the last trade details
    last_trade = get_last_trade(symbol)
    if not last_trade:
        print("No last trade found for the specified trading pair.")
        sys.exit(1)

    last_trade_price = Decimal(last_trade['price'])
    last_trade_qty = Decimal(last_trade['qty'])
    last_trade_side = last_trade['isBuyer']

    print(f"Last trade price: {last_trade_price} {symbol[3:]}")
    print(f"Last trade quantity: {last_trade_qty} {symbol[:3]}")
    print(f"Last trade side: {'BUY' if last_trade_side else 'SELL'}")

    # Get current price of the trading pair
    avg_price = client.get_avg_price(symbol=symbol)
    current_price = Decimal(avg_price['price'])
    print(f"Current price: {current_price} {symbol[3:]}")

    # Calculate breakeven price
    breakeven_price = calculate_breakeven_price(last_trade, current_price)
    print(f"Breakeven price: {breakeven_price} {symbol[3:]}")

    # Calculate percentage difference from current price to breakeven price
    percentage_difference = ((current_price - breakeven_price) / breakeven_price) * 100

    if last_trade_side:
        print(f"Percentage difference to breakeven (if SELL): {percentage_difference:.2f}%")
    else:
        print(f"Percentage difference to breakeven (if BUY): {percentage_difference:.2f}%")

    # Calculate time elapsed since last trade
    last_trade_time = datetime.fromtimestamp(last_trade['time'] / 1000, tz=timezone.utc)
    current_time = datetime.now(tz=timezone.utc)
    time_elapsed = current_time - last_trade_time

    print(f"Time elapsed since last trade: {format_timedelta(time_elapsed)}")

if __name__ == "__main__":
    main()
