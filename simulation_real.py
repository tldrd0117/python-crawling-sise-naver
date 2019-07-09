
# In[0]: 날짜...
from datetime import datetime, timedelta
now = datetime.now()
before = now- timedelta(days=90)
now = '%04d-%02d-%02d' % (now.year, now.month, now.day)
before = '%04d-%02d-%02d' % (before.year, before.month, before.day)


# In[1]: 상장기업...
import pandas as pd
kospiCompanyDf = pd.read_excel('fin/시가총액_2019_01_02.xlsx',sheet_name='시가총액', skiprows=3, converters={'종목코드':str})
kospiCompanyDf = kospiCompanyDf.iloc[1:]
codeName = {}
for index, row in kospiCompanyDf.iterrows():
    codeName[row['종목코드']] = row['종목명']
codeName
# In[2]: crawling 현재가...
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.data.NaverDate import NaverDate

prices = dict()
date = NaverDate.create(startDate=before, endDate=now)
progress = 0
compliteLen = len(codeName.keys())
for key in codeName:
    print(codeName[key],'collect...', str(progress),'/',str(compliteLen) ,str(progress/compliteLen*100)+'%')
    crawler = NaverStockCrawler.create(key)
    data = crawler.crawling(date)
    prices[key] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
    progress+=1

topDf = pd.DataFrame(prices)
topDf
# In[3]: 재무제표
upCodes = ['제조업', '은행업', '증권업', '보험업', '종합금융업', '여신전문금융업', '신용금고']
factors = ['per', 'pcr', 'pbr', 'roe', '당기순이익', '영업활동으로인한현금흐름', '투자활동으로인한현금흐름', '재무활동으로인한현금흐름']
factorDf = {}
for upCode in upCodes:
    for factor in factors:
        name = 'fin/'+upCode+'_'+factor+'.xlsx'
        df = pd.read_excel(name,sheet_name='계정별 기업 비교 - 특정계정과목', skiprows=8)
        df.columns = list(df.iloc[0])
        df = df.drop([0])
        df = df.set_index("종목코드")
        if factor not in factorDf:
            factorDf[factor] = pd.DataFrame()
        factorDf[factor] = pd.concat([factorDf[factor], df])

# In[4]: look
topDf.resample('M').mean()


