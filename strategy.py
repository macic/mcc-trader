import sys
import ta
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from helpers.logger import log


class conditionsIntefrace(object):

    def open_position(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def close_postion(self, *args, **kwargs) -> bool:
        raise NotImplementedError


class emafastConditions(conditionsIntefrace):

    def open_position(self, df, n_fast=12):
        df['ema_fast'] = ta.ema_fast(df['close'], n_fast=int(n_fast))
        last = df.iloc[-1]
        previous = df.iloc[-2]
        two_before = df.iloc[-3]

        if (previous['high'] >= previous['ema_fast'] >= previous['low']) and (
                two_before['high'] >= two_before['ema_fast'] >= two_before['low']):
            if last['high'] < last['ema_fast']:
                return 'short'
            elif last['low'] > last['ema_fast']:
                return 'long'

        return False

    def close_position(self, df, n_fast=12):
        return True


class strategyParser(object):
    df = None
    MAKER_FEE = Decimal(0.016)
    TAKER_FEE = Decimal(0.026)

    def __init__(self, balance=0):
        self.open_position = None
        self.open_price = None
        self.open_volume = None
        self.balance = Decimal(balance)
        self.fees_taken = 0

    def set_df(self, df):
        self.df = df

    def get_df(self):
        return self.df

    def check_positions(self, strategy_name, **kwargs):
        if self.balance <= 0:
            return 0
        conditions = getattr(sys.modules[__name__], strategy_name)
        if not issubclass(conditions, conditionsIntefrace):
            raise NotImplementedError
        current_price = Decimal(self.df.iloc[-1]['close']).quantize(Decimal('.01'))
        if not self.open_position:
            should_open = self.should_open_position(conditions, **kwargs)
            if should_open:
                self.open_volume = Decimal(self.balance / 2 / current_price).quantize(Decimal('.001'),
                                                                                      rounding=ROUND_DOWN)
                if self.open_volume == 0.000:
                    return 0
                self.open_price = Decimal(current_price)
                self.fees_taken = Decimal(self.open_price * self.open_volume * self.MAKER_FEE).quantize(Decimal('.01'),
                                                                                                        rounding=ROUND_UP)
                self.open_position = should_open
                self.balance = self.balance - self.open_volume * self.open_price - self.fees_taken
                log.debug("position open", extra={'open_position': self.open_position, 'open_volume': self.open_volume,
                                                  'price': self.open_price, 'fees_taken': self.fees_taken,
                                                  'balance_after': self.balance})
                return should_open
        else:
            should_close = self.should_close_position(conditions, **kwargs)
            if should_close:
                earnings = current_price * Decimal(self.open_volume)
                if self.open_position == 'long':
                    earnings = -earnings
                self.fees_taken = Decimal(self.fees_taken + current_price * self.open_volume * self.MAKER_FEE).quantize(
                    Decimal('.01'), rounding=ROUND_UP)
                self.balance = self.balance + earnings - self.fees_taken
                log.debug("position closed", extra={'earnings': earnings, 'closing price': current_price,
                                                    'closing balance': self.balance, 'fees_taken': self.fees_taken})
                self.open_position = None
                self.open_price = None
                self.open_volume = 0
                self.fees_taken = 0
                return earnings

    def should_open_position(self, conditions, **kwargs):

        return conditions().open_position(self.df, **kwargs)

    def should_close_position(self, conditions, **kwargs):
        return conditions().close_position(self.df, **kwargs)
