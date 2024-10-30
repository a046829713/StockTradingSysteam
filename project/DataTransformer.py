import pandas as pd
import numpy as np
from utils.TimeCountMsg import TimeCountMsg

class DataTransformer():
    def __init__(self) -> None:
        pass

    @staticmethod
    def GetSuperTrends_mode1(each_symbol_data: pd.DataFrame) -> bool:
        """
        each_id(str):'2330'
            股價必須要高於 150 天(收盤價)的平均,和200天(收盤價)的平均
            並且 150 天(收盤價)的平均 ,要在 200天(收盤價)上方
        """

        Close = each_symbol_data['收盤價']
        Close_mean_50 = Close.rolling(window=50).mean()
        Close_mean_150 = Close.rolling(window=150).mean()
        Close_mean_200 = Close.rolling(window=200).mean()

        if Close.iloc[-1] > Close_mean_150.iloc[-1] and Close.iloc[-1] > Close_mean_200.iloc[-1] and Close_mean_150.iloc[-1] > Close_mean_200.iloc[-1] \
                and Close_mean_50.iloc[-1] > Close_mean_150.iloc[-1] and Close_mean_50.iloc[-1] > Close_mean_200.iloc[-1]:
            return True
        else:
            return False

    @staticmethod
    def is_moving_avg_up_for_month(each_symbol_data: pd.DataFrame, days=200, period=30) -> bool:
        """判斷向上趨勢是否有滿一個月

        Args:
            each_symbol_data (pd.DataFrame): _description_
            days (int, optional): _description_. Defaults to 200.
            period (int, optional): _description_. Defaults to 30.

        Returns:
            bool: _description_
        """
        Close = each_symbol_data['收盤價']

        each_symbol_data['Moving_Avg'] = Close.rolling(window=days).mean()

        # Calculate the difference between each day's moving average and the previous day's
        each_symbol_data['Diff'] = each_symbol_data['Moving_Avg'].diff()

        # Check if the difference is positive (indicating an increase)
        each_symbol_data['Is_Up'] = np.where(
            each_symbol_data['Diff'] > 0, 1, 0)

        # Calculate the rolling sum of Is_Up over the past month
        each_symbol_data['Up_For_Month'] = each_symbol_data['Is_Up'].rolling(
            window=period).sum()

        # Check if Up_For_Month equals period (indicating the moving average has increased every day for a month)
        each_symbol_data['Condition_Met'] = np.where(
            each_symbol_data['Up_For_Month'] == period, True, False)

        if each_symbol_data['Condition_Met'].iloc[-1] == True:
            return True
        else:
            return False

    @staticmethod
    def is_price_up_More_percent(each_symbol_data: pd.DataFrame, weeks=52):
        """當前收盤價至少比前52周最低價的最底價格高出百分之25

        Args:
            data (_type_): _description_
            weeks (int, optional): _description_. Defaults to 52.

        Returns:
            _type_: _description_
        """

        Low = each_symbol_data['最低價']
        Close = each_symbol_data['收盤價']

        each_symbol_data['Lowest_in_52_Weeks'] = Low.rolling(
            window=weeks*5).min()

        each_symbol_data['Diff'] = Close - \
            each_symbol_data['Lowest_in_52_Weeks']

        # # Calculate the percentage difference
        each_symbol_data['Percentage_Diff'] = (
            each_symbol_data['Diff'] / each_symbol_data['Lowest_in_52_Weeks']) * 100

        # # Check if the current closing price is at least 25% higher than the lowest price in the past 52 weeks
        each_symbol_data['Condition_Met'] = np.where(
            each_symbol_data['Percentage_Diff'] >= 25, True, False)

        if each_symbol_data['Condition_Met'].iloc[-1] == True:
            return True
        else:
            return False
        

    def calculate_rsr(each_symbol_data: pd.DataFrame, period=126, weeks=6):        
        """Calculate the Relative Strength Ranking over a specified period"""
        # Calculate the rate of return over the specified period
        Close = each_symbol_data['收盤價']

        each_symbol_data['Return'] = Close.pct_change(periods=period)

        # Rank the returns
        each_symbol_data['RS_Rank'] = each_symbol_data['Return'].rank(
            pct=True) * 100

        if each_symbol_data['RS_Rank'].iloc[-1] > 70:
            # Calculate the 6-week moving average of the RS ranking
            each_symbol_data['RSR_MA'] = each_symbol_data['RS_Rank'].rolling(
                window=weeks*5).mean()
            # Calculate the difference between each week's moving average and the previous week's
            each_symbol_data['Diff'] = each_symbol_data['RSR_MA'].diff()

            # Check if the difference is positive (indicating an increase)
            each_symbol_data['Is_Up'] = each_symbol_data['Diff'] > 0

            # Calculate the rolling sum of Is_Up over the past six weeks
            each_symbol_data['Up_For_Six_Weeks'] = each_symbol_data['Is_Up'].rolling(window=weeks).sum()

            each_symbol_data['Condition_Met'] = each_symbol_data['Up_For_Six_Weeks'] == weeks

            if each_symbol_data['Condition_Met'].iloc[-1] == True:
                return True
            else:
                return False
            

        return False
    
    
    @staticmethod
    def find_duplicates(lst):
        """
        lst = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
        duplicates = find_duplicates(lst)
        print(duplicates)  # 會印出 {2, 3, 4}

        Args:
            lst (_type_): _description_

        Returns:
            _type_: _description_
        """
        seen = set()
        duplicates = set()

        for item in lst:
            if item in seen:
                duplicates.add(item)
            seen.add(item)

        return duplicates