"""
1.根据选股需要，从wind和本地SQL获取相关原始数据
2.进一步处理和计算原始数据以便筛选
3.筛选股票
"""

import pandas as pd
import numpy as np
import datetime
from Wind_StockSelector_V2.GetData import StockData


# 定义生成获取数据的日期列表
def get_stock_data(field, stock_codes, operate_date, terms, span="Y", update=False):
    
    """
    Input params
    field: "name" in field
    
    """
    
    
    
    """
    根据条件，生成获取数据的日期列表

    :param stock_codes: 股票代码列表
    :param operate_date: 操作日期
    :param terms: 期数
    :param span: 期间跨度
    :param field: 指标名
    :return: 原始数据
    """
    # 获得数据的日期列表
    primary_date = datetime.datetime.strptime(operate_date, "%Y-%m-%d").date()  # 操作时间
    dates = []  # 日期列表
    for term in range(terms):
        if span == "Y":  # 按年获取数据，时间点为从去年开始的xxxx-12-31
            dates.append(primary_date.replace(primary_date.year - terms + term, 12, 31))
        elif span == "Q":  # 按季度获取数据，时间点为从上季度开始的xxxx-xx-最后一天
            quarter = (primary_date.month - 1) // 3 + 1
            if quarter == 1:
                dates.append(datetime.date(primary_date.year - 1, 12, 31))  # 去年四季度
            elif quarter == 2:
                dates.append(datetime.date(primary_date.year, 3, 31))  # 今年一季度
            elif quarter == 3:
                dates.append(datetime.date(primary_date.year, 6, 30))  # 今年二季度
            else:
                dates.append(datetime.date(primary_date.year, 9, 30))  # 今年三季度
    dates.sort()

    # 从本地SQL获取数据
    get_data = StockData(update=update)  # 实例化数据获取器
    get_data.data_from_SQL(stock_codes, dates, field)  # 先从本地SQL数据库获取数据
    # 如果本地SQL数据不足，再从Wind请求数据
    if get_data.blank_list:
        get_data.data_from_Wind()  # 从Wind请求数据
        get_data.data_to_SQL()  # 将数据保存在SQL中
        # 再次初始化数据获取器，并从SQL中获取数据
        get_data = StockData(update=False)  # 初始化数据获取器
        get_data.data_from_SQL(stock_codes, dates, field)  # 从SQL中获取数据
        
    return get_data.SQL_data # SQLdataframe

'''
Sample SQL_data:

# Sample data for self.SQL_data:
# self.SQL_data.index = stock_codes
# self.SQL_data.index.name = field
# self.SQL_date.columns = dates

nXd 的一个dataframe, with each row represents the each share, each columns shows each period term.
'''



### 定义计算处理数据的函数
def calculate(df_list, description, **kwargs):
    
    '''
    input sample:
    df_list: 
        
    a list of dataframes:
        [df_1, df_2, df_3]
        with each df inside of the list:
            n X d dataframe, withe index = share code, columns = date, index.name = 'ebitda'
    
    description: 'EBITDA 增速均值 > 10% 3Y'
    
    **kwargs: 
    "params": {'growth_rate': True, 
               'mean': True}
    '''
    
    if len(df_list) > 1:  # 多个df：先做df四则运算
        index = 0
        document = "df_list[0]"
        for s in kwargs["dfarithmetic"]:
            # "params": {'dfarithmetic': ['/'], 'point': -1}
            document = document + s + "df_list[" + str(index + 1) + "]"
            index += 1
        calculate_df = eval(document)
    else:
        calculate_df = df_list[0].copy()

    for k in kwargs.keys():
        # 取增速
        if k == "growth_rate" and kwargs["growth_rate"]:
            # calculate_df
            """
            col1: data in 2015
            col2: data in 2016
            col3: data in 2017
            """
            calculate_df = calculate_df.pct_change(axis=1)
            
            # calculate_df
            """
            col1: Nan
            col2: 2016/2015 - 1
            col3: 2017/2016 - 1
            """
            
            calculate_df = calculate_df.iloc[:, 1:]
        
        # 取节点值
        if k == "point":
        # "params": {"point": -1}
            calculate_df["target_value"] = calculate_df.iloc[:, kwargs["point"]].values.tolist()  # 拿出最近值
        # 取均值
        if k == "mean" and kwargs["mean"]:
            # calculate_df = calculate_df.iloc[:, 1:]
            calculate_df["target_value"] = calculate_df.mean(axis=1).values.tolist()  # 均值df
        # 常数四则运算
        if k == "arithmetic":
        # input: kwargs["arithmetic"] == '*2'
            calculate_df = eval("calculate_df%s" % kwargs["arithmetic"])
        # 单调性
        if k == "monotonicity":
        # input: kwargs["monotonicity"] == '>0' 
            calculate_df_diff = eval("calculate_df.diff(axis=1).iloc[:, 1:]%s" % kwargs["monotonicity"])
            calculate_df["target_value"] = calculate_df_diff.all(axis=1)
        # 全部满足
        if k == "all":
        # input: kwargs["all"] = '(calculate_df>0)'
            calculate_df["target_value"] = eval("%s.all(axis=1)" % kwargs["all"])
        # 计数
        if k == "count":
        # input 'count': "(calculate_df<0)"
            calculate_df["target_value"] = eval("%s.sum(axis=1)" % kwargs["count"])
        # 忽略最早一期数据
        if k == "omit_first":
            calculate_df = calculate_df.iloc[:, 1:]
        # lambda 行函数
        if k == 'function':
            # "function" : lambda x: x * 1.05
            calculate_df = calculate_df.apply(kwargs["function"], axis = 1)
        # 自定义操作
        if k == 'self_define':
        # "self_define" : 'calculate_df.iloc[:,-1] - calculate_df.iloc[:,-3] * 1.05'
            calculate_df['target_value'] = eval(kwargs["self_define"])
            
        # 取复合增速  
        if k == 'compound_growth_rate' and kwargs["compound_growth_rate"] : 
        # input: kwargs["compound_growth_rate"] = True
        
            # drop the first columns since the calculate_df will return term+1 data, 
            calculate_df = calculate_df.iloc[:,1:]

            # -1: calculate the count of year, give three columns, there are only two years.
            cols = calculate_df.shape[1]-1
            # calculate the compound growth rate
            calculate_df["target_value"] = (calculate_df.iloc[:, -1] / calculate_df.iloc[:, 1]).apply(lambda x: np.power(x,1/cols)-1)
            

    processed_df = calculate_df.copy()  # 经过处理计算过的dataframe

    return processed_df


