
# In[1]: Import
from crawler.NaverCrawler import NaverCrawler
from crawler.NaverWorldCrawler import NaverWorldCrawler
from crawler.NaverTopMarketCapCrawler import NaverTopMarketCapCrawler
from crawler.NaverCapFromCodeCrawler import NaverCapFromCodeCrawler
from crawler.NaverStockCrawler import NaverStockCrawler
from crawler.NavarSearchCodeCrawler import NavarSearchCodeCrawler
from crawler.NaverPbrCrawler import NaverPbrCrawler
from crawler.DartCrawler import DartCrawler

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
startDateStr = '2008-05-01'
endDateStr = '2019-12-31'
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
    def loadDartData(self, topcap):
        name = 'DART_'+ '2007-01-01_2019-12-31.h5'
        if not os.path.isfile(name):
            targets = []
            for index, row  in topcap.iterrows():
                value = {'Code': row['Code'], 'Name': row['Name']}
                if not value in targets:
                    targets.append(value)
            df = pd.DataFrame(columns=['종목코드','종목명','당기순이익', '자본총계', '주식수', '시가총액'])
            for target in targets:
                print(target)
                dartCrawler = DartCrawler.create(target, '2007-01-01', '2019-12-31')
                data = dartCrawler.crawling()
                if not data:
                    continue
                newdf = pd.DataFrame(columns=['종목코드','종목명','당기순이익', '자본총계', '주식수', '시가총액'])
                for v in data:
                    date = pd.to_datetime(v['date'], format='%Y.%m')
                    marcap = topcap[topcap['Code']==target['Code']]
                    if date.year in marcap.index.year:
                        marcap = marcap[str(date.year)]['Marcap'].values[0]
                    else:
                        marcap = None
                    #append로 변경해야함
                    newdf.loc[date] = [v['Code'], v['Name'],v['profit'], v['total'], v['stockNum'], marcap]
                print(newdf)
                time.sleep(0.5)
                df = pd.concat([df,newdf])
                # values[target['Name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
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
    
    def loadFactor(self):
        upCodes = ['제조업', '은행업', '증권업', '보험업', '종합금융업', '여신전문금융업', '신용금고']
        factors = ['per', 'pcr', 'pbr', 'roe', '당기순이익', '영업활동으로인한현금흐름', '투자활동으로인한현금흐름', '재무활동으로인한현금흐름']
        dfs = {}
        for upCode in upCodes:
            for factor in factors:
                name = 'fin/'+upCode+'_'+factor+'.xlsx'
                df = pd.read_excel(name,sheet_name='계정별 기업 비교 - 특정계정과목', skiprows=8)
                df.columns = list(df.iloc[0])
                df = df.drop([0])
                df = df.set_index("종목코드")
                if factor not in dfs:
                    dfs[factor] = pd.DataFrame()
                dfs[factor] = pd.concat([dfs[factor], df])
        return dfs
    

sl = StockLoader.create()
# In[22]: 재무제표
factordf = sl.loadFactor()
pcrdf = factordf['pcr']
salesdf = factordf['영업활동으로인한현금흐름']
investdf = factordf['투자활동으로인한현금흐름']
findf = factordf['재무활동으로인한현금흐름']
factordf['투자활동으로인한현금흐름2']=pcrdf.iloc[:,3:]*salesdf.iloc[:,3:]/investdf.iloc[:,3:]
factordf['재무활동으로인한현금흐름2']=pcrdf.iloc[:,3:]*salesdf.iloc[:,3:]/findf.iloc[:,3:]
factordf['투자활동으로인한현금흐름2']['종목명'] = investdf['종목명']
factordf['재무활동으로인한현금흐름2']['종목명'] = findf['종목명']


pcrdf = factordf['영업활동으로인한현금흐름']
compdf = pcrdf.shift(-1, axis=1)
compdf['종목명'] = np.nan
compdf['결산월'] = np.nan
compdf['단위'] = np.nan
targetdf = pcrdf-compdf
targetdf['종목명'] = pcrdf['종목명']
factordf['영업활동으로인한현금흐름증가율'] = targetdf
# dfs['per'][2018].sort_values()
# In[22]: getETF
KODEX = sl.loadSearchCodeName('KODEX')
TIGER = sl.loadSearchCodeName('TIGER')
KOSEF = sl.loadSearchCodeName('KOSEF')


