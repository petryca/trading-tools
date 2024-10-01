#!/usr/bin/env python3

import sys
from binance.exceptions import BinanceAPIException, BinanceRequestException

def print_help():
    print("Usage: trade-limit.py <symbol> <BUY/SELL> <price> <quantity>")
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
        if balance is None:
            raise ValueError(f"Could not retrieve balance for asset: {asset}")
        available_balance = float(balance.get('free', 0.0))
        return available_balance

    def get_symbol_info(symbol):
        """Get the exchange info for a specific trading pair symbol."""
        exchange_info = client.get_symbol_info(symbol)
        if exchange_info is None:
            raise ValueError(f"Could not retrieve symbol info for: {symbol}")
        return exchange_info

    def round_down(quantity, decimals):
        """Round down a quantity to the specified number of decimal places."""
        factor = Decimal(10) ** decimals
        return (Decimal(quantity) * factor).to_integral_value(ROUND_DOWN) / factor

    def place_limit_order(symbol, side, price, quantity):
        """Place a limit order on Binance."""
        order = client.order_limit(
            symbol=symbol,
            side=side,
            price=str(price),
            quantity=str(quantity)
        )
        return order

    def main():
        if len(sys.argv) != 5:
            print("Usage: python trade-limit.py <symbol> <BUY/SELL> <price> <quantity>")
            sys.exit(1)

        symbol = sys.argv[1].upper()
        action = sys.argv[2].upper()
        price = float(sys.argv[3])
        quantity = float(sys.argv[4])

        if action not in ['BUY', 'SELL']:
            print("Invalid action. Use BUY or SELL.")
            sys.exit(1)

        try:
            base_asset, quote_asset = symbol.split('/')
        except ValueError:
            print("Invalid symbol format. Use format BASE/QUOTE (e.g., DOGE/BTC).")
            sys.exit(1)

        symbol = base_asset + quote_asset

        symbol_info = get_symbol_info(symbol)
        filters = symbol_info.get('filters', [])
        lot_size_filter = next((f for f in filters if f['filterType'] == 'LOT_SIZE'), None)
        if lot_size_filter is None:
            raise ValueError(f"Could not find LOT_SIZE filter for symbol: {symbol}")

        step_size = float(lot_size_filter['stepSize'])
        step_size_decimals = len(str(step_size).rstrip('0').split('.')[1])

        quantity = round_down(quantity, step_size_decimals)

        if action == 'BUY':
            # Get available funds in the quote asset (e.g., BTC)
            available_funds = get_available_balance(quote_asset)
            print(f"Getting funds in {quote_asset} wallet: {available_funds} {quote_asset}")

            total_cost = quantity * price
            if total_cost > available_funds:
                print(f"Not enough funds. Required: {total_cost} {quote_asset}, Available: {available_funds} {quote_asset}")
                sys.exit(1)

        elif action == 'SELL':
            # Get available funds in the base asset (e.g., DOGE)
            available_funds = get_available_balance(base_asset)
            print(f"Getting funds in {base_asset} wallet: {available_funds} {base_asset}")

            if quantity > available_funds:
                print(f"Not enough funds. Required: {quantity} {base_asset}, Available: {available_funds} {base_asset}")
                sys.exit(1)

        # Place the limit order
        print(f"Placing {action} order for {quantity} {base_asset} at {price} {quote_asset} per unit.")
        order = place_limit_order(symbol, SIDE_BUY if action == 'BUY' else SIDE_SELL, price, quantity)
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
except ValueError as e:
    print(f"ValueError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")