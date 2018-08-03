from pymongo.cursor import Cursor
import pandas as pd


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