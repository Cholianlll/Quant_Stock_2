'''
1.根据选股需要，从wind和本地SQL获取相关原生数据
2.进一步处理和计算原生数据以便筛选
3.筛选股票
'''

import pandas as pd
import numpy as np

###定义类：选股器Filter(),包含2个方法：理和计算数据，筛选
class Filter():

    filter_report = pd.DataFrame(columns=["筛选条件描述","原股票池股票数","筛除股票数","筛除百分比","剩余股票数"]) # 各次筛选的report汇总
    score_report = pd.DataFrame(columns=["总分"]) # 各次评分汇总

    dataframes = [] # 记录各次筛选的df和report

    def __init__(self,Stock_pool,description):
        self.Stock_pool = Stock_pool # 要筛选的股票池
        self.description = description # 筛选条件的描述
        self.report = {"筛选条件描述":description} #筛选结果
        print("正在筛选条件：%s" %self.description)

    ##方法：处理和计算数据
    def calculate(self,df_list,**kwargs):

        if "target_value" not in df_list.copy()[0].columns.values.tolist():
            self.primary_df = df_list.copy()  # 原生数据df'

        if len(df_list) > 1: #多个df：先做df四则运算
            index = 0
            document = "df_list[0]"
            for s in kwargs["dfarithmetic"]:
                document = document + s + "df_list[" + str(index + 1) + "]"
                index += 1
            calculate_df = eval(document)
        else:
            calculate_df = df_list[0].copy()

        for k in kwargs.keys():
            #取增速
            if k == "growth_rate" and kwargs["growth_rate"]:
                calculate_df = calculate_df.pct_change(axis=1)
            #取节点值
            if k == "point":
                calculate_df["target_value"] = calculate_df.iloc[:, kwargs["point"]].values.tolist()  # 拿出最近值
            #取均值
            if k == "mean" and kwargs["mean"]:
                calculate_df=calculate_df.iloc[:,1:]
                calculate_df["target_value"] = calculate_df.mean(axis=1).values.tolist()  # 均值df
            #常数四则运算
            if k == "arithmetic":
                calculate_df = eval("calculate_df%s" %kwargs["arithmetic"])
            #单调性
            if k == "monotonicity":
                calculate_df_diff = eval("calculate_df.diff(axis=1).iloc[:, 1:]%s" %kwargs["monotonicity"])
                calculate_df["target_value"] = calculate_df_diff.all(axis=1)
            #全部满足
            if k == "all":
                calculate_df["target_value"] = eval("%s.all(axis=1)" %kwargs["all"])

        self.processed_df = calculate_df.copy() # 经过处理计算过的dataframe
        self.processed_df.insert(0, "筛选条件", self.description)

        return calculate_df

    ##方法：筛选股票
    def filter(self,processed_df,signal,counterpart):
        
        filter_df = processed_df.copy() # copy处理过的表格进行筛选
        filter_df.insert(0,'description',self.description)  # 插入筛选条件描述列

        filter_df["threshold"] = signal+str(counterpart) # 记录判断条件threshold
        filter_df["isright"] = eval("filter_df['target_value']%s%s" % (signal, counterpart)) # 是否符合条件
        filter_df["ifnan"] = np.isnan(filter_df['target_value'])  # 是否为空值

        filter_df["reserve"] = filter_df["isright"] | filter_df["ifnan"] # 插入判断是否保留列
        filtered_df = eval("filter_df[(filter_df['target_value']%s%s) | (np.isnan(filter_df['target_value']))]" % (signal, counterpart))

        print(filter_df.iloc[:,[-5,-4,-1]])  # 打印股票的筛选情况
        self.Stock_pool.stock_codes = filtered_df.index.tolist()  # 最终筛选后得到的股票池代码列表
        self.filter_df = filter_df # 筛选情况df

        filtered_stock_codes = set(filter_df.index.values.tolist()) - set(self.Stock_pool.stock_codes) # 被筛选掉的股票代码
        print("此次筛选掉%s支股票" %len(filtered_stock_codes))
        print("筛选后的股票池中包含%s支股票\n" %len(self.Stock_pool.stock_codes))

        ##记录筛选结果
        print("正在记录此轮筛选结果")
        self.report["原股票池股票数"] = len(set(filter_df.index.values.tolist()))  # 原股票池股票数
        self.report["筛除股票数"] = len(filtered_stock_codes) # 筛除股票数
        self.report["筛除百分比"] = '%.3f' %(len(filtered_stock_codes)/len(set(filter_df.index.values.tolist()))) # 筛除百分比
        self.report["剩余股票数"] = len(self.Stock_pool.stock_codes)  # 剩余股票数
        Filter.filter_report = Filter.filter_report.append(self.report,ignore_index=True)
        ##记录各df和结果
        self.result = {"primary_df":self.primary_df,"processed_df":self.processed_df,"result_df": self.filter_df,"report":self.report}
        Filter.dataframes.append(self.result)

        ## 从股票池筛掉不符合条件的股票，并将筛选结果记录在Stock实例中
        print("正在修改股票池")
        for s in self.Stock_pool.pool[:]:
            if s.code in filtered_stock_codes:
                self.Stock_pool.pool.remove(s)
                s.status = "out of the pool"
            args = filter_df.loc[s.code,["description","target_value","threshold","reserve"]]
            s.filter_record(args[0],args[1],args[2],args[3],s.code) # 记录筛选结果

    ##方法：股票评分
    def score(self,processed_df,how="ascending",weight=None):

        #将指标数值标准化
        def standardization(data,how):
            mu = np.mean(data, axis=0)
            sigma = np.std(data, axis=0)
            if how == "ascending": # 数值越大分数越高
                return (data - mu) / sigma
            else:
                return (mu-data) / sigma
        def normalization(data):
            data = (data-np.min(data))/(np.max(data)-np.min(data))
            return data

        score_df = processed_df.copy()  # copy处理过的表格进行筛选
        score_df.insert(0,'description',self.description)  # 插入评分条件描述列

        score_df["score"] = standardization(score_df["target_value"],how)*100 # 标准化评分
        score_df["score"] = score_df["score"] * weight  # 根据权重赋分
        score_df["score"] = score_df["score"]

        print(score_df.iloc[:,[-5,-4,-1]]) # 打印评分情况
        self.score_df = score_df  # 评分情况df
        self.result = {"primary_df": self.primary_df, "processed_df": self.processed_df, "result_df": self.score_df}
        #记录各df和结果
        Filter.dataframes.append(self.result)
        Filter.score_report[self.description] = self.score_df["score"]
        Filter.score_report["总分"] = Filter.score_report.iloc[:, 2:].sum(axis=1)
        Filter.score_report["总分"] = normalization(Filter.score_report["总分"])