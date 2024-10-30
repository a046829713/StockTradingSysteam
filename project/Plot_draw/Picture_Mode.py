import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.dates as dates
import matplotlib.dates as mdates  # 處理日期


# 初始化
plt.style.use('seaborn-deep')


class Picture_maker():
    def __init__(self, Order_info: Np_Order_Info) -> None:
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
        # for i in range(dd_perdata.shape[0]):
        #     if dd_perdata[i] == 0:
        #         ax1.plot(i, y1_data[i], marker="8", color='#008000')

        ax1.grid(True)
        ax1.set_title("ClosedPostionprofit")

        
        # # 坐標軸的位置
        # ax2.set_xticks(out_list)
        # # 坐標軸的內容
        # ax2.set_xticklabels(out_lables)
        # ax2.bar(range(len(x1_data)), dd_data, width=0.4, color='#F08080')
        # ax2.grid(True)
        # ax2.set_title("MDD")

        # # 坐標軸的位置
        # ax3.set_xticks(out_list)
        # # 坐標軸的內容
        # ax3.set_xticklabels(out_lables)
        # ax3.bar(range(len(x1_data)), dd_perdata, width=0.4, color='#22C32E')
        # ax3.grid(True)
        # ax3.set_title("MDDPer")
        plt.show()