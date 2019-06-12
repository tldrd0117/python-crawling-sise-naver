from urllib.request import urlopen
import bs4
from functools import reduce
import itertools
from crawler.data.NaverTopMarketCapData import NaverTopMarketCapData
from crawler.data.NaverDate import NaverDate
class NaverTopMarketCapCrawler:
    @staticmethod
    def create():
        newCrawler = NaverTopMarketCapCrawler()
        return newCrawler

    def __init__(self):
        pass
    def makeUrl(self, pageNo):
        return 'https://finance.naver.com/sise/sise_market_sum.nhn?&page=%s' % (str(pageNo))

    def crawling(self, rank):
        pageNo = 1
        data = []
        isRunning = True
        while(isRunning):
            text = urlopen(self.makeUrl(pageNo)).read()
            soup = bs4.BeautifulSoup(text, 'lxml')
            table = soup.find(class_='type_2')
            #table 자식
            rows = filter(lambda val : type(val) == bs4.element.Tag, table.children)
            #자식들에서 td태그를 찾음
            tds = map(lambda row: row.find_all('td'), list(rows))
            #1차원으로 변경
            flattenTds = list(itertools.chain(*tds))
            #없는 자식들 제거
            tdsf = filter(lambda td: type(td) == bs4.element.Tag, flattenTds )
            texts = map(lambda value: value.a if value.a else value, tdsf)
            # for item in tdsf:
                # print(item)
            #텍스트 추출
            values = map(lambda value: [value['href'][value['href'].index("=") + 1:], value.string] if value.name == 'a' and value.string is not None  else value.stripped_strings, texts)
            #1차원으로 변경
            strings = list(itertools.chain(*values))
            #13개씩 자름
            splitData = [strings[i:i + 13] for i in range(0, len(strings), 13)]
            print(splitData)
            for one in splitData:
                # print(dateData.startDate)
                # print(dateData.endDate)
                curRank = int(one[0])
                startRank = rank[0]
                endRank = rank[1]
                if startRank <= curRank and curRank <= endRank :
                    resultData = NaverTopMarketCapData.create(
                        rank=one[0],
                        code=one[1],
                        name=one[2], 
                        price=one[3], 
                        diff=one[4], 
                        rate=one[5], 
                        parValue=one[6], 
                        marketCap=one[7], 
                        listedShares=one[8], 
                        foreignerRate=one[9], 
                        volume=one[10], 
                        per=one[11], 
                        roe=one[12])
                    data.append(resultData)
                elif endRank < curRank:
                    isRunning = False
                    break
            # print('pageNo:' + str(pageNo))
            # for value in data:
                # print(value)
            # print(data)
            if soup.find('td', class_='pgRR'):
                pageNo += 1
            else:
                break
        return data

