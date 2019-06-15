# In[1]:
from crawler.NaverCrawler import NaverCrawler
from crawler.NaverWorldCrawler import NaverWorldCrawler
from crawler.NaverTopMarketCapCrawler import NaverTopMarketCapCrawler
from crawler.NaverCapFromCodeCrawler import NaverCapFromCodeCrawler
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.data.NaverDate import NaverDate
from crawler.data.NaverResultData import NaverResultData

import pandas as pd
from functools import reduce
import datetime as dt
import numpy as np
from sklearn.linear_model import LinearRegression

# In[2]: font 설정
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

path = '/Library/Fonts/NanumBarunGothicLight.otf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
mpl.rc('font', family=font_name) 

def topK(num):
    crawler = NaverTopMarketCapCrawler.create()
    data = crawler.crawling([1,num])
    codes = [ {'code':item.code, 'name':item.name}  for item in data ]
    return codes

# In[9]: 1년동안 시뮬레이션 
# In[10]: 날짜 설정
startDate = pd.to_datetime('2018-06-01', format='%Y-%m-%d')
endDate = pd.to_datetime('2019-06-01', format='%Y-%m-%d')

before = startDate + pd.Timedelta(-1, unit='Y')
end = endDate

beforeStr = before.strftime(format='%Y-%m-%d')
endStr = end.strftime(format='%Y-%m-%d')

# In[11]: 데이터수집
prices = dict()
#30종목 + KODEX 인버스
targets = topK(30) + [{'code':"114800", 'name':'KODEX 인버스'}]
date = NaverDate.create(startDate=beforeStr, endDate=endStr)
for target in targets:
    print(target,'collect...')
    crawler = NaverStockCrawler.create(target['code'])
    data = crawler.crawling(date)
    prices[target['name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
topdf = pd.DataFrame(prices)

# In[12]: 평균
monthly_topdf = topdf.resample('M').mean()
monthly_topdf

# In[13]: 시작날 부터 모멘텀 구하기
money = 10000000
print('startMoney: ', money)
stockWallet = pd.DataFrame()
moneyWallet = pd.DataFrame()
current = startDate

def buy(rate, date, valuedf, money, wallet):
    rateMoney = rate * money
    stockValue = valuedf.iloc[valuedf.index.get_loc(date, method='nearest')][rateMoney.index]
    for col in rateMoney.index:
        rMoney = rateMoney[col]
        sValue = stockValue[col]

        while rMoney - sValue> 0:
            if col in wallet.columns:
                wallet[col][date] = wallet[col][date]+1
            else:
                dt = pd.DataFrame([{col: 1}], index=[date])
                wallet = pd.concat([wallet, dt], axis=1)
            money -= sValue
            rMoney -= sValue
    return money, wallet

beforeOneYear = startDate + pd.Timedelta(-1, unit='Y')
start = monthly_topdf.index.get_loc(beforeOneYear, method='nearest')
end = monthly_topdf.index.get_loc(current, method='nearest')
oneYearDf = monthly_topdf.iloc[start:end]
momentum = oneYearDf.iloc[-1] - oneYearDf
momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
sortedValues = momentumScore.mean().sort_values(ascending=False)
share = sortedValues.head(5)
rate = share / share.sum()
money, stockWallet = buy(rate, current, topdf, money, stockWallet)

beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][share.index]

current = startDate + pd.Timedelta(1, unit='M')
stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][share.index]
#구매
stockValue / beforeValue 
# print(money)
# wallet

# wallet[current] = rateMoney
# print(wallet)
# stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][stock.index]
# stockValue




# beforeOneMonth = current
# current = startDate + pd.Timedelta(1, unit='M')
# currentStock = topdf.iloc[topdf.index.get_loc(current, method='nearest')][stock.index]
# stock[beforeOneMonth] * (currentStock / beforeStock)


# stock + rateMoney
# prices[target['name']]
# money 




# topdfMomentum = monthly_topdf.iloc[-1] - monthly_topdf
# topdfMomentumScore = topdfMomentum.applymap(lambda val: 1 if val > 0 else 0 )
# sortedValues = topdfMomentumScore.mean().sort_values(ascending=False)
# share = sortedValues.head(5)
# share / share.sum()

#%%
