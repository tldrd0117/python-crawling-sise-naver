# In[1]: Import
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
startDateStr = '2008-01-01'
endDateStr = '2018-12-31'
startDate = pd.to_datetime(startDateStr, format='%Y-%m-%d')
endDate = pd.to_datetime(endDateStr, format='%Y-%m-%d')

before = startDate + pd.Timedelta(-1, unit='Y')
end = endDate

beforeStr = before.strftime(format='%Y-%m-%d')
endStr = end.strftime(format='%Y-%m-%d')

# In[11]: 데이터수집
#30종목 + KODEX 인버스

# crawler = NavarSearchCodeCrawler.create('KODEX')
# targets = crawler.crawling()

# def filteredList(filterList, items):
#     return [ t['name'] for word in filterList for t in filter(lambda x : x['name'].find(word) >= 0, items)]
# def filteredListReverse(filterList, items):
#     targetList = []
#     for target in items:
#         isIn = False
#         for word in filterList:
#             if target['name'].find(word) > 0:
#                 isIn = True
#                 break
#         if not isIn:
#             targetList.append(target['name'])

#     return targetList


# for word in ['액티브', '삼성']:
#     targets = list(filter(lambda x : word not in x['name'], targets))
# bond = filteredList([' 국고채', ' 국채'], targets)
# foreign = filteredList(['미국', '대만', '중국', '심천', '선진국', '일본', 'China', '원유', 'WTI', '글로벌', '차이나', '라틴', '유로'],targets)
# domestic = filteredListReverse(['미국', '대만', '중국', '심천', '선진국', '일본', 'China', '원유', 'WTI', '글로벌', '국고채', '국채'], targets)

# #중복제거
# bond = list(set(bond))
# foreign = list(set(foreign))
# domestic = list(set(domestic))

# print('채권:',bond)
# print('해외:',foreign)
# print('국내:',domestic)
# # targets
# # targets = topK(100)
# In[11]: define price
prices = dict()

# In[12]: read

topcap = pd.read_hdf('topcap2007-06-20-2018-06-20.h5')
# In[12]
targets = []
# topcap['Code']
# v1 = list(set(topcap['Code'].values))
# v2 = list(set(topcap['Name'].values))
# print(len(v1), len(v2))
for index, row  in topcap.iterrows():
    targets.append({'Code':row['Code'], 'Name':row['Name']})
# print(targets[0]['Code'])
# def prrr(t):
#     print(t['Code'])
#     print(t['Code'] in list(topcap['Code'])
#     return t['Code'] in list(topcap['Code'])
#     # lambda t: t['Code'] in list(topcap['Code'])
# ta = filter(prrr,targets)
# print(len(targets))
# print(len(list(ta)))
# In[12]: range
# topcap.loc['2016-06-20',['Code','Name']]['Code']
# shares = topcap.loc['2016'+'-06-20',['Code','Name']]
# for index, row  in shares.iterrows():
    # print(row['Code'])
