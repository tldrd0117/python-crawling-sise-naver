
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
from time import sleep

# In[2]: font 설정
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt
import platform


startTime = time.time()  # 시작 시간 저장
print(platform.system())
if platform.system()=='Darwin':
    path = '/Library/Fonts/NanumBarunGothicLight.otf'
else:
    path = 'C:/Windows/Fonts/malgun.ttf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
mpl.rc('font', family=font_name) 

# In[2]: date
startDateStr = '2012-01-01'
endDateStr = '2018-12-31'
startDate = pd.to_datetime(startDateStr, format='%Y-%m-%d')
endDate = pd.to_datetime(endDateStr, format='%Y-%m-%d')
before = startDate + pd.Timedelta(-1, unit='Y')
end = endDate
beforeStr = before.strftime(format='%Y-%m-%d')
endStr = end.strftime(format='%Y-%m-%d')

print(beforeStr, endStr)

# In[3]: 주식 불러오기
class StockLoader:
    @staticmethod
    def create():
        stockloader = StockLoader()
        return stockloader
    
    def makeName(self, name, beforeStr=beforeStr, endDateStr=endDateStr):
        return name + '_' + beforeStr + '_' + endDateStr + '.h5'

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
                print(target['Name'], 'collect...')
                crawler = NaverStockCrawler.create(target['Code'])
                data = crawler.crawling(date)
                prices[target['Name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
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
    
    def loadSearchCodeName(self, name):
        crawler = NavarSearchCodeCrawler.create(name)
        return crawler.crawling()

    def chooseCodeName(self, filterList, items):
        return [ {'Name':t['Name'], 'Code':t['Code']} for word in filterList for t in filter(lambda x : x['Name'].find(word) >= 0, items)]
    
    def exceptCodeName(self, filterList, items):
        targetList = []
        for target in items:
            isIn = False
            for word in filterList:
                if target['Name'].find(word) > 0:
                    isIn = True
                    break
            if not isIn:
                targetList.append({'Name':target['Name'], 'Code':target['Code']})

        return targetList

sl = StockLoader.create()


# In[23]: ETF
#KODEX 종목 (삼성자산운용)
blackWords = ['액티브', '삼성']
bondWords = [' 국고채', ' 국채']
foreignWords = ['미국', '대만', '중국', '심천', '선진국', '일본', 'China', '글로벌', '차이나', '라틴', '유로', '인도', '하이일드']
KODEX = sl.loadSearchCodeName('KODEX')
KODEX = sl.exceptCodeName(blackWords, KODEX)
KODEX_bond = sl.chooseCodeName(bondWords, KODEX)
KODEX_foreign = sl.chooseCodeName(foreignWords, KODEX)
KODEX_domestic = sl.exceptCodeName(bondWords + foreignWords, KODEX)


#TIGER 종목 (미래에셋대우)
TIGER = sl.loadSearchCodeName('TIGER')
TIGER = sl.exceptCodeName(blackWords, TIGER)
TIGER_bond = sl.chooseCodeName(bondWords, TIGER)
TIGER_foreign = sl.chooseCodeName(foreignWords, TIGER)
TIGER_domestic = sl.exceptCodeName(bondWords + foreignWords, TIGER)


# In[24]: load

#시가총액순 종목
topcap = sl.load(sl.makeName('TOPCAP', '2007-01-01', '2019-12-31'))

#시가
targetShares = {}
for index, row  in topcap.iterrows():
    targetShares[row['Code']] = row['Name']
#종목별 종가
etfdf = sl.loadStockFromArr(sl.makeName('ETF', endDateStr='2019-12-31'), KODEX + TIGER, beforeStr, '2019-12-31')
topcapdf = sl.loadStockFromDict(sl.makeName('SHARETOPCAP', beforeStr='2006-01-01', endDateStr='2019-12-31'), targetShares, '2005-12-31', '2019-12-31')
etfdf.index = etfdf.index.map(lambda dt: pd.to_datetime(dt.date()))
topcapdf.index = topcapdf.index.map(lambda dt: pd.to_datetime(dt.date()))
topdf = pd.concat([etfdf,topcapdf], sort=False, axis=1)
# bonddf = sl.loadStockFromArr(sl.makeName('BOND_ETF'), KODEX_bond + TIGER_bond, beforeStr, endDateStr)
#채권 종가
# bonddf = sl.loadStockFromArr(sl.makeName('BOND'),[{'code':'114260','name':'KODEX 국고채3년'}],beforeStr, endDateStr)
kospidf = sl.loadDomesticIndex(sl.makeName('KOSPI', '2005-12-31', '2019-12-31'), '2005-12-31', '2019-12-31')

# topdf
# topcapdf.loc['2012-01-01':endDateStr]

# In[5]: look
# kospidf
# len(KODEX_foreign+TIGER_foreign)

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
        momentumIndex = momentum / oneYearDf
        momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        return momentumIndex.mean(), momentumScore.mean()

    def get12MomentumMean(self, current, df):
        mdf = df.resample('M').mean()
        beforeMomentumDate = current + pd.Timedelta(-1, unit='Y')
        start = mdf.index.get_loc(beforeMomentumDate, method='nearest')
        end = mdf.index.get_loc(current, method='nearest')
        oneYearDf = mdf.iloc[start:end+1]
        momentum = oneYearDf.iloc[-1] - oneYearDf
        momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        # print(df[momentumScore.iloc[0] > 0])
        return df[list(momentumScore.iloc[0][momentumScore.iloc[0] > 0].index)]

    def getMomentumInvestRate(self, momentumIndex, momentumScoreMean, shareNum, cashRate, mementumLimit):
        sortValue = momentumIndex.sort_values(ascending=False)
        sortValue = sortValue.dropna()
        # print(1,sortValue.head(shareNum).index)
        # print(2,momentumScoreMean)
        share = momentumScoreMean[list(sortValue.head(shareNum).index)]
        distMoney = share / (share + cashRate)
        distMoney = distMoney[share > mementumLimit]
        sumMoney = distMoney.sum()
        return {'invest':distMoney / sumMoney, 'perMoney':sumMoney / share.size if share.size != 0 else 0}

    def setMonmentumRate(self, shares, current, topdf, cashRate, mNum, mUnit, mementumLimit, limit12 = False):
        momentumdf = topdf if not limit12 else self.get12MomentumMean(current, topdf)
        # print('momentum:',len(list(momentumdf.columns)))
        momentumMean, momentumScoreMean = self.getMomentumMean(current, momentumdf, mNum=mNum, mUnit=mUnit)
        rate = self.getMomentumInvestRate(momentumMean[shares.shareList], momentumScoreMean[shares.shareList], shareNum=shares.shareNum, cashRate=cashRate, mementumLimit=mementumLimit)
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
        print('투자리스트')
        print('=================================================')
        print('investNum', len(rateMoney.index), '투자금 합계: ',rateMoney.sum() - money)
        print(list(rateMoney.index))
        print('=================================================')

    # def restInvestBuy(self, buyDate, valuedf, money, wallet):
        # bondValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][bonddf.columns[0]]
        # stockNum = 0
        # while bondValue < money:
            # money -= bondValue
            # stockNum += 1
        # wallet.bondNum = stockNum
        # wallet.restMoney = money


class Shares:
    def __init__(self, name, shareNum, moneyRate, shareList):
        self.name = name
        self.shareNum = shareNum
        self.moneyRate = moneyRate
        self.shareList = shareList
        self.investRate = None
        self.perMoneyRate = None
    
    def calculateInvestMoney(self, sumMoneyRate, stockMoney):
        self.investMoney = self.moneyRate/sumMoneyRate * stockMoney * self.perMoneyRate
        self.restMoney = self.moneyRate/sumMoneyRate * stockMoney * (1 - self.perMoneyRate)
    
    @staticmethod
    def toNameList(dictList):
        return list(set([ dic['Name'] for dic in dictList ]))

class Wallet:
    def __init__(self):
        self.stockWallet = pd.DataFrame()
        self.moneyWallet = pd.DataFrame()
        self.stockMoney = 0
        self.restMoney = 0
        self.bondNum = 0

    def goOneMonthAndlossCut(self, current, topdf, allIndex):
        nextDate = current + pd.Timedelta(1, unit='M')
        indexloc = topdf.index.get_loc(current, method='nearest')
        firstValue = topdf.iloc[indexloc][allIndex] 
        # print(self.stockWallet.iloc[-1])
        firstBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * firstValue).values], index=[current], columns=self.stockWallet.columns)
        restStockSellMoney = 0
        cutlist=[]
        while nextDate > current:
            # beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex] 
            # beforeBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=self.stockWallet.columns)
            # self.moneyWallet = pd.concat([self.moneyWallet, beforeBuyMoney], sort=False)
            #하루지나감 어렵다
            current = topdf.index[indexloc+1]
            dateIndex = self.stockWallet.index.get_loc(current, method='ffill')
            # buyTargets = self.stockWallet.loc[:,self.stockWallet.iloc[dateIndex]>0].columns
            
            stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
            buyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * stockValue).values], index=[current], columns=self.stockWallet.columns)
            returnRate = buyMoney/firstBuyMoney.values
            returnRate = returnRate[allIndex]
            returnRate = returnRate.dropna(axis=1, how='all')
            returnRate = returnRate[returnRate <= 0.95]
            returnRate = returnRate.dropna(axis=1, how='all')
            intersect = list(set(returnRate.columns) & set(cutlist))
            returnRate = returnRate.drop(intersect, axis=1)
            
            #cutlist를 returnRate있게 걸러야함
            for col in returnRate.columns:
                cutlist.append(col)
                # print('1',self.stockWallet.iloc[dateIndex])
                # print('2',stockValue)
                self.restMoney += self.stockWallet.iloc[dateIndex][col] * stockValue[col]
                restStockSellMoney += stockValue[col]
            indexloc+=1
        print('losscut',current, len(cutlist), cutlist)
        intersect = list(set(self.stockWallet.columns) & set(cutlist))
        dropStockWallet = self.stockWallet.drop(intersect, axis=1)
        dropStockValue = stockValue.drop(intersect, axis = 0)
        self.stockMoney = (dropStockWallet.iloc[-1][dropStockValue.index] * dropStockValue).values.sum() + restStockSellMoney
            # beforeBuyMoney * buyMoney / beforeBuyMoney
        return current

    def goOneMonth(self, current, topdf, bonddf, allIndex):
        beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
        buyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=self.stockWallet.columns)
        
        
        # self.moneyWallet = pd.concat([self.moneyWallet, buyMoney], sort=False)

        current = current + pd.Timedelta(1, unit='M')
        stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
        
        if bonddf:
            self.restMoney = self.restMoney + self.bondNum * bonddf.iloc[bonddf.index.get_loc(current, method='nearest')][bonddf.columns[0]]
        self.stockMoney = (self.stockWallet.iloc[-1][stockValue.index] * stockValue).values.sum()
        return current
        
