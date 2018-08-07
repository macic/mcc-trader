import pandas as pd


def read_csv(filename, ts_field='ts'):
    names = [ts_field, 'price', 'volume']
    df = pd.read_csv(filename, names=names)
    df.index = pd.to_datetime(df.ts, unit='s')
    return df
