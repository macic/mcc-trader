import pandas as pd

df = pd.read_csv('btceEUR.csv', names=['ts', 'price', 'volume'])
df.index = pd.to_datetime(df.ts, unit='s')

df = df['price'].resample('12h').ohlc()
print(df)