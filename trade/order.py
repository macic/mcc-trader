from dataclasses import dataclass, asdict
import ccxt
from settings.config import kraken_secret, kraken_key
from random import randint
from database.services import save_order

broker = ccxt.kraken({
    'apiKey': kraken_key,
    'secret': kraken_secret,
    'verbose': False,  # switch it to False if you don't want the HTTP log
})


@dataclass()
class Order:
    status: str = ''  # open / closed
    open_price: float = 0.0  # price used to open the order
    closing_price: float = 0.0  # price used to close the order

    symbol: str = ''  # BTCUSD
    position: str = ''  # buy / sell
    ordertype: str = ''  # market limit ...
    # price: str #price used to create order
    # price2: str #price2 used to create order
    volume: float = 0.0  # volume
    leverage: int = 0
    fees_taken: float = 0.0
    closing_fees_taken: float = 0.0
    id: str = ''

    def open_order(self):
        # response = broker.create_order(self.symbol, 'limit', self.position, self.volume, self.open_price)
        # @TODO call ccxt.open_order or whatever
        # parse respone and update data
        response = {'id': randint(1000, 9999)}
        if response.get('id'):
            self.id = response['id']
            self.status = 'open'
            self.ordertype = 'limit'
            money_taken = float("{:.2f}".format(self.open_price * self.volume))
            print("money taken", money_taken)
            self.fees_taken = float("{:.2f}".format(money_taken * 0.016))
            self.save()
            return money_taken + self.fees_taken
        return False

    def close_order(self, closing_price, closing_position):
        # response = broker.create_order(self.symbol, 'limit', self.position, self.volume, self.open_price)
        response = {'id': self.id}
        if response.get('id'):
            self.status = 'closed'
            self.closing_price = closing_price
            short_adjustement = 0
            opening_money = float("{:.2f}".format(self.open_price * self.volume))
            closing_money = float("{:.2f}".format(closing_price * self.volume))
            if self.position=='sell':
                short_adjustement = opening_money - closing_money
            money_received = short_adjustement + closing_money
            print("money received", money_received)
            self.closing_fees_taken = float("{:.2f}".format(money_received * 0.016))
            self.save()
            return money_received - self.closing_fees_taken
        return False

    def save(self):
        to_save = asdict(self)
        save_order(to_save)
