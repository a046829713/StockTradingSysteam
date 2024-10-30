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

#  資金購買上限


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

        # 第一次的進場價位
        self.entryprice = 0.0
        # 平均的進場價位
        self.average_entryprice = 0.0

        self.exitsprice = 0.0
        self.diff_price = 0.0
        self.data = data
        self.entry_high_price = 0.0
        self.Profit = 0.0
        self.Buy_Fee = 0.0
        self.Sell_Fee = 0.0
        self.tax = 0.0  # 稅
        self.sheets = 0  # 股票張數

        self.buy_count = 0  # 用來計算加碼了幾次
        # 買入日期
        self.entry_date = ''

    def days_diff(self, start_date: str, end_date: str) -> int:
        """取得天數的差異

        Args:
            start_date (str): _description_
            end_date (str): _description_

        Returns:
            _type_: _description_
        """
        date_format = "%Y-%m-%d %H:%M:%S"
        start_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)

        delta = end_date - start_date
        return delta.days

    def get_sell_singnl(self, allcash: float, each_date: str):
        # 普通的model
        if self.marketpostion > 0:
            # 可能個股當天沒有資料,(集資之類的)
            if each_date not in self.data.index:
                return 0
            # 取得收盤價
            close_price = self.data['收盤價'][each_date]

            diff_price = float(Decimal(str(close_price)) -
                               Decimal(str(self.average_entryprice)))

            # 停損
            if (diff_price * self.sheets * 1000 < - allcash * 0.25 * 0.1):
                print("目前股票:", self.stockid, "第一次入場價格:", self.entryprice, "平均入場價格:", self.average_entryprice, "價格差異", diff_price, "張數:", self.sheets, "收盤價:",
                      close_price, '停損金額:', - allcash * 0.25 * 0.1)
                # 將停損訊號送出去
                return -1

            # 移動停損
            high_price = self.data['最高價'][each_date]

            if high_price > self.entry_high_price:
                self.entry_high_price = high_price

            if close_price < self.entry_high_price * 0.85:
                return -1

            if self.days_diff(self.entry_date, each_date) > 30:
                return -1

        return 0

    def get_sheets(self, allcash: float, entryprice: float, mode: str = 'NoAddCount'):
        """ 用來取得下注量 """
        cost_money = entryprice * 1000 + entryprice * 1000 * 0.001425

        # 第一次只下注4分之
        if mode == 'NoAddCount':
            self.sheets = self.sheets + \
                math.floor(allcash * 0.25 / cost_money)
        else:
            self.sheets = self.sheets + \
                math.floor(allcash * 0.0625 / cost_money)

        self.sheets = 1 if self.sheets == 0 else self.sheets  # 股票張數 # 最低為1

    def update_info(self, singnal: np.float64, each_date: str, allcash: float, remainingcash: float, slippage: float = 0.0025,) -> None:
        """
        用來取得每一檔股票的狀態
        all_cash : 可以當成及時資金
        買賣手續費:0.1425％
        證交稅 (賣出的時候才收):0.3％
        Args:
            singnal (np.float64):  訊號:[0.0 ,1.0]
            each_date (str): _description_
            allcash (float): _description_
            remainingcash (float): 剩餘現金
            slippage (float, optional): 買賣滑價(0.01). Defaults to 0.01.
        """
        self.Buy_Fee = 0.0
        self.Sell_Fee = 0.0
        self.tax = 0.0
        self.cost_money = 0.0
        self.back_money = 0.0  # 賣掉的時候用來記錄返回了多少錢
        self.Profit = 0.0

        if singnal == 0:
            pass

        elif singnal == 1:
            if self.marketpostion == 0:
                # 先判斷是否還有資金可以購買
                _entryprice = self.data[self.data['stock_id'] ==
                                        self.stockid]['開盤價'][each_date] * (1+slippage)

                _cost_money = _entryprice * 1000 + _entryprice * 1000 * 0.001425

                if remainingcash > _cost_money:
                    self.marketpostion = 1
                    self.entryprice = self.data[self.data['stock_id']
                                                == self.stockid]['開盤價'][each_date] * (1+slippage)
                    self.get_sheets(allcash, self.entryprice)
                    self.Buy_Fee = self.entryprice * self.sheets * 1000 * 0.001425
                    self.cost_money = self.entryprice * self.sheets * 1000  # 買股票的成本
                    # 第一次的部位狀況
                    self.average_entryprice = self.entryprice
                    self.exitsprice = 0.0
                    # 計算加碼次數
                    self.buy_count += 1
                    # 紀錄買入日期
                    self.entry_date = each_date

        elif singnal == -1:
            self.marketpostion = 0

            self.exitsprice = self.data[self.data['stock_id']
                                        == self.stockid]['收盤價'][each_date] * (1-slippage)
            self.Sell_Fee = self.exitsprice * self.sheets * 1000 * 0.001425
            self.tax = self.exitsprice * self.sheets * 1000 * 0.003
            self.back_money = self.exitsprice * self.sheets * 1000
            self.Profit = float(Decimal(str(self.exitsprice)) -
                                Decimal(str(self.average_entryprice))) * self.sheets * 1000  # 取得不含成本的損益 # 且只有平倉才算
            self.sheets = 0
            self.entryprice = 0.0
            self.average_entryprice = 0.0
            self.entry_high_price = 0
            self.buy_count = 0
            self.entry_date = ''

        # if self.marketpostion == 1:
        #     # 可能個股當天沒有資料,(集資之類的)
        #     if each_date not in self.data.index:
        #         return 0
        #     # 如果有多的單情況下
        #     close_price = self.data['收盤價'][each_date]

        #     if self.buy_count < 4:
        #         # 當行情比平均的入場價還要高時
        #         if (close_price - self.average_entryprice) * self.sheets * 1000 > allcash * 0.0625 * 0.05 * self.buy_count:
        #             # 還是要在判斷一次，還有沒有錢可以買
        #             cost_money = close_price * 1000 + close_price * 1000 * 0.001425

        #             if remainingcash > cost_money:
        #                 self.buy_count += 1
        #                 old_sheets = self.sheets
        #                 new_sheets = math.floor(allcash * 0.0625 / cost_money)
        #                 self.cost_money = close_price * new_sheets * 1000  # 買股票的成本
        #                 self.sheets = self.sheets + new_sheets
        #                 self.Buy_Fee = close_price * new_sheets * 1000 * 0.001425
        #                 self.average_entryprice = (old_sheets *
        #                                            self.average_entryprice + new_sheets * close_price) / (old_sheets+new_sheets)


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


