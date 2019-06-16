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

# In[2]: font 설정
import matplotlib.font_manager as fm
import matplotlib as mpl
import matplotlib.pyplot as plt

path = '/Library/Fonts/NanumBarunGothicLight.otf'
font_name = fm.FontProperties(fname=path, size=18).get_name()
print(font_name)
mpl.rc('font', family=font_name) 

# In[3]: test 
# prices = dict()
# date = NaverDate.create(startDate='1997-06-01')
# crawler = NaverStockCrawler.create('035720', logging=True)
# data = crawler.crawling(date)
# prices['카카오'] = { pd.to_datetime(item.date, format='%Y-%m-%d') : item.close for item in data }
# topdf = pd.DataFrame(prices)
# topdf
crawler = NavarSearchCodeCrawler.create('KODEX')
data = crawler.crawling()
data

#%%