# In[23]: ETF 분할
#KODEX 종목 (삼성자산운용)
blackWords = ['액티브', '삼성']
bondWords = [' 국고채', ' 국채']
foreignWords = ['미국', '대만', '중국', '심천', '선진국', '일본', 'China', '글로벌', '차이나', '라틴', '유로', '인도', '하이일드']
inverseWords = ['인버스']
productWords = ['원유', '골드선물', '금선물', '은선물', '달러선물', '농산물', '금속선물', '금은선물', '엔선물', '구리선물', '구리실물', '콩선물']
KODEX = sl.exceptCodeName(blackWords, KODEX)
KODEX_bond = sl.chooseCodeName(bondWords, KODEX)
KODEX_foreign = sl.chooseCodeName(foreignWords, KODEX)
KODEX_domestic = sl.exceptCodeName(bondWords + foreignWords + inverseWords + productWords, KODEX)
KODEX_exceptProduct = sl.exceptCodeName(productWords + foreignWords, KODEX)
KODEX_inverse = sl.chooseCodeName(inverseWords, KODEX_exceptProduct)
KODEX_product = sl.chooseCodeName(productWords, KODEX)


#TIGER 종목 (미래에셋대우)
TIGER = sl.exceptCodeName(blackWords, TIGER)
TIGER_bond = sl.chooseCodeName(bondWords, TIGER)
TIGER_foreign = sl.chooseCodeName(foreignWords, TIGER)
TIGER_domestic = sl.exceptCodeName(bondWords + foreignWords + inverseWords + productWords, TIGER)
TIGER_exceptProduct = sl.exceptCodeName(productWords + foreignWords, TIGER)
TIGER_inverse = sl.chooseCodeName(inverseWords, TIGER)
TIGER_product = sl.chooseCodeName(inverseWords, TIGER)

#KOSEF 종목 (키움)
KOSEF = sl.exceptCodeName(blackWords, KOSEF)
KOSEF_bond = sl.chooseCodeName(bondWords, KOSEF)
KOSEF_foreign = sl.chooseCodeName(foreignWords, KOSEF)
KOSEF_domestic = sl.exceptCodeName(bondWords + foreignWords + inverseWords + productWords, KOSEF)
KOSEF_exceptProduct = sl.exceptCodeName(productWords + foreignWords, KOSEF)
KOSEF_inverse = sl.chooseCodeName(inverseWords, KOSEF_exceptProduct)
KOSEF_product = sl.chooseCodeName(productWords, KOSEF)


# In[24]: load

#시가총액순 종목
topcap = sl.load(sl.makeName('TOPCAP', '2007-01-01', '2019-12-31'))

#시가
targetShares = {}
for index, row  in topcap.iterrows():
    targetShares[row['Code']] = row['Name']
