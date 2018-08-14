import pandas as pd
import ta


def multiplied_keltner_channel_lband(high, low, close, n=14, m=2, fillna=False):
    """Multiplied Keltner channel (MKC)

    Showing a simple moving average line (low) of typical price.

    https://en.wikipedia.org/wiki/Keltner_channel

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        m(int): multiplier

    Returns:
        pandas.Series: New feature generated.
    """
    lower = ta.ema_fast(close, n, fillna) - (m * ta.average_true_range(high, low, close, n, fillna))
    if fillna:
        lower = lower.fillna(method='backfill')
    return pd.Series(lower, name='mkc_lband')


def multiplied_keltner_channel_hband(high, low, close, n=14, m=2, fillna=False):
    """Multiplied Keltner channel (MKC)

    Showing a simple moving average line (low) of typical price.

    https://en.wikipedia.org/wiki/Keltner_channel

    Args:
        high(pandas.Series): dataset 'High' column.
        low(pandas.Series): dataset 'Low' column.
        close(pandas.Series): dataset 'Close' column.
        n(int): n period.
        m(int): multiplier

    Returns:
        pandas.Series: New feature generated.
    """
    middle = ta.ema_fast(close, n, fillna)
    lower = middle + (m * ta.average_true_range(high, low, close, n, fillna))
    if fillna:
        lower = lower.fillna(method='backfill')
    return pd.Series(lower, name='mkc_hband')
