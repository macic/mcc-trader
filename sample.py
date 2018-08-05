import datetime
import plotly

from database.services import get_dataframe_from_timerange
from helpers.common import plotly_candles
from settings.config import plotly_key, plotly_username

plotly.tools.set_credentials_file(plotly_username, plotly_key)


rolling_window = 20
no_of_std = 1.5
field = 'close'
time_range = '5T'
filename = 'bitstampUSD.csv'
start_date = '2018-07-28'
end_date = '2018-12-12'
pair_name = 'BTC_USD'

money = 100
open_trade_type = None
open_trade_price = None
open_trade_volume = 0

"""
df = read_csv()
save_to_db(pair_name, time_range, df)
print(df.tail(5))
del df
"""
from settings.config import mongo_db, mongo_uri
from database.services import  init_database
mongo_client = init_database(mongo_uri)

start_date_ts = datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp()
end_date_ts = datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp()
df = get_dataframe_from_timerange(mongo_client[mongo_db], pair_name, 'ticks', start_date_ts, end_date_ts)
#df['ts'] = pd.to_datetime(df['ts'], unit='s')
df = df.set_index('ts')
df = df['last'].resample(time_range).ohlc()
print(df.tail(5))

rolling_mean = df[field].rolling(rolling_window).mean()
rolling_std = df[field].rolling(rolling_window).std()
df['rolling_mean'] = rolling_mean
df['bollinger_high'] = rolling_mean + (rolling_std * no_of_std)
df['bollinger_low'] = rolling_mean - (rolling_std * no_of_std)

df['position'] = None


def close_previous_open_new_trade(type_, price):
    global open_trade_volume, open_trade_type, open_trade_price, money
    if open_trade_type is not None:
        price_diff = price - open_trade_price
        revenue = -(price_diff * open_trade_volume) if open_trade_type == 'sell' else (price_diff * open_trade_volume)
        money = revenue  # get the money back
        if money <= 0:
            exit()
        open_trade_type = None
    open_trade_type = type_
    open_trade_price = price
    open_trade_volume = money / price
    # print("close previous open new")
    # print("type", open_trade_type)
    # print("volume", open_trade_volume)
    # print("price", price)
    # print("money", money)
    # print("------------------------")

#
# trades_list = []
# previous = None
# for row in range(len(df)):
#
#     if (df[field].iloc[row] > df['bollinger_high'].iloc[row]) and (
#             df[field].iloc[row - 1] < df['bollinger_high'].iloc[row - 1]) \
#             and previous != 'sell':
#         df['position'].iloc[row] = -1
#         previous = 'sell'
#         # check if position was different before
#         if df['position'].iloc[row - 1] != -1:
#             trades_list.append({'sell': {field: df[field].iloc[row], 'ts': df.index[0]}})
#             close_previous_open_new_trade('sell', df[field].iloc[row])
#
#     if (df[field].iloc[row] < df['bollinger_low'].iloc[row]) and (
#             df[field].iloc[row - 1] > df['bollinger_low'].iloc[row - 1]) \
#             and previous != 'buy':
#         df['position'].iloc[row] = 1
#         previous = 'buy'
#         if df['position'].iloc[row - 1] != 1:
#             trades_list.append({'buy': {field: df[field].iloc[row], 'ts': df.index[0]}})
#             close_previous_open_new_trade('buy', df[field].iloc[row])
#
# df['position'].fillna(method='ffill', inplace=True)
#
# # Calculate the daily market return and multiply that by the position to determine strategy returns
# df['timeframe_return'] = np.log(df[field] / df[field].shift(1))
# df['strategy_return'] = df['timeframe_return'] * df['position']
#
# # count total the strategy returns
# total = df['strategy_return'].cumsum()
# print("last total value", total.iloc[-1:])
#
# print(df.tail())
# quandl - daily data library - easy
plotly_candles(df, pair_name, ['bollinger_high', 'bollinger_low'])
