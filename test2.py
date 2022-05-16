import psycopg2
import pymysql
import datetime
import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
import warnings
from WindPy import w
w.start()
# w.menu()
w.isconnected()
import datetime


# For adding the "numpy.float64" data type when inserting the data into double
pymysql.converters.encoders[np.float64] = pymysql.converters.escape_float
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)

# conn = pymysql.connect(db="Wind", user="admin", password="TFqt3qihVYei4qZz", 
#                        host="jacarandastock.com", port=3306)
conn = pymysql.connect(db="Wind", user="cholian", password="123Q456w", 
                       host="43.132.196.216", port=3306)

cursor = conn.cursor()


codes = ['300648.SZ','603081.SH','603041.SH','603078.SH']
begin_date = '2013-12-31'
end_date= '2016-12-31'
field= 'ebitda'
term= 'Y'
days="Alldays",
fill="Previous"
status_code, Wind_data = w.wsd(codes=codes, beginTime=begin_date, endTime=end_date, fields=field,
                                               Period=term, Days=days, Fill=fill, PriceAdj="F", zoneType=1, rptType=1,
                                               ruleType=2, gRateType=1, returnType=1, unit=1, usedf=True)
stock_codes = Wind_data.columns.values.tolist()  # 股票代码列表
dates = Wind_data.index.values.tolist()  # 日期列表
stock_codes


data_list = []
for code in stock_codes:
    for date in dates:
        data_dict = {"stock_code": code,  # 股票代码
                        "date": date,  # 日期
                        "field": Wind_data.index.name,  # 指标名称
                        "value": Wind_data.iloc[dates.index(date), stock_codes.index(code)]  # 数值
                        }
        if data_dict["value"] == None or np.isnan(data_dict["value"]):  # 如果获取的数值为空值None，则转换为空值Nan，以便区分
            # data_dict["value"] = np.NaN
            data_dict["value"] = ''
        data_list.append(data_dict)  # 将每个数据字典保存在列表中
        
sql = """INSERT INTO stockdata (stock_code,date,""" + data_dict[
                "field"] + """) VALUES (%s,%s,%s);"""

params = (data_dict["stock_code"], data_dict["date"], data_dict["value"])

cursor.execute(sql, params)
conn.commit()