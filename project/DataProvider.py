import pandas as pd
import requests
from io import StringIO
from Database import SQL_operate, Back_up_check
from dateutil.rrule import rrule, DAILY, MONTHLY
from datetime import datetime, date
import time
import random
import matplotlib.pyplot as plt
from DataTransformer import DataTransformer
import json
import os
import tqdm
import zipfile
import re


class DataProvider():
    """
        取得股價資料
    """

    def __init__(self) -> None:
        self.session = requests.session()
        self.SQL = SQL_operate.DB_operate()
        Back_up_check.checkIFtable()

    def import_history_data(self):
        """ 
            將資料導入資料庫裡面
        """
        df = pd.read_csv('TaiwanStockHistoryDailyData.csv')
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        self.SQL.write_Dateframe(
            df, tablename='dailytwstock', exists='replace')

    def export_history_data(self):
        """
            to export taiwan stock history data to csv
        """
        df = self.SQL.read_Dateframe(f"select * from `dailytwstock`;")
        df.set_index('date', inplace=True)
        df.to_csv("TaiwanStockHistoryDailyData.csv")

    def GetALLStockData(self, index=None):
        df = self.SQL.read_Dateframe(f"select * from `dailytwstock`;")
        if index:
            df.set_index('date', inplace=True)
        return df
        # return self.SQL.read_Dateframe(f"select * from `dailytwstock` where stock_id = '3026' or stock_id ='3035' or stock_id ='5258' or stock_id ='5469';")

    def crawl_SecuritiesListingOverviewMonthlyReport(self, start_date: str = "2013-01-01", end_date: str = str(datetime.today().date())):
        """

            用來獲取 發行股數等相關股票資料
        Args:
            start_date (str, optional): Defaults to "2013-01-01".
            end_date (str, optional): Defaults to str(datetime.today().date()).
        """
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        all_month = [str(dt.date()).replace('-', '')[:6]
                     for dt in rrule(MONTHLY, dtstart=start_date, until=end_date)]

        # 設定請求頭
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        }

        catch_name = []
        dir_path = 'History/SecuritiesListingOverviewMonthlyReport'  # 將這裡替換為您的目錄路徑
        files = os.listdir(dir_path)

        for file in files:
            if file == 'extract':
                continue
            catch_name.append(file.replace('.zip', ''))

        for each_month in all_month:
            print(each_month)
            if each_month in catch_name:
                continue
            url = f'https://www.twse.com.tw/rwd/staticFiles/inspection/inspection/04/004/{each_month}_C04004.zip'
            # 更改為你希望儲存文件的路徑
            output_path = f"History/SecuritiesListingOverviewMonthlyReport/{each_month}.zip"

            # 發送 GET 請求並下載文件
            response = self.session.get(url, headers=headers)
            response.raise_for_status()  # 確認請求成功，如果返回的 HTTP 狀態碼表示錯誤，則會產生異常

            # 檢查是否為HTML
            # <title>首頁 - TWSE 臺灣證券交易所</title>

            try:
                # 二進位不能成功解碼
                response.content.decode('utf-8')
            except:
                # 寫入文件
                with open(output_path, 'wb') as f:
                    f.write(response.content)

            time.sleep(30)

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
            last_date = last_date[0][0]
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

    def Rank_Symbol(self, TargetSymobls:list):
        allStockData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`")
        
        Rank_data = {}
        for each_symbol in TargetSymobls:
            each_symbol_data = allStockData[allStockData['stock_id'] == each_symbol]
            if each_symbol_data['收盤價'].iloc[-1] >210:
                continue
            Rank_data[each_symbol] = (each_symbol_data['成交股數'] * each_symbol_data['收盤價']).iloc[-1]

        Rank_data = dict(sorted(Rank_data.items(), key=lambda item: item[1]))
        print(Rank_data)
        

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

        # 取得資料庫已經擁有的選股紀錄
        daytargets = self.SQL.get_db_data("select * from everydaytarget;")
        checked_day = [_daytarget[0] for _daytarget in daytargets]

        parser_data = {}
        for index, each_date in enumerate(date_list):

            filter_symbols = []
            # 整體的股票先過濾要大於300天
            if index < 300:
                continue

            if each_date in checked_day:
                continue

            print("目前天數:", each_date)
            for each_id in allStockID:
                print("目前解析股票:", each_id)
                if each_id in parser_data:
                    each_stock_data = parser_data[each_id]
                else:
                    each_stock_data = allStockData[allStockData['stock_id'] == each_id]
                    parser_data[each_id] = each_stock_data

                each_date_list = each_stock_data['date'].to_list()
                each_date_list = [str(i) for i in each_date_list]

                # 該日期是否存在
                if each_date not in each_date_list:
                    continue

                # 個別的資料量也要大於300
                if each_date_list.index(each_date) < 300:
                    continue
                
                each_symbol_data = each_stock_data[:index]
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

            filter_symbols_json = json.dumps(filter_symbols)
            # 將資料保存到資料庫
            self.SQL.change_db_data(
                f"INSERT INTO everydaytarget (date, target_symbol) VALUES ('{each_date}', '{filter_symbols_json}');")

    def get_daytargets(self, start_date=None):
        if start_date:
            daytargets = self.SQL.get_db_data(
                f"select * from everydaytarget where date >'{start_date}';")
        else:
            daytargets = self.SQL.get_db_data("select * from everydaytarget;")
        return daytargets

    def getIssueSharesData(self):
        df = self.SQL.read_Dateframe(
            f"select * from IssueShares ;")

        df.set_index('stock_id', inplace=True)
        return df

    def get_myself_filtersymbol(self, Trends_symbol: list, systeam_money: int = 500000):
        """
            用來將趨勢模板所過濾出來的股票
            再次過濾

        Args:
            Trends_symbol (list): ['0051', '0056', '00640L', '00645', '00646', '00657', '00661', '00662', '00670L', '00713', '00733', '00735', '00737',
         '00757', '00762', '00770', '00830', '00851', '00861', '00878', '00893', '00895', '00901', '00903', '02001L', '020022', '020028', '020029', '1108', '1229', '1234', '1337', '1340', '1418', '1423', '1432', '1449', '1464', '1472', '1477', '1504', '1512', '1525', '1528', '1538', '1540', '1583', '1608', '1612', '1616', '1618', '1786', '1904', '1905', '1907', '2206', '2228', '2236', '2239', '2301', '2308', '2323', '2324', '2329', '2331', '2332', '2344', '2345', '2352', '2356', '2360', '2365', '2368', '2371', '2376', '2377', '2382', '2383', '2393', '2397', '2399', '2402', '2409', '2414', '2421', '2423', '2424', '2425', '2427', '2428', '2439', '2449', '2466', '2468', '2486', '2488', '2489', '2493', '2515', '2528', '2536', '2539', '2630', '2704', '2705', '2712', '2722', '3013', '3017', '3025', '3026', '3032', '3033', '3038', '3046', '3055', '3231', '3266', '3312', '3356', '3380', '3481', '3515', '3518', '3543', '3583', '3607', '3617', '3622', '3653', '3673', '3694', '3706', '4439', '4526', '4532', '4572', '4967', '5258', '5469', '5706', '5906', '6116', '6120', '6142', '6166', '6191', '6197', '6214', '6215', '6235', '6243', '6282', '6285', '6412', '6451', '6579', '6592', '6605', '6669', '8016', '8163', '8210', '8215', '8271', '8996', '9110', '911608']
        """

        # 取得資料庫的最後一天
        last_Date = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' order by date DESC limit 1;")
        last_Date = last_Date['date'].iloc[0]

        # 在透過今天的日期去過濾
        last_DateData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`where date='{last_Date}';")
        last_DateData.set_index("stock_id", inplace=True)

        # 流動性過差會可能導致大的滑價
        # 由於擔心價格過高會無法買入,所以再次將過高的股票過濾掉 (總資金百分之二十五)
        out_list = []
        for _each_stock in Trends_symbol:
            _eachStockMoney = last_DateData[last_DateData.index ==
                                            _each_stock].iloc[0]['成交金額']
            _eachClosePrice = last_DateData[last_DateData.index ==
                                            _each_stock].iloc[0]['收盤價']

            if _eachStockMoney > 10000000:
                if _eachClosePrice * 1000 < systeam_money * 0.25:
                    out_list.append(_each_stock)

    def get_myself_filtersymbol_condtion2(self, Trends_symbol: list):
        # 取得資料庫的最後一天
        last_Date = self.SQL.read_Dateframe(
            "select date from `dailytwstock` where stock_id='2330' order by date DESC limit 1;")
        last_Date = last_Date['date'].iloc[0]

        # 在透過今天的日期去過濾
        last_DateData = self.SQL.read_Dateframe(
            f"select * from `dailytwstock`where date='{last_Date}';")
        last_DateData.set_index("stock_id", inplace=True)

        # 取得發行股數
        last_IssueShares_lastday = self.SQL.read_Dateframe(
            f"select * from IssueShares order by issue_date DESC limit 1;")

        last_IssueShares = self.SQL.read_Dateframe(
            f"select * from IssueShares where issue_date={last_IssueShares_lastday['issue_date'][0]}")

        last_IssueShares.set_index("stock_id", inplace=True)

        share_capitals = []
        for _each_stock in Trends_symbol:
            if last_IssueShares[last_IssueShares.index == _each_stock].empty:
                continue
            _IssueShares = last_IssueShares[last_IssueShares.index ==
                                            _each_stock].iloc[0]['IssueShares']
            _eachClosePrice = last_DateData[last_DateData.index ==
                                            _each_stock].iloc[0]['收盤價']

            share_capitals.append(
                [_each_stock, _IssueShares * _eachClosePrice])

        return sorted(share_capitals, key=lambda x: x[1])

    def parser_SecuritiesListingOverviewMonthlyReport(self):
        """
            首頁:https://www.twse.com.tw/zh/trading/statistics/list04-223.html

            用來爬取上市股數之資料
        """
        files = os.listdir('History/SecuritiesListingOverviewMonthlyReport')
        month_files = [file_name.replace(
            '.zip', '') for file_name in files if file_name != 'extract']

        for month_file in month_files:
            print(month_file)
            if month_file < '202307':
                continue

            with zipfile.ZipFile(f'History\SecuritiesListingOverviewMonthlyReport\{month_file}.zip', 'r') as zip_ref:
                file_name = zip_ref.namelist()[0]

            with zipfile.ZipFile(f'History\SecuritiesListingOverviewMonthlyReport\{month_file}.zip', 'r') as zip_ref:
                zip_ref.extractall(
                    'History\SecuritiesListingOverviewMonthlyReport\extract')

            if month_file == '201503':
                df = pd.read_excel(
                    f"History\SecuritiesListingOverviewMonthlyReport\extract\{file_name}", sheet_name='7.print')
            else:
                df = pd.read_excel(
                    f"History\SecuritiesListingOverviewMonthlyReport\extract\{file_name}", sheet_name='7')

            df = df[['上市股票     Listed Stocks', 'Unnamed: 1', 'Unnamed: 11']][5:]
            df = df.rename(columns={"上市股票     Listed Stocks": "stock_id",
                                    'Unnamed: 1': "stockName",
                                    "Unnamed: 11": "IssueShares"})

            df['stock_id'] = df['stock_id'].apply(lambda x: str(x).strip())
            df.set_index('stock_id', inplace=True)
            df.dropna(inplace=True)

            check_symbol = DataTransformer.find_duplicates(df.index.to_list())

            # 創建一個新的 DataFrame 用於儲存不重複的符號
            filtered_df = pd.DataFrame()

            for i in range(df.shape[0]):
                if df.iloc[i].name in check_symbol and '普 通' not in df.iloc[i]['stockName']:
                    continue
                else:
                    filtered_df = pd.concat([filtered_df, df.iloc[i:i+1]])

            # 以股數計算
            filtered_df['IssueShares'] = filtered_df['IssueShares'] * 1000
            filtered_df['IssueShares'] = filtered_df['IssueShares'].astype(
                'int64')
            filtered_df = filtered_df[['IssueShares']]

            for i in range(filtered_df.shape[0]):
                self.SQL.change_db_data(
                    f"INSERT INTO issueshares (issue_date, stock_id, IssueShares) VALUES ('{month_file}', '{filtered_df['IssueShares'].index[i]}', {filtered_df['IssueShares'].iloc[i]});")


