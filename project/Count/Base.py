import pandas as pd
import numpy as np

class Pandas_count():
    @staticmethod
    def highest(row_data: pd.Series, freq: int):
        """
            取得資料滾動的最高價
        """
        return row_data.rolling(freq).max()

    @staticmethod
    def lowest(row_data: pd.Series, freq: int):
        """
            取得資料滾動的最低價
        """
        return row_data.rolling(freq).min()
    

class vecbot_count():
    @staticmethod
    def max_rolling(a, window, axis=1):
        try:
            max_arr = np.empty(shape=a.shape[0])
            shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
            strides = a.strides + (a.strides[-1],)
            rolling = np.lib.stride_tricks.as_strided(
                a, shape=shape, strides=strides)
            max_arr[window-1:] = np.roll(np.maximum.reduce(rolling, axis=1), 1)
            max_arr[:window] = np.nan
            return max_arr
        except Exception as e:
            if "negative dimensions are not allowed" in str(e):
                return 0
            else:
                raise e
    @staticmethod
    def min_rolling(a, window, axis=1):
        try:
            min_arr = np.empty(shape=a.shape[0])
            shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
            strides = a.strides + (a.strides[-1],)
            rolling = np.lib.stride_tricks.as_strided(
                a, shape=shape, strides=strides)
            min_arr[window-1:] = np.roll(np.minimum.reduce(rolling, axis=1), 1)
            min_arr[:window] = np.nan
            return min_arr
        except Exception as e:
            if "negative dimensions are not allowed" in str(e):
                return 0
            else:
                raise e