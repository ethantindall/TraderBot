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