#종목별 종가
# etfdf = sl.loadStockFromArr(sl.makeName('ETF2', endDateStr='2019-12-31'), KODEX + TIGER + KOSEF, beforeStr, '2019-12-31')
topcapdf = sl.loadStockFromDict(sl.makeName('SHARETOPCAP', beforeStr='2006-01-01', endDateStr='2019-12-31'), targetShares, '2005-12-31', '2019-12-31')
# etfdf.index = etfdf.index.map(lambda dt: pd.to_datetime(dt.date()))
# topcapdf.index = topcapdf.index.map(lambda dt: pd.to_datetime(dt.date()))
# topdf = pd.concat([etfdf,topcapdf], sort=False, axis=1)
topdf = topcapdf#pd.concat([etfdf,topcapdf], sorst=False, axis=1)

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
        latelyValue = oneYearDf.iloc[-1]
        momentum = pd.DataFrame(latelyValue.values - oneYearDf.values, oneYearDf.index, oneYearDf.columns)
        # momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        momentumValues = momentum.values
        momentumValues[momentumValues>0] = 1
        momentumValues[momentumValues<=0] = 0
        momentumScore = pd.DataFrame(momentumValues, momentum.index, momentum.columns)
        # momentumScore = momentumScore.query('')
        # momentumScore = momentumScore[momentumScore >= minVal]
        
        return list(momentumScore.mean().sort_values(ascending=False).head(limit).index)
        
    
    def getFactorList(self, shares, current, targetdf, factordf, factor, ascending, num, minVal=-10000000, maxVal=10000000):
        yearDf = factordf[factor][factordf[factor]['종목명'].isin(list(targetdf.columns))]
        if current.month > 4:
            yearDf = yearDf[current.year - 1]
        else:
            yearDf = yearDf[current.year - 2]
        yearDf = yearDf[yearDf >= minVal]
        yearDf = yearDf[yearDf <= maxVal]
        # intersect = list(set(yearDf.columns) & set(nameList))
        shcodes = list(yearDf.sort_values(ascending=ascending).head(num).index)
        nameList = list(factordf[factor].loc[shcodes]['종목명'])
        intersect = list(set(targetdf.columns) & set(nameList))
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
        for col in rateMoney.index:
            rMoney = rateMoney[col]
            sValue = stockValue[col]
            while (rMoney - sValue) > 0:
                if col in stockWallet.columns and buyDate in stockWallet.index:
                    a = stockWallet.at[buyDate, col]
                    stockWallet.at[buyDate, col] = a + 1
                money -= sValue
                rMoney -= sValue
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
        self.losscutDf = pd.DataFrame(columns=['갯수', '평균', '전체평균'])
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
            comp = shares.stockHoldMoney > 0
            shares.stockHoldMoney = pd.Series(shares.stockHoldMoney.values[comp], shares.stockHoldMoney.index[comp])
            # shares.stockHoldMoney = shares.stockHoldMoney[shares.stockHoldMoney>0]
    def calYield(self, buydf, cutlist):
        for shares in self.assetGroup:
            target = buydf[shares.investRate.index].dropna(axis=0, how='all')
            target = target[target > 0]
            # print(buydf[shares.investRate.index].sum())
            intersect = list(set(shares.stockHoldMoney.index) & set(cutlist))
            
            self.losscutDf.loc[current] = [len(cutlist), target[intersect].mean() / shares.stockHoldMoney.mean(), target.mean() / shares.stockHoldMoney.mean()]
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
        currentloc = topdf.index.get_loc(current, method='ffill')
        before = current + pd.Timedelta(-1, unit='M')
        beforeloc = topdf.index.get_loc(before, method='ffill')
        beforedf = target.iloc[beforeloc:currentloc]
        # return 1 - (((beforedf.max() - beforedf.min()) / beforedf.mean())*1)
        return 0

    def goOneMonthAndlossCut(self, current, topdf, allIndex, ag):
        nextDate = current + pd.Timedelta(1, unit='M')
        indexloc = topdf.index.get_loc(current, method='ffill')
        firstValue = topdf.iloc[indexloc][allIndex] 
        # print(self.stockWallet.iloc[-1])
        firstBuyMoney = (self.stockWallet.iloc[-1] * firstValue).dropna(axis=0, how='all')
        # firstBuyMoney = firstBuyMoney[firstBuyMoney > 0]
        # firstBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * firstValue).values], index=[current], columns=self.stockWallet.columns)
        ag.recordBeforeHold(firstBuyMoney)
        cutlist=[]
        indexloc+=1
        dfSize = len(topdf.index)
        breaker = False
        time1 = time.time()
        
        while nextDate > current:
            # beforeValue = topdf.iloc[topdf.index.get_loc(current, method='nearest')][allIndex] 
            # beforeBuyMoney = pd.DataFrame([(self.stockWallet.iloc[-1] * beforeValue).values], index=[current], columns=self.stockWallet.columns)
            # self.moneyWallet = pd.concat([self.moneyWallet, beforeBuyMoney], sort=False)
            if dfSize -1 <= indexloc:
                print('sizeFull')
                breaker = True
                break
            current = topdf.index[indexloc]
            if nextDate <= current:
                current = topdf.index[indexloc - 1]
                break
            dateIndex = self.stockWallet.index.get_loc(current, method='ffill')
            latelyWallet = self.stockWallet.iloc[-1].dropna(axis=0, how='all') 
            stockValue = topdf.iloc[topdf.index.get_loc(current, method='ffill')][latelyWallet.index]
            # print(self.stockWallet.iloc[-1].values)
            # print(stockValue.values)
            buyValues = latelyWallet.values * stockValue.values
            # buyValues = buyValues[buyValues > 0]
            # print(elf.stockWallet.iloc[-1])
            assert latelyWallet.index.equals(stockValue.index), '#####인덱스가 다른데요?'
            
            buyMoney = pd.Series(buyValues, stockValue.index).dropna(axis=0, how='all')
            intersect = list((set(buyMoney.index)).difference(set(cutlist)))
            returnRate = pd.Series(buyMoney.values/firstBuyMoney.values, index = buyMoney.index)
            returnRate = returnRate[intersect].dropna(axis=0, how='all')
            losscutlate = pd.Series(index=returnRate.index)
            for idx in list(losscutlate.index):
                losscutlate.at[idx] = self.calculateLosscutRate(current, topdf, idx)
            returnValues = returnRate.values <= losscutlate.values
            if np.where(returnValues)[0].size > 0:
                for col in returnRate.index[returnValues]:
                    if col in cutlist:
                        continue
                    cutlist.append(col)
                    self.restMoney += self.stockWallet.iloc[dateIndex].at[col] * stockValue.at[col]
            # intersect = list(set(returnRate.index) & set(cutlist))
            # returnRate = returnRate.drop(intersect, axis=0)
            #cutlist를 returnRate있게 걸러야함
            indexloc+=1
        print('losscut',current, len(cutlist), cutlist)
        intersect = list(set(self.stockWallet.columns) & set(cutlist))

        # print('dropStockWallet', dropStockWallet.iloc[-1][dropStockValue.index])
        # print('dropStockValue', dropStockValue)
        # print('restStockSellMoney', restStockSellMoney)
        # dropStockValue = dropStockValue.fillna(value=0.0)
        latelyWallet = self.stockWallet.iloc[-1].dropna(axis=0, how='all') 
        stockValue = topdf.iloc[topdf.index.get_loc(current, method='ffill')][latelyWallet.index]

        ag.calYield( latelyWallet * stockValue, cutlist )
        
        dropStockWallet = latelyWallet.drop(intersect, axis=0)
        dropStockValue = stockValue.drop(intersect, axis = 0)
        
        self.stockMoney = ( dropStockWallet * dropStockValue ).values.sum()
            # beforeBuyMoney * buyMoney / beforeBuyMoney
        print('시간흐름:', time.time() - time1)
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
        