#투자금
money = 10000000
#현금비율
rebalaceRate = 0

current = startDate

st = StockTransaction.create()
bondList = []#Shares.toNameList(KODEX_bond+TIGER_bond)
foreignList = []#['TIGER 미국S&P500레버리지(합성 H)','KODEX China H 레버리지(H)','TIGER 유로스탁스레버리지(합성 H)','KODEX 일본TOPIX100','TIGER 인도니프티50레버리지(합성)']#Shares.toNameList(KODEX_foreign+TIGER_foreign)
#domesticList = Shares.toNameList(KODEX_domestic+TIGER_domestic)
domesticList = list(topcap[str(current.year)]['Name'])

bondListNum = 0#3 #int(len(KODEX_bond+TIGER_bond) * 3 / 10)
foreignListNum = 0#5#int(len(KODEX_foreign+TIGER_foreign) * 3 / 10)
domesticListNum = 200#int(len(KODEX_domestic+TIGER_domestic) * 3 / 10)

print(bondListNum, foreignListNum, domesticListNum)

wallet = Wallet()
moneySum = pd.DataFrame()

bond = Shares('bond', shareNum=bondListNum, moneyRate=1, shareList=bondList)
foreign = Shares('foreign', shareNum=foreignListNum, moneyRate=1, shareList=foreignList)
domestic = Shares('domestic', shareNum=domesticListNum, moneyRate=1, shareList=list(topcap[str(current.year)]['Name']))


