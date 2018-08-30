import pandas as pd
import ta
import inspect


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
                    # print(yellow("Adding %s with arguments:" % indicator), self.indicator_args[indicator])
            self.df[indicator] = ind(**kwargs)

    def set_df(self, df):
        self.df = df

    def get_df(self):
        return self.df

    def should_open_position(self, *args, **kwargs):
        raise NotImplementedError

    def should_close_position(self, *args, **kwargs):
        raise NotImplementedError

    def opposite_candle(self, position, check_two_candles=False, **kwargs):
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        if position == 'buy':
            if last['close'] < last['open']:
                if check_two_candles:
                    if prev['close'] < prev['open']:
                        return True
                    else:
                        return False
                return True
        elif position == 'sell':
            if last['close'] > last['open']:
                if check_two_candles:
                    if prev['close'] > prev['open']:
                        return True
                    else:
                        return False
                return True

    def take_profit_percentage_with_trailing_stop_loss(self, open_price, position, gain=7.5, absolute_stop_loss=0,
                                                       **kwargs):
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        if position == 'buy':
            more = open_price * (1 + gain / 100)  # take profit via percentage
            less = max(prev['close'] - absolute_stop_loss, open_price - absolute_stop_loss)  # stop loss absolute value
        else:
            more = min(prev['close'] + absolute_stop_loss, open_price + absolute_stop_loss)  # stop loss absolute value
            less = open_price * (1 - gain / 100)  # take profit via %
        if last['close'] > more or last['close'] < less:
            return True

    def price_moved_by_percentage(self, open_price, position, gain=7.5, loose=2.5, **kwargs):
        last = self.df.iloc[-1]
        if position == 'buy':
            percentage_more = open_price * (1 + gain / 100)  # 7.5%
            percentage_less = open_price * (1 - loose / 100)  # 2.5%
        else:
            percentage_more = open_price * (1 + loose / 100)  # 2.5%
            percentage_less = open_price * (1 - gain / 100)  # 7.5%
        if last['close'] > percentage_more or last['close'] < percentage_less:
            return True

    @staticmethod
    def is_pinbar(candle, pinbar_min_size=50, pinbar_percentage=20, nose_toleration_percentage=5, **kwargs):
        total = abs(candle['high'] - candle['low'])
        if total < pinbar_min_size:
            return False, False
        body = abs(candle['open'] - candle['close'])

        top_wick = candle['high'] - max(candle['close'], candle['open'])
        bottom_wick = min(candle['close'], candle['open']) - candle['low']

        if top_wick <= (nose_toleration_percentage / 100) * total:
            if body <= (pinbar_percentage / 100) * total:
                print("PINBAR BUY", body, total, top_wick)
                return True, 'buy'
        elif bottom_wick <= (nose_toleration_percentage / 100) * total:
            if body <= (pinbar_percentage / 100) * total:
                print("PINBAR SELL", body, total, bottom_wick)
                return True, 'sell'
        return False, False
