# 指标信息
确认：
1. 营业收入： 近三年（e.g: 18,19,20）复合增速
2. EBITDA：复合增速，并且每年EBITDA不允许有负值
3. 扣非净利润：复合增速，每年扣非净利润允许有负值


09-Mar
问题：
1. ROA中近三年有提升是指？比如18年 5%， 19年6% ，20年7% 这样？且每年的ROA
均大于5%对吗？

1.第3年比第1年高且大于5%即可。

2. 综合毛利率是指？就是毛利率对吧，然后时间刻度是最新期的毛利率要>15%，这样理解对吗？

2.理解是对的

3. 如何理解 “近三年” 的OCF增长率 “年均” 增速（算出来是一个数字，三年增速的均值） 不低于 “同期” 扣非增速50%（算出来是三个数字） ？ 


我的理解是近三年，每年的OCF增速 “均” 要不低于 当期扣非增速50%，
e.g：
17 OCF: 5%, 扣非50%： 12%*0.5；
18 OCF: 6%, 扣非50%： 14%*0.5；
19 OCF: 6%, 扣非50%： 17%*0.5；

3.您举例是对的，三年期间里，每年都满足。否则计算净利润增速就没有匹配同期现金流的质量了。

4. 费用资本化率
如何理解近三年累计开发支出 < 研发支出50%？如何把三年的累积值与某一年的值相比？对应的应该是会计的哪个科目？

4.可以直接把资产负债表里的开发支出的绝对金额相加，比上损益表里的研发支出绝对金额相加。

5. 评分指标中
如何理解使用wind一致预期的标准差进行评分？
我的理解是，win一致预期的标准差是指一致预期的标准差越小，市场对于该股的预期越集中，评分越高吗？

5.一致预期，是作为最后一期业绩纳入统计和计算peg，对wind一致预期不需要做计算。在评分的时候为了避免头尾差异过大，全部样本分数的标准差。

6. 特定条件中
跳转至第7项筛选评分是指？

6.满足特定条件即资产大规模增加的，不适用于从第1至第6项的筛选指标，从第7项毛利率开始。


# 更新日志

16-May

1. 评分指标中 的ROE的近三年ROE增长幅度是指？因为标准差至少需要3+的数据才能计算，但是如果仅仅是三年的数据来计算标注差的话，会出现很大的偏差和波动，这里给出两个建议，第一：按照三年ROE增长率的均值进行排序，第二：按照WIND一致预测的ROE预测的最新标准差进行排序


19-May:

1. 标识指标是做什么用的？
2. 经营性现金流净额OCF增长率，50%这个数值太过严格




2022 0516 :
1. debug for compound return

e.g:
{'stock_code': '603081.SH', 'date': datetime.date(2013, 12, 31), 'field': 'ebitda', 'value': None}

the returning data is "nan" from wind, we need transfer it into the None to be inserted into the Mysql database

2. shrink the database to 65 rows, see the constituents_all

3. change the date with "2022-05-16", the original date is "2017-05-01"

4. can not use the small size database because of stocks will be filtered all out.

5. the first step is to build the complete database for the whole 2022 0516 day data.

2022 0517：

1. compound growth rate error: all is inf
2. added a second version of writing mysql in GetData
3. pandas to sql can not insert the data if no such a column exists.
4. 增加了stock_code 和date作为primary key看看， failed
5. stockdata 中应该是date还是datetime？


2022 0518: 

1. add a verification on the column because the pandas can not append to the database if no such column exists.
2. change the new type of writing new columns to the database.
3. finished the database


2022 0519: 
1. change the datetime with date.
2. distinct the rows in the database.




# 数据库
ip: jacarandastock.com 
username: admin 
password: TFqt3qihVYei4qZz



ip: jacarandastock.com
Port: 3306
Username:jacaranda
Password: U9qJA32zpUEiwey8cECi

