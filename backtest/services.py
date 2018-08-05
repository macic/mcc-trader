import pandas as pd


def read_csv(filename, ts_field='ts', fields=None):
    if fields is None:
        fields = ['price', 'volume']
    names = [ts_field].append(fields)
    df = pd.read_csv(filename, names=names)
    df.index = pd.to_datetime(df.ts, unit='s')
    return df

