import baker
from time import time, mktime
import datetime
from database.services import init_database, get_dataframe_from_timerange, resample_and_save_ticks, \
    get_last_order, clear_collection, get_orders, resample_and_save
from settings.config import *
from trade.order import Order
from trade.balance import Balance
from helpers.common import plotly_candles
from helpers.logger import log
from backtest.services import read_csv
import ta
from trade.strategies import EmaStrategy, BBPinbarStrategy, BBPinbarOppositeBandStrategy

client = init_database(mongo_uri)
db = client[mongo_db]

balance = Balance(current_balance=1000.0)


@baker.command
def import_and_convert(filename, ts_field, symbol, grouping_range):
    ticks = read_csv(filename, ts_field)
    resample_and_save_ticks(ticks, symbol, grouping_range, price_field='price')


@baker.command
def resample(symbol, from_grouping, to_grouping):
    data = get_dataframe_from_timerange(db, symbol, from_grouping, 0)
    if from_grouping == 'ticks':
        resample_and_save_ticks(data, symbol, to_grouping)
    else:
        resample_and_save(data, symbol, to_grouping)


@baker.command
def plot(symbol, grouping_range, ts_start=0, ts_end=0, skip_orders=False):
    if not ts_start:
        d = datetime.date(2018, 1, 11)
        ts_start = mktime(d.timetuple())
    if not ts_end:
        d2 = datetime.date(2018, 12, 18)
        ts_end = mktime(d2.timetuple())

    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=ts_start, ts_end=ts_end)
    df['ema_fast'] = ta.ema_fast(df['close'], 32)
    df['ema_slow'] = ta.ema_slow(df['close'], 9)
    df['bollinger_hband'] = ta.bollinger_hband(df['close'], 26, 1.9)
    df['bollinger_lband'] = ta.bollinger_lband(df['close'], 26, 1.9)
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

    if not skip_orders:
        orders = get_orders(symbol, ts_start=ts_start, ts_end=ts_end)
    else:
        orders = None
    plotly_candles(df, 'test_plot', orders=orders, indicators=['bollinger_hband', 'bollinger_lband'])
    # plotly_candles(df, 'test_plot', orders=orders)


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
    # strategy = EmaStrategy(df, indicators_args=indicator_args)
    strategy = BBPinbarStrategy(df, indicators_args=indicator_args)
    #strategy = BBPinbarOppositeBandStrategy(df, indicators_args=indicator_args)

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

    # EMA - n_slow = 32, n_fast= 9, sl_p = 2, tp_p=12 grouping=H

    n_range = [26]
    ndev_range = [1.9]
    pinbar_min_size_range = [1.8]
    pinbar_percentage_range = [19]
    tp_percentage_range = [8]
    sl_percentage_range = [3.5]
    for tp_percentage in tp_percentage_range:
        for sl_percentage in sl_percentage_range:
            for n in n_range:
                for ndev in ndev_range:
                    for pinbar_min_size in pinbar_min_size_range:
                        for pinbar_percentage in pinbar_percentage_range:
                            # set args
                            indicator_args = {'bollinger_lband': {'n': n, 'ndev': ndev},
                                              'bollinger_hband': {'n': n, 'ndev': ndev}}
                            params = {'pinbar_percentage': pinbar_percentage,
                                      'pinbar_min_size': pinbar_min_size,
                                      'take_profit_percentage': tp_percentage,
                                      'trailing_stop_loss_percentage': sl_percentage}

                            if clear_orders:
                                clear_collection('orders')
                            balance.set_balance(1000.0)
                            start_ts = int(time())
                            log.info("Starting", extra={'indicator_args': indicator_args, 'balance': balance.current_balance,
                                                        'theparams': params})

                            end = len(df.index)
                            for end_pos in range(50, end):
                                start_pos = 0 if end_pos < 300 else end_pos - 300
                                sliced_df = df.iloc[start_pos:end_pos].copy()
                                run_strategy(symbol, grouping_range, ts_start, df=sliced_df,
                                             indicator_args=indicator_args,
                                             **params)
                                del sliced_df
                            log.info("Final BALANCE", extra={'indicator_args': indicator_args, 'balance': balance.current_balance,
                                                             'theparams': params, 'duration': int(time() - start_ts)})
                            sys.stdout.flush()


if __name__ == '__main__':
    baker.run()
