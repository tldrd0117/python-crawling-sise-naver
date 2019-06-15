
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


# print(plt.rcParams['font.family'])
# path = '/Library/Fonts/NanumBarunpenRegular.otf'
# fontprop = fm.FontProperties(fname=path, size=18)
path = '/Library/Fonts/NanumBarunGothicLight.otf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
# plt.rcParams["font.family"] = font_name
mpl.rc('font', family=font_name) # For MacOS

# mpl.rcParams['axes.unicode_minus'] = False
# plt.rcParams['font.monospace']
# plt.rcParams["font.family"] = 'Nanum Brush Script OTF'
# font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')

# ttf 폰트 전체개수
# print(len(font_list))
# fm.fontManager.ttflist
# [(f.name, f.fname) for f in fm.fontManager.ttflist if 'Nanum' in f.name]


# In[3]:

def makeDataFrame():
    crawler = NaverCrawler.create(targetName='KPI200')
    date = NaverDate.create(startDate='2019-01-02', endDate='2019-05-04')
    kospi200 = crawler.crawling(dateData=date)
    kospi200Close = { NaverDate.formatDate(item.date): item.close for item in kospi200 }

    worldDate = NaverDate.create(startDate='2019-01-02', endDate='2019-05-04')
    worldCrawler = NaverWorldCrawler.create(targetName='SPI@SPX')
    sp500 = worldCrawler.crawling(dateData=worldDate)

    sp500Close = { NaverDate.formatDate(item.date): item.close for item in sp500 }

    data = {'S&P500' : sp500Close, 'KOSPI200' : kospi200Close}
    df = pd.DataFrame(data)
    df = df.fillna(method='ffill')
    if df.isnull().values.any():
        df = df.fillna(method='bfill')
    return df

def showGraph():
    df = makeDataFrame()
    plt.figure(figsize=(10, 5))
    plt.plot(df['S&P500'] / df['S&P500'].loc[dt.date(2019,1,2)] * 100)
    plt.plot(df['KOSPI200'] / df['KOSPI200'].loc[dt.date(2019,1,2)] * 100)
    plt.legend(loc=0)
    plt.grid(True, color='0.7', linestyle=':', linewidth=1)
    # plt.show()

def showLinearRegression(df):
    df_ratio_2019_now = df.loc[dt.date(2019,1,2):] / df.loc[dt.date(2019,1,2)] * 100

    x = df_ratio_2019_now['S&P500']
    y = df_ratio_2019_now['KOSPI200']

    # 1개 칼럼 np,array로 변환
    independent_var = np.array(x).reshape(-1, 1)
    dependent_var = np.array(y).reshape(-1, 1)

    # Linear Regression
    regr = LinearRegression()
    regr.fit(independent_var, dependent_var)

    result = { 'Slope':regr.coef_[0,0], 'Intercept':regr.intercept_[0], "R^2": regr.score(independent_var, dependent_var)}
    print(result)

    #그래프
    plt.figure(figsize=(5,5))
    plt.scatter(independent_var, dependent_var, marker='.', color='skyblue')
    plt.plot(independent_var, regr.predict(independent_var), color='r', linewidth=3)
    plt.grid(True, color='0.7', linestyle=':', linewidth=1)
    plt.xlabel('S&P500')
    plt.ylabel('KOSPI200')
    plt.show()

def topK(num):
    crawler = NaverTopMarketCapCrawler.create()
    data = crawler.crawling([1,num])
    codes = [ {'code':item.code, 'name':item.name}  for item in data ]
    return codes

def k10FromDate():
    prices = dict()
    top10 = topK(10)
    date = NaverDate.create(startDate='2019-01-02', endDate='2019-05-04')
    for code in top10:
        crawler = NaverStockCrawler.create(code)
        data = crawler.crawling(date)
        prices[code] = { NaverDate.formatDate(item.date) : item.close for item in data }
    df = pd.DataFrame(prices)
    df = df.fillna(method='ffill')
    if df.isnull().values.any(): #그래도 구멍이 남아 있으면
        df = df.fillna(method='bfill')
    return df

def makeK10():
    crawler = NaverTopMarketCapCrawler.create()
    crawler2 = NaverCapFromCodeCrawler.create()
    top10 = crawler.crawling([1,10])
    outstanding = dict()
    floating = dict()
    price = dict()
    name = dict()
    for item in top10:
        result = crawler2.crawling(item.code)
        outstanding[item.code] = result['outstanding']
        floating[item.code] = result['floating']
        price[item.code] = item.price
        name[item.code] = item.name
    data = {\
            'Outstanding' : outstanding,\
            'Floating' : floating,\
            'Price': price,\
            'Name': name\
        }
    k10_info = pd.DataFrame(data)
    k10_info['f Market Cap'] = k10_info['Outstanding'] * k10_info['Floating'] * k10_info['Price'] * 0.01
    k10_info['Market Cap'] = k10_info['Outstanding'] * k10_info['Price'] * 0.01
    return k10_info

