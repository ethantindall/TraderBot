from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from datetime import datetime


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
    amount_buying: Optional[Decimal] = 1
    amount_selling: Optional[Decimal] = 0.002
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
