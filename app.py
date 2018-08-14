import baker
from database.services import init_database, get_dataframe_from_timerange, save_data, resample_and_save_ticks, \
    get_last_order, clear_collection, get_orders
from settings.config import *
from strategy import strategyParser
from trade.order import Order
from trade.indicators import multiplied_keltner_channel_lband, multiplied_keltner_channel_hband
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
    resample_and_save_ticks(ticks, symbol, grouping_range, price_field='price')


@baker.command
def resample(symbol, to_grouping):
    ticks = get_dataframe_from_timerange(db, symbol, 'ticks', 0)
    resample_and_save_ticks(ticks, symbol, to_grouping)


@baker.command
def plot(symbol, grouping_range, ts_start=0):
    import datetime
    d = datetime.date(2017, 1, 1)
    import time
    ts_start = time.mktime(d.timetuple())
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=ts_start)
    df['ema_fast'] = ta.ema_fast(df['close'], 32)
    df['ema_slow'] = ta.ema_slow(df['close'], 9)
    df['ichimoku_a'] = ta.ichimoku_a(df['high'], df['low'])
    df['ichimoku_b'] = ta.ichimoku_b(df['high'], df['low'])
    # df['keltner_low'] = ta.keltner_channel_lband(df['high'], df['low'], df['close'])
    # df['keltner_high'] = ta.keltner_channel_hband(df['high'], df['low'], df['close'])
    # df['mkl'] = multiplied_keltner_channel_lband(df['high'], df['low'], df['close'], n=14, m=2)
    # df['atr'] = ta.average_true_range(df['high'], df['low'], df['close'], n=14)
    # df['ema'] = ta.ema_slow(df['close'], 14)
    # df['mkh'] = multiplied_keltner_channel_hband(df['high'], df['low'], df['close'], n=14, m=2)
    # df['mkh'] = multiplied_keltner_channel_hband(df['high'], df['low'], df['close'], n=14, m=2)
    # plotly_candles(df, 'test_plot', ['ichimoku_a', 'ichimoku_b'])

    orders = get_orders(symbol, ts_start=ts_start)
    #print(orders.head())
    plotly_candles(df, 'test_plot', orders=orders, indicators=['ema_fast', 'ema_slow'])


@baker.command
def run_strategy(symbol, grouping_range, ts_start=0, df=None, indicator_args=None, **kwargs):
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
    strategy = EmaStrategy(df, indicators_args=indicator_args)

    order = get_last_order(symbol)
    last_price = df.iloc[-1]['close']
    ts = df.iloc[-1]['ts']
    if order:
        if order.status == 'open':
            should_close = strategy.should_close_position(order, **kwargs)
            if should_close:
                balance_given = order.close_order(closing_price=last_price, ts=ts)
                balance.set_balance(balance.current_balance + balance_given)
            return

    should_open, position = strategy.should_open_position(**kwargs)
    if should_open:
        # calculate how much we can open in volume

        volume = balance.calculate_possible_order_volume(last_price)
        # create order instance
        order = Order(symbol=symbol, position=position, volume=volume, open_price=last_price)

        balance_taken = order.open_order(ts)
        balance.set_balance(balance.current_balance - balance_taken)

import sys
@baker.command
def backtest_strategy(symbol, grouping_range, ts_start=0, clear_orders=False):
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=ts_start)

    n_slows = [32] #32
    n_fasts = [9]  #9
    stop_loss_percentages = [2] #2
    take_profit_percentages = [12] #12
    for n_slow in n_slows:
        for n_fast in n_fasts:
            for sl_p in stop_loss_percentages:
                for tp_p in take_profit_percentages:
                    params = {'stop_loss_percentage': sl_p, 'take_profit_percentage': tp_p}
                    if clear_orders:
                        clear_collection('orders')
                    balance.set_balance(1000.0)
                    indicator_args ={'ema_slow': {'n_slow': n_slow}, 'ema_fast': {'n_fast': n_fast}}
                    print("STARTING", indicator_args, balance.current_balance, params)
                    sys.stdout.flush()

                    end = len(df.index)
                    for end_pos in range(50, end):
                        start_pos = 0 if end_pos < 300 else end_pos-300
                        sliced_df = df.iloc[start_pos:end_pos].copy()
                        run_strategy(symbol, grouping_range, ts_start, df=sliced_df, indicator_args=indicator_args, **params)
                        del sliced_df
                    print("FINAL BALANCE", indicator_args, balance.current_balance, params)

    #plotly_candles(df, 'backtest2', indicators=['ema_fast', 'ema_slow'])


if __name__ == '__main__':
    baker.run()
