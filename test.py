from Wind_StockSelector_V2.Stock import Stock_pool, Stock
from Wind_StockSelector_V2.Selector import Filter, Scorer
# w.start()
# w.menu()
# 实例化股票池
operate_date = "2017-05-01"
pool = Stock_pool()
pool.get_constituent(operate_date, "a001010100000000")  # 获取当年成分股
score_procedure = [
    {
        "fields":
            [
                {
                    "name": ["est_stdnetprofit"],
                    "params": {}
                }
            ],
        "fields_arithmetic": {},
        "how": "ascending",
        "period": "1Y",
        "weight": 0.15,
        "description": "净利润增速一致预期 1Y"
    },
]
# 根据评分条件进行评分
scorer = Scorer(pool, operate_date)
scorer.score_procedure(score_procedure)
scorer.score()