
from DataProvider import DataProvider
from Count import Base
import matplotlib.pyplot as plt
import pandas as pd
from decimal import Decimal
import numpy as np
import math

# class Backtest():


#     def __init__(self) -> None:


class ProfileTrader():
    def __init__(self, initcash: float) -> None:
        self.dataprovider = DataProvider()
        self.initcash = initcash
        self.all_cash = initcash

        self.strategys_active = []
        self.strategys_singnal_map = {}  # 用來記錄已經算好的買入訊號

        self.marketpostions = {}
        self.entryprices = {}
        self.exitsprices = {}
        self.Profits = {}  # 單次買賣價差 不包含成本
        self.Buy_Fees = {}  # 買入手續費
        self.Sell_Fees = {}  # 賣出手續費
        self.taxs = {}  # 交易稅
        self.sheetses = {}  # 持有股票單位數
        self._transorStockData()
        self.get_Trade_date()
        self.StartCount()

    def _transorStockData(self) -> pd.DataFrame:
        """
            設定index
        """
        self.all_data = self.dataprovider.GetALLStockData()
        self.all_data.set_index('date', inplace=True)

    def get_Trade_date(self):
        # 以2330 0050 來取得所有的交日期
        data = self.all_data[self.all_data['stock_id'] == '2330']
        self.all_trade_date = data.index.astype(str).to_list()

    def changeInTimeMoney(self, cash: float, Profit: float, Buy_Fee: float, Sell_Fee: float, tax: float):
        self.all_cash = cash + Profit - Buy_Fee - Sell_Fee - tax

    def changesingnal(self, data: dict):
        if sum(list(data.values())) >= 4:
            return 0

    def merge_singnal(self, each_singnal: pd.Series, each_date: str, sell_singnal: int, index: int):
        """
        0,1,-1

        Args:
            each_singnal (pd.Series): _description_
            each_date (str): _description_
            sell_singnal (int): _description_
        """
        out_singnal = each_singnal[each_date] if sell_singnal == 0 else sell_singnal

        # 開始判斷還能不能買
        if self.marketpostions and out_singnal == 1:
            if self.changesingnal(
                    self.marketpostions[list(self.marketpostions.keys())[index-1]]) == 0:
                out_singnal = 0

        return out_singnal

    def StartCount(self):
        """
        用來將標的VCP (3T 買進訊號計算出來)

        1T = 10W ( 10個禮拜)
        1W = 5D (5天)
        # 佔總淨值1.25%的風險,25% 的部位 5% 停損
        # 透過買點訊號計算賣出價格
        # 2015-09-11
        """
        for each_symobl in ['0051', '0056', '00640L', '00645', '00646', '00657', '00661', '00662', '00670L', '00713', '00731', '00733', '00735', '00737', '00757', '00762', '00770', '00830', '00850', '00851', '00861', '00876', '00878', '00881', '00893', '00895', '00896', '00901', '00903', '020020', '020022', '020028', '020029', '1108',
                            '1229', '1337', '1340', '1418', '1423', '1432', '1454', '1472', '1477', '1504', '1525', '1528', '1535', '1540', '1583', '1609', '1612', '1615', '1616', '1618', '1786', '1904', '1905', '1907', '2206', '2228', '2236', '2241', '2247', '2301', '2308', '2321', '2323', '2324', '2329', '2331', '2332', '2344', '2345', '2352', '2353', '2356', '2360', '2365', '2368', '2371', '2376', '2377', '2382', '2383', '2393', '2397', '2399', '2402', '2408', '2409', '2413', '2414', '2421', '2424', '2425', '2427', '2428', '2439', '2449', '2455', '2460', '2466', '2468', '2485', '2486', '2488', '2489', '2515', '2528', '2530', '2536', '2539', '2630', '2704', '2705',
                            '2722', '2886', '3013', '3017', '3025', '3026', '3032', '3033', '3035', '3038', '3046', '3055', '3231', '3266', '3308', '3312', '3338', '3356', '3380', '3481', '3515', '3518', '3543', '3550', '3583', '3607', '3617', '3622', '3653', '3673', '3694', '3702', '3704', '3706', '4439', '4526', '4532', '4566', '4916', '4934', '4960', '4967', '4994', '5234', '5258', '5469', '5484', '5906', '6116', '6120', '6166', '6189', '6191', '6197', '6201', '6235', '6239', '6243', '6257', '6282', '6285', '6412', '6451', '6579', '6592', '6605', '6669', '6691', '8016', '8105', '8110', '8210', '8215', '8271', '8996', '911608', '9906', '9958']:
            self.strategys_singnal_map.update({each_symobl: Strategy(stockID=each_symobl,
                                                                     data=self.all_data[self.all_data['stock_id'] == each_symobl].copy()).GetSignal()})
            self.strategys_active.append(Trade_Strategy_info(
                each_symobl, data=self.all_data[self.all_data['stock_id'] == each_symobl].copy()))

        for index, each_date in enumerate(self.all_trade_date):
            for each_stock_id, each_singnal in self.strategys_singnal_map.items():
                for each_strategy_info in self.strategys_active:
                    if each_stock_id == each_strategy_info.stockid:
                        # 有些股票可能沒有開盤之類的跳過
                        if each_date not in each_singnal:
                            continue

                        sell_singnal = each_strategy_info.get_sell_singnl(
                            self.all_cash, each_date)

                        each_strategy_info.update_info(
                            self.merge_singnal(each_singnal, each_date, sell_singnal, index), each_date, self.all_cash)

                        self.changeInTimeMoney(
                            self.all_cash, each_strategy_info.Profit, each_strategy_info.Buy_Fee, each_strategy_info.Sell_Fee, each_strategy_info.tax)

                        # 部位歷史紀錄
                        if each_date in self.marketpostions:
                            self.marketpostions[each_date].update(
                                {each_stock_id: each_strategy_info.marketpostion})
                        else:
                            self.marketpostions[each_date] = {
                                each_stock_id: each_strategy_info.marketpostion}

                        # 進場價格歷史紀錄
                        if each_date in self.entryprices:
                            self.entryprices[each_date].update(
                                {each_stock_id: each_strategy_info.entryprice})
                        else:
                            self.entryprices[each_date] = {
                                each_stock_id: each_strategy_info.entryprice}

                        # 出場價格歷史紀錄
                        if each_date in self.exitsprices:
                            self.exitsprices[each_date].update(
                                {each_stock_id: each_strategy_info.exitsprice})
                        else:
                            self.exitsprices[each_date] = {
                                each_stock_id: each_strategy_info.exitsprice}

                        # 單次買賣價差
                        if each_date in self.Profits:
                            self.Profits[each_date].update(
                                {each_stock_id: each_strategy_info.Profit})
                        else:
                            self.Profits[each_date] = {
                                each_stock_id: each_strategy_info.Profit}

                        # 買入手續費
                        if each_date in self.Buy_Fees:
                            self.Buy_Fees[each_date].update(
                                {each_stock_id: each_strategy_info.Buy_Fee})
                        else:
                            self.Buy_Fees[each_date] = {
                                each_stock_id: each_strategy_info.Buy_Fee}

                        # 賣出手續費
                        if each_date in self.Sell_Fees:
                            self.Sell_Fees[each_date].update(
                                {each_stock_id: each_strategy_info.Sell_Fee})
                        else:
                            self.Sell_Fees[each_date] = {
                                each_stock_id: each_strategy_info.Sell_Fee}

                        # 交易費用
                        if each_date in self.taxs:
                            self.taxs[each_date].update(
                                {each_stock_id: each_strategy_info.tax})
                        else:
                            self.taxs[each_date] = {
                                each_stock_id: each_strategy_info.tax}

                        # 持有部位
                        if each_date in self.sheetses:
                            self.sheetses[each_date].update(
                                {each_stock_id: each_strategy_info.sheets})
                        else:
                            self.sheetses[each_date] = {
                                each_stock_id: each_strategy_info.sheets}

        print(self.marketpostions)


