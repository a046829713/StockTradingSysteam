import json
from Database import router
from sqlalchemy import text
import pandas as pd
import time
from . import clients


class DB_operate():
    def __init__(self) -> None:
        self._checkALLDataBaseTables()

    def _checkALLDataBaseTables(self):
        """
            當建立好SQL的最上層物件
            應該要檢查所有的應該存在的相關資料庫
        """
        clients.checkIfDataBase()

    def wirte_data(self, quoteSymbol: str, out_list: list):
        """
        將商品資料寫入資料庫
        [{'Date': '2022/07/01', 'Time': '09:25:00', 'Open': '470',
            'High': '470', 'Low': '470', 'Close': '470', 'Volume': '10'}]
        """
        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:
                sql_sentence = f'INSERT INTO `{quoteSymbol}` (Date, Time, Open, High, Low, Close, Volume) VALUES (:Date, :Time, :Open, :High, :Low, :Close, :Volume)'
                conn.execute(
                    text(sql_sentence),
                    out_list
                )
        except Exception as e:
            print(e)

    def get_db_data(self, text_msg: str) -> list:
        """
            專門用於select from
        """
        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:

                result = conn.execute(
                    text(text_msg)
                )
                # 資料範例{'Date': '2022/07/01', 'Time': '09:25:00', 'Open': '470', 'High': '470', 'Low': '470', 'Close': '470', 'Volume': '10'}

                return list(result)
        except Exception as e:
            print(e)

    def change_db_data(self, text_msg: str) -> None:
        """ 用於下其他指令
        Args:
            text_msg (str): SQL_Query
        Returns:
            None
        """
        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:
                conn.execute(text(text_msg))
        except Exception as e:
            print(e)

    def create_table(self, text_msg: str) -> None:
        """ 創建日線資料表
        Args:
            text_msg (str): symbolcode TC.F.TWF.IAF.HOT
        """

        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:
                conn.execute(text(
                    f"CREATE TABLE `financialdata`.`{text_msg}`(`Date` date NOT NULL,`Time` time NOT NULL,`Open` FLOAT NOT NULL,`High` FLOAT NOT NULL,`Low` FLOAT NOT NULL,`Close` FLOAT NOT NULL,`Volume` FLOAT  NOT NULL,PRIMARY KEY(`Date`, `Time`));"))
        except Exception as e:
            print(e)

    def read_Dateframe(self, text_msg: str) -> pd.DataFrame:
        """
            to get pandas Dateframe
            symbol_name: 'btcusdt-f'
        """
        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:
                return pd.read_sql(text_msg, con=conn)
        except Exception as e:
            print(e)

    def write_Dateframe(self, df: pd.DataFrame, tablename: str, exists='replace') -> pd.DataFrame:
        """
            to write pandas Dateframe
            symbol_name or tablename: 
        """
        try:
            self.userconn = router.Router().mysql_financialdata_conn
            with self.userconn as conn:
                df.to_sql(tablename, con=conn, if_exists=exists)
        except Exception as e:
            print(e)


class SqlSentense():
    @staticmethod
    def createEveryDayTarget() -> str:
        sql_query = '''
            CREATE TABLE everydaytarget (
                date VARCHAR(255),
                target_symbol TEXT
            );
        '''

        return sql_query

    @staticmethod
    def createIssueShares() -> str:
        sql_query = '''
            CREATE TABLE issueshares (
                issue_date VARCHAR(255),
                stock_id VARCHAR(255),
                IssueShares bigint,
                PRIMARY KEY (stock_id, issue_date)
            );

        '''

        return sql_query
