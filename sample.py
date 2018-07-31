import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from mpl_finance import candlestick_ochl
import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
import plotly
plotly.tools.set_credentials_file('macic', 'qtTIvT3FMnMIEF7gTt5L')

matplotlib.use('TkAgg')

rolling_window = 20
no_of_std = 1.5
field = 'close'
time_range = 'D'
filename = 'bitstampUSD.csv'
start_date = '2018-05-25'
end_date ='2018-12-12'

money = 100
open_trade_type = None
open_trade_price = None
open_trade_volume = 0

df = pd.read_csv(filename, names=['ts', 'price', 'volume'])
df.index = pd.to_datetime(df.ts, unit='s')
df = df.loc[start_date:end_date]
df = df['price'].resample(time_range).ohlc()


def plotly_candles(df, name='candles', indicators=None):
    if not indicators:
        indicators = []
    candles = go.Candlestick(x=df.index,
                           open=df.open,
                           high=df.high,
                           low=df.low,
                           close=df.close,
                           name=name)
    draw_obj = [candles]
    for indicator in indicators:
        draw_obj.append(
            go.Scatter(
                x=df.index,
                y=df[indicator],
                mode='lines',
                name=indicator
            )
        )
    py.plot(draw_obj, filename='simple_candlestick')

def plot_candles():
    global df
    # drop the date index from the dateframe
    df.reset_index(inplace=True)
    # convert the datetime64 column in the dataframe to 'float days'
    df.ts = mdates.date2num(df.ts)
    # make an array of tuples in the specific order needed
    dataAr = [tuple(x) for x in df[['ts', 'open', 'close', 'high', 'low']].to_records(index=False)]
    # construct and show the plot
    fig = plt.figure()
    ax1 = plt.subplot(1, 1, 1)
    candlestick_ochl(ax1, dataAr, colorup='k', colordown='r', alpha=0.8)
    plt.show()


#plot_candles()
from ta import bollinger_hband_indicator
rolling_mean = df[field].rolling(rolling_window).mean()
rolling_std = df[field].rolling(rolling_window).std()
df['rolling_mean'] = rolling_mean
df['bollinger_high'] = rolling_mean + (rolling_std * no_of_std)
df['bollinger_low'] = rolling_mean - (rolling_std * no_of_std)

#plotly_candles(df, 'BTC/USD', ['bollinger_high', 'bollinger_low'])


df['position'] = None
def close_previous_open_new_trade(type_, price):
    global open_trade_volume, open_trade_type, open_trade_price, money
    if open_trade_type is not None:
        price_diff = price - open_trade_price
        revenue = -(price_diff * open_trade_volume) if open_trade_type=='sell' else (price_diff * open_trade_volume)
        money = revenue # get the money back
        if money<=0:
            exit()
        open_trade_type = None
    open_trade_type = type_
    open_trade_price = price
    open_trade_volume = money / price
    print ("close previous open new")
    print ("type", open_trade_type)
    print ("volume", open_trade_volume)
    print ("price", price)
    print ("money", money)
    print ("------------------------")

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
            close_previous_open_new_trade('sell', df[field].iloc[row])

    if (df[field].iloc[row] < df['bollinger_low'].iloc[row]) and (
            df[field].iloc[row - 1] > df['bollinger_low'].iloc[row - 1]) \
            and previous != 'buy':
        df['position'].iloc[row] = 1
        previous = 'buy'
        if df['position'].iloc[row - 1] != 1:
            trades_list.append({'buy': {field: df[field].iloc[row], 'ts': df.index[0]}})
            close_previous_open_new_trade('buy', df[field].iloc[row])

df['position'].fillna(method='ffill', inplace=True)

# Calculate the daily market return and multiply that by the position to determine strategy returns
df['timeframe_return'] = np.log(df[field] / df[field].shift(1))
df['strategy_return'] = df['timeframe_return'] * df['position']

# Plot the strategy returns
total = df['strategy_return'].cumsum()
#print("trades_list", trades_list)
#print("number of trades", len(trades_list))
print("last total value", total.iloc[-1:])
#total.plot()
#plt.show()
#df[[field, 'bollinger_high', 'bollinger_low', 'position']].plot()

#plt.show()

print(df.tail())
#quandl - daily data library - easy