class Trade_Strategy_info():
    def __init__(self, stockID: str, data: pd.DataFrame) -> None:
        """
        self.order['Order'] = orders
        self.order['OpenPostionprofit'] = OpenPostionprofit
        self.order['ClosedPostionprofit'] = ClosedPostionprofit
        self.order['Gross_profit'] = Gross_profit
        self.order['Gross_loss'] = Gross_loss
        self.order['netprofit'] = netprofit
        """
        self.stockid = stockID
        self.marketpostion = 0
        self.entryprice = 0.0
        self.exitsprice = 0.0
        self.diff_price = 0.0
        self.data = data
        self.entry_high_price = 0.0
        self.Profit = 0.0
        self.Buy_Fee = 0.0
        self.Sell_Fee = 0.0
        self.tax = 0.0  # 稅
        self.sheets = 0  # 股票張數

    def get_sell_singnl(self, allcash: float, each_date: str):
        if self.marketpostion > 0:
            # 取得收盤價
            close_price = self.data[self.data['stock_id']
                                    == self.stockid]['收盤價'][each_date]

            diff_price = float(Decimal(str(close_price)) -
                               Decimal(str(self.entryprice)))

            # 停損
            if (diff_price * self.sheets * 1000 < - allcash*0.0125):
                # 將停損訊號送出去
                return -1

            # 移動停損
            high_price = self.data[self.data['stock_id']
                                   == self.stockid]['最高價'][each_date]

            if high_price > self.entry_high_price:
                self.entry_high_price = high_price

            if close_price < self.entry_high_price * 0.8:
                return -1
        return 0

    def get_sheets(self, allcash: float, entryprice: float):
        cost_money = entryprice * 1000 + entryprice * 1000 * 0.001425
        self.sheets = math.floor(allcash * 0.25 / cost_money)
        self.sheets = 1 if self.sheets == 0 else self.sheets  # 股票張數 # 最低為1

    def update_info(self, singnal: np.float64, each_date: str, allcash: float):
        """ 用來取得每一檔股票的狀態
        all_cash : 可以當成及時資金
        買賣手續費:0.1425％
        證交稅 (賣出的時候才收):0.3％
        Args:
            singnal (np.float64): 訊號:[0.0 ,1.0]

        Returns:
            _type_: _description_
        """
        self.Buy_Fee = 0.0
        self.Sell_Fee = 0.0
        self.tax = 0.0

        if singnal == 0:
            self.Profit = 0.0

        elif singnal == 1:
            self.Profit = 0
            if self.marketpostion == 0:
                self.marketpostion = 1
                self.entryprice = self.data[self.data['stock_id']
                                            == self.stockid]['開盤價'][each_date]
                self.get_sheets(allcash, self.entryprice)
                self.Buy_Fee = self.entryprice * self.sheets * 1000 * 0.001425

                self.exitsprice = 0.0

        elif singnal == -1:
            self.marketpostion = 0

            self.exitsprice = self.data[self.data['stock_id']
                                        == self.stockid]['收盤價'][each_date]
            self.Sell_Fee = self.exitsprice * self.sheets * 1000 * 0.001425
            self.tax = self.exitsprice * self.sheets * 1000 * 0.003
            self.Profit = float(Decimal(str(self.exitsprice)) -
                                Decimal(str(self.entryprice))) * self.sheets * 1000  # 取得不含成本的損益 # 且只有平倉才算
            self.sheets = 0
            self.entryprice = 0.0
            self.entry_high_price = 0


class Strategy():
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


ProfileTrader(500000.0)
