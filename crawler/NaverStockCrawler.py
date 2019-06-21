from urllib.request import urlopen
import bs4
from functools import reduce
import itertools
from crawler.data.NaverStockResultData import NaverStockResultData
from crawler.data.NaverDate import NaverDate
    
class NaverStockCrawler:
    @staticmethod
    def create(targetName, logging=False):
        newCrawler = NaverStockCrawler()
        newCrawler.targetName = targetName
        newCrawler.logging = logging
        return newCrawler

    def __init__(self):
        pass
    def makeUrl(self, pageNo):
        return 'https://finance.naver.com/item/sise_day.nhn?code=%s&page=%s' % (self.targetName, str(pageNo))

    def crawling(self, dateData):
        pageNo = 1
        data = []
        isRunning = True
        while(isRunning):
            text = urlopen(self.makeUrl(pageNo), timeout=500).read()
            soup = bs4.BeautifulSoup(text, 'lxml')
            table = soup.find(class_='type2')
            #table 자식
            rows = filter(lambda val : type(val) == bs4.element.Tag, table.children)
            #자식들에서 td태그를 찾음
            tds = map(lambda row: row.find_all('td'), list(rows))
            #1차원으로 변경
            flattenTds = list(itertools.chain(*tds))
            #없는 자식들 제거
            tdsf = filter(lambda td: type(td) == bs4.element.Tag, flattenTds )
            #텍스트 추출
            values = map(lambda value: value.stripped_strings, tdsf)
            #1차원으로 변경
            strings = list(itertools.chain(*values))
            #7개씩 자름
            splitData = [strings[i:i + 7] for i in range(0, len(strings), 7)]
            for one in splitData:
                if not len(one) == 7 :
                    isRunning = False
                    break
                if len(one[0]) < 8:
                    isRunning = False
                    break
                date = NaverDate.formatDate(date=one[0])
                # print(dateData.startDate)
                # print(date)
                # print(dateData.endDate)
                
                if dateData.startDate <= date and date <= dateData.endDate :
                    resultData = NaverStockResultData.create(
                        date=one[0], 
                        close=one[1],
                        diff=one[2],
                        open=one[3],
                        high=one[4],
                        low=one[5],
                        volume=one[6])
                    data.append(resultData)
                elif dateData.startDate > date:
                    isRunning = False
                    break
            # if self.logging:
                # print('pageNo:' + str(pageNo))
                # for value in data:
                    # print(value)
            # print(data)
            if soup.find('td', class_='pgRR'):
                pageNo += 1
            else:
                print('break')
                break
        return data


