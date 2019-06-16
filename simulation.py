# In[1]:
from crawler.NaverCrawler import NaverCrawler
from crawler.NaverWorldCrawler import NaverWorldCrawler
from crawler.NaverTopMarketCapCrawler import NaverTopMarketCapCrawler
from crawler.NaverCapFromCodeCrawler import NaverCapFromCodeCrawler
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.NavarSearchCodeCrawler import NavarSearchCodeCrawler

from crawler.data.NaverDate import NaverDate
from crawler.data.NaverResultData import NaverResultData

import pandas as pd
from functools import reduce
import datetime as dt
import numpy as np
from sklearn.linear_model import LinearRegression
from IPython.display import display

# In[2]: font 설정
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

path = '/Library/Fonts/NanumBarunGothicLight.otf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
mpl.rc('font', family=font_name) 

# In[3]: 함수
def topK(num):
    crawler = NaverTopMarketCapCrawler.create()
    data = crawler.crawling([1,num])
    codes = [ {'code':item.code, 'name':item.name}  for item in data ]
    return codes

def printPd(name,target):
    if type(target) is pd.DataFrame:
        display(name)
        display(target)
    else:
        print(name)
        print(target)

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

crawler = NavarSearchCodeCrawler.create('KODEX')
targets = crawler.crawling()
# targets = topK(100)
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
investShareNum = 10
momentumMonth = 12
rebalaceRate = 0.25
print('startMoney: ', money)
stockWallet = pd.DataFrame()
moneyWallet = pd.DataFrame()
moneySum = pd.DataFrame()
current = startDate

def buy(rate, buyDate, valuedf, money, wallet):
    rateMoney = rate * money
    stockValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][rateMoney.index]
    rowdf = pd.DataFrame(data=[[0]*len(rateMoney.index)], index=[buyDate], columns=rateMoney.index)
    wallet = pd.concat([wallet, rowdf])
    for col in rateMoney.index:
        rMoney = rateMoney[col]
        sValue = stockValue[col]
        while rMoney - sValue> 0:
            if col in wallet.columns and buyDate in wallet.index:
                wallet[col][buyDate] = wallet[col][buyDate]+1
            elif col in wallet.columns :
                dt = pd.DataFrame([{col: 1}], index=[buyDate])
                wallet = pd.concat([wallet, dt], axis=0)
            else:
                dt = pd.DataFrame([{col: 1}], index=[buyDate])
                wallet = pd.concat([wallet, dt], axis=1)
            money -= sValue
            rMoney -= sValue
    return money, wallet

while endDate > current:
    print('simulate...', current)
    #money 전체 가치
    #stockMoney 주식에 투자할 가치
    #restMoney 잔금
    stockMoney = money * (1-rebalaceRate)
    restMoney = money * rebalaceRate
    
    beforeMomentumDate = current + pd.Timedelta(-momentumMonth, unit='M')
    start = monthly_topdf.index.get_loc(beforeMomentumDate, method='nearest')
    end = monthly_topdf.index.get_loc(current, method='nearest')
    oneYearDf = monthly_topdf.iloc[start:end+1]
    momentum = oneYearDf.iloc[-1] - oneYearDf
    momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
    sortedValues = momentumScore.mean().sort_values(ascending=False)
    share = sortedValues.head(investShareNum)
    rate = share / share.sum()
    print('beforeBuy',money)
    stockRestMoney, stockWallet = buy(rate, current, topdf, stockMoney, stockWallet)
   
    beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][share.index]

    buyMoney = pd.DataFrame([(stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=stockWallet.columns)
    moneyWallet = pd.concat([moneyWallet, buyMoney])
   
    current = current + pd.Timedelta(1, unit='M')
    stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][share.index]
    
    #구매
    # print(money)
    # printPd('##현재자산가치', (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum() + money)
    stockMoney = (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum()
    restMoney = stockRestMoney + restMoney
    moneydf = pd.DataFrame( [[stockMoney + restMoney,stockMoney, restMoney]],index=[current], columns=['total', 'stock', 'rest'])
    moneySum = pd.concat([moneySum, moneydf])
    money = stockMoney + restMoney
    
printPd('##수익률', stockValue / beforeValue)
printPd('##소유주식', stockWallet)
printPd('##주식가격', moneyWallet)
printPd('##Total', moneySum)

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
