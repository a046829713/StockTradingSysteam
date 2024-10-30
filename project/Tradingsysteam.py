from DataProvider import DataProvider
from Backtest import ProfileTrader

# 
class Tradingsysteam(object):
    def __init__(self) -> None:
        self.provider = DataProvider()
        # self.provider.GetALLDailyHistroyData() # 爬取股價資料
        # self.provider.get_everyday_target_ymobl() # 分析每日標的(不包含VCP買點)
        # self.provider.crawl_SecuritiesListingOverviewMonthlyReport() # 抓取發行股數計算股本
        # print("開始計算投資組合")
        # ProfileTrader(
        #     500000.0, start_date="2023-10-01").StartCount(Details=True)
        
if __name__ == '__main__':
    app = Tradingsysteam()
