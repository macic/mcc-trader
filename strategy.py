import pandas as pd
import sys
import ta

class conditionsIntefrace(object):

    def open_position(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def close_postion(self, *args, **kwargs) -> bool:
        raise NotImplementedError

class testConditions(conditionsIntefrace):

    def open_position(self, df):
        # poprzednia swieca zawiera EMA 12
        # high ostatniej swiecy jest ponizej EMA 12 - SHORT

        # poprzednia swieca zawiera EMA 12
        # low ostatniej swiecy jest powyzej EMA 12 - LONG

        df['ema_fast'] = ta.ema_fast(df['close'])
        last = df.iloc[-1]
        previous = df.iloc[-2]

        if previous['high'] >= previous['ema_fast'] >= previous ['low']:
            if last['high'] < last['ema_fast']:
                return 'short'
            elif last['low'] > last['ema_fast']:
                return 'long'

        return False

    def close_position(self, df):
        return True

class strategyParser(object):

    def __init__(self, df):
        self.df = df
        self.open_position = None
        self.open_price = None

    def set_df(self, df):
        self.df = df

    def get_df(self):
        return self.df

    def check_positions(self, strategy_name):
        conditions = getattr(sys.modules[__name__], strategy_name)
        if not issubclass(conditions, conditionsIntefrace):
            raise NotImplementedError
        if not self.open_position:
            position = self.should_open_position(conditions)
            if position:
                self.open_position = position
                self.open_price = self.df.iloc[-1]['close']
                return position
        else:
            print("closing")
            self.open_position = None
            self.open_price = None

    def should_open_position(self, conditions):

        return conditions().open_position(self.df)

    def should_close_position(self, conditions):
        return conditions().close_position(self.df)