while endDate > current:
    print('simulate...', current)
    domestic.shareList = list(topcap[str(current.year)]['Name'])
    wallet.stockMoney = money * (1-rebalaceRate)
    wallet.restMoney = money * rebalaceRate
    stockRestMoney = 0

    #해당돼는 날짜(Current)의 종목별 모멘텀 평균을 구한다
    st.setMonmentumRate(bond, current, topdf, cashRate=0, mNum=6, mUnit='M', mementumLimit=0)
    st.setMonmentumRate(foreign, current, topdf, cashRate=0.2, mNum=6, mUnit='M', mementumLimit=0, limit12=False)
    st.setMonmentumRate(domestic, current, topdf, cashRate=0.2, mNum=6, mUnit='M', mementumLimit=0.25, limit12=True)
    #TARGET
    sumMoneyRate = bond.moneyRate + foreign.moneyRate + domestic.moneyRate
    bond.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)
    foreign.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)
    domestic.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)

    st.buy(bond, wallet, current, topdf)
    st.buy(foreign, wallet, current, topdf)
    st.buy(domestic, wallet, current, topdf)

    #사고남은돈 + 지갑에 남은돈
    sumRestMoney = bond.restMoney + foreign.restMoney + domestic.restMoney + wallet.restMoney
    wallet.restMoney = sumRestMoney
    # st.restInvestBuy(current, bonddf, sumRestMoney, wallet)

    allIndex = list(bond.investRate.index) + list(foreign.investRate.index) + list(domestic.investRate.index)
    allIndex = list(set(allIndex))
    # print(allIndex)

    current = wallet.goOneMonthAndlossCut(current, topdf, allIndex)

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
    print('=================================================')
    print('total', money, wallet.stockMoney, wallet.restMoney)
    print('=================================================')


