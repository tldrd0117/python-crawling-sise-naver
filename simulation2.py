
# In[1]: Import
from crawler.NaverCrawler import NaverCrawler
from crawler.NaverWorldCrawler import NaverWorldCrawler
from crawler.NaverTopMarketCapCrawler import NaverTopMarketCapCrawler
from crawler.NaverCapFromCodeCrawler import NaverCapFromCodeCrawler
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.NavarSearchCodeCrawler import NavarSearchCodeCrawler
from crawler.NaverPbrCrawler import NaverPbrCrawler

from crawler.data.NaverDate import NaverDate
from crawler.data.NaverResultData import NaverResultData

import pandas as pd
from functools import reduce
import datetime as dt
import numpy as np
from sklearn.linear_model import LinearRegression
from IPython.display import display
import time
import random
import os.path


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
startDateStr = '2007-01-01'
endDateStr = '2019-12-31'
startDate = pd.to_datetime(startDateStr, format='%Y-%m-%d')
endDate = pd.to_datetime(endDateStr, format='%Y-%m-%d')
before = startDate + pd.Timedelta(-1, unit='Y')
end = endDate
beforeStr = before.strftime(format='%Y-%m-%d')
endStr = end.strftime(format='%Y-%m-%d')

# In[3]: 주식 불러오기
class StockLoader:
    @staticmethod
    def create():
        stockloader = StockLoader()
        return stockloader
    
    def makeName(self, name):
        return name + '_' + startDateStr + '_' + endDateStr + '.h5'

    def topk(self, num):
        crawler = NaverTopMarketCapCrawler.create()
        data = crawler.crawling([1,num])
        codes = [ {'code':item.code, 'name':item.name}  for item in data ]
        return codes

    def load(self, name):
        print(name, 'read...')
        return pd.read_hdf(name, key='df')
    
    def loadStockFromDict(self, name, targets, beforeStr, endStr):
        prices = dict()
        if not os.path.isfile(name):
            date = NaverDate.create(startDate=beforeStr, endDate=endStr)
            progress = 0
            compliteLen = len(targets.keys())
            for key in targets:
                print(targets[key],'collect...', str(progress),'/',str(compliteLen) ,str(progress/compliteLen)+'%')
                crawler = NaverStockCrawler.create(key)
                data = crawler.crawling(date)
                prices[targets[key]] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
                progress+=1

            topdf = pd.DataFrame(prices)
            topdf.to_hdf(name, key='df', mode='w')
        else:
            print(name, 'read...')
            topdf = pd.read_hdf(name, key='df')
        return topdf
    
    def loadStockFromArr(self, name, targets, beforeStr, endStr):
        prices = dict()
        if not os.path.isfile(name):
            date = NaverDate.create(startDate=beforeStr, endDate=endStr)
            for target in targets:
                print(target['name'], 'collect...')
                crawler = NaverStockCrawler.create(target['code'])
                data = crawler.crawling(date)
                prices[target['name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
            bonddf = pd.DataFrame(prices)
            bonddf.to_hdf(name, key='df', mode='w')
        else:
            print(name, 'read...')
            bonddf = pd.read_hdf(name, key='df')
        return bonddf
    
    def loadDomesticIndex(self, name, beforeStr, endStr):
        if not os.path.isfile(name):
            print(name, 'collect...')
            crawler = NaverCrawler.create(targetName=name.split('_')[0])
            date = NaverDate.create(startDate=beforeStr, endDate=endStr)
            data = crawler.crawling(dateData=date)
            df = pd.DataFrame(columns=['종가', '전일비', '등락률', '거래량', '거래대금'])
            for v in data:
                df.loc[v.index()] = v.value()
            df.to_hdf(name, key='df', mode='w')
        else:
            print(name, 'read...')
            df = pd.read_hdf(name, key='df')
        return df

sl = StockLoader.create()
#시가총액순 종목
topcap = sl.load(sl.makeName('TOPCAP'))

#시가
targetShares = {}
for index, row  in topcap.iterrows():
    targetShares[row['Code']] = row['Name']
#종목별 종가
topdf = sl.loadStockFromDict(sl.makeName('SHARETOPCAP'),targetShares, beforeStr, endDateStr)
#채권 종가
bonddf = sl.loadStockFromArr(sl.makeName('BOND'),[{'code':'114260','name':'KODEX 국고채3년'}],beforeStr, endDateStr)
kospidf = sl.loadDomesticIndex(sl.makeName('KOSPI'), beforeStr, endDateStr)

# In[5]: look
# kospidf

# In[4]: 시뮬레이션



class StockTransaction:
    @staticmethod
    def create():
        st = StockTransaction()
        return st
    
    def getMomentumMean(self, current, df, mNum, mUnit):
        mdf = df.resample('M').mean()
        beforeMomentumDate = current + pd.Timedelta(-mNum, unit=mUnit)
        start = mdf.index.get_loc(beforeMomentumDate, method='nearest')
        end = mdf.index.get_loc(current, method='nearest')
        oneYearDf = mdf.iloc[start:end+1]
        momentum = oneYearDf.iloc[-1] - oneYearDf
        momentumIndex = (oneYearDf.iloc[-1] - oneYearDf) / oneYearDf
        momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        return momentumIndex.mean(), momentumScore.mean()

    def getMomentumInvestRate(self, momentumMean, momentumScoreMean, shareNum, cashRate):
        sortValue = momentumMean.sort_values(ascending=False)
        share = momentumScoreMean[sortValue.head(shareNum).index]
        distMoney = share / (share + cashRate)
        distMoney = distMoney[share > 0.8]
        sumMoney = distMoney.sum()
        print('investNum',len(list(distMoney.index)))
        return {'invest':distMoney / sumMoney, 'perMoney':sumMoney / share.size if share.size != 0 else 0}

    def setMonmentumRate(self, shares, current, topdf, cashRate, mNum, mUnit):
        momentumMean, momentumScoreMean = self.getMomentumMean(current, topdf, mNum=mNum, mUnit=mUnit)
        rate = self.getMomentumInvestRate(momentumMean[shares.shareList], momentumScoreMean[shares.shareList], shareNum=shares.shareNum, cashRate=cashRate)
        shares.investRate = rate['invest']
        shares.perMoneyRate = rate['perMoney']

    def buy(self, shares, wallet, buyDate, valuedf):
        money = shares.investMoney
        rateMoney = shares.investRate * shares.investMoney
        stockWallet = wallet.stockWallet
        stockValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][rateMoney.index]
        rowdf = pd.DataFrame(data=[[0]*len(rateMoney.index)], index=[buyDate], columns=rateMoney.index)
        intersect = list(set(stockWallet.columns) & set(rowdf.columns))
        if buyDate not in stockWallet.index:
            stockWallet = pd.concat([stockWallet, rowdf], axis=0, sort=False)
        else:
            if len(intersect) > 0:
                stockWallet.loc[buyDate, intersect] = 0
                rowdf = rowdf.drop(columns=intersect)
                stockWallet = pd.concat([stockWallet, rowdf], axis=1, sort=False)
            else:
                stockWallet = pd.concat([stockWallet, rowdf], axis=1, sort=False)
        for col in rateMoney.index:
            rMoney = rateMoney[col]
            sValue = stockValue[col]
            while (rMoney - sValue) > 0:
                if col in stockWallet.columns and buyDate in stockWallet.index:
                    stockWallet[col][buyDate] = stockWallet[col][buyDate] + 1
                money -= sValue
                rMoney -= sValue
        wallet.stockWallet = stockWallet
        shares.restMoney += money

    def restInvestBuy(self, buyDate, valuedf, money, wallet):
        bondValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][bonddf.columns[0]]
        stockNum = 0
        while bondValue < money:
            money -= bondValue
            stockNum += 1
        wallet.bondNum = stockNum
        wallet.restMoney += money

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

