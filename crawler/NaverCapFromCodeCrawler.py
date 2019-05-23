from urllib.request import urlopen
import bs4
from functools import reduce
import itertools
from crawler.data.NaverResultData import NaverResultData
    
class NaverCapFromCodeCrawler:
    @staticmethod
    def create():
        newCrawler = NaverCapFromCodeCrawler()
        return newCrawler

    def __init__(self):
        pass
    def makeUrl(self, code):
        return 'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=%s' % (code)

    def crawling(self, code):
        #cTB11 > tbody > tr:nth-child(7) > td
        text = urlopen(self.makeUrl(code)).read()
        soup = bs4.BeautifulSoup(text, 'lxml')
        value = soup.select('#cTB11 > tbody > tr:nth-child(7) > td')[0].string.strip()
        splitValue = value.split('/')
        outstanding = self.format(splitValue[0].strip()[:-1])
        floating = self.format(splitValue[1].strip()[:-1])
        return { 'outstanding' : outstanding, 'floating': floating }
        
    def format(self, value):
        return float(value.replace(',', '').replace('%',''))

