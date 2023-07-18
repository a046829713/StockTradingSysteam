import pandas as pd
import requests
import io
from io import StringIO
from Database import SQL_operate
from dateutil.rrule import rrule, DAILY, MONTHLY
from datetime import datetime, date
import time
import random
import matplotlib.pyplot as plt
from DataTransformer import DataTransformer


class DataProvider():
    """
        取得股價資料
    """

    def __init__(self) -> None:
        self.session = requests.session()
        self.SQL = SQL_operate.DB_operate()

    def import_history_data(self):
        pass

    def export_history_data(self):
        """
            to export taiwan stock history data to csv
        """
        df = self.SQL.read_Dateframe(f"select * from `dailytwstock`;")
        df.set_index('date', inplace=True)
        df.to_csv("TaiwanStockHistoryDailyData.csv")

    def GetALLStockData(self):
        return self.SQL.read_Dateframe(f"select * from `dailytwstock`;")
        # return self.SQL.read_Dateframe(f"select * from `dailytwstock` where stock_id = '3026' or stock_id ='3035' or stock_id ='5258' or stock_id ='5469';")

    def crawl_price(self, date: str) -> pd.DataFrame:
        """
        date:"2023-06-16"

        Returns:
            pd.DataFrame
        """
        try:
            datestr = date.replace('-', '')
            respone = self.session.get(
                'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=ALLBUT0999')
        except Exception as e:
            print('**WARRN: cannot get stock price at', datestr)
            raise e

        content = respone.text.replace('=', '')
        lines = content.split('\n')
        lines = list(filter(lambda l: len(l.split('",')) > 10, lines))
        content = "\n".join(lines)

        if content == '':
            return None

        df = pd.read_csv(StringIO(content))
        df = df.astype(str)
        df = df.apply(lambda s: s.str.replace(',', ''))
        df['date'] = pd.to_datetime(date)
        df = df.rename(columns={'證券代號': 'stock_id'})
        df = df.set_index(['stock_id', 'date'])
        df = df.apply(lambda s: pd.to_numeric(s, errors='coerce'))
        df = df[df.columns[df.isnull().all() == False]]
        df = df[~df['收盤價'].isnull()]

        return df

    def date_range(self, start_date, end_date):
        return [dt.date() for dt in rrule(DAILY, dtstart=start_date, until=end_date)]

    def GetALLDailyHistroyData(self, start_date: str = "2013-01-01", end_date: str = datetime.today()):
        """
            取得所有時間範圍內的資料
        """
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

        last_date = self.SQL.get_db_data(
            "select * from `dailytwstock` order by date DESC limit 1;")

        if last_date:
            last_date = last_date[0][1]
            # 當資料庫最後的時間已經是今天代表不需要再次回補
            if last_date.date() == date.today():
                print('今日資料已經回補過了')
                return

        # 取得資料庫最後的時間 (從2013之後開始計算)
        # datetime的格式
        if last_date:
            date_range = self.date_range(last_date, end_date)
            # 資料庫已經存在不需要再回補一次
            date_range.remove(last_date.date())
        else:
            date_range = self.date_range(start_date, end_date)

        # 將日期範圍排除假日(優先排除六,日)
        date_range = list(filter(lambda x: True if x.isoweekday(
        ) != 6 and x.isoweekday() != 7 else False, date_range))

        for _date in date_range:
            _date = str(_date)
            df = self.crawl_price(_date)
            if df is not None:
                self.SQL.write_Dateframe(
                    df, tablename="dailytwstock", exists="append")
                print(f"日期:{_date},寫入成功")
            else:
                print(f"日期:{_date},當天沒有資料")

            print("休息時間:", random.randint(10, 25))
            time.sleep(random.randint(10, 25))

    def GetTargetSymobl(self):
        """
            取得符合趨勢模板的股票
        """

        #  取得資料庫的最後一天
        last_Date = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' order by date DESC limit 1;")
        last_Date = last_Date['date'].iloc[0]

        # 並且取得目前現有的股票
        allStockID = self.SQL.read_Dateframe(
            f"select stock_id from `dailytwstock` where date='{last_Date}';")
        allStockID = allStockID['stock_id'].to_list()

        print("資料開始取得")
        # 取得所有股票資料
        allStockData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`;")

        print("資料取得完畢")
        filter_symbols = []
        for each_id in allStockID:
            print("目前解析股票:", each_id)
            each_symbol_data = allStockData[allStockData['stock_id'] == each_id]

            # Create a copy of each_symbol_data for each condition to prevent internal modifications
            each_symbol_data_cond1 = each_symbol_data.copy()
            each_symbol_data_cond2 = each_symbol_data.copy()
            each_symbol_data_cond3 = each_symbol_data.copy()
            each_symbol_data_cond4 = each_symbol_data.copy()

            condtion1 = DataTransformer.GetSuperTrends_mode1(
                each_symbol_data_cond1)
            condtion2 = DataTransformer.is_moving_avg_up_for_month(
                each_symbol_data_cond2)
            condtion3 = DataTransformer.is_price_up_More_percent(
                each_symbol_data_cond3)
            condtion4 = DataTransformer.calculate_rsr(each_symbol_data_cond4)

            if condtion1 and condtion2 and condtion3 and condtion4:
                # 畫圖
                # each_symbol_data['成交股數'].plot(kind='line')

                # 將圖片保存為 'output.png'
                # plt.savefig(f'image/{each_id}.png')
                # 清除圖形
                # plt.clf()

                filter_symbols.append(each_id)
                print("目前合格股票:", filter_symbols)

    def get_everyday_target_ymobl(self):
        """
            取得每一天符合趨勢模板的股票
        """

        #  取得資料庫的最後一天
        last_Date = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' order by date DESC limit 1;")
        last_Date = last_Date['date'].iloc[0]

        # 並且取得目前現有的股票 # 下市的就不管了
        allStockID = self.SQL.read_Dateframe(
            f"select stock_id from `dailytwstock` where date='{last_Date}';")
        allStockID = allStockID['stock_id'].to_list()

        # 取得所有交易的日期
        df = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' or stock_id='0050'")

        date_list = df['date'].to_list()  # 5124
        date_list = list(set([str(i) for i in date_list]))
        date_list.sort()

        print("資料開始取得")
        # 取得所有股票資料
        allStockData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`;")

        print("資料取得完畢")

        all_data = {}
        for index, each_date in enumerate(date_list):
            filter_symbols = []
            # 整體的股票先過濾要大於300天
            if index < 300:
                continue

            print(each_date)
            if index > 301:
                break

            for each_id in allStockID:
                print("目前解析股票:", each_id)
                each_date_list = allStockData[allStockData['stock_id'] == each_id]['date'].to_list(
                )
                each_date_list = [str(i) for i in date_list]
                if each_date_list.index(each_date) != index:
                    raise
                each_symbol_data = allStockData[allStockData['stock_id']
                                                == each_id][:index]

                # Create a copy of each_symbol_data for each condition to prevent internal modifications
                each_symbol_data_cond1 = each_symbol_data.copy()
                each_symbol_data_cond2 = each_symbol_data.copy()
                each_symbol_data_cond3 = each_symbol_data.copy()
                each_symbol_data_cond4 = each_symbol_data.copy()

                condtion1 = DataTransformer.GetSuperTrends_mode1(
                    each_symbol_data_cond1)
                condtion2 = DataTransformer.is_moving_avg_up_for_month(
                    each_symbol_data_cond2)
                condtion3 = DataTransformer.is_price_up_More_percent(
                    each_symbol_data_cond3)
                condtion4 = DataTransformer.calculate_rsr(
                    each_symbol_data_cond4)

                if condtion1 and condtion2 and condtion3 and condtion4:
                    filter_symbols.append(each_id)
                    print("目前合格股票:", filter_symbols)
            all_data.update({each_date: filter_symbols})

        print(all_data)

    def get_myself_filtersymbol(self, Trends_symbol: list, systeam_money: int = 500000):
        """
            用來將趨勢模板所過濾出來的股票
            再次過濾

        Args:
            Trends_symbol (list): ['0051', '0056', '00640L', '00645', '00646', '00657', '00661', '00662', '00670L', '00713', '00733', '00735', '00737',
         '00757', '00762', '00770', '00830', '00851', '00861', '00878', '00893', '00895', '00901', '00903', '02001L', '020022', '020028', '020029', '1108', '1229', '1234', '1337', '1340', '1418', '1423', '1432', '1449', '1464', '1472', '1477', '1504', '1512', '1525', '1528', '1538', '1540', '1583', '1608', '1612', '1616', '1618', '1786', '1904', '1905', '1907', '2206', '2228', '2236', '2239', '2301', '2308', '2323', '2324', '2329', '2331', '2332', '2344', '2345', '2352', '2356', '2360', '2365', '2368', '2371', '2376', '2377', '2382', '2383', '2393', '2397', '2399', '2402', '2409', '2414', '2421', '2423', '2424', '2425', '2427', '2428', '2439', '2449', '2466', '2468', '2486', '2488', '2489', '2493', '2515', '2528', '2536', '2539', '2630', '2704', '2705', '2712', '2722', '3013', '3017', '3025', '3026', '3032', '3033', '3038', '3046', '3055', '3231', '3266', '3312', '3356', '3380', '3481', '3515', '3518', '3543', '3583', '3607', '3617', '3622', '3653', '3673', '3694', '3706', '4439', '4526', '4532', '4572', '4967', '5258', '5469', '5706', '5906', '6116', '6120', '6142', '6166', '6191', '6197', '6214', '6215', '6235', '6243', '6282', '6285', '6412', '6451', '6579', '6592', '6605', '6669', '8016', '8163', '8210', '8215', '8271', '8996', '9110', '911608']
        """

        #  取得資料庫的最後一天
        last_Date = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' order by date DESC limit 1;")
        last_Date = last_Date['date'].iloc[0]

        # # 在透過今天的日期去過濾
        last_DateData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`where date='{last_Date}';")
        last_DateData.set_index("stock_id", inplace=True)

        # 流動性過差會可能導致大的滑價
        # 由於擔心價格過高會無法買入,所以再次將過高的股票過濾掉 (總資金百分之二十五)
        out_list = []
        for _each_stock in Trends_symbol:
            _eachStockMoney = last_DateData[last_DateData.index
                                            == _each_stock].iloc[0]['成交金額']
            _eachClosePrice = last_DateData[last_DateData.index
                                            == _each_stock].iloc[0]['收盤價']

            if _eachStockMoney > 10000000:
                if _eachClosePrice * 1000 < systeam_money * 0.25:
                    out_list.append(_each_stock)

        print(out_list)


if __name__ == '__main__':
    app = DataProvider()
    # print(app.date_range(datetime.strptime("2023-06-09","%Y-%m-%d"),datetime.strptime("2023-06-12","%Y-%m-%d")))
    # app.GetALLDailyHistroyData()

    app.export_history_data()
