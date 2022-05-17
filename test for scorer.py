from WindPy import w
from Wind_StockSelector_V2.Stock import Stock_pool, Stock
from Wind_StockSelector_V2.Selector import Filter, Scorer
import pandas as pd

w.start(waitTime=60)  # 启动API 默认命令超时时间为120秒，如需设置超时时间可以加入waitTime参数，例如waitTime=60,即设置命令超时时间为60秒

# 筛选条件
filter_procedure = [
]


# 评分条件
score_procedure = [

    #万德一致预测（指定年度）-预测净利润标准差
    {
        "fields":
            [
                {
                    "name": ["est_stdnetprofit"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {},
        "how": "descending",
        "period": "1Y",
        "weight": 0.15,
        "description": "万德一致预测 净利润标准差"
    },

    #万德一致预测（指定年度）-预测营业收入标准差
    {
        "fields":
            [
                {
                    "name": ["est_stdsales"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {},
        "how": "descending",
        "period": "1Y",
        "weight": 0.15,
        "description": "万德一致预测 营业收入标准差"
    },
    
    #ROE
    {
        "fields":
            [
                {
                    "name": ["roe"],
                    "params": {'growth_rate': True, 'mean': True,}
                }
            ],
        "fields_arithmetic": {},
        "how": "ascending",
        "period": "3Y",
        "weight": 0.15,
        "description": "ROE 3Y"
    },
    
    # 费用增速均值/营收增速均值 3Y
    {
        "fields":
            [
                {
                    "name": ["selling_dist_exp", "gerl_admin_exp", "fin_exp_is"],
                    "params": {'dfarithmetic': ['+', '+'], 'growth_rate': True, 'mean': True}
                },
                {
                    "name": ["oper_rev"],
                    "params": {'growth_rate': True, 'mean': True}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/']},
        "how": "descending",
        "period": "3Y",
        "weight": 0.1,
        "description": "费用增速均值/营收增速均值 3Y"
    },
    
    # FCF (PPT中的公式): 息前税后营业利润+折旧与摊销-资本支出 (购建固定资产、无形资产支付的现金)
    {
        "fields":
            [
                {
                    "name": ["noplat",'wgsd_dep_exp_of','cash_pay_acq_const_fiolta'],
                    "params": {'dfarithmetic': ['+', '-'], 'growth_rate': True, 'mean': True}
                }
            ],
        "fields_arithmetic": {},
        "how": "ascending",
        "period": "3Y",
        "weight": 0.1,
        "description": "FCF增速均值 3Y"
    },
    # PEG/净利润同比增速(wind一致预测)
    {
        "fields":
            [
                {
                    "name": ["peg"],
                    "params": {}
                },
                {
                    "name": ["est_yoynetprofit"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/']},
        "how": "descending",
        "period": "1Y",
        "weight": 0.35,
        "description": "PEG/净利润同比增速(wind一致预测) 1Y"
    },
    
    
    
]

# 实例化股票池
operate_date = "2022-05-16"
pool = Stock_pool()
pool.get_constituent(operate_date, "a001010100000000")  # 获取当年成分股

# 根据筛选条件进行筛选
filter = Filter(pool, operate_date)
filter.filter_procedure(filter_procedure)
filter.filter()

# 根据评分条件进行评分
scorer = Scorer(pool, operate_date)
scorer.score_procedure(score_procedure)
scorer.score()

# # 回测表格
# pool.traceback(scorer, operate_date, "anlysis/", 50)

# # 查看
# pd.set_option('display.max_columns', 1000)
# pd.set_option('display.max_rows', 1000)
# pd.set_option('display.width', 1000)
# pd.set_option('display.max_colwidth', 1000)
# check = 1
# while check ==1:
#     check = int(input("进行查看请按1，结束程序请按0"))
#     assert check == 1 or check == 0, "只能输入0或1"
#     if check == 0:
#         break

#     check_type = int(input("查看筛选各步骤概况请按1，查看评分各步骤概况请按2，查看特定个股筛选过程请按3"))
#     assert check_type == 1 or check_type == 2 or check_type == 3, "只能输入1或2或3"
#     if check_type == 1:
#         count = 0
#         for f in filter.look_into:
#             print("\n以下是筛选条件 %s 的相关内容" %filter_procedure[count]["description"])
#             for df in f["primary_df"]:
#                 print("原始数据：",df,"\n")
#             print("运算处理后的指标值：",f["processed_df"],"\n")
#             print("筛选结果：",f["result_df"],"\n")
#             print("结果简述：",f["result"],"\n")
#             count += 1
#     elif check_type == 2:
#         count = 0
#         for s in scorer.look_into:
#             print("\n以下是评分标准 %s 的相关内容" %score_procedure[count]["description"])
#             for df in s["primary_df"]:
#                 print("原始数据：",df,"\n")
#             print("运算处理后的指标值：",s["processed_df"],"\n")
#             print("评分结果：",s["result_df"],"\n")
#             count += 1
#     else:
#         stock_code = input("请输入要查看的股票代码，格式如XXXXXX.SZ或XXXXXX.SH")
#         primary_df, processed_df = Stock.get_stock(stock_code, filter)
#         print("\n各相关指标原始数据：", primary_df,"\n")
#         print("各评分标准中的运算处理后指标值：", processed_df)