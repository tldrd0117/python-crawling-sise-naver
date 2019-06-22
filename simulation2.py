# In[1]: Import
from crawler.NaverCrawler import NaverCrawler
from crawler.NaverWorldCrawler import NaverWorldCrawler
from crawler.NaverTopMarketCapCrawler import NaverTopMarketCapCrawler
from crawler.NaverCapFromCodeCrawler import NaverCapFromCodeCrawler
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.NavarSearchCodeCrawler import NavarSearchCodeCrawler

from crawler.data.NaverDate import NaverDate
from crawler.data.NaverResultData import NaverResultData

from backtest.StockLoader import StockLoader
from backtest.StockTransaction import StockTransaction

import pandas as pd
from functools import reduce
import datetime as dt
import numpy as np
from sklearn.linear_model import LinearRegression
from IPython.display import display
import time
import random

# In[2]: font 설정
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

startTime = time.time()  # 시작 시간 저장

path = '/Library/Fonts/NanumBarunGothicLight.otf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
mpl.rc('font', family=font_name) 

# In[2]: date
startDateStr = '2008-01-01'
endDateStr = '2018-12-31'
startDate = pd.to_datetime(startDateStr, format='%Y-%m-%d')
endDate = pd.to_datetime(endDateStr, format='%Y-%m-%d')
before = startDate + pd.Timedelta(-1, unit='Y')
end = endDate
beforeStr = before.strftime(format='%Y-%m-%d')
endStr = end.strftime(format='%Y-%m-%d')

# In[3]: 주식 불러오기
sl = StockLoader.create()
st = StockTransaction.create()
#시가총액순 종목
topcap = sl.load('ZIPTOPCAP2007-01-01-2019-12-31.h5')

#시가
targetShares = {}
for index, row  in topcap.iterrows():
    targetShares[row['Code']] = row['Name']
#종목별 종가
topdf = sl.loadStockFromDict('STOCKZIPTOPCAP2007-01-01-2019-12-31.h5',targetShares, beforeStr, endDateStr)
#채권 종가
bonddf = sl.loadStockFromArr('BOND'+beforeStr+'-'+endStr+'.h5',[{'code':'114260','name':'KODEX 국고채3년'}],beforeStr, endDateStr)

# In[4]: 시뮬레이션

#투자금
money = 10000000
#현금비율
rebalaceRate = 0
targetDict = {}

class Shares:
    def __init__(self, name, shareNum, moneyRate, shareList):
        self.name = name
        self.shareNum = shareNum
        self.moneyRate = moneyRate
        self.shareList = shareList
        self.investRate = 0
        self.perMoneyRate = 0
    
    def calculateInvestMoney(self, sumMoneyRate, stockMoney):
        self.investMoney = self.moneyRate/sumMoneyRate * stockMoney * self.perMoneyRate
        self.restMoney = self.moneyRate/sumMoneyRate * stockMoney * (1 - self.perMoneyRate)

bond = Shares('bond', shareNum=0, moneyRate=0, shareList=[])
foreign = Shares('foreign', shareNum=0, moneyRate=0, shareList=[])
domestic = Shares('domestic', shareNum=0, moneyRate=0, shareList=[])
current = startDate

while endDate > current:
    print('simulate...', current)
    bond.shareList = list(topcap[str(current.year)]['Name'])
    stockMoney = money * (1-rebalaceRate)
    restMoney = money * rebalaceRate
    stockRestMoney = 0

    #해당돼는 날짜(Current)의 종목별 모멘텀 평균을 구한다
    st.setMonmentumRate(bond, current, topdf, cashRate=1, mNum=12, mUnit='M')
    st.setMonmentumRate(foreign, current, topdf, cashRate=1, mNum=12, mUnit='M')
    st.setMonmentumRate(domestic, current, topdf, cashRate=1, mNum=12, mUnit='M')
    #TARGET
    sumMoneyRate = bond.moneyRate + foreign.moneyRate + domestic.moneyRate
    bond.calculateInvestMoney(sumMoneyRate, stockMoney)
    foreign.calculateInvestMoney(sumMoneyRate, stockMoney)
    domestic.calculateInvestMoney(sumMoneyRate, stockMoney)

    stockRestMoney += (bondRateRestMoney + foreignRateRestMoney + domesticRateRestMoney)

    bondRestMoney, stockWallet = buy(bondRate, current, topdf, bondMoney, stockWallet)
    # printPd('채권잔금:', stockWallet)
    foreignRestMoney, stockWallet = buy(foreignRate, current, topdf, foreignMoney, stockWallet)
    # printPd('해외잔금:', stockWallet)
    domesticRestMoney, stockWallet = buy(domesticRate, current, topdf, domesticMoney, stockWallet)
    # printPd('국내잔금:', stockWallet)
    stockRestMoney += (bondRestMoney + foreignRestMoney + domesticRestMoney)

    bondNum, restMoney = restBondBuy(current, bonddf, stockRestMoney + restMoney)

    allIndex = list(bondRate.index) + list(foreignRate.index) + list(domesticRate.index)
    allIndex = list(set(allIndex))
    # print(allIndex)

    beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
    print(stockWallet)
    buyMoney = pd.DataFrame([(stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=stockWallet.columns)
    moneyWallet = pd.concat([moneyWallet, buyMoney])
   
    current = current + pd.Timedelta(1, unit='M')
    stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
    restMoney = restMoney + bondNum * bonddf.iloc[bonddf.index.get_loc(current, method='nearest')][restBond]

    #구매
    # print(money)
    # printPd('##현재자산가치', (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum() + money)
    stockMoney = (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum()
    # print('잔금',restMoney)
    # restMoney = stockRestMoney + restMoney
    # printPd('##수익률', stockValue / beforeValue)
    # printPd('##수익률평균', (stockValue / beforeValue).values.mean())
    # print('주식', stockMoney)
    # print('현금', restMoney)
    # print('total', restMoney + stockMoney)
    # print('수익률', (stockMoney + restMoney)/money )
    moneydf = pd.DataFrame( [[stockMoney + restMoney, stockMoney, restMoney]],index=[current], columns=['total', 'stock', 'rest'])
    moneySum = pd.concat([moneySum, moneydf])
    money = stockMoney + restMoney