date = NaverDate.create(startDate=beforeStr, endDate=endStr)
for code in list(topcap['Code']):
    print(code,'collect...')
    crawler = NaverStockCrawler.create(code)
    data = crawler.crawling(date)
    prices[data['name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
topdf = pd.DataFrame(prices)
topdf.to_hdf('TOPCAPSTOCK2007-06-20-2018-06-20.h5', key='df', mode='w')


# In[12]: 데이터 가져오기
# import os.path
# name = 'KODEX'+beforeStr+'-'+endStr+'.h5'
# if not os.path.isfile(name):
#     print('collect start',beforeStr,endStr)
#     date = NaverDate.create(startDate=beforeStr, endDate=endStr)
#     for target in targets:
#         print(target,'collect...')
#         crawler = NaverStockCrawler.create(target['code'])
#         data = crawler.crawling(date)
#         prices[target['name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
#     topdf = pd.DataFrame(prices)
#     topdf.to_hdf(name, key='df', mode='w')
# else:
#     print('read...')
#     topdf = pd.read_hdf(name, key='df')
# print(topdf)

# In[12]: S&P500 데이터
# date = NaverDate.create(startDate=beforeStr, endDate=endStr)
# crawler = NaverWorldCrawler.create('SPI@SPX')
# data = crawler.crawling(date)
# prices['S&P500'] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data } 
# topdf = pd.DataFrame(prices)
# bond = ['S&P500']
# foreign = []
# domestic = []

# In[12]: print
# topdf.index.get_loc(pd.to_datetime('2014-04-21', format='%Y-%m-%d'), method='nearest')
topdf

# In[12]: 평균
topdf = topdf.fillna(0)
monthly_topdf = topdf.resample('M').mean()
monthly_topdf

# In[13]: 시작날 부터 모멘텀 구하기
money = 10000000

bondNum = 0 
foreignNum = 3 
domesticNum = 3 

bondRateMoney = 1 
foreignRateMoney = 1
domesticRateMoney = 1

momentumNum = 12
momentumUnit = 'M'
rebalaceRate = 0
print('startMoney: ', money)
stockWallet = pd.DataFrame()
moneyWallet = pd.DataFrame()
moneySum = pd.DataFrame()
current = startDate
stockRestMoney = 0
restBond = 'KODEX 국채선물10년'

def restBondBuy(buyDate, valuedf, money):
    bondValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][restBond]
    stockNum = 0
    while bondValue < money:
        money -= bondValue
        stockNum += 1
    return stockNum, money

def buy(rate, buyDate, valuedf, money, wallet):
    rateMoney = rate * money
    stockValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][rateMoney.index]
    rowdf = pd.DataFrame(data=[[0]*len(rateMoney.index)], index=[buyDate], columns=rateMoney.index)
    # if buyDate in wallet.index:
    #     wallet = pd.concat([wallet, rowdf], axis=1)
    # else:
    #     wallet = pd.concat([wallet, rowdf], axis=0)
    intersect = list(set(wallet.columns) & set(rowdf.columns))
    if buyDate not in wallet.index:
        wallet = pd.concat([wallet, rowdf], axis=0)
    else:
        if len(intersect) > 0:
            wallet.loc[buyDate, intersect] = 0
            rowdf = rowdf.drop(columns=intersect)
            wallet = pd.concat([wallet, rowdf], axis=1)
        else:
            wallet = pd.concat([wallet, rowdf], axis=1)
    for col in rateMoney.index:
        rMoney = rateMoney[col]
        sValue = stockValue[col]
        while (rMoney - sValue) > 0:
            if col in wallet.columns and buyDate in wallet.index:
                wallet[col][buyDate] = wallet[col][buyDate] + 1
            # elif col in wallet.columns :
            #     dt = pd.DataFrame([{col: 1}], index=[buyDate])
            #     wallet = pd.concat([wallet, dt], axis=0)
            # else:
            #     dt = pd.DataFrame([{col: 1}], index=[buyDate])
            #     wallet = pd.concat([wallet, dt], axis=1)
            money -= sValue
            rMoney -= sValue
    return money, wallet

def getInvestRate(momentumScoreMean, shareNum, cashRate):
    sortValue = momentumScoreMean.sort_values(ascending=False)
    share = sortValue.head(shareNum)
    distMoney = share / (share + cashRate)
    sumMoney = distMoney.sum()
    return distMoney / sumMoney, sumMoney / share.size if share.size != 0 else 0