if __name__ == '__main__':
    app = DataProvider().Rank_Symbol(["0052", "0053", "0057", "006208", "00631L", "00640L", "00645", "00646", "00647L", "00657", "00657K", "00661", "00662", "00663L", "00670L", "00675L", "00685L", "00757", "00762", "00830", "00851", "00861", "00875", "00876", "00891", "00892", "00894", "00895", "00904", "00905", "00909", "00913", "020030", "020031", "020034", "1203", "1307", "1319", "1418", "1432", "1436", "1438", "1445", "1472", "1473", "1514", "1519", "1522", "1524", "1535", "1538", "1560", "1568", "1615", "1616", "1773", "1805", "1806", "1809", "2006", "2024", "2025", "2062", "2105", "2204", "2233", "2330", "2347", "2348", "2365", "2369", "2387", "2390", "2404", "2417", "2420", "2442", "2443", "2460", "2465", "2467", "2476", "2493", "2509", "2515", "2527", "2535", "2537", "2539", "2543", "2546", "2891", "2906", "3002", "3005", "3010", "3017", "3025", "3029", "3034", "3036", "3041", "3050", "3055", "3149", "3167", "3266", "3296", "3311", "3321", "3376", "3413", "3437", "3530", "3533", "3543", "3545", "3607", "3622", "3653", "3661", "3679", "3702", "3711", "4555", "4720", "4746", "4912", "4930", "4956", "4961", "4994", "5215", "5225", "5244", "5269", "5484", "5515", "5519", "6108", "6136", "6165", "6189", "6197", "6201", "6239", "6243", "6257", "6442", "6451", "6585", "6668", "6695", "6756", "6789", "6807", "8011", "8103", "8110", "8112", "8163", "8271", "8442", "8467", "9906", "9912", "9924", "9930", "9939", "9946", "9958"])

    # print(app.date_range(datetime.strptime("2023-06-09","%Y-%m-%d"),datetime.strptime("2023-06-12","%Y-%m-%d")))

    # print(app.get_myself_filtersymbol(json.loads(app.get_daytargets()[-1][1])))

    # get_myself_filtersymbol

    # print(app.crawl_finance_statement(2021, 3, "2330"))

    # 取得最後一天的資料
    # print(app.get_myself_filtersymbol(app.get_daytargets()[-1][1]))