###定义类：选股器Filter(),包含2个方法：理和计算数据，筛选
class Filter:

    def __init__(self, stock_pool, operate_date):
        self.stock_pool = stock_pool  # 要筛选的股票池
        self.operate_date = operate_date  # 操作日期

        self.filter_report = pd.DataFrame(columns=["筛选条件描述", "原股票池股票数", "筛除股票数", "筛除百分比", "剩余股票数"])  # 各次筛选的report汇总
        self.look_into = []

    ## 方法：录入筛选条件
    def filter_procedure(self, procedure):
        self.procedure = procedure

    ##方法：筛选股票
    def filter(self):

        for procedure in self.procedure:

            fields = procedure["fields"]
            description = procedure["description"]  # 筛选条件描述
            fields_kwargs = procedure["fields_arithmetic"]  # 指标间运算参数
            sgn = procedure["sgn"]  # 数学符号
            period = procedure["period"]  # 时期
            threshold = procedure["threshold"]  # 阈值

            ## 获取原始数据
            primary_dfs = []
            span = period[-1]  # 跨度, e.g: '3Y' -> 'Y': span = 'Y"
            terms = int(period.split(span)[0]) + 1  # 期数 , e.g "3Y"-> terms = 4
            field_list = []  # 子变量列表
            for field in fields:
                df_list = []  # 子变量的基础变量列表
                for name in field["name"]:  # 基础变量
                    primary_df = get_stock_data(name, self.stock_pool.stock_codes, self.operate_date, terms,
                                                span)  # 获取所需的数据
                    df_list.append(primary_df)
                    primary_dfs.append(primary_df)  # 记录原始数据
                field_list.append(df_list)

            ## 计算和处理原始数据
            # 对各指标df-转换方法元组进行转换
            field_processed_dfs = []  # 存放各个被处理过的指标列表生成的df
            # 基础变量→子变量
            for df_list, field in zip(field_list, fields):
                field_processed_dfs.append(calculate(df_list, description, **field["params"]))
            # 合并子变量
            if fields_kwargs != {}:  # 有多个子变量
                processed_df = calculate(field_processed_dfs, description, **fields_kwargs)
                processed_df.index.name = description
            else:  # 仅有一个子变量
                processed_df = field_processed_dfs[0]
                processed_df.index.name = description

            ## 筛选
            print("正在筛选条件：%s" % description)
            filter_df = processed_df.copy()  # copy处理过的表格进行筛选
            filter_df.insert(0, 'description', description)  # 插入筛选条件描述列

            filter_df["threshold"] = sgn + str(threshold)  # 记录判断条件threshold
            filter_df["isright"] = eval("filter_df['target_value']%s%s" % (sgn, threshold))  # 是否符合条件
            filter_df["ifnan"] = np.isnan(filter_df['target_value'])  # 是否为空值

            filter_df["reserve"] = filter_df["isright"] | filter_df["ifnan"]  # 插入判断是否保留列
            filtered_df = eval(
                "filter_df[(filter_df['target_value']%s%s) | (np.isnan(filter_df['target_value']))]" % (sgn, threshold))

            print(filter_df.iloc[:, [-5, -4, -1]])  # 打印股票的筛选情况
            self.stock_pool.stock_codes = filtered_df.index.tolist()  # 最终筛选后得到的股票池代码列表
            self.filter_df = filter_df  # 筛选情况df

            ## 记录筛选结果
            filtered_stock_codes = set(filter_df.index.values.tolist()) - set(self.stock_pool.stock_codes)  # 被筛选掉的股票代码
            print("此次筛选掉%s支股票" % len(filtered_stock_codes))
            print("筛选后的股票池中包含%s支股票\n" % len(self.stock_pool.stock_codes))
            dict = {"筛选条件描述": description}  # 筛选结果字典
            dict["原股票池股票数"] = len(set(filter_df.index.values.tolist()))  # 原股票池股票数
            dict["筛除股票数"] = len(filtered_stock_codes)  # 筛除股票数
            dict["筛除百分比"] = '%.3f' % (len(filtered_stock_codes) / len(set(filter_df.index.values.tolist())))  # 筛除百分比
            dict["剩余股票数"] = len(self.stock_pool.stock_codes)  # 剩余股票数
            self.filter_report = self.filter_report.append(dict, ignore_index=True)

            # 记录各dataframe和筛选结果，便于查看筛选各过程
            detail = {
                "primary_df": primary_dfs,
                "processed_df": processed_df,
                "result_df": filter_df,
                "result": pd.DataFrame(dict, index=[0])
            }
            self.look_into.append(detail)

            ## 从股票池筛掉不符合条件的股票，并将筛选结果记录在Stock实例中
            print("正在修改股票池")
            for s in self.stock_pool.pool[:]:
                if s.code in filtered_stock_codes:
                    self.stock_pool.pool.remove(s)
                    s.status = "out of the pool"
                args = filter_df.loc[s.code, ["description", "target_value", "threshold", "reserve"]]
                s.filter_record(args[0], args[1], args[2], args[3], s.code)  # 记录个股的筛选结果


