"""
1. 从本地SQL数据库获得数据
2. 从Wind请求数据
3. 将从Wind请求得到的数据保存在本地SQL数据库中
"""

import psycopg2
import pymysql
import datetime
import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
import warnings
from WindPy import w

warnings.filterwarnings("ignore")  # 关闭警告
# 连接SQL数据库
# conn = psycopg2.connect(database="WindStockData", user="postgres", password="191124", host="localhost", port="5432")
# 获得游标，一个游标对象可以对数据库进行执行操作，多个应用会在同一个连接种创建多个光标

# For adding the "numpy.float64" data type when inserting the data into double
pymysql.converters.encoders[np.float64] = pymysql.converters.escape_float
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)

# conn = pymysql.connect(db="Wind", user="admin", password="TFqt3qihVYei4qZz", 
#                        host="jacarandastock.com", port=3306)
conn = pymysql.connect(db="Wind", user="cholian", password="123Q456w", 
                       host="43.132.196.216", port=3306)

cursor = conn.cursor()


class StockData:

    def __init__(self, update=False):
        self.SQL_data = pd.DataFrame(None)  # SQLdataframe
        self.Wind_data = pd.DataFrame(None)  # Winddataframe
        self.blank_list = []  # 未录入清单
        self.update = update  # 是否更新数据

    def data_from_SQL(self, stock_codes: list, dates: list, field: str) -> DataFrame:
        """
        从本地SQL数据库中获取stock_code-date-field数据；记录SQL数据中没有保存的数据

        :param stock_codes: 股票代码列表
        :param dates: 日期(datetime.date)列表
        :param field: 指标名
        :return: SQL数据dataframe
        """

        # 检查SQL中是否存在此指标
        # 20220507 debug: table_schema='public' has wrong with the result in the next version, so dropped it
        
        # sql = """
        # SELECT column_name FROM information_schema.columns 
        # WHERE table_schema='public' AND table_name='stockdata';
        # """
        
        sql = '''
        SELECT column_name FROM information_schema.columns
        WHERE table_name='stockdata';       
        '''
        cursor.execute(sql)
        column_names = [t[0] for t in cursor.fetchall()]  # 列名
        
        # 若field对应列名不存在，在TABLE中加入此列
        if field.lower() not in column_names:
            sql = """ALTER TABLE stockdata ADD %s double precision;""" % field
            cursor.execute(sql)
            conn.commit()
            print("已向本地SQL数据库添加指标%s" % field)

        # 创建一个用来存放数据的DataFrame
        print("向本地SQL数据库请求数据")
        self.SQL_data = pd.DataFrame(np.zeros(shape=(len(stock_codes), len(dates))), columns=dates)
        self.SQL_data.index = stock_codes
        self.SQL_data.index.name = field

        # 将股票代码列表和日期列表转换为元组格式
        stock_codes = tuple(stock_codes)  # 股票代码元组
        dates = [datetime.datetime.strftime(date, "%Y-%m-%d") for date in dates]  # 将datetime改为str格式
        dates_tuple = tuple(dates)  # 日期元组

        # 将所有code，date，field组合放入未录入清单
        for code in stock_codes:
            for date in dates:
                self.blank_list.append({"stock_code": code, "date": date, "field": field})
        if len(stock_codes) == 1:
            stock_codes = "('" + str(stock_codes[0]) + "')"  # 对于只有1个元素的股票代码元组，去掉元素后面的逗号
        if len(dates) == 1:
            dates_tuple = "('" + str(dates[0]) + "')"  # 对于只有1个元素的日期元组，去掉元素后面的逗号

        # 根据stock_codes和dates查询field的数据
        sql = "SELECT stock_code,date," + field + " FROM stockdata WHERE stock_code IN " + str(
            stock_codes) + " AND date IN " + str(dates_tuple)
        
        cursor.execute(sql)
        SQLdata = cursor.fetchall() 
        #! 从本地SQL返回的数据行列表，每行元素分别为stock_code,date,value
        
        # if SQLdata.empty:
        #     SQLdata = pd.DataFrame()
    
        # 将每个value录入DataFrame对应单元格，并从未录入清单中剔除对应code，date和field组合
        for row in SQLdata:
            if (row == None) or (row[-1] == None) or (self.update == True):  # 如果为空值或需要更新数据，不做任何处理
                pass
            else:
                # ! Sample data for self.SQL_data:
                # ! self.SQL_data.index = stock_codes
                # ! self.SQL_data.index.name = field
                
                self.SQL_data.loc[row[0], row[1]] = row[-1]  # 录入数据  -> self.SQL_data.loc[‘000001.SH’, '2021-05-01'] = '25.5'
                try:
                    self.blank_list.remove(
                        {"stock_code": row[0], "date": datetime.datetime.strftime(row[1], "%Y-%m-%d"),
                        "field": field})  # 从未录入清单中删除
                except:
                    continue

        if self.blank_list:
            print("需要向Wind请求%s条数据" % len(self.blank_list))
        else:
            print("成功")

        return self.SQL_data

    def data_from_Wind(self, stock_code=0, begin_date=0, end_date=0, field=0, term="Y", days="Alldays",
                       fill="Previous") -> DataFrame:
        """
        从Wind请求数据

        :param stock_code: 股票代码(str或list)
        :param begin_date: 开始日期
        :param end_date: 结束日期
        :param field: 指标
        :param term: 报告期类型
        :param days: 返回数据的日期类型
        :param fill: 缺漏值的处理办法
        :return: Wind数据dataframe
        """
        assert not (type(stock_code) == list and type(field) == list), "股票代码和指标不能同时为多个"

        # 默认从本地SQL数据库未保存的数据中获得对应股票代码和日期
        if stock_code == 0 or begin_date == 0 or end_date == 0 or field == 0:
            stock_code = list(set([dic["stock_code"] for dic in self.blank_list]))  # 股票代码列表
            dates = list(set([dic["date"] for dic in self.blank_list]))  # 日期列表
            dates.sort()
            begin_date = dates[0]  # 数据获取开始日期
            end_date = dates[-1]  # 数据获取结束日期
            field = self.SQL_data.index.name  # 指标名称

        print("向Wind请求数据")
        if type(stock_code) == list:
            print("codes:", stock_code[0], "...", stock_code[-1])
        print("begin_date:", begin_date)
        print("end_date:", end_date)
        print("fields:", field)
        print("Period:", term)

        # 利用Wind WSD函数从Wind获取数据
        if type(stock_code) == list and len(stock_code) > 2000:  # 若有超过2000个股票代码，则分成3个package请求数据
            codes_package = [stock_code[:int(len(stock_code) / 3)],
                             stock_code[int(len(stock_code) / 3):int(2 * len(stock_code) / 3)],
                             stock_code[int(2 * len(stock_code) / 3):]]
            Wind_data_dfs = []
            for codes in codes_package:
                status_code, Wind_data = w.wsd(codes=codes, beginTime=begin_date, endTime=end_date, fields=field,
                                               Period=term, Days=days, Fill=fill, PriceAdj="F", zoneType=1, rptType=1,
                                               ruleType=2, gRateType=1, returnType=1, unit=1, usedf=True)
                Wind_data_dfs.append(Wind_data)  # 保存所有的package
            self.Wind_data = pd.concat(Wind_data_dfs, axis=1)  # 合并所有的package
            self.Wind_data.index.name = field
        else:  # 否则一起请求数据
            status_code, self.Wind_data = w.wsd(codes=stock_code, beginTime=begin_date, endTime=end_date, fields=field,
                                                Period=term, Days=days, Fill=fill, PriceAdj="F", zoneType=1, rptType=1,
                                                ruleType=2, gRateType=1, returnType=1, unit=1, usedf=True)
            self.Wind_data.index.name = field

        # 统一Wind_data格式：index为日期列表，column为股票代码列表
        if type(stock_code) == list and len(stock_code) > 1:
            pass
        elif type(stock_code) == list and len(stock_code) == 1:
            self.Wind_data.columns = [stock_code[0]]
        elif type(stock_code) == str:
            self.Wind_data.columns = [stock_code]
        if begin_date == end_date:
            self.Wind_data.columns = [begin_date]
            self.Wind_data = pd.DataFrame(self.Wind_data.values.T, index=self.Wind_data.columns,
                                          columns=self.Wind_data.index)
            self.Wind_data.columns.name = ""
            self.Wind_data.index.name = field

        return self.Wind_data

    def data_to_SQL(self, Wind_data=0):
        """
        将Wind数据保存在SQL中

        :param Wind_data: Wind数据dataframe
        """
        # 默认使用实例获取的Wind_data
        if Wind_data == 0:
            Wind_data = self.Wind_data

        # 通过Wind数据DataFrame获得股票代码列表和日期列表
        print("正在向本地SQL数据库保存数据")
        stock_codes = Wind_data.columns.values.tolist()  # 股票代码列表
        dates = Wind_data.index.values.tolist()  # 日期列表

        # 将DataFrame的每组stock_code-date-field-value信息整理为字典，存放在列表中
        data_list = []
        for code in stock_codes:
            for date in dates:
                data_dict = {"stock_code": code,  # 股票代码
                             "date": date,  # 日期
                             "field": Wind_data.index.name,  # 指标名称
                             "value": Wind_data.iloc[dates.index(date), stock_codes.index(code)]  # 数值
                             }
                if data_dict["value"] and np.isnan(data_dict["value"]):  # 如果获取的数值为空值None，则转换为空值Nan，以便区分
                    # BUG WIND可能返回nan 或者None, we need to transfer the nan into None
                    # BUG make sure not theh None then judge the nan.
                    data_dict["value"] = None
                data_list.append(data_dict)  # 将每个数据字典保存在列表中

        # 将列表中的每组信息保存到SQL中
        for data_dict in data_list:
            print(data_dict)
            # 查询表中每行stock_code-date
            sql = """SELECT stock_code,date FROM stockdata;"""
            cursor.execute(sql)
            code_dates = [t for t in cursor.fetchall()]
            # 若stock_code-date不存在，则INSERT INTO整个data_dict作为一条新数据
            if (data_dict["stock_code"], data_dict["date"]) not in code_dates:
                sql = """INSERT INTO stockdata (stock_code,date,""" + data_dict[
                    "field"] + """) VALUES (%s,%s,%s);"""
                params = (data_dict["stock_code"], data_dict["date"], data_dict["value"])
                
                cursor.execute(sql, params)
                conn.commit()
            # 若code-date存在，则检查code-date-field是否存在
            else:
                sql = "SELECT " + data_dict["field"] + " FROM stockdata WHERE " \
                    "stock_code=" + "('" + data_dict["stock_code"] + "')" + " and " \
                    "date=" + "('" + datetime.datetime.strftime(data_dict["date"],"%Y-%m-%d") + "');"
                cursor.execute(sql)
                value = cursor.fetchone()[0]  # 取到的单元格value
                if value == data_dict["value"]:  # 若现有值存在且一致，跳过
                    pass
                else:  # 若现有值为空，或现有值存在但不一致：更新值
                    sql = """UPDATE stockdata SET """ + data_dict[
                        "field"] + """ = %s WHERE stock_code=%s AND date=%s;"""
                    params = (data_dict["value"], data_dict["stock_code"], data_dict["date"])
                    cursor.execute(sql, params)
                    conn.commit()


