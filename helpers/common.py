from plotly import graph_objs as go, plotly as py, tools
from pymongo.cursor import Cursor
import pandas as pd
from settings.config import plotly_key, plotly_username

tools.set_credentials_file(plotly_username, plotly_key)


def convert_docs_to_df(docs: Cursor) -> pd.DataFrame:
    df = pd.DataFrame(list(docs))
    df.index = pd.to_datetime(df.ts, unit='s')
    del df['_id']
    return df


def resample_df(df: pd.DataFrame, field: str, grouping_range: str) -> pd.DataFrame:
    return df[field].resample(grouping_range).ohlc()


def add_ts_based_on_index(df: pd.DataFrame) -> pd.DataFrame:
    df['ts'] = pd.to_datetime(df.index)
    return df


def plotly_candles(df, name='candles', indicators=None, shorts=None, longs=None):
    if not indicators:
        indicators = []
    candles = go.Candlestick(x=df.index,
                             open=df.open,
                             high=df.high,
                             low=df.low,
                             close=df.close,
                             name=name)
    draw_obj = [candles]
    layout = None
    for indicator in indicators:
        draw_obj.append(
            go.Scatter(
                x=df.index,
                y=df[indicator],
                mode='lines',
                name=indicator
            )
        )
    shapes = []
    if shorts:
        for short in shorts:
            shapes.append({
                        'type': 'line',
                        'x0': short['ts'],
                        'y0': int(short['high'])-0.01*int(short['high']),
                        'x1': short['ts'],
                        'y1': int(short['high'])+0.01*int(short['high']),
                        'line': {
                            'color': 'rgb(55, 128, 191)',
                            'width': 1,
                            'dash': 'dash'
                        },
                    })
    if longs:
        for long in longs:
            shapes.append({
                        'type': 'line',
                        'x0': long['ts'],
                        'y0': int(long['high'])-0.01*int(long['high']),
                        'x1': long['ts'],
                        'y1': int(long['high'])+0.01*int(long['high']),
                        'line': {
                            'color': 'rgb(128, 128, 55)',
                            'width': 1,
                            'dash': 'dash'
                        },
                })
    if shapes:
        layout = {
            'shapes': shapes
        }
    if layout:
        fig = {
            'data': draw_obj,
            'layout': layout,
        }
    else:
        fig = draw_obj
    py.plot(fig, filename=name)