class Scorer:

    def __init__(self, stock_pool, operate_date):
        self.stock_pool = stock_pool  # 要筛选的股票池
        self.operate_date = operate_date  # 操作日期
        self.score_report = pd.DataFrame(columns=["总分"])  # 各次评分汇总
        self.look_into = []

    # 方法：录入评分条件
    def score_procedure(self, procedure):
        self.procedure = procedure

    # 方法：评分
    def score(self):
        # 定义标准化/归一化函数
        def standardization(data, how):
            mu = np.mean(data, axis=0)
            sigma = np.std(data, axis=0)
            if how == "ascending":  # 数值越大分数越高
                return (data - mu) / sigma
            else:
                return (mu - data) / sigma

        def normalization(data):
            data = (data - np.min(data)) / (np.max(data) - np.min(data))
            return data

        for procedure in self.procedure:

            #  导入条件
            fields = procedure["fields"]  # 变量
            description = procedure["description"]  # 评分条件描述
            fields_kwargs = procedure["fields_arithmetic"]  # 指标间运算参数
            how = procedure["how"]  # 取优方向
            period = procedure["period"]  # 时期
            weight = procedure["weight"]  # 评分权重

            # 获取原始数据
            primary_dfs = []  # 原始数据列表
            span = period[-1]  # 跨度
            terms = int(period.split(span)[0]) + 1  # 期数
            field_list = []  # 子变量列表
            for field in fields:
                df_list = []  # 子变量的基础变量列表
                for name in field["name"]:
                    primary_df = get_stock_data(name, self.stock_pool.stock_codes, self.operate_date, terms, span)
                    df_list.append(primary_df)
                    primary_dfs.append(primary_df)
                field_list.append(df_list)

            # 计算和处理原始数据
            # 对各指标df-转换方法元组进行转换
            field_processed_dfs = []  # 存放各个被处理过的指标列表生成的df
            for df_list, field in zip(field_list, fields):
                field_processed_dfs.append(calculate(df_list, description, **field["params"]))
            # 对所有整理后指标df进行合并整理
            if fields_kwargs != {}:
                processed_df = calculate(field_processed_dfs, description, **fields_kwargs)
            else:
                processed_df = field_processed_dfs[0]
                processed_df.index.name = description

            # 评分
            score_df = processed_df.copy()
            score_df.insert(0, 'description', description)  # 插入评分条件描述列
            score_df["score"] = standardization(score_df["target_value"], how) * 100  # 标准化评分
            score_df["score"] = normalization(score_df["score"]) * 100
            score_df["score"] = score_df["score"] * weight  # 根据权重赋分

            print(score_df.iloc[:, [-5, -4, -1]])  # 打印评分情况
            detail = {
                "primary_df": primary_dfs,
                "processed_df": processed_df,
                "result_df": score_df
            }
            self.look_into.append(detail)

            # 加总得到总分，记录结果
            self.score_report[description] = score_df["score"]
            self.score_report["总分"] = self.score_report.iloc[:, 2:].sum(axis=1)

        self.score_report = self.score_report.sort_values(by="总分", ascending=False)  # 按分数降序排序
        # 记录股票名称
        stock_names = [self.stock_pool.constituens.get(code) for code in self.score_report.index.values.tolist()]
        self.score_report.insert(0, "stock_name", stock_names)
        # 按评分计算仓位权重
        self.score_report.insert(2, "仓位权重", [score / self.score_report["总分"].sum() for score in
                                             self.score_report["总分"].values.tolist()])
        self.score_report.index.name = ""
        print(self.score_report)
        self.score_report.to_excel("%s评分.xlsx" % self.operate_date)
