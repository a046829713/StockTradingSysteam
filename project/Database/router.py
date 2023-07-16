import time
import typing
from sqlalchemy import engine
from Database import clients
from sqlalchemy import text

def check_alive(connect: engine.base.Connection):
    """
    在每次使用之前，先確認 connect 是否活者
    """
    connect.execute(text("SELECT 1 + 1;"))



def reconnect(connect_func: typing.Callable) -> engine.base.Connection:
    """如果連線斷掉，重新連線"""
    try:
        connect = connect_func()
    except Exception as e:
        print(e)
    return connect


def check_connect_alive(connect: engine.base.Connection, connect_func: typing.Callable):
    if connect:
        try:
            check_alive(connect)
            return connect
        except Exception as e:
            print(e)
            time.sleep(1)
            connect = reconnect(connect_func)
            return check_connect_alive(connect, connect_func)
    else:
        connect = reconnect(connect_func)
        return check_connect_alive(connect, connect_func)


class Router:
    def __init__(self):
        self._mysql_financialdata_conn =clients.get_mysql_financialdata_conn()
    

    def check_mysql_financialdata_conn_alive(self):
        self._mysql_financialdata_conn = check_connect_alive(self._mysql_financialdata_conn,clients.get_mysql_financialdata_conn)
        return self._mysql_financialdata_conn

    @property
    def mysql_financialdata_conn(self):
        """
        使用 property，在每次拿取 connect 時，
        都先經過 check alive 檢查 connect 是否活著
        """
        return self.check_mysql_financialdata_conn_alive()