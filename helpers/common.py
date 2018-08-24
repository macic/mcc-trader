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

def convert_orders_to_df(docs: Cursor) -> pd.DataFrame:
    df = pd.DataFrame(list(docs))
    #print(df.head())
    #df.open_ts = pd.to_datetime(df.open_ts, unit='s')
    #df.close_ts = pd.to_datetime(df.close_ts, unit='s')
    #del df['_id']
    return df



def resample_df(df: pd.DataFrame, field: str, grouping_range: str) -> pd.DataFrame:
    return df[field].resample(grouping_range).ohlc()

def resample_ohlc(df: pd.DataFrame, grouping_range: str) -> pd.DataFrame:
    return df.resample(grouping_range).agg({'open': 'first',
                           'high': 'max',
                           'low': 'min',
                           'close': 'last'})

def add_ts_based_on_index(df: pd.DataFrame) -> pd.DataFrame:
    df['ts'] = pd.to_datetime(df.index)
    return df


def plotly_candles(df, name='candles', indicators=None, orders=None):
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
    annotations = []
    if orders is not None:
        for idx, order in orders.iterrows():
            text = order.position + ' ' + str(order.volume)
            ay = 130 if order.position=='buy' else -130
            ax= 20
            annotations.append({
                'x': order.open_ts,
                'y': order.open_price,
                'text': 'open '+ text,
                'showarrow': True,
                'font': {'family':'Courier New, monospace','size':14, 'color':'#ffffff'},
                'align':'center',
                'arrowhead': 2,
                'arrowsize': 1,
                'arrowwidth': 2,
                'arrowcolor':'#636363',
                'ax':  ax,
                'ay': ay,
                'bordercolor': '#c7c7c7',
                'borderwidth': 2,
                'borderpad': 4,
                'bgcolor': '#ff7f0e',
                'opacity': 0.8
            })
            annotations.append({
                'x': order.close_ts,
                'y': order.close_price,
                'text': 'close',
                'showarrow': True,
                'font': {'family': 'Courier New, monospace', 'size': 14, 'color': '#ffffff'},
                'align': 'center',
                'arrowhead': 2,
                'arrowsize': 1,
                'arrowwidth': 2,
                'arrowcolor': '#636363',
                'ax': ax,
                'ay': -ay,
                'bordercolor': '#c7c7c7',
                'borderwidth': 2,
                'borderpad': 4,
                'bgcolor': '#ff7f0e',
                'opacity': 0.8
            })
    if annotations:
        layout = {
            'annotations': annotations
        }
    if layout:
        fig = {
            'data': draw_obj,
            'layout': layout,
        }
    else:
        fig = draw_obj
    py.plot(fig, filename=name)
