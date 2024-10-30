from numba import njit
import numpy as np

@njit
def get_ATR(Length, high_array: np.array, low_array: np.array, close_array: np.array, parameter_timeperiod):
    last_close_array = np.roll(close_array, 1)
    last_close_array[0] = 0

    def moving_average(a, n=3):
        """
            決定平均類別不向後移動
        """
        ret = np.cumsum(a)
        ret[n:] = ret[n:] - ret[:-n]
        ret[:n] = np.nan
        return ret/n

    # maximum 這個要兩兩比較 不然會有問題
    each_num = np.maximum(close_array - low_array,
                          np.abs(high_array - last_close_array))
    TR = np.maximum(each_num, np.abs(low_array - last_close_array))
    ATR = moving_average(TR, parameter_timeperiod)

    return ATR


@njit
def DynamicStrategy(high_array: np.array, low_array: np.array, ATR_shortArr: np.array, ATR_longArr: np.array, lowestarr1: np.array, lowestarr2: np.array):
    trends = np.zeros(shape=len(high_array))
    orders = np.where((ATR_shortArr > ATR_longArr) & (low_array < lowestarr1), -1, trends)
    orders = np.where((ATR_shortArr <= ATR_longArr) & (low_array < lowestarr2), -1, orders)
    shiftorder = np.roll(orders, 1)
    shiftorder[0] = 0
    return shiftorder


@njit
def get_drawdown_per(ClosedPostionprofit: np.ndarray, init_cash: float):
    DD_per_array = np.empty(shape=ClosedPostionprofit.shape[0])
    max_profit = init_cash
    for i in range(ClosedPostionprofit.shape[0]):
        if ClosedPostionprofit[i] > max_profit:
            max_profit = ClosedPostionprofit[i]
            DD_per_array[i] = 0
        else:
            DD_per_array[i] = 100 * (ClosedPostionprofit[i] -
                                     max_profit) / max_profit
    return DD_per_array


@njit
def get_drawdown(ClosedPostionprofit: np.ndarray):
    DD_array = np.empty(shape=ClosedPostionprofit.shape[0])
    max_profit = 0
    for i in range(ClosedPostionprofit.shape[0]):
        if ClosedPostionprofit[i] > max_profit:
            max_profit = ClosedPostionprofit[i]
            DD_array[i] = 0
        else:
            DD_array[i] = (ClosedPostionprofit[i] - max_profit)
    return DD_array