# print('##소유주식', wallet.stockWallet)
# print('##주식가격', wallet.moneyWallet)
print('##Total', moneySum)

# In[6]: 통계
moneySum.index = moneySum.index.map(lambda dt: pd.to_datetime(dt.date()))

portfolio = moneySum['total'] / moneySum['total'].iloc[0]
투자기간 = len(moneySum.index)/12
print(투자기간)
# print(portfolio)
print('연평균 수익률',(portfolio[-2]**(1/투자기간)*100-100))

print('최대 하락률',((portfolio.shift(1) - portfolio)*100).min())
print('최대 상승률',((portfolio.shift(1) - portfolio)*100).max())

# In[7]: 그래프
# In[15]: 그래프 그리기
choosedDf = moneySum[['total']]
choosedDf['KOSPI'] = kospidf['종가']
# choosedDf[bonddf.columns[0]] = bonddf[bonddf.columns[0]]
choosedDf = choosedDf.fillna(method='bfill').fillna(method='ffill')
# print(choosedDf)
jisuDf = choosedDf / choosedDf.iloc[0]
print(jisuDf)
plt = jisuDf.plot(figsize = (18,12), fontsize=12)
fontProp = fm.FontProperties(fname=path, size=18)
plt.legend(prop=fontProp)
print(plt)











#%%
