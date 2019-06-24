# from urllib.request import urlopen
import urllib3
import bs4
from functools import reduce
import itertools
# from crawler.data.NaverStockResultData import NaverStockResultData
from crawler.data.NaverDate import NaverDate
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import pandas as pd
    
class NaverPbrCrawler:
    @staticmethod
    def create(logging=False):
        newCrawler = NaverPbrCrawler()
        newCrawler.logging = logging
        return newCrawler

    def __init__(self):
        pass
    def makeUrl(self, code):
        return 'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=%s' % (code)

    def format(self, date):
        date = date.replace('/','-')
        date = date.replace('(E)','')
        date += '-31'
        return pd.to_datetime(date, format='%Y-%m-%d')


    def crawling(self, code):
        #'C:/Users/lsj/Downloads/phantomjs-2.1.1-windows/bin/phantomjs.exe'
        driver = webdriver.PhantomJS('C:/Users/lsj/Downloads/phantomjs-2.1.1-windows/bin/phantomjs.exe')
        driver.get(self.makeUrl(code))
        text = driver.page_source
        soup = bs4.BeautifulSoup(text, 'lxml')
        columns = []
        col1 = soup.select('#bG05RlB6cn > table:nth-child(2) > thead > tr:nth-child(2) > th.r02c00.bg')[0].stripped_strings
        col2 = soup.select('#bG05RlB6cn > table:nth-child(2) > thead > tr:nth-child(2) > th.r02c01.bg')[0].stripped_strings
        col3 = soup.select('#bG05RlB6cn > table:nth-child(2) > thead > tr:nth-child(2) > th.r02c02.bg')[0].stripped_strings
        col4 = soup.select('#bG05RlB6cn > table:nth-child(2) > thead > tr:nth-child(2) > th.r02c03.bg')[0].stripped_strings
        columns.append(list(col1)[0])
        columns.append(list(col2)[0])
        columns.append(list(col3)[0])
        columns.append(list(col4)[0])

        values = []
        val1 = soup.select('#bG05RlB6cn > table:nth-child(2) > tbody > tr:nth-child(27) > td:nth-child(2) > span')[0].stripped_strings
        val2 = soup.select('#bG05RlB6cn > table:nth-child(2) > tbody > tr:nth-child(27) > td:nth-child(3) > span')[0].stripped_strings
        val3 = soup.select('#bG05RlB6cn > table:nth-child(2) > tbody > tr:nth-child(27) > td:nth-child(4) > span')[0].stripped_strings
        val4 = soup.select('#bG05RlB6cn > table:nth-child(2) > tbody > tr:nth-child(27) > td:nth-child(5) > span')[0].stripped_strings
        values.append(list(val1)[0])
        values.append(list(val2)[0])
        values.append(list(val3)[0])
        values.append(list(val4)[0])

        columns = list(map(self.format, columns))
        return pd.DataFrame(values, index=columns, columns=[code])
        #hbG05RlB6cn
        #table 자식
        # rows = filter(lambda val : type(val) == bs4.element.Tag, table.children)
        #자식들에서 td태그를 찾음
        # tds = map(lambda row: row.find_all('td'), list(rows))
        #1차원으로 변경
        # flattenTds = list(itertools.chain(*tds))
        #없는 자식들 제거
        # tdsf = filter(lambda td: type(td) == bs4.element.Tag, flattenTds )
        #텍스트 추출
        # values = map(lambda value: value.stripped_strings, tdsf)
        #1차원으로 변경
        # strings = list(itertools.chain(*values))
        #7개씩 자름
        # splitData = [strings[i:i + 7] for i in range(0, len(strings), 7)]
            

        # return {col1:per1, col2:per2, col3:per3, col4:per4}

if __name__ == "__main__":
    crawler = NaverPbrCrawler()
    data = crawler.crawling('005930')
    print(data)
