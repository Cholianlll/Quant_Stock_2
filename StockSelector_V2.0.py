"""
Author: 魏园村等团队

20220308 - V2.0 修改
Author 1: Cholian
cholianli970518@gmail.com

Author 1: Russell
????


选股器主程序
利用wind数据库选股，考察上市公司基本情况，盈利能力，财务质量，估值和重大事项几个方面，筛选符合条件的股票

设定筛选条件和评分标准
运行程序前检查三个参数：调仓日期，初始股票板块，Excel表格输出路径


requried database: 

database name: Wind
mysql database structure

Wind
-stockdata
    --stock_code varchar(64)
    --date  datetime? date?
-pg_tables
    --tablename  varchar(255)
-constituents
    --sectorid varchar(20)
    --date date
    --stock_code varchar(9)
    --stock_name varchar(16)
    
    
Query:
create database Wind;

create table stockdata(
    stock_code varchar(64) not null,
    date date not null,
    primary key (stock_code,date)
);

create table stockdata(
    sectorid  varchar(20) not null,
    date date not null,
    primary key (stock_code,date)
);
    
    
database account privilege: needed to be administrator
"""

from WindPy import w
from Wind_StockSelector_V2.Stock import Stock_pool, Stock
from Wind_StockSelector_V2.Selector import Filter, Scorer
import pandas as pd

w.start(waitTime=60)  # 启动API 默认命令超时时间为120秒，如需设置超时时间可以加入waitTime参数，例如waitTime=60,即设置命令超时时间为60秒

