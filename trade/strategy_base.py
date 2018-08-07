import pandas as pd
import ta
import inspect

class StrategyParser(object):

    indicators_required: list = []
    indicator_ranges: dict = None
    df: pd.DataFrame = None

    def __init__(self, df):
        self.df = df
        self.calculate_indicators()

    def calculate_indicators(self):
        if self.df is None:
            raise RuntimeError
        for indicator in self.indicators_required:
            ind = getattr(ta, indicator)
            available_ind_args = inspect.getargs(ind.__code__)[0]
            args = []
            #if 'close' in available_ind_args:
             #   args.append(self.df['close'])
            for available_ind_arg in available_ind_args:
                if available_ind_arg in self.df.columns:
                    args.append(self.df[available_ind_arg])
            print("Adding %s with arguments: %s." %(indicator, str(args)))
            self.df[indicator] = ind(*args)
            print(self.df.tail())

    def set_df(self, df):
        self.df = df

    def get_df(self, df):
        return self.df