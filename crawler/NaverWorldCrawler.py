from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from crawler.data.NaverWorldResultData import NaverWorldResultData
from crawler.data.NaverDate import NaverDate
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import bs4
from functools import reduce
import itertools

class NaverWorldCrawler:
    @staticmethod
    def create(targetName):
        newCrawler = NaverWorldCrawler()
        newCrawler.targetName = targetName
        return newCrawler
    def makeWorldUrl(self):
        return 'https://finance.naver.com/world/sise.nhn?symbol=%s' % (self.targetName)
    
    def crawling(self, dateData = ''):
        driver = webdriver.PhantomJS()
        driver.get(self.makeWorldUrl())
        data = []
        pageNo = '1'
        isRunning = True
        while(isRunning):
            elePage = driver.find_element_by_link_text(pageNo)
            if not elePage:
                break
            elePage.click()
            pageNo = elePage.text

            text = driver.page_source
            soup = bs4.BeautifulSoup(text, 'lxml')
            table = soup.find(class_='tb_status2 tb_status2_t2' ).find('tbody')
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
            #6개씩 자름
            splitData = [strings[i:i + 6] for i in range(0, len(strings), 6)]
            for one in splitData:
                date = NaverDate.formatDate(date=one[0])
                # print(dateData.startDate)
                print(date)
                # print(dateData.endDate)
                if dateData.startDate <= date and date <= dateData.endDate :
                    resultData = NaverWorldResultData.create(
                        date=one[0], 
                        close=one[1],
                        diff=one[2],
                        open=one[3],
                        high=one[4],
                        low=one[5])
                    data.append(resultData)
                elif dateData.startDate > date:
                    isRunning = False
                    break
            print('pageNo:' + str(pageNo))
            for value in data:
                print(value)
            # print(data)
            eleNext = driver.find_elements_by_css_selector('#dayPaging .next')
            nextPageNo = str(int(pageNo) + 1)
            if len(eleNext) > 0 and int(pageNo) % 10 == 0:
                eleNext[0].click()
                wait = WebDriverWait(driver,10)
                wait.until(EC.presence_of_element_located((By.LINK_TEXT, nextPageNo)))
                driver.implicitly_wait(1)
            pageNo = nextPageNo
            if len(driver.find_elements_by_link_text(pageNo)) == 0:
                break
        driver.close()
        return data