# In[5]: 함수 설정
import numpy as np
import time

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
        share = momentumScoreMean#[list(sortValue.tail(shareNum).index)]
        distMoney = share / (share + cashRate)
        distMoney = distMoney[share > mementumLimit]
        distMoney = distMoney[sortValue.head(shareNum).index]
        sumMoney = distMoney.sum()
        return {'invest':distMoney / sumMoney, 'perMoney':sumMoney / distMoney.size if distMoney.size != 0 else 0}

    def setMonmentumRate(self, shares, current, topdf, cashRate, mNum, mUnit, mementumLimit, limit12 = False):
        momentumdf = topdf if not limit12 else self.get12MomentumMean(current, topdf)
        # print('momentum:',len(list(momentumdf.columns)))
        momentumMean, momentumScoreMean = self.getMomentumMean(current, momentumdf, mNum=mNum, mUnit=mUnit)
        intersect = list(set(momentumMean.index) & set(shares.shareList))
        rate = self.getMomentumInvestRate(momentumMean[intersect], momentumScoreMean[intersect], shareNum=shares.shareNum, cashRate=cashRate, mementumLimit=mementumLimit)
        shares.investRate = rate['invest']
        shares.perMoneyRate = rate['perMoney']
    
    def setFactorRate(self, shares, current, topdf, factordf, factor):
        targetdf = None
        factor = list(filter(lambda x : x['name']==factor, shares.factor.factors))
        if len(factor) <= 0:
            return
        factor = factor[0]
        targetdf = factordf[factor['name']][current.year - 1]
        shcodes = list(targetdf.sort_values(ascending=factor['ascending']).head(factor['num']).index)
        nameList = list(factordf[factor['name']].loc[shcodes]['종목명'])
        rate = pd.Series([1/len(nameList)]*len(nameList), index=nameList)
        shares.investRate = rate
        shares.perMoneyRate = 1

    def getMomentumList(self, shares, current, targetdf, mNum, mUnit, limit, minVal=-1):
        mdf = targetdf.resample('M').mean()
        beforeMomentumDate = current + pd.Timedelta(-mNum, unit=mUnit)
        start = mdf.index.get_loc(beforeMomentumDate, method='nearest')
        end = mdf.index.get_loc(current, method='nearest')
        oneYearDf = mdf.iloc[start:end+1]
        momentum = oneYearDf.iloc[-1] - oneYearDf
        momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        momentumScore = momentumScore[momentumScore >= minVal]
        return list(momentumScore.mean().sort_values(ascending=False).head(limit).index)
        
    
    def getFactorList(self, shares, current, targetdf, factordf, factor, ascending, num, minVal=-10000000, maxVal=10000000):
        yearDf = factordf[factor][factordf[factor].index.isin(list(targetdf.columns))]
        yearDf = yearDf[current.year - 1]
        yearDf = yearDf[yearDf >= minVal]
        yearDf = yearDf[yearDf <= maxVal]
        # intersect = list(set(yearDf.columns) & set(nameList))
        shcodes = list(yearDf.sort_values(ascending=ascending).head(num).index)
        # nameList = list(factordf[factor].loc[shcodes]['종목코드'])
        intersect = list(set(targetdf.columns) & set(shcodes))
        return intersect
    
    def calculateFactorList(self, shares, nameList):
        rate = pd.Series([1/len(nameList)]*len(nameList), index=nameList)
        shares.investRate = rate
        shares.perMoneyRate = 1

    def buy(self, shares, wallet, buyDate, valuedf):
        money = shares.investMoney
        rateMoney = shares.investRate * shares.investMoney
        stockWallet = wallet.stockWallet
        # stockWallet = pd.DataFrame()
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
        #구매
        start1 = time.time()
        for col in rateMoney.index:
            rMoney = rateMoney[col]
            sValue = stockValue[col]
            while (rMoney - sValue) > 0:
                if col in stockWallet.columns and buyDate in stockWallet.index:
                    a = stockWallet.at[buyDate, col]
                    stockWallet.at[buyDate, col] = a + 1
                money -= sValue
                rMoney -= sValue
        print("time :", time.time() - start1)  # 현재시각 - 시작시간 = 실행 시간
        wallet.stockWallet = stockWallet
        shares.restMoney += money
        print('투자리스트:',shares.name)
        print('=================================================')
        print('investNum', len(rateMoney.index), '투자금 합계: ',rateMoney.sum() - money)
        print(list(rateMoney.index))
        print('=================================================')

    def restInvestBuy(self, buyDate, valuedf, money, wallet):
        bondValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][valuedf.columns[0]]
        stockNum = 0
        while bondValue < money:
            money -= bondValue
            stockNum += 1
        wallet.bondNum = stockNum
        wallet.restMoney = money

class Shares:
    def __init__(self, name, shareNum, moneyRate, shareList):
        self.name = name
        self.shareNum = shareNum
        self.moneyRate = moneyRate
        self.shareList = shareList
        self.investRate = None
        self.perMoneyRate = None
        self.momentum = None
    
    def calculateInvestMoney(self, sumMoneyRate, stockMoney):
        perMoney = self.perMoneyRate if self.perMoneyRate else 1
        self.investMoney = self.moneyRate/sumMoneyRate * stockMoney * perMoney
        self.restMoney = self.moneyRate/sumMoneyRate * stockMoney * (1 - perMoney)
    def setMomentum(self, momentum):
        self.momentum = momentum
    def setFactor(self, factor):
        self.factor = factor

    @staticmethod
    def toNameList(dictList):
        return list(set([ dic['Name'] for dic in dictList ]))

class MomentumStrategy:
    def __init__(self, cashRate=0, mNum=6, mUnit='M', mementumLimit=0, limit12=False):
        self.cashRate = cashRate
        self.mNum = mNum
        self.mUnit = mUnit
        self.mementumLimit = mementumLimit
        self.limit12 = limit12

class FactorStrategy:
    def __init__(self, cashRate=0, factors=[{'name':'per', 'num': 30, 'ascending':True}]):
        self.cashRate = cashRate
        self.factors = factors
# class LosscutStrategy:
    # def __init__(self, losscut=0):
        # self.losscut = losscut

