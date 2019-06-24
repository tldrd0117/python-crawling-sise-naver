from urllib.request import urlopen
import bs4
from functools import reduce
import itertools
from crawler.data.NaverResultData import NaverResultData
from crawler.data.NaverDate import NaverDate
    
class NavarSearchCodeCrawler:
    @staticmethod
    def create(targetName):
        newCrawler = NavarSearchCodeCrawler()
        newCrawler.targetName = targetName
        return newCrawler

    def __init__(self):
        pass
    def makeUrl(self, pageNo):
        return 'https://finance.naver.com/search/searchList.nhn?query=%s&page=%s' % (self.targetName, str(pageNo))

    def crawling(self):
        pageNo = 1
        data = []
        isRunning = True
        while(isRunning):
            text = urlopen(self.makeUrl(pageNo)).read()
            soup = bs4.BeautifulSoup(text, 'lxml')
            table = soup.find(class_='tbl_search')
            #table 자식
            # rows = filter(lambda val : type(val) == bs4.element.Tag, table.children)
            # #자식들에서 td태그를 찾음
            # tds = map(lambda row: row.find_all('td'), list(rows))
            # #1차원으로 변경
            # flattenTds = list(itertools.chain(*tds))
            # #없는 자식들 제거
            # tdsf = filter(lambda td: type(td) == bs4.element.Tag, flattenTds )

            topPageNo = 0
            for a in soup.find_all('a', href=True):
                href = str(a['href'])
                name = a.string
                if href.startswith('/item/main.nhn?code='):
                    data.append({'Code':href.replace('/item/main.nhn?code=', ''),'Name':name})
                if href.startswith('/search/searchList.nhn?query='+self.targetName+'&page='):
                    num = href.replace('/search/searchList.nhn?query='+self.targetName+'&page=', '')
                    if num.isdecimal() and topPageNo < int(num):
                        topPageNo = int(num)
            curPage = int(soup.find('a', class_='on').string)
            if curPage < topPageNo:
                pageNo += 1
            else:
                break
        return data


