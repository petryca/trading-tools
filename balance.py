#!/usr/bin/env python3

import sys
from binance.exceptions import BinanceAPIException, BinanceRequestException

def print_help():
    print("Usage: balance.py <arg1>")
    print("Description: This script checks the balance of the specified cryptocurrency in your Binance account.")

if '-h' in sys.argv or '--help' in sys.argv:
    print_help()
    sys.exit(0)

try:
    import os
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceRequestException
    from keys import API_KEY, API_SECRET

    # Initialize the Binance client
    client = Client(API_KEY, API_SECRET)

    opening_balance = 0.00130951

    try:
        # Get account information
        account_info = client.get_account()

        # Fetch latest prices
        prices = client.get_all_tickers()
        price_dict = {price['symbol']: float(price['price']) for price in prices}

        total_btc = 0

        print("--------------------------------------------------------------")
        print("Asset Balances:")
        for balance in account_info['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked

            if total > 0:
                if asset == 'BTC':
                    btc_value = total
                elif asset == 'USDT':
                    btc_value = total / price_dict['BTCUSDT']
                else:
                    # Find the BTC equivalent price for the asset
                    btc_symbol = asset + 'BTC'
                    if btc_symbol in price_dict:
                        btc_value = total * price_dict[btc_symbol]
                    else:
                        btc_value = 0

                total_btc += btc_value

                # Print asset balance if it's greater than a threshold (e.g., 0.0001 BTC)
                if btc_value > 0.0001:
                    print(f"Asset: {asset}, Free: {free}, Locked: {locked}, BTC Value: {btc_value:.8f}")

        print("--------------------------------------------------------------")
        print(f"Total Balance in BTC: {total_btc:.8f}")
        
        # Calculate percentage change
        percentage_change = ((total_btc - opening_balance) / opening_balance) * 100
        print(f"Percentage change from opening balance: {percentage_change:.2f}%")
        
        print("--------------------------------------------------------------")
    except BinanceAPIException as e:
        # Handle API exception
        print(f"Binance API exception occurred: {e}")
    except BinanceRequestException as e:
        # Handle request exception
        print(f"Binance request exception occurred: {e}")
    except Exception as e:
        # Handle general exception
        print(f"An error occurred: {e}")

except BinanceAPIException as e:
    print(f"Binance API Exception: {e}")
except BinanceRequestException as e:
    print(f"Binance Request Exception: {e}")
except IndexError:
    print("Error: Missing command line arguments.")
    print_help()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
