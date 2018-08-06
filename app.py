import baker
from database.services import init_database, get_dataframe_from_timerange
from settings.config import *
from strategy import strategyParser
from helpers.common import plotly_candles

@baker.command
def backtest(symbol, grouping_range, strategy_name, **kwargs):
    client = init_database(mongo_uri)
    db = client[mongo_db]
    df = get_dataframe_from_timerange(db, symbol, grouping_range, ts_start=0)

    shorts = []
    longs = []
    revenue = []
    strategy_object = strategyParser(balance=1000)
    for i in range(3, len(df.index)):
        sliced_df = df.iloc[0:i]
        strategy_object.set_df(sliced_df)
        result = strategy_object.check_positions(strategy_name, **kwargs)
        if result =='short':
            shorts.append({'ts': sliced_df.iloc[-1]['ts'], 'high': sliced_df.iloc[-1]['high']})
        elif result == 'long':
            longs.append({'ts': sliced_df.iloc[-1]['ts'], 'high': sliced_df.iloc[-1]['high']})
        elif isinstance(result, float):
            revenue.append(result)

    plotly_candles(sliced_df, 'backtest1', ['ema_fast'], shorts=shorts, longs=longs)

    #print ("shorty", shorts)
    #print ("longi", longs)
    #print ("revenue", revenue)
    print ("suma", sum(revenue))

    return sum(revenue)

if __name__=='__main__':
    baker.run()