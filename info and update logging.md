# 指标日志

1. 资产负债率

筛选掉963
剩余3844

2. 营业收入
筛选掉2209
剩余1635

3. EBITDA 
筛选335
剩余1280

4. 扣非净利润
筛选72
剩余1208

5. ROA 
筛选148
剩余1060

6. 总资产周转率
筛选180
剩余880

7. 毛利率
筛掉12
剩余868

8. 应收账款
筛掉221
剩余647

9. ocf
筛掉258
剩余389

10. 自由现金流 （删去）

11. 费用化研发支出 删除

12. 资本化研发支出占比
筛选69
剩余320

13. 审计意见
筛选2
剩余318

14. 应收账款比营收 
删掉 

15. 商誉

筛选3 
剩余315

16. peg
筛选111
剩余204



# 指标修改

第六项

1. 资产负债率

筛选掉963
剩余3844

2. 营业收入
筛选掉2209
剩余1635

3. EBITDA 
筛选335
剩余1280

4. 扣非净利润
筛选72
剩余1208

5. ROA (改)
！！
近三年均高于5% 且第三年高于第一年
筛选152
剩余1056

6. 总资产周转率
筛选174
剩余882

7. 毛利率 （改）
！！
近三年每年毛利率均高于15%
筛掉754
剩余128

8. 应收账款
筛掉15
剩余113

9. ocf （改）
！！经营性现金流的复合增速大于净利润的复合增速

筛掉89
剩余24

10. 自由现金流 （删去）
筛掉24
剩余0

11. 研发支出占比 （改）
改成费用化研发支出

12. 费用资本化率
开发支出占营收15%删去

改成费用资本化率>50% 

13. 审计意见

14. 应收账款比营收 
删掉 

15. 商誉
正常
16. peg
正常

评分指标：
1. 改为最新期净利润指标
2. 营业收入改为最新其
3. ROE
改为 三年复合增长率
4. 改为fcff 万得的
5. peg改成和16 同样的计算方式 


23，24 保留， 25 删除


特定条件






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
## 阿里云数据库（最低配）

链接
https://rdsbuy.console.aliyun.com/create/rds/mysql

配置
包年包月 - 1年
节点：上海
系列：基础版
实例规格： 1核1G
存储空间： 50GB
价格： 675 元/年

![YWGb2k](https://raw.githubusercontent.com/Cholianlll/Upic_repo/main/uPic/YWGb2k.png?token=ANDW5GWMRT2W7LG65SYVYW3CTJ7NO)



