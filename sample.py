import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use('TkAgg')

rolling_window = 100
no_of_std = 1.5
field = 'close'
time_range = '12h'

df = pd.read_csv('btceEUR.csv', names=['ts', 'price', 'volume'])
df.index = pd.to_datetime(df.ts, unit='s')

df = df['price'].resample(time_range).ohlc()

rolling_mean = df[field].rolling(rolling_window).mean()
rolling_std = df[field].rolling(rolling_window).std()
df['rolling_mean'] = rolling_mean
df['bollinger_high'] = rolling_mean + (rolling_std * no_of_std)
df['bollinger_low'] = rolling_mean - (rolling_std * no_of_std)

print(df.tail())

df['position'] = None

# df[[field, 'bollinger_high', 'bollinger_low']].plot()
# plt.show()


# Fill our newly created position column - set to sell (-1) when the price hits the upper band, and set to buy (1) when it hits the lower band
trades_list = []
previous = None
for row in range(len(df)):

    if (df[field].iloc[row] > df['bollinger_high'].iloc[row]) and (
            df[field].iloc[row - 1] < df['bollinger_high'].iloc[row - 1]) \
            and previous != 'sell':
        df['position'].iloc[row] = -1
        previous = 'sell'
        # check if position was different before
        if df['position'].iloc[row - 1] != -1:
            trades_list.append({'sell': {field: df[field].iloc[row], 'ts': df.index[0]}})

    if (df[field].iloc[row] < df['bollinger_low'].iloc[row]) and (
            df[field].iloc[row - 1] > df['bollinger_low'].iloc[row - 1]) \
            and previous != 'buy':
        df['position'].iloc[row] = 1
        previous = 'buy'
        if df['position'].iloc[row - 1] != 1:
            trades_list.append({'buy': {field: df[field].iloc[row], 'ts': df.index[0]}})

df['position'].fillna(method='ffill', inplace=True)

# Calculate the daily market return and multiply that by the position to determine strategy returns
df['timeframe_return'] = np.log(df[field] / df[field].shift(1))
df['strategy_return'] = df['timeframe_return'] * df['position']

# Plot the strategy returns
total = df['strategy_return'].cumsum()
print("total", total)
print(df.tail(n=5))
print("trades_list", trades_list)
print("number of trades", len(trades_list))
# total.plot()
# plt.show()
