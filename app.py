import baker
from database.services import init_database, get_dataframe_from_timerange, save_data, resample_and_save_ticks, get_last_order, clear_collection
from settings.config import *
from strategy import strategyParser
from trade.order import Order
from trade.balance import Balance
from helpers.common import plotly_candles
from backtest.services import read_csv
import ta

from trade.strategies import EmaStrategy

client = init_database(mongo_uri)
db = client[mongo_db]

balance = Balance(current_balance=1000.0)

@baker.command
def import_and_convert(filename, ts_field, symbol, grouping_range):
    ticks = read_csv(filename, ts_field)
    resample_and_save_ticks(ticks, db, symbol, grouping_range, price_field='price')


@baker.command
def plot(symbol, grouping_range, ts_start=0):
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start)
    plotly_candles(df, 'test_plot')


@baker.command
def backtest(symbol, grouping_range, strategy_name, **kwargs):
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=0)

    shorts = []
    longs = []
    revenue = []
    strategy_object = strategyParser(balance=1000)
    for i in range(3, len(df.index)):
        sliced_df = df.iloc[0:i]
        strategy_object.set_df(sliced_df)
        result = strategy_object.check_positions(strategy_name, **kwargs)
        if result == 'short':
            shorts.append({'ts': sliced_df.iloc[-1]['ts'], 'high': sliced_df.iloc[-1]['high']})
        elif result == 'long':
            longs.append({'ts': sliced_df.iloc[-1]['ts'], 'high': sliced_df.iloc[-1]['high']})
        elif isinstance(result, float):
            revenue.append(result)

    # recalculate for plot
    df['ichimoku_a'] = ta.ichimoku_a(df['high'], df['low'])
    df['ichimoku_b'] = ta.ichimoku_b(df['high'], df['low'])
    df['macd'] = ta.macd(df['close'], n_fast=int(kwargs.get('n_fast', 12)), n_slow=int(kwargs.get('n_slow', 40)))
    df['ema_fast'] = ta.ema_fast(df['close'], n_fast=int(kwargs.get('n_fast', 12)))
    df['ema_slow'] = ta.ema_slow(df['close'], n_slow=int(kwargs.get('n_slow', 40)))
    print(df.tail())
    plotly_candles(df.iloc[0:1000], 'backtest1', ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b'], shorts=shorts, longs=longs)

    # print ("shorty", shorts)
    # print ("longi", longs)
    # print ("revenue", revenue)
    print("suma", sum(revenue))

    return sum(revenue)

@baker.command
def run_strategy(symbol, grouping_range, ts_start=0, df=None):

    # load data from mongo for given timeframe
    # initialize strategy with indicators and their parameters
    # check if order is open
        # yes - check if should close order
            # yes - close order (save to db, calculate revenue)
            # no - iterate
        # no - check if should open order
            # yes - open order (save to db)
            # no - iterate

    if df is None:
        df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=ts_start)
    #strategy = EmaStrategy(df, indicators_args={'ema_fast': {'n_fast': 5}})
    strategy = EmaStrategy(df)

    order = get_last_order(symbol)
    last_price = df.iloc[-1]['close']
    if order:
        if order.status == 'open':
            should_close = strategy.should_close_position(order.position)
            if should_close:
                closing_position = 'buy' if order.position=='sell' else 'sell'
                balance_given = order.close_order(closing_price=last_price, closing_position=closing_position)
                balance.set_balance(balance.current_balance + balance_given)
            return

    should_open, position = strategy.should_open_position()
    if should_open:
        #calculate how much we can open in volume

        volume = balance.calculate_possible_order_volume(last_price)
        # create order instance
        order = Order(symbol=symbol, position=position, volume=volume, open_price=last_price)

        balance_taken = order.open_order()
        balance.set_balance(balance.current_balance-balance_taken)
    #plotly_candles(df.iloc[0:1000], 'backtest2', ['ema_fast', 'ema_slow', 'ichimoku_a', 'ichimoku_b'])


@baker.command
def backtest_strategy(symbol, grouping_range, ts_start=0, clear_orders=False):
    if clear_orders:
        clear_collection('orders')
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=ts_start)

    #for i in range(100, 110):
    end = len(df.index)
    end = 1000
    for i in range(100, end):
        sliced_df = df.iloc[0:i]
        run_strategy(symbol, grouping_range, ts_start, df=sliced_df)
    print("FINAL BALANCE", balance.current_balance)


if __name__ == '__main__':
    baker.run()

