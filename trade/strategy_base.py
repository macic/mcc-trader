import pandas as pd
import ta
import inspect
from helpers.console_colors import yellow
from trade.order import Order


class StrategyParser(object):
    indicators_required: list = []
    indicator_ranges: dict = None
    indicator_args: dict = {}  # example {'ema_slow': {'n_slow': 12}, 'ichimoku_a': {'n1': 12}}}
    df: pd.DataFrame = None

    def __init__(self, df, indicators_args=None):
        self.df = df
        self.indicator_args = indicators_args if indicators_args else {}
        self.calculate_indicators()

    def calculate_indicators(self):
        if self.df is None:
            raise RuntimeError
        for indicator in self.indicators_required:
            ind = getattr(ta, indicator)
            available_ind_args = inspect.getargs(ind.__code__)[0]
            args = []
            kwargs = {}
            for available_ind_arg in available_ind_args:
                # convert high, open, close, low to kwargs used by indicator
                if available_ind_arg in self.df.columns:
                    args.append(self.df[available_ind_arg])
                    kwargs[available_ind_arg] = self.df[available_ind_arg]

                # convert specified kwargs to kwargs used by indicator
                if indicator in self.indicator_args and available_ind_arg in self.indicator_args[indicator]:
                    kwargs.update(self.indicator_args[indicator])
                    #print(yellow("Adding %s with arguments:" % indicator), self.indicator_args[indicator])
            self.df[indicator] = ind(**kwargs)

    def set_df(self, df):
        self.df = df

    def get_df(self, df):
        return self.df

    def should_open_position(self, *args, **kwargs):
        raise NotImplementedError

    def should_close_position(self, *args, **kwargs):
        raise NotImplementedError

    def opposite_candle(self, position):
        last = self.df.iloc[-1]
        if position == 'buy':
            if last['close'] < last['open']:
                return True
        elif position == 'sell':
            if last['close'] > last['open']:
                return True

    def price_moved_by_percentage(self, open_price, position, gain=7.5, loose=2.5):
        last = self.df.iloc[-1]
        if position == 'buy':
            percentage_more = open_price * (1 + gain / 100)  # 7.5%
            percentage_less = open_price * (1 - loose / 100)  # 2.5%
        else:
            percentage_more = open_price * (1 + loose / 100)  # 2.5%
            percentage_less = open_price * (1 - gain / 100)  # 7.5%
        if last['close'] > percentage_more or last['close'] < percentage_less:
            return True