class Wallet:
    def __init__(self):
        self.stockWallet = pd.DataFrame()
        self.moneyWallet = pd.DataFrame()
        self.stockMoney = 0
        self.restMoney = 0
        self.bondNum = 0
    def goOneMonth(self, current, topdf, bonddf, allIndex):
        beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
        buyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=self.stockWallet.columns)
        self.moneyWallet = pd.concat([self.moneyWallet, buyMoney], sort=False)
    
        current = current + pd.Timedelta(1, unit='M')
        stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
        self.restMoney = self.restMoney + self.bondNum * bonddf.iloc[bonddf.index.get_loc(current, method='nearest')][bonddf.columns[0]]
        self.stockMoney = (self.stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum()
        return current


        
#투자금
money = 10000000
#현금비율
rebalaceRate = 0.25
st = StockTransaction.create()


bond = Shares('bond', shareNum=0, moneyRate=0, shareList=[])
foreign = Shares('foreign', shareNum=0, moneyRate=0, shareList=[])
domestic = Shares('domestic', shareNum=200, moneyRate=1, shareList=[])
wallet = Wallet()
moneySum = pd.DataFrame()
current = startDate

while endDate > current:
    print('simulate...', current)
    domestic.shareList = list(topcap[str(current.year)]['Name'])
    wallet.stockMoney = money * (1-rebalaceRate)
    wallet.restMoney = money * rebalaceRate
    stockRestMoney = 0

    #해당돼는 날짜(Current)의 종목별 모멘텀 평균을 구한다
    st.setMonmentumRate(bond, current, topdf, cashRate=0.3, mNum=6, mUnit='M')
    st.setMonmentumRate(foreign, current, topdf, cashRate=0.3, mNum=6, mUnit='M')
    st.setMonmentumRate(domestic, current, topdf, cashRate=0.3, mNum=6, mUnit='M')
    #TARGET
    sumMoneyRate = bond.moneyRate + foreign.moneyRate + domestic.moneyRate
    bond.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)
    foreign.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)
    domestic.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)

    st.buy(bond, wallet, current, topdf)
    st.buy(foreign, wallet, current, topdf)
    st.buy(domestic, wallet, current, topdf)

    sumRestMoney = bond.restMoney + foreign.restMoney + domestic.restMoney

    st.restInvestBuy(current, bonddf, sumRestMoney, wallet)

    allIndex = list(bond.investRate.index) + list(foreign.investRate.index) + list(domestic.investRate.index)
    allIndex = list(set(allIndex))
    # print(allIndex)

    current = wallet.goOneMonth(current, topdf, bonddf, allIndex)

    #구매
    # print(money)
    # printPd('##현재자산가치', (stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum() + money)
    # print('잔금',restMoney)
    # restMoney = stockRestMoney + restMoney
    # printPd('##수익률', stockValue / beforeValue)
    # printPd('##수익률평균', (stockValue / beforeValue).values.mean())
    # print('주식', stockMoney)
    # print('현금', restMoney)
    # print('수익률', (stockMoney + restMoney)/money )
    moneydf = pd.DataFrame( [[wallet.stockMoney + wallet.restMoney, wallet.stockMoney, wallet.restMoney]],index=[current], columns=['total', 'stock', 'rest'])
    moneySum = pd.concat([moneySum, moneydf], sort=False)
    money = wallet.stockMoney + wallet.restMoney
    print('total', money, wallet.stockMoney, wallet.restMoney)


print('##소유주식', wallet.stockWallet)
print('##주식가격', wallet.moneyWallet)
print('##Total', moneySum)

# In[6]: 통계
moneySum.index = moneySum.index.map(lambda dt: pd.to_datetime(dt.date()))

portfolio = moneySum['total'] / moneySum['total'].iloc[0]
투자기간 = len(moneySum.index)/12
# print(portfolio)
print('연평균 수익률',(portfolio[-1]**(1/투자기간)*100-100))

print('최대 하락률',((portfolio.shift(1) - portfolio)*100).min())
print('최대 상승률',((portfolio.shift(1) - portfolio)*100).max())

# In[7]: 그래프
# In[15]: 그래프 그리기
choosedDf = moneySum[['total']]
choosedDf['KOSPI'] = kospidf['종가']
choosedDf[bonddf.columns[0]] = bonddf[bonddf.columns[0]]
choosedDf = choosedDf.fillna(method='bfill').fillna(method='ffill')
# print(choosedDf)
jisuDf = choosedDf / choosedDf.iloc[0]
print(jisuDf)
plt = jisuDf.plot(figsize = (18,12), fontsize=12)
fontProp = fm.FontProperties(fname=path, size=18)
plt.legend(prop=fontProp)
print(plt)











#%%
