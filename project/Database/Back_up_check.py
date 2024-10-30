from .SQL_operate import DB_operate, SqlSentense


def checkIFtable():
    """
        用來檢查資料表名稱是否存在
    """

    getAllTablesName = DB_operate().get_db_data('show tables;')
    getAllTablesName = [y[0] for y in getAllTablesName]

    if 'everydaytarget' not in getAllTablesName:
        sql = SqlSentense.createEveryDayTarget()
        DB_operate().change_db_data(sql)

    if 'issueshares' not in getAllTablesName:
        sql = SqlSentense.createIssueShares()
        DB_operate().change_db_data(sql)