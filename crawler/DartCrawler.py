# In[3]:
import urllib3
import bs4
from functools import reduce
import itertools
import json
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 
http = urllib3.PoolManager()

apiKey = '48a43d39558cf752bc8d8e52709da34569a80372'

class DartCrawler:
    @staticmethod
    def create(target, startDate, endDate):
        newCrawler = DartCrawler()
        newCrawler.name = target['name']
        newCrawler.code = target['code']
        newCrawler.startDate = startDate.replace('-','')
        newCrawler.endDate = endDate.replace('-','')
        return newCrawler
    
    def apiUrl(self, pageNo):
        return 'http://dart.fss.or.kr/api/search.json?auth=%s&crp_cd=%s&start_dt=%s&end_dt=%s&bsn_tp=A001&page_no=%s' % (apiKey, self.code, self.startDate, self.endDate, pageNo)
    
    def getJsonData(self, pageNo):
        apiUrl = self.apiUrl(pageNo)
        r = http.request('GET', apiUrl, timeout=10, retries=10)
        text = r.data.decode('utf-8')
        return json.loads(text)
    
    def getRcpNo(self, jsonData):
        return list(map(lambda x : x['rcp_no'],jsonData['list']))
    
    def viewerUrl(self, rcpNo):
        return 'http://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s' % (rcpNo)
    def getViewerParam(self, rcpNo, menuName):
        viewerUrl = self.viewerUrl(rcpNo)
        r = http.request('GET', viewerUrl, timeout=10, retries=10)
        text = r.data.decode('utf-8')
        targetIndex = text.find(menuName)
        startIndex = text.find('viewDoc', targetIndex)
        endIndex = text.find(';', startIndex)
        values = self.getInSingleQuote(text[startIndex:endIndex])
        return values
    
    def getInSingleQuote(self, text):
        startIndex = text.find('\'')
        values = []
        while startIndex >=0:
            endIndex = text.find('\'', startIndex + 1)
            values.append(text[startIndex + 1:endIndex])
            startIndex = text.find('\'', endIndex + 1)
        return values

    def viewerDetailUrl(self, params):
        return 'http://dart.fss.or.kr/report/viewer.do?rcpNo=%s&dcmNo=%s&eleId=%s&offset=%s&length=%s&dtd=%s' % (params[0], params[1], params[2], params[3], params[4], params[5])

    def getViewerHTML(self,params):
        viewerDetailUrl = self.viewerDetailUrl(params)
        r = http.request('GET', viewerDetailUrl, timeout=10, retries=10)
        text = r.data.decode('utf-8')
        return text
       
    def crawling(self):
        jsonData = self.getJsonData(1)
        totalPageNo = jsonData['total_page']
        rcpNo = []
        rcpNo += self.getRcpNo(jsonData)
        if int(totalPageNo) >= 2:
            for pno in range(2, int(totalPageNo) + 1):
                jsonData = self.getJsonData(pno)
                rcpNo += self.getRcpNo(jsonData)
        html = self.getViewerHTML(self.getViewerParam(rcpNo[0], '주식의 총수'))
        stockNum = self.getStockNum(html)
        html = self.getViewerHTML(self.getViewerParam(rcpNo[0], '요약재무정보'))
        total, profit = self.getTotal(html)
        return {'stockNum':stockNum, 'total':total, 'profit':profit}
        # htmlFile = open('finhtml/'+self.name+'_'+rcpNo[0]+'.html', 'w')
        # htmlFile.write(str(html))
        # htmlFile.close()
    def getStockNum(self, html):
        dfs = pd.read_html(html)
        df = dfs[1]
        index = df['구 분'][df['구 분']=='Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)'].dropna().index[0]
        stockNum = df.iloc[index]['주식의 종류']['합계']
        return stockNum
    def getTotal(self, html):
        dfs = pd.read_html(html)
        total = None
        profit = None
        for df in dfs:  
            if '구 분' in list(df.columns):
                index1 = df['구 분'][df['구 분']=='자본총계'].index
                if len(index1) == 0:
                    continue
                index2 = df['구 분'][df['구 분']=='당기순이익'].index
                if len(index2) == 0:
                    index2 = df['구 분'][df['구 분']=='당기순이익(손실)'].index
                    if len(index2) == 0:
                        continue
                total = df.iloc[index1[0]].iloc[1]
                profit = df.iloc[index2[0]].iloc[1]
                break
        return total, profit



# if __name__ == "__main__":
    # 현대중공업지주267250
dartCrawler = DartCrawler.create({'name':'현대중공업지주','code':'267250'}, '2007-01-01', '2019-12-31')
data = dartCrawler.crawling()
print(data)

# df['구 분'][df['구 분']=='자본총계':df['구 분']=='매출액']

# In[1]
# df['합계']
# df['Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)']
# df.query('Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)')
# df['구 분'][df['구 분'] == 'Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)']
# df['Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)','합계']
# print(dfs[1]['합계'])
           


#%%
