import pandas as pd
import numpy as np
from . import nb


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

    @staticmethod
    def std_rolling(a, window, axis=1):
        """用來計算標準差

        Args:
            a (_type_): _description_
            window (_type_): _description_
            axis (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        try:
            max_arr = np.empty(shape=a.shape[0])
            shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
            strides = a.strides + (a.strides[-1],)
            rolling = np.lib.stride_tricks.as_strided(
                a, shape=shape, strides=strides)
            max_arr[window-1:] = np.roll(np.std(rolling, axis=1, ddof=0), 1)
            max_arr[:window] = np.nan
            return max_arr
        except Exception as e:
            if "negative dimensions are not allowed" in str(e):
                return 0
            else:
                print(a, window)
                raise e

    @staticmethod
    def mean_rolling(a, window, axis=1):
        """用來計算平均值

        Args:
            a (_type_): _description_
            window (_type_): _description_
            axis (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        try:
            max_arr = np.empty(shape=a.shape[0])
            shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
            strides = a.strides + (a.strides[-1],)
            rolling = np.lib.stride_tricks.as_strided(
                a, shape=shape, strides=strides)
            max_arr[window-1:] = np.roll(np.mean(rolling, axis=1), 1)
            max_arr[:window] = np.nan
            return max_arr
        except Exception as e:
            if "negative dimensions are not allowed" in str(e):
                return 0
            else:
                raise e

    @staticmethod
    def get_active_max_rolling(prices, window_sizes):
        """
        取得動態最大值
        [nan, nan, 5.0, nan, 6.0, 6.0, 5.0, 8.0, 8.0]
        """
        out_list = np.empty(shape=prices.shape[0])
        last_num = np.nan
        for index, window_size in enumerate(window_sizes):
            if index - window_size < 0:
                target = np.nan
            else:
                target = np.max(prices[index - window_size: index])
            if not np.isnan(last_num):
                if np.isnan(target):
                    out_list[index] = last_num
                else:
                    out_list[index] = target
            else:
                # 如果最後的值還是空值就只好加入進去
                out_list[index] = target
                last_num = target
        return out_list

    @staticmethod
    def get_active_min_rolling(prices, window_sizes):
        """
        取得動態最大值
        [nan, nan, 5.0, nan, 6.0, 6.0, 5.0, 8.0, 8.0]
        """
        out_list = np.empty(shape=prices.shape[0])
        last_num = np.nan
        for index, window_size in enumerate(window_sizes):
            if index - window_size < 0:
                target = np.nan
            else:
                target = np.min(prices[index - window_size: index])
            if not np.isnan(last_num):
                if np.isnan(target):
                    out_list[index] = last_num
                else:
                    out_list[index] = target
            else:
                # 如果最後的值還是空值就只好加入進去
                out_list[index] = target
                last_num = target
        return out_list

    @staticmethod
    def batch_normalize_and_scale(data, batch_size=20, scale_min=1, scale_max=100):
        # 初始化一個與原始數據形狀相同的陣列來儲存結果
        result = np.empty_like(data)

        # 對每一個批次進行標準化和縮放
        for i in range(0, len(data), batch_size):
            batch = data[i: i + batch_size]
            batch = np.nan_to_num(batch)
            batch_original = np.max(batch) - np.min(batch)

            if batch_original == 0:
                result[i: i + batch_size] = (scale_min + scale_max) / 2
            else:
                batch_change = scale_max - scale_min
                rescaled = batch_change / batch_original
                new_batch = (batch - np.min(batch)) * rescaled
                new_batch = np.where(new_batch < 1, 1, new_batch)
                result[i: i + batch_size] = new_batch

        return result.astype(int)














