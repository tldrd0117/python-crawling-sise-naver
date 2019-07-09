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
startDateStr = '2008-01-01'
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
# dfs['per'][2018].sort_values()

# In[24]: load

#시가총액순 종목
topcap = sl.load(sl.makeName('TOPCAP', '2007-01-01', '2019-12-31'))

#시가
targetShares = {}
for index, row  in topcap.iterrows():
    targetShares[row['Code']] = row['Name']
#종목별 종가
topcapdf = sl.loadStockFromDict(sl.makeName('SHARETOPCAP', beforeStr='2006-01-01', endDateStr='2019-12-31'), targetShares, '2005-12-31', '2019-12-31')
topcapdf.index = topcapdf.index.map(lambda dt: pd.to_datetime(dt.date()))
topdf = topcapdf
kospidf = sl.loadDomesticIndex(sl.makeName('KOSPI', '2005-12-31', '2019-12-31'), '2005-12-31', '2019-12-31')

# topdf
# topcapdf.loc['2012-01-01':endDateStr]
# In[9]: look
topcap[topcap['Name']=='삼성전자'].iloc[0].Code


# In[10]: topdf => 종목코드로
# topdf.columns = [topcap[topcap['Name']==column].iloc[0].Code for column in list(topdf.columns)]
# print(topdf.columns)
topdf

# In[11]: pcr 전년대비

pcrdf = factordf['pcr']
compdf = pcrdf.shift(-1, axis=1)
compdf['종목명'] = np.nan
compdf['결산월'] = np.nan
compdf['단위'] = np.nan
pcrdf-compdf

# In[12]: 투자 및 재무활동비율 구하기
pcrdf = factordf['pcr']
salesdf = factordf['영업활동으로인한현금흐름']
investdf = factordf['투자활동으로인한현금흐름']
findf = factordf['재무활동으로인한현금흐름']
factordf['투자활동으로인한현금흐름2']=pcrdf.iloc[:,3:]*salesdf.iloc[:,3:]/investdf.iloc[:,3:]
factordf['재무활동으로인한현금흐름2']=pcrdf.iloc[:,3:]*salesdf.iloc[:,3:]/findf.iloc[:,3:]
factordf['투자활동으로인한현금흐름2']['종목명'] = investdf['종목명']
factordf['재무활동으로인한현금흐름2']['종목명'] = findf['종목명']
    


#%%