#투자금
firstMoney = 10000000
money = firstMoney
#현금비율
rebalaceRate = 0

current = startDate

st = StockTransaction.create()
bondETFList = Shares.toNameList(KODEX_bond+TIGER_bond+KOSEF_bond)
foreignETFList = Shares.toNameList(KODEX_foreign+TIGER_foreign+KOSEF_foreign)
inverseETFList = Shares.toNameList(KODEX_inverse+TIGER_inverse+KOSEF_inverse)
domesticETFList = Shares.toNameList(KODEX_domestic+TIGER_domestic+KOSEF_domestic)
#domesticList = Shares.toNameList(KODEX_domestic+TIGER_domestic)
domesticList = list(topcap[str(current.year)]['Name'])


# bondListNum = 3 #int(len(KODEX_bond+TIGER_bond) * 3 / 10)
# foreignListNum = 5 #int(len(KODEX_foreign+TIGER_foreign) * 3 / 10)
# domesticListNum = 100#int(len(KODEX_domestic+TIGER_domestic) * 3 / 10)

# print(bondETFNum, foreignETFNum, inverseETFNum,domesticETFNum,domesticNum)

wallet = Wallet()
moneySum = pd.DataFrame()

bondETF = Shares('채권', shareNum=1, moneyRate=0, shareList=bondETFList)
# foreignETF = Shares('외국 ETF', shareNum=5, moneyRate=1, shareList=foreignETFList)
# inverseETF = Shares('인버스 ETF', shareNum=5, moneyRate=1, shareList=inverseETFList)
# domesticETF = Shares('국내 ETF', shareNum=10, moneyRate=1, shareList=domesticETFList)
domestic = Shares('국내 주식 코스피', shareNum=200, moneyRate=1, shareList=domesticList)
# domestic.setFactor(FactorStrategy(factors=[{'name':'per', 'num': 30, 'ascending': True}]))
# bondETF.setMomentum(MomentumStrategy(cashRate=0, mNum=12, mUnit='M', mementumLimit=0))
# foreignETF.setMomentum(MomentumStrategy(cashRate=0, mNum=6, mUnit='M', mementumLimit=0, limit12=True))
# inverseETF.setMomentum(MomentumStrategy(cashRate=0, mNum=3, mUnit='M', mementumLimit=0.25, limit12=False))
# domesticETF.setMomentum(MomentumStrategy(cashRate=0, mNum=6, mUnit='M', mementumLimit=0, limit12=True))
# domestic.setMomentum(MomentumStrategy(cashRate=0.5, mNum=6, mUnit='M', mementumLimit=0.25, limit12=True))


