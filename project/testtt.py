from DataProvider import DataProvider
import json
import pandas as pd
from Count import Base
from Count.Performance import Portfolio_Performance_Info, Picture_maker
from decimal import Decimal
import math
import numpy as np
import time
import copy
from utils.TimeCountMsg import TimeCountMsg
from datetime import datetime
from Count.Base import nb
from Count.Base import vecbot_count


class VCPStrategy():
    def __init__(self, stockID: str, data: pd.DataFrame) -> None:
        self.stockid = stockID
        self.data = data

    def GetSignal(self):

        # 1T
        one_t_high = Base.vecbot_count.max_rolling(
            self.data['最高價'].to_numpy(), 50)
        one_t_low = Base.vecbot_count.min_rolling(
            self.data['最低價'].to_numpy(), 50)
        self.data['1T'] = (one_t_high - one_t_low) / one_t_high
        self.data['2T'] = self.data['1T'].shift(50)
        self.data['3T'] = self.data['1T'].shift(100)

        self.data['Signal'] = (self.data['1T'] < self.data['2T']) & (
            self.data['2T'] < self.data['3T']) & (self.data['最高價'] > one_t_high)

        # 做向後移位的動作 並且以當天開盤價格做回測
        self.data['Signal'] = self.data['Signal'].astype(int)
        self.data['Signal'] = self.data['Signal'].shift()
        self.data['Signal'] = self.data['Signal'].fillna(0)

        return self.data['Signal']


class DynamicStrategy():
    def __init__(self, stockID: str, data: pd.DataFrame) -> None:
        self.stockid = stockID
        self.data = data
        self.Length = len(self.data)
        self.ATR_short1 = 20
        self.ATR_long2 = 100

        self.high_array = self.data['最高價'].to_numpy()
        self.low_array = self.data['最低價'].to_numpy()
        self.close_array = self.data['收盤價'].to_numpy()

        self.ATR_shortArr = nb.get_ATR(
            self.Length, self.high_array, self.low_array, self.close_array, self.ATR_short1)

        self.ATR_longArr = nb.get_ATR(
            self.Length, self.high_array, self.low_array, self.close_array, self.ATR_long2)

        self.highestarr = vecbot_count.get_active_max_rolling(
            self.high_array, vecbot_count.batch_normalize_and_scale(self.ATR_shortArr))

    def GetSignal(self):
        orders = np.where((self.high_array - self.highestarr > 0) &
                          (self.ATR_shortArr-self.ATR_longArr > 0), 1, 0)

        shiftorder = np.roll(orders, 1)
        # 将 Numpy 数组转换为 Pandas Series，并使用数据的原始索引
        shiftorder_series = pd.Series(shiftorder, index=self.data.index)
        return shiftorder_series


df = pd.read_csv("TaiwanStockHistoryDailyData.csv")
df = df[df['stock_id'] == '2330']
df.set_index('date', inplace=True)
series = DynamicStrategy(stockID="2330", data=df).GetSignal()
print(series[series != 0])