import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import os
from dotenv import load_dotenv
import socket
from pprint import pprint
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from utils import *
import time
import altair as alt
import json

st.set_page_config(layout="wide")
st.title('PROJECT: DAYMOON 🚀')
st.sidebar.title("Automated Trading")


# -------------- CREATE SESSION STATE VARIABLES------------
session_state_vars = {
    "binance": "",
    "usd_balance": 0,
    "eth_balance": 0,
    "btc_balance": 0,
    "usdt_balance": 0,
    "gross_balance_csv_path": r"/home/ethan/Documents/git/TraderBot/data/historical_gross_balance.csv",
    "transaction_records_csv_path": r"/home/ethan/Documents/git/TraderBot/data/transaction_records.csv",
    "TEST_MODE": True,
    "last_buy_point": 0,
    "bot_running" : False
}
for key, value in session_state_vars.items(): 
    if key not in st.session_state:
        st.session_state[key] = value


# ----------- IF TEST MODE -----------------
if st.session_state['TEST_MODE'] == True:
    st.session_state["gross_balance_csv_path"] = r"/home/ethan/Documents/git/TraderBot/data/historical_gross_balance_TEST.csv"


# ---------- Load API keys from .env --------------
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

# Set socket to use ipv4 instead of ipv6
_original_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = getaddrinfo_ipv4


# --------- TRY CONNECTING TO BINANCE --------
try:
    # Set up Binance exchange
    st.session_state['binance'] = ccxt.binanceus({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,  # prevents API bans
    })
    balance = st.session_state['binance'].fetch_balance()
    st.write("🟢 CONNECTED TO BINANCE")
except Exception as e:
    st.write("🔴 UNABLE TO CONNECT TO BINANCE")
    with st.expander("Error Message"):
        st.write(e)
if st.session_state['TEST_MODE']:
    st.write("🟣 TEST MODE ACTIVE")

st.markdown("----")



# ----------- GROSS BALANCE ---------------  
if st.session_state['TEST_MODE'] == True:
    gross_balance_df = pd.read_csv(st.session_state['gross_balance_csv_path'])
    gross_balance_df['timestamp'] = pd.to_datetime(gross_balance_df['timestamp'], unit='ms')
    # Set usd_balance to the last value in the "total_usd" column
    if not gross_balance_df.empty and 'total_usd' in gross_balance_df.columns:
        st.session_state['usd_balance'] = gross_balance_df['total_usd'].iloc[-1]
    else:
        st.session_state['usd_balance'] = 0.0  # fallback
    st.header("Gross Balance: $" + str(round(st.session_state['usd_balance'], 4)))    
    # CREATE LINE CHART    
    with st.expander("Asset breakdown:", expanded=True):
        st.line_chart(gross_balance_df, x="timestamp", x_label = "Timestamp", y="total_usd", y_label = "Total USD")
     
        with open("data/token_balances.json", "r") as f:
            json_dump = json.load(f)

            tokenlist = []
            for token in json_dump['balances']:
                if token['symbol'] != "USDT":
                    tokenlist.append(f"{token['symbol']}/USDT")

            # Fetch latest prices
            ticker = st.session_state['binance'].fetchTickers(tokenlist)
            for token in json_dump['balances']:
                symbol = token['symbol']
                balance = float(token['balance'])
                if symbol == "USDT":
                    total_worth = balance
                else:
                    pair = f"{symbol}/USDT"
                    price = ticker[pair]['last'] if pair in ticker else 0.0
                    total_worth = balance * price
                st.write(f"{symbol}: ${round(total_worth, 4)} ---- Number of tokens: {balance:.8f}")


if st.session_state['TEST_MODE'] == False:
    total_usd, asset_values = get_total_balance_usd()
    st.header("Gross Balance: $" + str(round(total_usd, 4)))
    timestamp = st.session_state['binance'].milliseconds()
    update_gross_balance(total_usd, timestamp)

    with st.expander("Asset breakdown:", expanded=True):
        gross_balance_df = pd.read_csv(st.session_state['gross_balance_csv_path'])
        gross_balance_df['timestamp'] = pd.to_datetime(gross_balance_df['timestamp'], unit='ms')
        st.line_chart(gross_balance_df, x="timestamp", x_label = "Timestamp", y="total_usd", y_label = "Total USD")
        for asset, value in asset_values.items():
            st.write(f"{asset}: ${round(value[0],4)} ---- Number of tokens: {value[1]:.8f}")



# ----------- SHOW HISTORICAL DATA FOR SELECT TOKENS --------------

symbols = ['ETH/USD','BTC/USD', 'USDT/USD']
ticker = st.session_state['binance'].fetchTickers(symbols)
for symbol, data in ticker.items():
    st.header(symbol + ": $" + str(data['last']))
    with st.expander("Line Chart"):
        timeframe="1h"
        # in last 7 days
        since = st.session_state['binance'].milliseconds() - 1* 24 * 60 * 60 * 1000
        ohlcv = st.session_state['binance'].fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1440)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        st.line_chart(df, x="timestamp", y="close")


with st.sidebar:
    token = st.selectbox("Select token to buy", ("SHIB", "ETH", "BTC"), index=None, placeholder="Select Token")
    bot_running = st.toggle("TURN BOT ON", value=st.session_state['bot_running'])
    

    #####################################
    symbol = 'ETH/USDT'
    timeframe = '1h'
    lookback_candles = 24  # use past 24 hours
    buy_threshold = -0.01  # -1%
    sell_threshold = 0.01  # +1%
    usd_balance = 100  # you could fetch this dynamically
    holding_token = False

    if bot_running != st.session_state['bot_running']:
        st.session_state['bot_running'] = bot_running

    if st.session_state['bot_running']:
        ticker = st.session_state['binance'].fetch_ticker(f'{token}/USDT')
        price = ticker['last']
        
        #check to see if funds are available
        if st.session_state['usdt_balance'] > 1 and price <= st.session_state['last_buy_point']*.98 or st.session_state['last_buy_point'] ==0:
            #if funds available, buy token
            try:
                buy(token, st.session_state['usdt_balance'])
            except Exception as e:
                st.error(f"ERROR: {e}")

        balance = st.session_state['binance'].fetch_balance()
        token_balance = balance['free'].get(token, 0)

        if price >= st.session_state['last_buy_point'] * 1.012 and token_balance > 0.0001:
            sell(token)
        time.sleep(60)
        st.rerun()
    