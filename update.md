reminder: 

GetData.py
58 - 67 lines

```
# ! start this is for temporary debugging############

''' since the above function will detect the columns existing, 
therefore, non-admin user can not attend the table column,
we should add columns manually'''

# if column_names == []:
#     column_names = ['debttoassets','deductedprofit']
    
# ! end #########################################
```

need to delete once getting a database account for obtaining the columns in database.

20220425:
change the database account,but it does not work.

20220507:
update the database

2022 0512: 
update the database

est_stdnetprofit some problem with this kinds of data. therefore we need to handle with it again.


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