class AssetGroup:
    def __init__(self, stockTransaction):
        self.assetGroup = []
        self.st = stockTransaction
    def addShares(self, shares):
        if type(shares) is list:
            for share in shares:
                self.assetGroup.append(share)
        else:
            self.assetGroup.append(shares)
    def calculateAllInvestMoney(self,wallet):
        if len(self.assetGroup) <= 0:
            print('투자리스트가 없습니다')
        # vals = [shares.moneyRate for shares in self.assetGroup]
        sumMoneyRate = sum(shares.moneyRate for shares in self.assetGroup)
        # sumMoneyRate = reduce(lambda sumVal, newVal: sumVal+newVal.moneyRate, vals)
        for shares in self.assetGroup:
            shares.calculateInvestMoney(sumMoneyRate, wallet.stockMoney)
    def buyAll(self, wallet, current, topdf):
        for shares in self.assetGroup:
            self.st.buy(shares, wallet, current, topdf)
    def getRestMoney(self, wallet):
        return sum(shares.restMoney for shares in self.assetGroup) + wallet.restMoney
        # return reduce(lambda sumVal, newVal: sumVal + newVal.restMoney, self.assetGroup) + wallet.restMoney
    def getInvestTargets(self):
        sumTargets = []
        for shares in self.assetGroup:
            sumTargets += list(shares.investRate.index)
        return list(set(sumTargets))
    def setMomentumRate(self, current, topdf):
        for shares in self.assetGroup:
            if shares.momentum:
                momentum = shares.momentum
                self.st.setMonmentumRate(shares, current, topdf, cashRate=momentum.cashRate, mNum=momentum.mNum, mUnit=momentum.mUnit, mementumLimit=momentum.mementumLimit, limit12=momentum.limit12)
    def setFactorRate(self, current, topdf, factordf, factor):
        for shares in self.assetGroup:
            if shares.factor:
                self.st.setFactorRate(shares, current, topdf, factordf, factor=factor)
    
    def recordBeforeHold(self, buydf):
        for shares in self.assetGroup:
            shares.stockHoldMoney = buydf[shares.investRate.index].dropna(axis=0, how='all')
            shares.stockHoldMoney = shares.stockHoldMoney[shares.stockHoldMoney > 0]
            # shares.stockHoldMoney = shares.stockHoldMoney[shares.stockHoldMoney>0]
    def calYield(self, buydf, cutlist):
        for shares in self.assetGroup:
            target = buydf[shares.investRate.index].dropna(axis=0, how='all')
            target = target[target > 0]
            # print(buydf[shares.investRate.index].sum())
            intersect = list(set(shares.stockHoldMoney.index) & set(cutlist))
            stockHoldMoney = shares.stockHoldMoney.drop(intersect, axis=0)
            print(stockHoldMoney.sum())
            print(target.sum())
            shares.yie = target.sum() / stockHoldMoney.sum()
            if np.isnan(shares.yie):
                shares.yie = 0.0
            print(shares.name,':',shares.yie)
