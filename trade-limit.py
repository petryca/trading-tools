#!/usr/bin/env python3

import sys
from binance.exceptions import BinanceAPIException, BinanceRequestException

def print_help():
    print("Usage: trade-limit.py <arg1> <arg2> <arg3>")
    print("Description: This script places a limit order for a specified cryptocurrency trading pair on Binance.")

if '-h' in sys.argv or '--help' in sys.argv:
    print_help()
    sys.exit(0)

try:
    from binance.client import Client
    from binance.enums import *
    from decimal import Decimal, ROUND_DOWN
    from keys import API_KEY, API_SECRET

    # Initialize the Binance client
    client = Client(API_KEY, API_SECRET)

    def get_available_balance(asset):
        """Get the available balance of a specific asset in the user's spot wallet."""
        balance = client.get_asset_balance(asset=asset)
        available_balance = float(balance['free'])
        return available_balance

    def get_symbol_info(symbol):
        """Get the exchange info for a specific trading pair symbol."""
        exchange_info = client.get_symbol_info(symbol)
        return exchange_info

    def get_current_price(symbol):
        """Get the current market price of a specific trading pair symbol."""
        avg_price = client.get_avg_price(symbol=symbol)
        current_price = float(avg_price['price'])
        return current_price

    def round_down(quantity, decimals):
        """Round down a quantity to the specified number of decimal places."""
        factor = Decimal(10) ** decimals
        return (Decimal(quantity) * factor).to_integral_value(ROUND_DOWN) / factor

    def place_order(symbol, side, quantity, price):
        """Place a limit order on Binance."""
        order = client.order_limit(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=str(price)
        )
        return order

    def main():
        if len(sys.argv) != 4:
            print("Usage: python trade-limit.py <symbol> <BUY/SELL> <price>")
            sys.exit(1)

        symbol = sys.argv[1].upper()
        action = sys.argv[2].upper()
        limit_price = float(sys.argv[3])

        if action not in ['BUY', 'SELL']:
            print("Error: Action must be 'BUY' or 'SELL'.")
            sys.exit(1)

        base_asset, quote_asset = symbol[:-3], symbol[-3:]
        current_price = get_current_price(symbol)

        if (action == 'BUY' and limit_price >= current_price) or (action == 'SELL' and limit_price <= current_price):
            print(f"Error: Limit price ({limit_price}) must be {'below' if action == 'BUY' else 'above'} the current market price ({current_price}).")
            sys.exit(1)

        symbol_info = get_symbol_info(symbol)
        lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', symbol_info['filters']))
        step_size = float(lot_size_filter['stepSize'])
        step_size_decimals = len(str(step_size).rstrip('0').split('.')[1])

        if action == 'BUY':
            # Get available funds in the quote asset (e.g., BTC)
            available_funds = get_available_balance(quote_asset)
            print(f"Getting funds in {quote_asset} wallet: {available_funds} {quote_asset}")

            # Calculate the quantity to buy
            quantity_to_buy = available_funds / limit_price
            quantity_to_buy = round_down(quantity_to_buy, step_size_decimals)

            # Place the buy order
            print(f"Placing BUY order for {quantity_to_buy} {base_asset} at {limit_price} {quote_asset}")
            order = place_order(symbol, SIDE_BUY, quantity_to_buy, limit_price)
            print("Order details:", order)
        
        elif action == 'SELL':
            # Get available funds in the base asset (e.g., BNB)
            available_funds = get_available_balance(base_asset)
            print(f"Getting funds in {base_asset} wallet: {available_funds} {base_asset}")

            # Round down the available funds to the correct step size
            available_funds = round_down(available_funds, step_size_decimals)

            # Place the sell order
            print(f"Placing SELL order for {available_funds} {base_asset} at {limit_price} {quote_asset}")
            order = place_order(symbol, SIDE_SELL, available_funds, limit_price)
            print("Order details:", order)

    if __name__ == "__main__":
        main()

except BinanceAPIException as e:
    print(f"Binance API Exception: {e}")
except BinanceRequestException as e:
    print(f"Binance Request Exception: {e}")
except IndexError:
    print("Error: Missing command line arguments.")
    print_help()
except Exception as e:
    print(f"An unexpected error occurred: {e}")

