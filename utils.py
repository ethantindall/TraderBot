import streamlit as st
import pandas as pd
from datetime import datetime

# GET TOTAL BALANCE OF ALL ASSETS
def get_total_balance_usd():
    balance = st.session_state['binance'].fetch_balance()
    tickers = st.session_state['binance'].fetch_tickers()
    
    total_usd = 0
    asset_values = {}

    for asset, amount in balance['total'].items():
        if amount > 0:
            if asset == 'USDT':
                usd_value = amount
            else:
                symbol = f"{asset}/USDT"
                if symbol in tickers:
                    price = tickers[symbol]['last']
                    usd_value = amount * price
                else:
                    continue  # skip non-tradeable assets
            asset_values[asset] = [usd_value, amount]
            total_usd += usd_value
    print(total_usd)
    print(asset_values)
    st.session_state['usd_balance'] = total_usd
    return total_usd, asset_values



# UPDATE THE GROSS BALANCE CSV
def update_gross_balance(total_usd, timestamp):
    # Read existing data or create new DataFrame if file doesn't exist
    try:
        df = pd.read_csv(st.session_state['gross_balance_csv_path'], parse_dates=["timestamp"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["timestamp", "total_usd"])
    new_row = pd.DataFrame([{"timestamp": timestamp, "total_usd": total_usd}])
   # Append and save
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(st.session_state['gross_balance_csv_path'], index=False)


# UPDATE TRANSACTION RECORDS CSV
def update_transaction_records(timestamp, token, amount, transaction_type):
    # Read existing data or create new DataFrame if file doesn't exist
    try:
        df = pd.read_csv(st.session_state['transaction_records_csv_path'], parse_dates=["timestamp"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["timestamp", "token", "amount", "transaction_type"])
    new_row = pd.DataFrame([{"timestamp": timestamp, "token": token, "amount": amount, "transaction_type": transaction_type}])
   # Append and save
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(st.session_state['transaction_records_csv_path'], index=False)


def fetch_prices():
    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=lookback_candles)
    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

def should_trade(df):
    last_price = df['close'].iloc[-1]
    moving_avg = df['close'].mean()
    deviation = (last_price - moving_avg) / moving_avg
    return deviation, last_price


"""
def performance_over_period(csv_to_read):
    try:
        df = pd.read_csv(st.session_state['gross_balance_csv_path'], parse_dates=["timestamp"])
        print(df)
        #1 week
        since = 7 * 24 * 60 * 60 * 1000
        sorted_df = df.sort_values(by="timestamp", ascending=False)
        print(sorted_df)
        timestamps_in_period = []
        #for index, row in sorted_df.iterrows():
        #    if row['timestamp'] > (sorted_df[["timestamp"] - since):
        #        timestamps_in_period.append(row)

    except FileNotFoundError:
        print("Cannot check performance record.")


def sell(token):
    # Step 1: Fetch your balance
    balance = st.session_state['binance'].fetch_balance()
    token_balance = balance['free'].get(token, 0)

    # Step 2: Round it and check if you have enough to sell
    amount_to_sell = round(token_balance, 6)

    # Step 3: Sell all token (market order)
    if amount_to_sell > 0:
        order = st.session_state['binance'].createMarketSellOrderWithCost(f'{token}/USDT', amount_to_sell)
        st.success(f"✅ Sold {token}:", order)
        update_transaction_records
    else:
        st.error(f"❌ No {token} available to sell.")

        
def buy(token, usdt_to_spend):
    ticker = st.session_state['binance'].fetch_ticker(f'{token}/USDT')
    price = ticker['last']
    #print(f"Current price: ${price}")
    token_amount = round(usdt_to_spend / price, 6)  # round to avoid precision errors
    order = st.session_state['binance'].createMarketBuyOrderWithCost(f'{token}/USDT', token_amount)
    print(f"Order placed at {datetime.now()}")
    print(order)
    st.success(order)
    st.session_state['last_buy_point'] = price
    update_transaction_records()


def test_buy(token, cost, quantity="Not Specified"):
    ticker = st.session_state['binance'].fetch_ticker(f'{token}/USDT')
    price = ticker['last']
    print(f"Current price: ${price}")
    usdt_to_spend = 5

def test_sell(token, quantity):
    pass
    

"""