class Wallet:
    def __init__(self):
        self.stockWallet = pd.DataFrame()
        self.moneyWallet = pd.DataFrame()
        self.stockMoney = 0
        self.restMoney = 0
        self.bondNum = 0
    
    def calculateLosscutRate(self, current, topdf, name):
        target = topdf[name]
        currentloc = topdf.index.get_loc(current, method='nearest')
        before = current + pd.Timedelta(-1, unit='M')
        beforeloc = topdf.index.get_loc(before, method='nearest')
        beforedf = target.iloc[beforeloc:currentloc]
        return 1 - (beforedf.max() - beforedf.min()) / beforedf.mean()

    def goOneMonthAndlossCut(self, current, topdf, allIndex, ag):
        nextDate = current + pd.Timedelta(1, unit='M')
        indexloc = topdf.index.get_loc(current, method='nearest')
        firstValue = topdf.iloc[indexloc][allIndex] 
        # print(self.stockWallet.iloc[-1])
        firstBuyMoney = (self.stockWallet.iloc[-1] * firstValue).dropna(axis=0, how='all')
        firstBuyMoney = firstBuyMoney[firstBuyMoney > 0]
        # firstBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * firstValue).values], index=[current], columns=self.stockWallet.columns)
        ag.recordBeforeHold(firstBuyMoney)
        cutlist=[]
        indexloc+=1
        dfSize = len(topdf.index)
        breaker = False
        while nextDate > current:
            # beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex] 
            # beforeBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=self.stockWallet.columns)
            # self.moneyWallet = pd.concat([self.moneyWallet, beforeBuyMoney], sort=False)
            #하루지나감 어렵다
            if dfSize -1 <= indexloc:
                print('sizeFull')
                breaker = True
                break
            current = topdf.index[indexloc]
            if nextDate <= current:
                current = topdf.index[indexloc - 1]
                break
            dateIndex = self.stockWallet.index.get_loc(current, method='ffill')
            # buyTargets = self.stockWallet.loc[:,self.stockWallet.iloc[dateIndex]>0].columns
            
            stockValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex]
            
            buyMoney = (self.stockWallet.iloc[-1] * stockValue).dropna(axis=0, how='all')
            buyMoney = buyMoney[buyMoney > 0]
            
            returnRate = buyMoney/firstBuyMoney
            intersect = list(set(returnRate.index) & set(allIndex))
            returnRate = returnRate[intersect]
            returnRate = returnRate.dropna(axis=0, how='all')
            losscutlate = pd.Series(index=returnRate.index)
            for idx in list(losscutlate.index):
                losscutlate.at[idx] = self.calculateLosscutRate(current, topdf, idx)
            returnRate = returnRate[returnRate <= losscutlate]
            returnRate = returnRate.dropna(axis=0, how='all')
            intersect = list(set(returnRate.index) & set(cutlist))
            returnRate = returnRate.drop(intersect, axis=0)
            
            #cutlist를 returnRate있게 걸러야함
            for col in returnRate.index:
                if col in cutlist:
                    continue
                cutlist.append(col)
                # print('1',self.stockWallet.iloc[dateIndex])
                # print('2',stockValue)
                self.restMoney += self.stockWallet.iloc[dateIndex][col] * stockValue[col]
                # restStockSellMoney += stockValue[col]
            indexloc+=1
        print('losscut',current, len(cutlist), cutlist)
        intersect = list(set(self.stockWallet.columns) & set(cutlist))
        dropStockWallet = self.stockWallet.drop(intersect, axis=1)
        dropStockValue = stockValue.drop(intersect, axis = 0)

        # print('dropStockWallet', dropStockWallet.iloc[-1][dropStockValue.index])
        # print('dropStockValue', dropStockValue)
        # print('restStockSellMoney', restStockSellMoney)
        dropStockValue = dropStockValue.fillna(value=0.0)
        ag.calYield( dropStockWallet.iloc[-1][dropStockValue.index] * dropStockValue, cutlist )
        self.stockMoney = ( dropStockWallet.iloc[-1][dropStockValue.index] * dropStockValue ).values.sum()
            # beforeBuyMoney * buyMoney / beforeBuyMoney
        
        return current, breaker

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

# In[5]: 기본 설정
money = 2000000
current = pd.to_datetime(now, format='%Y-%m-%d')
st = StockTransaction.create()
domesticList = codeName.keys()
domestic = Shares('국내 주식 코스피', shareNum=200, moneyRate=1, shareList=domesticList)
ag = AssetGroup(st)
ag.addShares([domestic])
# In[6]: 투자 종목선정
target = list(topDf.columns)
target = st.getMomentumList(domestic, current, topDf[target], mNum=2, mUnit='M', limit=1000, minVal=0)
target = st.getFactorList(domestic, current, topDf[target], factorDf, 'pcr', True, 50)
target = st.getFactorList(domestic, current, topDf[target], factorDf, 'per', True, 30, 0.1, 10)
st.calculateFactorList(domestic, target)

domestic.investRate.to_excel('output.xlsx',sheet_name='2019-07-07')

# for item in list(domestic.investRate.index):
    # print(codeName[item], domestic.investRate[item])

# In[7]: 손절 퍼센티지
wallet = Wallet()
losscutlate = pd.Series(index=domestic.investRate.index)
for idx in list(losscutlate.index):
    losscutlate.at[idx] = wallet.calculateLosscutRate(current, topDf, idx)
for item in list(losscutlate.index):
    print(codeName[item], losscutlate[item])
    

#%%