# 筛选条件
filter_procedure = [
    
    # 资产负债率 + 特定条件
    {
        "fields":
            [
                {
                    "name": ["debttoassets"],
                    "params": {'arithmetic': '<60'}
                },
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30'}
                },
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20'}
                },
            ],
        "fields_arithmetic": {'dfarithmetic': [' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": True,
        "period": "1Y",
        "description": "负债率 <60% 1Y (资产大规模增长除外)"
    },
    
    # 营业收入 + 特定条件
    {
        "fields":
            [
                {
                    "name": ["oper_rev"],
                    "params": {"compound_growth_rate" : True, 'arithmetic': '> 0.15'}
                },
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30', 'point': -1}
                },
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20','point': -1}
                },
            ],
        "fields_arithmetic": {'dfarithmetic': [' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "营业收入 复合增速 > 15% 3Y (资产大规模增长除外)"
    },

    # EBITDA + 特定条件
    {
        "fields":
            [
                {
                    "name": ["ebitda"],
                    "params": {"all": "(calculate_df>0)"}
                },
                {
                    "name": ["ebitda"],
                    "params": {'compound_growth_rate': True, 'arithmetic': '>0.1'}
                },
                # 资产大规模增长
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30', 'point': -1}
                },
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20','point': -1}
                },                
                
            ],
        "fields_arithmetic": {'dfarithmetic': [' & ', ' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "EBITDA 三年非负，复合增速 > 10% 3Y (资产大规模增长除外)"
    },
    

    
    # 扣非净利润 + 特定条件
    {
        "fields":
            [
                {
                    "name": ["deductedprofit"],
                    "params": {"compound_growth_rate" : True,'arithmetic': '> 0.1'}
                },
                # 资产同比增长率 > 30%
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30', 'point': -1}
                },
                # 净资产同比增长率 > 20%
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20','point': -1}
                },
            ],
        "fields_arithmetic": {'dfarithmetic': [' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "扣非净利润 复合增速 > 10% 3Y (资产大规模增长除外)"
    },
    
    # ROA + 特定条件
    {
        "fields":
            [
                # 第一年 ROA
                {
                    "name": ["roa"],
                    "params": {"arithmetic" : ' > (calculate_df.iloc[:,-3] * 1.05)', 'point': -1}
                },
                # 资产同比增长率 > 30%
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30', 'point': -1}
                },
                # 净资产同比增长率 > 20%
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20','point': -1}
                },                
            ],
        "fields_arithmetic": {'dfarithmetic': [' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "ROA 三年有提升 3Y (资产大规模增长除外)"
    },
    
    # 总资产周转率+净利率
    {
        "fields":
            [
                {
                    # 总资产周转率
                    "name": ["assetsturn1"],
                    "params": {'monotonicity': ">0"} 
                },
                {
                    # 总资产净利率
                    "name": ["roa"],
                    "params": {'monotonicity': ">0"}
                },
                {
                    "name": ["yoy_assets"],
                    "params": {'arithmetic': '>30', 'point': -1}
                },
                {
                    "name": ["yoy_equity"],
                    "params": {'arithmetic': '>20','point': -1}
                },
            ],
        "fields_arithmetic": {'dfarithmetic': [' | ', ' | ', ' & '], 'point': -1},
        "sgn": "==",
        "threshold": 1,
        "period": "3Y",
        "description": "总资产周转率和净利率无同时下滑 3Y"
    },  
    
    # 毛利率
    {
        "fields":
            [
                {
                    "name": ["grossprofitmargin"],
                    "params": {"growth_rate" : True, 'point':-1}
                }
            ],
        "fields_arithmetic": {},
        "sgn": ">",
        "threshold": 0.15,
        "period": "1Y",
        "description": "毛利率 最新一期增速 > 15% 1Y"
    },    
    # 应收帐款+应收票据增速/净利润增速
    {
        "fields":
            [
                {
                    "name": ["acct_rcv", "notes_rcv"],
                    "params": {'dfarithmetic': ['+'], 'growth_rate': True, 'mean': True}
                },
                {
                    "name": ["net_profit_is"],
                    "params": {"point": -1} # 拿出最新值
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/']},
        "sgn": "<",
        "threshold": 0.667,
        "period": "3Y",
        "description": "(应收帐款 + 应收票据)3Y年均增速 < 净利润增速"
    },
    # OCF增长率
    {
        "fields":
            [
                {
                    "name": ["net_cash_flows_oper_act"],
                    "params": {'growth_rate': True}
                },
                {
                    "name": ["grossprofitmargin"],
                    "params": {'growth_rate': True} 
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/'], 'all':'(calculate_df > 0.5)'},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "经营性现金流增速 > 50%扣非净利润增速 3Y"
    },
    # 每股净现金流
    {
        "fields":
            [
                {
                    # 每股现金流净额
                    "name": ["cfps"],
                    "params": {"all" : "(calculate_df > 0)"}
                }
            ],
        "fields_arithmetic": {},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "扣非净利润 复合增速 > 15% 3Y"
    },    
    # 研发支出占比
    {
        "fields":
            [
                {
                    "name": ["stmnote_rdexp_capital"],
                    "params": {}
                },
                {
                    "name": ["oper_rev"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/'], 'all': "(calculate_df > 0.08)"},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "资本化研发支出/营业收入 > 8% 3Y"
    },
    # 研发支出占比
    {
        "fields":
            [
                {
                    "name": ["stmnote_rdexp_capital"],
                    "params": {}
                },
                {
                    "name": ["oper_rev"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/'], 'all': "(calculate_df < 0.15)"},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "资本化研发支出/营业收入 < 15% 3Y"
    },
    # 审计意见
    {
        "fields":
            [
                {
                    "name": ["stmnote_audit_category"],
                    "params": {"all": "((calculate_df=='标准无保留意见')|(calculate_df=='带强调事项段的无保留意见'))"}
                }
            ],
        "fields_arithmetic": {},
        "sgn": "==",
        "threshold": True,
        "period": "3Y",
        "description": "审计意见 全部无保留 3Y"
    },
    # 应收帐款+票据 与 营收增速
    {
        "fields":
            [
                {
                    "name": ["acct_rcv", "notes_rcv"],
                    "params": {'dfarithmetic': ['+'], 'growth_rate': True, 'mean': True}
                },
                {
                    "name": ["oper_rev"],
                    "params": {'growth_rate': True, 'mean': True}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['/']},
        "sgn": "<",
        "threshold": 1.5,
        "period": "3Y",
        "description": "(应收账款+应收票据) 增速均值 < 营收1.5倍 增速均值 3Y"
    },   
    # 商誉 
    {
        "fields":
            [
                {
                    "name": ["goodwill", "tot_equity"],
                    "params": {'dfarithmetic': ['/'], 'point': -1}
                }
            ],
        "fields_arithmetic": {},
        "sgn": "<",
        "threshold": 0.3,
        "period": "1Y",
        "description": "商誉/净资产 近一年值 <30% 1Y"
    },
    # PEG and PB
    {
        "fields":
            [
                {
                    # PE
                    "name": ["pe", "net_profit_is"],
                    "params": {'dfarithmetic': ['/'], 'growth_rate': True, 'point': -1, 'all': "(calculate_df < 2.5)"}
                },
                {
                    # PB
                    "name": ["pb"],
                    "params": {'point': -1, 'all': "(calculate_df < 15)"}
                }
            ],
        "fields_arithmetic": {'dfarithmetic': ['*']},
        "sgn": "==",
        "threshold": True,
        "period": "1Y",
        "description": "PE/净利润<2.5 and PB < 15 1Y"
    }    
]


# 评分条件
score_procedure = [

    #万德一致预测（指定年度）-预测净利润标准差
    {
        "fields":
            [
                {
                    "name": ["est_stdnetprofit"],
                    "params": {'point': -1}
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
# operate_date = "2017-05-01"
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

# 回测表格
pool.traceback(scorer, operate_date, "anlysis/", 50)

# 查看
pd.set_option('display.max_columns', 1000)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 1000)
check = 1
while check ==1:
    check = int(input("进行查看请按1，结束程序请按0"))
    assert check == 1 or check == 0, "只能输入0或1"
    if check == 0:
        break

    check_type = int(input("查看筛选各步骤概况请按1，查看评分各步骤概况请按2，查看特定个股筛选过程请按3"))
    assert check_type == 1 or check_type == 2 or check_type == 3, "只能输入1或2或3"
    if check_type == 1:
        count = 0
        for f in filter.look_into:
            print("\n以下是筛选条件 %s 的相关内容" %filter_procedure[count]["description"])
            for df in f["primary_df"]:
                print("原始数据：",df,"\n")
            print("运算处理后的指标值：",f["processed_df"],"\n")
            print("筛选结果：",f["result_df"],"\n")
            print("结果简述：",f["result"],"\n")
            count += 1
    elif check_type == 2:
        count = 0
        for s in scorer.look_into:
            print("\n以下是评分标准 %s 的相关内容" %score_procedure[count]["description"])
            for df in s["primary_df"]:
                print("原始数据：",df,"\n")
            print("运算处理后的指标值：",s["processed_df"],"\n")
            print("评分结果：",s["result_df"],"\n")
            count += 1
    else:
        stock_code = input("请输入要查看的股票代码，格式如XXXXXX.SZ或XXXXXX.SH")
        primary_df, processed_df = Stock.get_stock(stock_code, filter)
        print("\n各相关指标原始数据：", primary_df,"\n")
        print("各评分标准中的运算处理后指标值：", processed_df)