while endDate > current:
    print('simulate...', current)
    #money 전체 가치
    #stockMoney 주식에 투자할 가치
    #restMoney 잔금
    stockMoney = money * (1-rebalaceRate)
    restMoney = money * rebalaceRate
    stockRestMoney = 0
    
    beforeMomentumDate = current + pd.Timedelta(-momentumNum, unit=momentumUnit)
    
    start = monthly_topdf.index.get_loc(beforeMomentumDate, method='nearest')
    end = monthly_topdf.index.get_loc(current, method='nearest')
    
    oneYearDf = monthly_topdf.iloc[start:end+1]

    momentum = oneYearDf.iloc[-1] - oneYearDf
    momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )

    momentumScoreMean = momentumScore.mean()
    # print(bond)
    # print(momentumScoreMean[bond])
    bondRate, bondMoneyRate = getInvestRate(momentumScoreMean[bond], bondNum, 1)
    foreignRate, foreignMoneyRate = getInvestRate(momentumScoreMean[foreign], foreignNum, 1)
    domesticRate, domesticMoneyRate = getInvestRate(momentumScoreMean[domestic], domesticNum, 1)
    #TARGET
    sumRateMoney = bondRateMoney + foreignRateMoney + domesticRateMoney
    bondMoney = bondRateMoney/sumRateMoney * stockMoney * bondMoneyRate
    bondRateRestMoney = bondRateMoney/sumRateMoney * stockMoney * (1 - bondMoneyRate)
    foreignMoney = foreignRateMoney/sumRateMoney * stockMoney * foreignMoneyRate
    foreignRateRestMoney = foreignRateMoney/sumRateMoney * stockMoney * (1 - foreignMoneyRate)
    domesticMoney = domesticRateMoney/sumRateMoney * stockMoney * domesticMoneyRate
    domesticRateRestMoney = domesticRateMoney/sumRateMoney * stockMoney * (1 - domesticMoneyRate)

    stockRestMoney += (bondRateRestMoney + foreignRateRestMoney + domesticRateRestMoney)

    bondRestMoney, stockWallet = buy(bondRate, current, topdf, bondMoney, stockWallet)
    # printPd('채권잔금:', stockWallet)
    foreignRestMoney, stockWallet = buy(foreignRate, current, topdf, foreignMoney, stockWallet)
    # printPd('해외잔금:', stockWallet)
    domesticRestMoney, stockWallet = buy(domesticRate, current, topdf, domesticMoney, stockWallet)
    # printPd('국내잔금:', stockWallet)
    stockRestMoney += (bondRestMoney + foreignRestMoney + domesticRestMoney)

    bondNum, restMoney = restBondBuy(current, topdf, stockRestMoney + restMoney)

    allIndex = list(bondRate.index) + list(foreignRate.index) + list(domesticRate.index)
    allIndex = list(set(allIndex))
    # print(allIndex)

    beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
    print(stockWallet)
    buyMoney = pd.DataFrame([(stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=stockWallet.columns)
    moneyWallet = pd.concat([moneyWallet, buyMoney])
   
    current = current + pd.Timedelta(1, unit='M')
    stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
    restMoney = restMoney + bondNum * topdf.iloc[topdf.index.get_loc(current, method='nearest')][restBond]

    #구매
    # print(money)
    printPd('##현재자산가치', (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum() + money)
    stockMoney = (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum()
    print('잔금',restMoney)
    # restMoney = stockRestMoney + restMoney
    printPd('##수익률', stockValue / beforeValue)
    printPd('##수익률평균', (stockValue / beforeValue).values.mean())
    print('주식', stockMoney)
    print('현금', restMoney)
    print('total', restMoney + stockMoney)
    print('수익률', (stockMoney + restMoney)/money )
    moneydf = pd.DataFrame( [[stockMoney + restMoney, stockMoney, restMoney]],index=[current], columns=['total', 'stock', 'rest'])
    moneySum = pd.concat([moneySum, moneydf])
    money = stockMoney + restMoney
    
printPd('##수익률', stockValue / beforeValue)
printPd('##소유주식', stockWallet)
printPd('##주식가격', moneyWallet)
printPd('##Total', moneySum)

# In[14]: 코스피 200 가져오기
crawler = NaverCrawler.create(targetName='KPI200')
date = NaverDate.create(startDate=startDateStr, endDate=endDateStr)
kospi200 = crawler.crawling(dateData=date)
df = pd.DataFrame(columns=['종가', '전일비', '등락률', '거래량', '거래대금'])
for v in kospi200:
    df.loc[v.index()] = v.value()
df

# In[15]: 날짜 normalize
moneySum.index = moneySum.index.map(lambda dt: pd.to_datetime(dt.date()))
# moneySum
# df.loc[moneySum.index, :]
# df.index

# In[16]: 연평균 수익률
portfolio = moneySum['total'] / moneySum['total'].iloc[0]
투자기간 = len(moneySum.index)/12
print(portfolio)
(portfolio[-1]**(1/투자기간)*100-100)

# In[15]: 그래프 그리기
choosedDf = moneySum[['total']]
choosedDf['KOSPI'] = df['종가']
choosedDf[restBond] = topdf[restBond]
choosedDf = choosedDf.fillna(method='bfill').fillna(method='ffill')
# print(choosedDf)
jisuDf = choosedDf / choosedDf.iloc[0]
print(jisuDf)
plt = jisuDf.plot(figsize = (18,12), fontsize=12)
fontProp = fm.FontProperties(fname=path, size=18)
plt.legend(prop=fontProp)
print(plt)

# In[14]: 계산
# stockWallet
# moneyWallet
# moneySum
# stockValue / beforeValue
# moneySum / moneySum.shift(1) 



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
