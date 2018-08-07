from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Order(object):
    status: str #open / closed
    open_price: Decimal #price used to open the order
    closing_price: Decimal #price used to close the order

    symbol: str #BTCUSD
    position: str #buy / sell
    ordertype: str #market limit ...
    #price: str #price used to create order
    #price2: str #price2 used to create order
    volume: Decimal #volume
    leverage: int