class ProfileTrader():
    """
        透過單個策略的買賣訊號,並且根據每一個Trade_Strategy_info object,
        去取得各個股票之狀態
    """

    def __init__(self, initcash: float, start_date: str = None) -> None:
        """_summary_

        Args:
            initcash (float): _description_
            start_date (str): 用來過濾起始時間
        """
        self.start_date = start_date
        self.dataprovider = DataProvider()
        self.all_data = self.dataprovider.GetALLStockData(index=True)
        self.IssueSharesData = self.dataprovider.getIssueSharesData()
        self.strategys_singnal_map = {}  # 用來記錄已經算好的買入訊號
        self.strategys_active = {}  # 用來取得各別商品的交易資訊

        self.ClosedPostionprofit = initcash  # 已平倉損益
        self.initcash = initcash  # 起始資金
        self.remainingcash = self.initcash  # 餘裕資金

        self.marketpostions = {}
        self.entryprices = {}
        self.exitsprices = {}
        self.Profits = {}  # 單次買賣價差 不包含成本
        self.Buy_Fees = {}  # 買入手續費
        self.Sell_Fees = {}  # 賣出手續費
        self.taxs = {}  # 交易稅
        self.sheetses = {}  # 持有股票單位數

        self.last_marketpostion = []  # 最後的持倉部位
        self.rsr_datas = {}  # 所有rsr的紀錄
        self.last_issueShares = {}  # 用來記錄最後的股本

        # 將資料匯出進行績效分析
        self.Portfolio_dates = []
        self.Portfolio_closedpostionprofits = []

        self.TARGET_UPPER_LIMIT = 4


    def changeInTimeMoney(self, cash: float, Profit: float, Buy_Fee: float, Sell_Fee: float, tax: float):
        """
            用來更新已平倉損益
        """
        self.ClosedPostionprofit = cash + Profit - Buy_Fee - Sell_Fee - tax

    @TimeCountMsg.record_timemsg
    def changesingnal(self, data: dict):
        if sum(list(data.values())) >= 4:
            return 0

    @TimeCountMsg.record_timemsg
    def merge_singnal(self, each_singnal: pd.Series, each_date: str, sell_singnal: int):
        """
        0,1,-1

        Args:
            each_singnal (pd.Series): _description_
            each_date (str): _description_
            sell_singnal (int): _description_
        """
        if each_date in each_singnal.index:
            out_singnal = each_singnal[each_date] if sell_singnal == 0 else sell_singnal
        else:
            out_singnal = 0

        return out_singnal

    @TimeCountMsg.record_timemsg
    def update_strategys_singnal_map(self, filtersymbol):
        """ 用來更新策略買入的訊號表 """
        for each_symobl in filtersymbol:
            if each_symobl not in self.strategys_singnal_map:
                self.strategys_singnal_map.update({each_symobl: VCPStrategy(stockID=each_symobl,
                                                                                data=self.all_data[self.all_data['stock_id'] == each_symobl].copy()).GetSignal()})

    @TimeCountMsg.record_timemsg
    def update_strategys_active(self, filtersymbol):
        for each_symobl in filtersymbol:
            if each_symobl not in self.strategys_active:
                self.strategys_active.update({each_symobl: Trade_Strategy_info(
                    each_symobl, data=self.all_data[self.all_data['stock_id'] == each_symobl].copy())})

    @TimeCountMsg.record_timemsg
    def get_myself_filtersymbol(self, date: str, Trends_symbol: list):
        """
            用來將趨勢模板所過濾出來的股票
            再次過濾

        Args:
            Trends_symbol (list): ['0051', '0056', '00640L', '00645', '00646', '00657', '00661', '00662', '00670L', '00713', '00733', '00735', '00737',
         '00757', '00762', '00770', '00830', '00851', '00861', '00878', '00893', '00895', '00901', '00903', '02001L', '020022', '020028', '020029', '1108', '1229', '1234', '1337', '1340', '1418', '1423', '1432', '1449', '1464', '1472', '1477', '1504', '1512', '1525', '1528', '1538', '1540', '1583', '1608', '1612', '1616', '1618', '1786', '1904', '1905', '1907', '2206', '2228', '2236', '2239', '2301', '2308', '2323', '2324', '2329', '2331', '2332', '2344', '2345', '2352', '2356', '2360', '2365', '2368', '2371', '2376', '2377', '2382', '2383', '2393', '2397', '2399', '2402', '2409', '2414', '2421', '2423', '2424', '2425', '2427', '2428', '2439', '2449', '2466', '2468', '2486', '2488', '2489', '2493', '2515', '2528', '2536', '2539', '2630', '2704', '2705', '2712', '2722', '3013', '3017', '3025', '3026', '3032', '3033', '3038', '3046', '3055', '3231', '3266', '3312', '3356', '3380', '3481', '3515', '3518', '3543', '3583', '3607', '3617', '3622', '3653', '3673', '3694', '3706', '4439', '4526', '4532', '4572', '4967', '5258', '5469', '5706', '5906', '6116', '6120', '6142', '6166', '6191', '6197', '6214', '6215', '6235', '6243', '6282', '6285', '6412', '6451', '6579', '6592', '6605', '6669', '8016', '8163', '8210', '8215', '8271', '8996', '9110', '911608']
        """
        # # 在透過今天的日期去過濾
        data = self.all_data[self.all_data.index == date]

        # 流動性過差會可能導致大的滑價
        # 由於擔心價格過高會無法買入,所以再次將過高的股票過濾掉 (總資金百分之二十五)
        out_list = []
        for _each_stock in Trends_symbol:
            _eachStockMoney = data[data['stock_id']
                                   == _each_stock].iloc[0]['成交金額']
            _eachClosePrice = data[data['stock_id']
                                   == _each_stock].iloc[0]['收盤價']

            if _eachStockMoney > 10000000:
                if _eachClosePrice * 1000 < self.ClosedPostionprofit * 0.25:
                    out_list.append(_each_stock)

        return out_list

    def get_myself_filtersymbol_condtion2(self, date: str, Trends_symbol: list):
        # 取得股本 2014-04-01 00:00:00
        traget_year_month = date.replace('-', '')
        traget_year_month = traget_year_month[:6]  # 202306

        # <class 'pandas.core.frame.DataFrame'>
        target_IssueShares = self.IssueSharesData[self.IssueSharesData['issue_date']
                                                  == traget_year_month]

        data = self.all_data[self.all_data.index == date]

        share_capitals = []
        for _each_stock in Trends_symbol:
            if target_IssueShares[target_IssueShares.index == _each_stock].empty:
                if _each_stock not in self.last_issueShares:
                    continue
                else:
                    _IssueShares = self.last_issueShares[_each_stock]
            else:
                _IssueShares = target_IssueShares[target_IssueShares.index ==
                                                  _each_stock].iloc[0]['IssueShares']
                self.last_issueShares[_each_stock] = _IssueShares

            _eachClosePrice = data[data['stock_id']
                                   == _each_stock].iloc[0]['收盤價']
            share_capitals.append(
                [_each_stock, _IssueShares * _eachClosePrice])

        share_capitals = sorted(share_capitals, key=lambda x: x[1])
        return [i[0] for i in share_capitals]

    @TimeCountMsg.record_timemsg
    def get_this_time_to_buy(self, date: str, filtersymbol: list) -> list:
        # 將過濾出來的標的 查看是否具有VCP之買點
        return [each_symbol for each_symbol in filtersymbol if self.strategys_singnal_map[each_symbol][date] == 1]

    @TimeCountMsg.record_timemsg
    def get_last_marketpostion(self, filtersymbol: list) -> None:
        """
            將新的標的物放入
        """
        filtersymbol = copy.deepcopy(filtersymbol)

        while len(self.last_marketpostion) < self.TARGET_UPPER_LIMIT and len(filtersymbol) != 0:
            self.last_marketpostion.append(filtersymbol.pop(0))
            self.last_marketpostion = list(set(self.last_marketpostion))

    @TimeCountMsg.record_timemsg
    def calculate_rsr(self, date: str, filtersymbol, period=126, weeks=6):
        """
            用來比較rsr的強度做商品排序
                                stock_id     成交股數  成交筆數      成交金額    開盤價    最高價    最低價    收盤價  漲跌價差  最後揭示買價  最後揭示買量  最後揭示賣價  最後揭示賣量    本益比    Return   RS_Rank
            date
            2013-01-02     1108   447114    96   3003763   6.71   6.75   6.68   6.71  0.03    6.71      20    6.73       6  15.25       NaN       NaN
            2013-01-03     1108   998320   251   6780351   6.78   6.89   6.72   6.80  0.09    6.80       9    6.83       5  15.45       NaN       NaN
            2013-01-04     1108  1718592   340  11906012   6.94   7.05   6.82   6.92  0.12    6.90      24    6.92      16  15.73       NaN       NaN
            2013-01-07     1108   797740   186   5581670   6.99   7.06   6.92   7.02  0.10    6.99       2    7.02      13  15.95       NaN       NaN
            2013-01-08     1108   520200   145   3612174   7.02   7.07   6.89   6.98  0.04    6.92       2    6.98       7  15.86       NaN       NaN
            ...             ...      ...   ...       ...    ...    ...    ...    ...   ...     ...     ...     ...     ...    ...       ...       ...
            2023-07-06     1108  1522196   677  24983837  16.60  16.65  16.25  16.30  0.35   16.25      20   16.30      12  10.06  0.502304  9.626437
            2023-07-07     1108   992342   548  15938018  16.20  16.20  15.90  16.10  0.20   16.10       3   16.15       8   9.94  0.497674  9.605911
            2023-07-10     1108  2069466   688  33641338  16.10  16.60  15.90  16.25  0.15   16.25      39   16.30      27  10.03  0.511628  9.663383
            2023-07-11     1108  1070919   481  17694092  16.55  16.70  16.40  16.55  0.30   16.50      17   16.55      43  10.22  0.525346  9.679803
            2023-07-12     1108   793098   418  12940525  16.40  16.55  16.20  16.20  0.35   16.20      88   16.25      13  10.00  0.500000  9.618227

            [2562 rows x 16 columns]
            DatetimeIndex(['2013-01-02', '2013-01-03', '2013-01-04', '2013-01-07',
                        '2013-01-08', '2013-01-09', '2013-01-10', '2013-01-11',
                        '2013-01-14', '2013-01-15',
                        ...
                        '2023-06-29', '2023-06-30', '2023-07-03', '2023-07-04',
                        '2023-07-05', '2023-07-06', '2023-07-07', '2023-07-10',
                        '2023-07-11', '2023-07-12'],
                        dtype='datetime64[ns]', name='date', length=2562, freq=None)
            <class 'str'>
        """
        all_rsr_data = {}
        for each_symobl in filtersymbol:
            if each_symobl in self.rsr_datas:
                each_symbol_data = self.rsr_datas[each_symobl]
            else:
                each_symbol_data = self.all_data[self.all_data['stock_id'] == each_symobl].copy(
                )
                Close = each_symbol_data['收盤價']

                each_symbol_data['Return'] = Close.pct_change(periods=period)

                # Rank the returns
                each_symbol_data['RS_Rank'] = each_symbol_data['Return'].rank(
                    pct=True) * 10

                self.rsr_datas[each_symobl] = each_symbol_data

            all_rsr_data.update(
                {each_symobl: each_symbol_data['RS_Rank'][date]})

        b = list(all_rsr_data.items())
        b = sorted(b, key=lambda x: x[1], reverse=True)

        return [stock_id for stock_id, value in b]

    @TimeCountMsg.record_timemsg
    def get_remainingcash(self, cash: float, Buy_Fee: float, Sell_Fee: float, tax: float, cost_money: float, back_money: float):
        """
            用來計算剩餘資金
            cost_money:買股票的成本
        """
        # 還缺一個賣掉股票所取回的錢
        self.remainingcash = cash - Buy_Fee - Sell_Fee - tax - cost_money + back_money

    def StartCount(self, Details=False):
        """
        用來將標的VCP (3T 買進訊號計算出來)

        1T = 10W ( 10個禮拜)
        1W = 5D (5天)
        # 佔總淨值1.25%的風險,25% 的部位 5% 停損
        # 透過買點訊號計算賣出價格
        # 2015-09-11
        """

        # symbol是準備要買的股票
        for date, symbol in self.dataprovider.get_daytargets(start_date=self.start_date):
            symbol = json.loads(symbol)
            filtersymbol = self.get_myself_filtersymbol(date, symbol)

            # 更新買入順序
            # filtersymbol = self.calculate_rsr(date, filtersymbol)
            filtersymbol = self.get_myself_filtersymbol_condtion2(
                date, filtersymbol)

            # 更新買入訊號
            self.update_strategys_singnal_map(filtersymbol)

            # 確認本次的買入標的 # 除了趨勢條件之外還要判斷VCP
            filtersymbol = self.get_this_time_to_buy(date, filtersymbol)

            # 紀錄本次購買的標的
            self.get_last_marketpostion(filtersymbol)

            # 初始化商品資訊
            self.update_strategys_active(filtersymbol)

            # 開始進入交易 # 將買賣訊號一起在函數裡面判斷
            for each_stock_id, each_singnal in self.strategys_singnal_map.items():
                if each_stock_id not in self.last_marketpostion:
                    continue

                # 取得賣出訊號
                sell_singnal = self.strategys_active[each_stock_id].get_sell_singnl(
                    self.ClosedPostionprofit, date)

                self.strategys_active[each_stock_id].update_info(
                    self.merge_singnal(each_singnal, date, sell_singnal), date, self.ClosedPostionprofit, self.remainingcash)

                self.changeInTimeMoney(
                    self.ClosedPostionprofit, self.strategys_active[each_stock_id].Profit, self.strategys_active[each_stock_id].Buy_Fee, self.strategys_active[each_stock_id].Sell_Fee, self.strategys_active[each_stock_id].tax)

                self.get_remainingcash(self.remainingcash, self.strategys_active[
                                       each_stock_id].Buy_Fee, self.strategys_active[each_stock_id].Sell_Fee, self.strategys_active[each_stock_id].tax, self.strategys_active[each_stock_id].cost_money, self.strategys_active[each_stock_id].back_money)
                # print("目前商品:", each_stock_id, "目前日期:", date, "加碼次數:",
                #       self.strategys_active[each_stock_id].buy_count, "目前張數:", self.strategys_active[each_stock_id].sheets)

                if self.strategys_active[each_stock_id].marketpostion == 0:
                    self.last_marketpostion.remove(each_stock_id)

                if Details:
                    # 部位歷史紀錄
                    if date in self.marketpostions:
                        self.marketpostions[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].marketpostion})
                    else:
                        self.marketpostions[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].marketpostion}

                    # 進場價格歷史紀錄
                    if date in self.entryprices:
                        self.entryprices[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].entryprice})
                    else:
                        self.entryprices[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].entryprice}

                    # 出場價格歷史紀錄
                    if date in self.exitsprices:
                        self.exitsprices[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].exitsprice})
                    else:
                        self.exitsprices[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].exitsprice}

                    # 單次買賣價差
                    if date in self.Profits:
                        self.Profits[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].Profit})
                    else:
                        self.Profits[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].Profit}

                    # 買入手續費
                    if date in self.Buy_Fees:
                        self.Buy_Fees[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].Buy_Fee})
                    else:
                        self.Buy_Fees[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].Buy_Fee}

                    # 賣出手續費
                    if date in self.Sell_Fees:
                        self.Sell_Fees[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].Sell_Fee})
                    else:
                        self.Sell_Fees[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].Sell_Fee}

                    # 交易費用
                    if date in self.taxs:
                        self.taxs[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].tax})
                    else:
                        self.taxs[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].tax}

                    # 持有部位
                    print("測試進入")
                    if date in self.sheetses:
                        self.sheetses[date].update(
                            {each_stock_id: self.strategys_active[each_stock_id].sheets})
                    else:
                        self.sheetses[date] = {
                            each_stock_id: self.strategys_active[each_stock_id].sheets}

            if self.sheetses.get(date, None):
                print("今天日期:", date, "今天持有部位:",
                      self.last_marketpostion, "現有資金:", self.ClosedPostionprofit, "目前持有張數:", self.sheetses[date])
            else:
                print("今天日期:", date, "今天持有部位:",
                      self.last_marketpostion, "現有資金:", self.ClosedPostionprofit)

            self.Portfolio_dates.append(date)
            self.Portfolio_closedpostionprofits.append(
                self.ClosedPostionprofit)

        pf = Portfolio_Performance_Info(
            self.initcash, self.Portfolio_dates, self.Portfolio_closedpostionprofits)
        return Picture_maker(pf)