# foreign = Shares('foreign', shareNum=foreignListNum, moneyRate=1, shareList=foreignList)
# domestic = Shares('domestic', shareNum=domesticListNum, moneyRate=1, shareList=list(topcap[str(current.year)]['Name']))

ag = AssetGroup(st)
ag.addShares([domestic])
# ag.addShares([bondETF, foreignETF, inverseETF, domesticETF, domestic])

while endDate > current:
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    print('simulate...', current)
    start1 = time.time()

    # plusMoney = 500000
    # print(plusMoney,'씩 적립')
    # money+=plusMoney
    
    domestic.shareList = list(topcap[str(current.year)]['Name'])
    wallet.stockMoney = money * (1-rebalaceRate)
    wallet.restMoney = money * rebalaceRate
    stockRestMoney = 0

    #해당돼는 날짜(Current)의 종목별 모멘텀 평균을 구한다
    # ag.setMomentumRate(current, topdf)
    # ag.setFactorRate(current, topdf, factordf, 'per')
    target = list(topdf.columns)
    # target = st.getMomentumList(domestic, current, topdf[target], mNum=12, mUnit='M', limit=500, minVal=0)
    target = st.getMomentumList(domestic, current, topdf[target], mNum=2, mUnit='M', limit=1000, minVal=0)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'pbr', True, 100)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'pcr', True, 750)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'per', True, 562, minVal=0.000001)
    # target = st.getMomentumList(domestic, current, topdf[target], mNum=4, mUnit='M', limit=421, minVal=0)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'pcr', True, 421)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'per', True, 315, minVal=0.000001)
    # target = st.getMomentumList(domestic, current, topdf[target], mNum=8, mUnit='M', limit=236, minVal=0)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'pcr', True, 176)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'per', True, 132, minVal=0.000001)
    # target = st.getMomentumList(domestic, current, topdf[target], mNum=12, mUnit='M', limit=99, minVal=0)
    target = st.getFactorList(domestic, current, topdf[target], factordf, 'pcr', True, 50)
    target = st.getFactorList(domestic, current, topdf[target], factordf, 'per', True, 30, minVal=0.000001)
    
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'pbr', False, 41)

    # target = st.getFactorList(domestic, current, topdf[target], factordf, '투자활동으로인한현금흐름2', False, 200)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, '재무활동으로인한현금흐름2', False, 100)

    # if current > pd.to_datetime('2009-05-01', format='%Y-%m-%d'):
        # print('ok')
        # target = st.getFactorList(domestic, current, topdf[target], factordf, '영업활동으로인한현금흐름증가율', False, 1000, minVal=0)
    
    # target = st.getMomentumList(domestic, current, topdf[target], mNum=2, mUnit='M', limit=100, minVal=0)




    
    # target = st.getFactorList(domestic, current, topdf[target], factordf, 'roe', True, 30)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, '영업활동으로인한현금흐름', False, 39)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, '투자활동으로인한현금흐름', True, 20)
    # target = st.getFactorList(domestic, current, topdf[target], factordf, '재무활동으로인한현금흐름', True, 30)
    st.calculateFactorList(domestic, target)
    # st.calculateFactorList(bondETF, ['KODEX 국고채3년','KOSEF 국고채10년'])
    #TARGET
    ag.calculateAllInvestMoney(wallet)
    ag.buyAll(wallet, current, topdf)
    wallet.restMoney = ag.getRestMoney(wallet)
    #사고남은돈 + 지갑에 남은돈
    allIndex = ag.getInvestTargets()
    # st.restInvestBuy(current, bonddf, wallet.restMoney, wallet)
    current, breaker = wallet.goOneMonthAndlossCut(current, topdf, allIndex, ag)

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
    print("걸린시간 :", time.time() - start1)  # 현재시각 - 시작시간 = 실행 시간
    print('=================================================')
    print('total', money, wallet.stockMoney, wallet.restMoney)
    print('=================================================')
    if breaker:
        break


