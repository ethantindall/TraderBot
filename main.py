from uniswap import Uniswap
from web3 import Web3
import requss
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal
import time
import os
from dotenv import load_dotenv

os.environ.clear()
load_dotenv(override=True)

MM_INFURA_URL = "https://mainnet.infura.io/v3/"
MM_PRIVATE_KEY = "b471f81b46bb4929a7b7e6addac2f87e"
MM_WALLET_ADDRESS = "0xF15DB64d4D430e0C5a7426F1595E842934987275"

web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/b471f81b46bb4929a7b7e6addac2f87e"))

uniswap = Uniswap(
    address = MM_WALLET_ADDRESS,
    private_key = MM_PRIVATE_KEY,
    provider = MM_INFURA_URL,
    version=3,
    web3 = web3
)

uniswap_v2 = Uniswap(
    address = MM_WALLET_ADDRESS,
    private_key = MM_PRIVATE_KEY,
    provider = MM_INFURA_URL,
    version=2,
    web3 = web3
)

@dataclass
class Trade:
    #What we're buying
    buying_ticker: str
    buying_address: str
    buying_decimals: int

    #What we're selling
    selling_ticker: str
    selling_address: str
    selling_decimals: int
    
    # Trade details
    amount_buying = Optional[Decimal] = 1
    amount_selling = Optional[Decimal] = 0.002
    price_in_usd: Optional[Decimal] = None

    #Transaction details
    tax_hash: Optional[str] = None
    receipt: Optional[dict] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False

    def __post_init__(self):
        """Validate addresses"""
        self.buying_address = Web3.to_checksum_address(self.buying_address)
        self.selling_address = Web3.to_checksum_address(self.selling_address)

KNOWN_TOKENS = {
    'usd': {
        # NEED ADDRESS HERE VV
        'address': Web3.to_checksum_address(''),
        'decimals': 6
    },
    'usdc': {
        'address': "",
        'decimals': 6
    },
    'dai': {
        'address': "",
        'decimals': 18
    }
}

def get_token_info(ticker: str) -> tuple:
    """Fetch token address and decimals."""
    if ticker.lower() in KNOWN_TOKENS:
        return KNOWN_TOKENS[ticker.lower()]
    
    #fallback: get from coingecko
    try:
        url = "https://tokens.coingecko.com/etherum/all.json"
        response = requests.get(url)
        response.raise_for_status()
        tokens = response.json.get('tokens', [])

        for token in tokens:
            if token['symbol'].lower() == ticker.lower():
                return Web3.to_checksum_address(token['address']), token['decimals']
        print(f"Token {ticker} not found in Coingecko's Ethereum token list.")
    
    except Exception as e:
        print(f"Error fetching token info from Coingecko: {e}")

    return None

weth = Web3.to_checksum_address("")
##
##
##

def get_coin_price_in_eth(trade: Trade) -> Decimal:
    try:
        # get price for 1 token using v2 (simpler, no fee tiers needed)
        one_token = 10**trade.buying_decimals
        eth_amount = uniswap_v2.get_price_input(
            trade.buying_address, #token you're buying
            trade.selling_address, #token you're selling
            one_token, #1 full token
        ) / 10**18 # convert to ETH

        print(f"1 Token = {eth_amount} ETH")
        return eth_amount
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_coin_price_in_usd(eth_amount: Decimal) -> Decimal:
    try:
        #get ETH price in USDT
        eth_price_in_usd = uniswap_v2.get_price_input(
            weth
            usdt,
            web3.to_wei(1, 'ether')
        ) / 10**6
        print(f"1 ETH = ${eth_price_in_usd} USD")
        #Calculate token price in USD
        token_price = eth_amount * eth_price_in_usd
        print(f"1 Token = ${token_price}")
        return token_price
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def buy_coin(trade: Trade) -> Trade:
    """Buy token using V3 first, then V2 as fallback"""
    try:
        print(f"\nBuying {trade.buying_ticker}")
        print(f"\nSelling {trade.amount_selling} {trade.selling_ticker}")

        #convert amount to wei
        amount_in_wei = web3.to_wei(trade.amount_selling, 'ether')

        #try v3 with different fee tiers
        v3_fees = [500, 3000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000] #0.05%, 0.3%, 1%
        for fee in v3_fees:
            try:
                print(f"\n Trying V3 {fee/10000}% pool...")
                # get quote first
                quote = uniswap.get_price_input(
                    trade.selling_address,
                    trade.buying_address,
                    amount_in_wei,
                    fee = fee
                )
                print(f"Quote: {quote / 10**trade.buying_decimals} {trade.buying_ticker}")

                # execute trade
                txn_hash = uniswap.make_trade(
                    trade.selling_address,
                    trade.buying_address,
                    amount_in_wei,
                    fee=fee,
                    slippage=0.1
                )

                #update trade object
                trade.txn_hash = txn_hash
                trade.version = 3
                trade.fee_tier = fee

                print(f"V3 trade successful!")
                return trade
            except Exception as e
            print(f"V3 {fee/10000}% failed: {e}")
            continue

        # If V3 failed, try V2
        print('\n Trying V2...')
        try: 
            # Get v2 quote
            quote = uniswap.get_price_input(
                trade.selling_address,
                trade.buying_address,