def showGraphK10():
    k10_price = k10FromDate()
    k10_info = makeK10()
    k10_historical_mc = k10_price * k10_info['Outstanding'] * k10_info['Floating']
    k10 = pd.DataFrame()
    k10['k10 Market Cap'] = k10_historical_mc.sum(axis=1)
    k10['k10'] = k10['k10 Market Cap'] / k10['k10 Market Cap'][0] * 100

    plt.figure(figsize=(10,5))
    plt.plot(k10['k10'])
    plt.legend(loc=0)
    plt.grid(True, color='0.7', linestyle=':', linewidth=1)

def showGraphK10KOSPI200():
    k10_price = k10FromDate()
    k10_info = makeK10()
    k10_historical_mc = k10_price * k10_info['Outstanding'] * k10_info['Floating']
    k10 = pd.DataFrame()
    k10['k10 Market Cap'] = k10_historical_mc.sum(axis=1)
    k10['k10'] = k10['k10 Market Cap'] / k10['k10 Market Cap'][0] * 100

    crawler = NaverCrawler.create(targetName='KPI200')
    date = NaverDate.create(startDate='2019-01-02', endDate='2019-05-04')
    kospi200 = crawler.crawling(dateData=date)
    kospi200Close = { NaverDate.formatDate(item.date): item.close for item in kospi200 }
    k200 = pd.DataFrame({'K200': kospi200Close})

    plt.figure(figsize=(10,5))
    plt.plot(k10['k10'])
    plt.plot(k200['K200'] / k200['K200'][0] * 100)
    plt.legend(loc=0)
    plt.grid(True, color='0.7', linestyle=':', linewidth=1)

# In[3]: 코스피 가져오기
crawler = NaverCrawler.create(targetName='KPI200')
date = NaverDate.create(startDate='2018-06-01')
kospi200 = crawler.crawling(dateData=date)
df = pd.DataFrame(columns=['종가', '전일비', '등락률', '거래량', '거래대금'])
for v in kospi200:
    df.loc[v.index()] = v.value()
df

# In[4]: 월 평균 값 
monthly_df = df.resample('M', how={'종가':np.mean})
monthly_df

# In[5]: 모멘텀 구하기
monthly_df['종가'][-1] - monthly_df['종가']
# In[6]: 30종목 종가 버그 있음
prices = dict()
targets = topK(30) + [{'code':"114800", 'name':'KODEX 인버스'}]
date = NaverDate.create(startDate='2018-06-01')
for target in targets:
    print(target,'collect...')
    crawler = NaverStockCrawler.create(target['code'])
    data = crawler.crawling(date)
    prices[target['name']] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
topdf = pd.DataFrame(prices)
topdf

# In[7]: 30종목 월 평균 값
monthly_topdf = topdf.resample('M').mean()
monthly_topdf


# In[8]: 30종목 모멘텀 구하기
topdfMomentum = monthly_topdf.iloc[-1] - monthly_topdf
topdfMomentumScore = topdfMomentum.applymap(lambda val: 1 if val > 0 else 0 )
print(topdfMomentumScore)
sortedValues = topdfMomentumScore.mean().sort_values(ascending=False)
choosedDf = topdf[sortedValues.head(10).index]
choosedDf['KOSPI'] = df['종가']
jisuDf = choosedDf / choosedDf.iloc[0]
plt = jisuDf.plot(figsize = (18,12), fontsize=12)
fontProp = fm.FontProperties(fname=path, size=18)
plt.legend(prop=fontProp)
print(plt)
# for index in sortedValues.head(5).index:
    # print(monthly_topdf[index] / monthly_topdf[index][0])





# In[7]: 30종목 월 평균 값








# In[7]: 30종목 월 평균 값
# topdf.to_hdf('30종목')
# In[5]:
# df2 = pd.DataFrame(index=[0,1,2,3], columns=['a','b','c','d'])
# df2.loc[0] = [1,2,3,4]
# df2.loc[1] = [5,6,7,8]
# df2.loc[2] = [9,10,11,12]
# df2.loc[3] = [13,14,15,16]
# df2.shift(-1)
    




   

    

#%%