class ConstituentsData():

    def __init__(self, sectorid, date):

        self.sectorid = sectorid  # 板块代码
        self.date = date  # 日期

    def constituents_from_SQL(self, sectorid=0, date=0):
        """
        从本地SQL数据库获取板块成分股数据
        """
        # 查询表名，若表constituents不存在，则创建一个
        sql = "SELECT tablename FROM pg_tables WHERE tablename NOT LIKE 'pg%' AND tablename NOT LIKE 'sql_%' ORDER BY tablename;"
        cursor.execute(sql)
        conn.commit()
        tablenames = [t[0] for t in cursor.fetchall()]
        if "constituents" not in tablenames:
            sql = """CREATE TABLE constituents (
                        sectorid VARCHAR(20) NOT NULL,
                        date DATE NOT NULL,
                        stock_code VARCHAR(9) NOT NULL,
                        stock_name VARCHAR(16) NOT NULL
                        );
                        """
            cursor.execute(sql)
            conn.commit()
            print("TABLE constituents成功创建")

        if sectorid == 0 or date == 0:
            sectorid = self.sectorid
            date = self.date
        print("向本地SQL数据库请求成分股数据")
        # 查询表中sectorid-date对应的stockcodes
        sql = """SELECT stock_code,stock_name FROM constituents
        WHERE sectorid = %s AND date = %s;"""
        params = (sectorid, date)
        cursor.execute(sql, params)
        self.SQLconstituents = dict([t for t in cursor.fetchall()])
        if self.SQLconstituents:
            print("成功")
            return self.SQLconstituents
        else:
            print("需要向Wind请求数据")

    def constituents_from_Wind(self, sectorid=0, date=0):
        """
        从Wind获取板块成分股数据
        """
        if sectorid == 0 or date == 0:
            sectorid = self.sectorid
            date = self.date
        print("向Wind请求成分股数据")
        Winddata = w.wset("sectorconstituent", date=date, sectorid=sectorid, usedf=True)[1]
        constituent_codes = Winddata["wind_code"].values.tolist()  # 股票代码
        constituent_names = Winddata["sec_name"].values.tolist()  # 股票简称
        self.Windconstituents = dict(zip(constituent_codes, constituent_names))  # 代码-名称字典
        print("成功获取成分股信息")
        return self.Windconstituents

    def constituents_to_SQL(self, constituents=0):
        """
        将Wind板块成分股数据存放在SQL数据库中
        """
        if constituents == 0:
            constituents = self.Windconstituents
        print("向本地SQL保存成分股数据")
        for code, name in zip(constituents.keys(), constituents.values()):
            sql = """INSERT INTO constituents (sectorid,date,stock_code,stock_name) VALUES (%s,%s,%s,%s);"""
            params = (self.sectorid, self.date, code, name)
            cursor.execute(sql, params)
            conn.commit()
        print("成功向SQL数据库保存成分股信息")