# print('##소유주식', wallet.stockWallet)
# print('##주식가격', wallet.moneyWallet)
print('##손절',ag.losscutDf)
print('##Total', moneySum)

# In[7] 정리
# moneySum = moneySum[:-1]
moneySum

# In[6]: 통계
moneySum.index = moneySum.index.map(lambda dt: pd.to_datetime(dt.date()))
print(moneySum['total'].iloc[0])
portfolio = moneySum['total'] / firstMoney
투자기간 = len(moneySum.index)/12
print(투자기간)
# print(portfolio)
e = pd.date_range(start=portfolio.index[12], periods=투자기간, freq=pd.DateOffset(years=1))
d = [ portfolio.index.get_loc(date, method='nearest')for date in e]
print(portfolio[d]/portfolio[d].shift(1))
# print((portfolio[d]**(1/12))*100-100)
print((portfolio/portfolio.shift(1)).sum()/len(portfolio.index))
print(portfolio[-1]/portfolio.std())
print((portfolio/portfolio.shift(1)))
# print(portfolio.std())

# In[7]: 통계 결과

# print('연간 수익률', pe)
print('연평균 수익률',((portfolio[-1]**(1/투자기간))*100-100))

print('최대 하락률',((portfolio - portfolio.shift(1))/portfolio.shift(1)*100).min())
print('최대 상승률',((portfolio - portfolio.shift(1))/portfolio.shift(1)*100).max())
# (portfolio.shift(1) - portfolio)
# (portfolio - portfolio.shift(1))/portfolio.shift(1)*100
# In[5]: kospi vs 손절
losscutdf = ag.losscutDf
kospiComp = kospidf['종가']
beforeKospiComp = kospiComp.shift(1)
kospiComp = (kospiComp - beforeKospiComp) / beforeKospiComp + 1
# print(moneySum['total'].loc[losscutdf.index])
totaldf = moneySum['stock'].loc[losscutdf.index]
beforetotaldf = totaldf.shift(1)
totalComp = (totaldf - beforetotaldf) / beforetotaldf + 1
losscutdf['실제'] = totalComp
losscutdf['코스피'] = kospiComp.loc[losscutdf.index]
print('손절승률',np.where(losscutdf['실제']>losscutdf['전체평균'])[0].size/len(losscutdf.index)*100, '%')
losscutdf

# In[7]: 그래프
# In[13]: 코스피만
kospidf['종가'].plot(figsize = (18,12), fontsize=12)

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





#123400327.99999969 losscut0.95 domestic 200 cashrate 0.2 avgmomentum 6 momentumlimit0.25 limit12 연평균 22%
#123400327.99999969보다 높음 losscut0.97 domestic 200 cashrate 0.2 avgmomentum 6 momentumlimit0.25 limit12 연평균 25%
#123400327.99999969보다 높음 losscut0.97 domestic 200 cashrate 0.2 avgmomentum 6 momentumlimit0.25 limit12 연평균 25%







#%%
