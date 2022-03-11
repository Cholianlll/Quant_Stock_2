"""
1.定义股票类
2.定义股票池类
"""
import pandas as pd
from Wind_StockSelector_V2.GetData import ConstituentsData
from WindPy import w


### 股票类
class Stock:
    stock_dict = {}  # 保存所有Stock实例的字典

    def __init__(self, code, status="in the pool"):

        self.code = code  # 股票代码
        self.status = status  # 状态：在股票池中或不在股票池中

        self.filter_report = pd.DataFrame(columns=["description", "value", "threshold", "reserve"])  # 记录筛选过程df
        self.score_report = pd.DataFrame(
            columns=["description", "value", "threshold", "reserve", "weight", "score"])  # 记录评分df

    ## 方法：记录筛选过程
    def filter_record(self, description, value, threshold, reserve, code):
        # 指标名称，值，判断条件，筛选结果，股票代码
        self.filter_report = self.filter_report.append(
            {"description": description, "value": value, "threshold": threshold, "reserve": reserve}, ignore_index=True)
        self.filter_report.index = [code] * len(self.filter_report.index)

    ## 方法：记录评分结果
    def score_record(self, description, value, threshold, reserve, weight, score, code):
        self.score_report = self.score_report.append(
            {"description": description, "value": value, "threshold": threshold, "reserve": reserve, "weight": weight,
             "score": score}, ignore_index=True)
        self.score_report.index = [code] * len(self.score_report.index)

    ## 类方法：通过股票代码返回股票的原始数据和处理后数据表格
    @classmethod
    def get_stock(cls, stock_code, filter):
        # 原始数据表格
        primarydata = pd.DataFrame(data=None)
        primarydata.index.name = stock_code
        for _filter in filter.look_into:
            for df in _filter["primary_df"]:
                if stock_code in df.index.values.tolist():
                    for date in df.columns.values.tolist():
                        primarydata.loc[df.index.name, date] = df.loc[stock_code, date]
        columns = primarydata.columns.values.tolist()
        columns.sort()
        primarydata = primarydata[columns]

        # 处理后表格
        processeddata = pd.DataFrame(data=None)
        for _filter in filter.look_into:
            if stock_code in _filter["processed_df"].index.values.tolist():
                for date in _filter["processed_df"].columns.values.tolist()[1:-1]:
                    processeddata.loc[_filter["processed_df"].index.name, date] = _filter["processed_df"].loc[
                        stock_code, date]
                processeddata.loc[_filter["processed_df"].index.name, "target_value"] = _filter["processed_df"].loc[
                    stock_code, "target_value"]
        columns = processeddata.columns.values.tolist()
        columns.remove("target_value")
        columns.sort()
        columns.append("target_value")
        processeddata = processeddata[columns]



        return primarydata, processeddata


### 股票池类
class Stock_pool():

    def __init__(self, codes=None):
        self.pool = None  # 股票池
        self.stock_codes = codes  # 股票池股票代码
        self.sectorid = None  # 板块代码
        self.constituens = []  # 初始板块成分股id列表

    ## 方法：获取成分股
    def get_constituent(self, date, sectorid="a001010100000000"):  # 默认板块：全部A股
        self.sectorid = sectorid  # 板块代号
        get_constituents = ConstituentsData(self.sectorid, date)  # 实例化ConstituentsData类
        get_constituents.constituents_from_SQL()  # 尝试从SQL获得成分股数据
        if get_constituents.SQLconstituents:  # 如果能够从SQL获得相关数据
            self.stock_codes = list(get_constituents.SQLconstituents.keys())  # 初始股票池股票代码
            self.constituens = get_constituents.SQLconstituents  # 初始股票池成分股信息(代码+名称)
        else:  # 如果SQL中没有相关数据，则从Wind数据库请求相关数据，并且将数据保存在SQL中
            Windconstituents = get_constituents.constituents_from_Wind()  # 从wind获取成分股
            self.stock_codes = list(Windconstituents.keys())  # 初始股票池股票代码
            self.constituens = Windconstituents  # 初始股票池成分股信息(代码+名称)
            get_constituents.constituents_to_SQL()  # 将Wind成分股数据保存在本地SQL数据库

        # 将成分股中所有股票代码实例化,放入Stock类的stock_dict变量,放入股票池
        for code in self.stock_codes:
            Stock.stock_dict[code] = Stock(code, "in the pool")  # Stock实例化
        self.pool = list(Stock.stock_dict.values())  # 股票池为包含所有Stock实例的列表
        print("已获取%s成分股%s，初始股票池中共有%s支股票\n" % (date, self.sectorid, len(self.stock_codes)))

    # 方法：导出回测表格
    def traceback(self, scorer, operate_date, export_root, range="all", asset=1e6, end_date=0, update_stockprice=False):
        """
        导出一个可以导入到Wind组合管理中进行回测的表格

        :param operate_date: 操作日期
        :param range: 取股范围
        :param asset: 资金头寸
        """
        if range == "all":
            df = scorer.score_report.iloc[:, [0, 1, 2]].copy()
        else:
            df = scorer.score_report.iloc[:range, [0, 1]].copy()
            df.insert(2, "仓位权重", [score / df["总分"].sum() for score in df["总分"].values.tolist()])
        stock_codes = df.index.values.tolist()

        # 获取股价数据
        data = w.wsd(codes=stock_codes, beginTime=operate_date, endTime=operate_date, fields="close", Period="D",
                     Days="ALLdays", Fill="Previous", zoneType=1, rptType=1, ruleType=2, gRateType=1, returnType=1,
                     unit=1, usedf=True)[1]

        # 按权重计算调整日期各股持股数量
        prices = data["CLOSE"].values.tolist()
        df["调整日期"] = [operate_date] * len(df.index)
        df["成本价格"] = prices
        df["市值"] = df["仓位权重"] * asset
        df["持仓数量"] = df["市值"] // df["成本价格"]
        self.position = (df["持仓数量"] * df["成本价格"]).sum()  # 总仓位
        df.index.name = "证券代码"
        df.columns = ['股票名称', '总分', '仓位权重', '调整日期', '成本价格', '市值', '持仓数量']
        df["仓位权重"] = ["{:.4f}%".format(number * 100) for number in df["仓位权重"].values.tolist()]
        df.to_excel(export_root + "%s回测-%s.xlsx" % (operate_date, str(range)))
        print("已导出回测表格")

        if end_date != 0:
            end_price = w.wsd(codes=stock_codes, beginTime=end_date, endTime=end_date, fields="close", Period="D",
                              Days="ALLdays", Fill="Previous", zoneType=1, rptType=1, ruleType=2, gRateType=1,
                              returnType=1, unit=1, usedf=True)[1]
            prices = end_price["CLOSE"].values.tolist()
        self.end_position = (df["持仓数量"] * prices).sum()  # 回测结束日仓位
