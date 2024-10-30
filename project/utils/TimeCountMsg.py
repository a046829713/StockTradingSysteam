from time import time


class TimeCountMsg():
    @staticmethod
    def record_timemsg(func):
        def wrapper(*args, **kwargs):

            begin_time = time()
            result = func(*args, **kwargs)
            end_time = time()
            # print("函數名稱:",func)
            # print("使用時間:",end_time-begin_time)
            return result

        return wrapper