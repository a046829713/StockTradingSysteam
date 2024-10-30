import pandas as pd
import numpy as np
from . import nb
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as dates
import matplotlib.dates as mdates  # 處理日期
# Traceback (most recent call last):
#   File "c:/Users/user/Desktop/程式專區/StockTradesysteam/StockTradingSysteam/project/Backtest.py", line 489, in <module>
#     ProfileTrader(2000000.0).StartCount()
#   File "c:/Users/user/Desktop/程式專區/StockTradesysteam/StockTradingSysteam/project/Backtest.py", line 486, in StartCount
#     return Picture_maker(pf)
#   File "c:\Users\user\Desktop\程式專區\StockTradesysteam\StockTradingSysteam\project\Count\Performance.py", line 53, in __init__
#     self.get_Mdd_UI(self.pf.order.index.to_numpy(
#   File "c:\Users\user\Desktop\程式專區\StockTradesysteam\StockTradingSysteam\project\Count\Performance.py", line 80, in get_Mdd_UI
#     for i in range(dd_perdata.shape[0]):
# AttributeError: 'NoneType' object has no attribute 'shape'


class Portfolio_Performance_Info():
    """
        用來計算投資組合的績效顯示
    """
    def __init__(self, initcash: float, dates: list, ClosedPostionprofits: list) -> None:
        self.order = pd.DataFrame(dates, columns=['Datetime'])
        self.order['ClosedPostionprofits'] = ClosedPostionprofits
        self.order.set_index("Datetime", inplace=True)
        self.ClosedPostionprofit_array = self.order['ClosedPostionprofits'].to_numpy(
        )

        self.Portfolio_initcash = initcash
    
    @property
    def drawdown(self):
        """
            取得回撤金額
        """
        return nb.get_drawdown(self.ClosedPostionprofit_array)

    @property
    def drawdown_per(self):
        """
            取得回撤百分比

        """

        return nb.get_drawdown_per(self.ClosedPostionprofit_array, self.Portfolio_initcash)



# 初始化
plt.style.use('seaborn-deep')

class Picture_maker():
    def __init__(self, Order_info: Portfolio_Performance_Info) -> None:
        self.pf = Order_info
        
        self.get_Mdd_UI(self.pf.order.index.to_numpy(
        ), self.pf.ClosedPostionprofit_array, self.pf.drawdown, self.pf.drawdown_per)

    def get_Mdd_UI(self, x1_data: np.ndarray, y1_data, dd_data: np.ndarray, dd_perdata: np.ndarray):

        x1_data = np.array([date.split(' ')[0] for date in x1_data])

        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1, figsize=(80, 10), height_ratios=(2, 1, 1),dpi=80)

        # X 軸相關設置
        out_list = []
        out_lables = []
        i = 0
        for _i in range(8):
            out_list.append(i)
            out_lables.append(x1_data[i])
            i = i + divmod(x1_data.shape[0], 8)[0]

        # 坐標軸的位置
        ax1.set_xticks(out_list)
        # 坐標軸的內容
        ax1.set_xticklabels(out_lables)
        
        ax1.plot(y1_data)

        # 創新高時畫上綠點
        for i in range(dd_perdata.shape[0]):
            if dd_perdata[i] == 0:
                ax1.plot(i, y1_data[i], marker="8", color='#008000')

        ax1.grid(True)
        ax1.set_title("ClosedPostionprofit")

        
        # 坐標軸的位置
        ax2.set_xticks(out_list)
        # 坐標軸的內容
        ax2.set_xticklabels(out_lables)
        ax2.bar(range(len(x1_data)), dd_data, width=0.4, color='#F08080')
        ax2.grid(True)
        ax2.set_title("MDD")

        # 坐標軸的位置
        ax3.set_xticks(out_list)
        # 坐標軸的內容
        ax3.set_xticklabels(out_lables)
        ax3.bar(range(len(x1_data)), dd_perdata, width=0.4, color='#22C32E')
        ax3.grid(True)
        ax3.set_title("MDDPer")
        plt.show()
        
        
        
class Order_Info(object):
    """ 用來處理訂單的相關資訊
    Args:
        object (_type_): _description_
    """

    def __init__(self, datetime_list,
                 orders: np.ndarray,
                 marketpostion: np.ndarray,
                 entryprice: np.ndarray,
                 buy_Fees: np.ndarray,
                 sell_Fees: np.ndarray,
                 OpenPostionprofit: np.ndarray,
                 ClosedPostionprofit: np.ndarray,
                 profit: np.ndarray,
                 Gross_profit: np.ndarray,
                 Gross_loss: np.ndarray,
                 all_Fees: np.ndarray,
                 netprofit: np.ndarray,
                 ) -> None:
        # 取得order儲存列

        self.order['Order'] = orders
        self.order['Marketpostion'] = marketpostion
        self.order['Entryprice'] = entryprice
        self.order['Buy_Fees'] = buy_Fees
        self.order['Sell_Fees'] = sell_Fees
        self.order['OpenPostionprofit'] = OpenPostionprofit

        self.order['Profit'] = profit
        self.order['Gross_profit'] = Gross_profit
        self.order['Gross_loss'] = Gross_loss
        self.order['all_Fees'] = all_Fees
        self.order['netprofit'] = netprofit

        # 壓縮資訊減少運算
        self.order = self.order[self.order['Order'] != 0]
        self.order.set_index("Datetime", inplace=True)

        # 取得需要二次運算的資料(計算勝率，賠率....繪圖)

    # def register(self, strategy_info: Strategy_base):
    #     """將原始策略的資訊記錄起來

    #     Args:
    #         strategy_info (_type_): _description_
    #     """
    #     self.strategy_info = strategy_info

    @property
    def avgloss(self) -> float:
        """
            透過毛損來計算平均策略虧損

        Returns:
            _type_: _description_
        """
        if self.LossTrades == 0:
            return -100.0  # 由於都沒有交易輸的紀錄
        else:
            return self.order['Gross_loss'].iloc[-1] / self.LossTrades

    @property
    def TotalTrades(self) -> int:
        """ 透過訂單的長度即可判斷交易的次數

        Returns:
            _type_: _description_
        """
        return divmod(len(self.order), 2)[0]

    @property
    def WinTrades(self) -> int:
        """ 取得獲勝的次數
        Returns:
            _type_: _description_
        """
        return len(self.order['Profit'][self.order['Profit'] > 0])

    @property
    def LossTrades(self) -> int:
        """取得失敗的次數

        Returns:
            int: to get from profit
        """
        return len(self.order['Profit'][self.order['Profit'] < 0])

    @property
    def Percent_profitable(self) -> float:
        """取得盈利(勝率)(非百分比) 不全部輸出小數點位數

        Returns:
            float: _description_
        """
        return round(self.WinTrades / self.TotalTrades, 3)
