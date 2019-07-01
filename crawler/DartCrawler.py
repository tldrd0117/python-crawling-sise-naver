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
        newCrawler.name = target['Name']
        newCrawler.code = target['Code']
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
    
    def getInfo(self, jsonData):
        return list(map(lambda x : (x['rcp_no'], self.getInBracket(x['rpt_nm'])),jsonData['list']))

    def viewerUrl(self, rcpNo):
        return 'http://dart.fss.or.kr/dsaf001/main.do?rcpNo=%s' % (rcpNo)
    def getViewerParam(self, rcpNo, menuName):
        viewerUrl = self.viewerUrl(rcpNo)
        r = http.request('GET', viewerUrl, timeout=10, retries=10)
        text = r.data.decode('utf-8')
        for menu in menuName:
            targetIndex = text.find(menu)
            if targetIndex != -1:
                break

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
    def getInBracket(self, text):
        startIndex = text.find('(')
        values = []
        while startIndex >=0:
            endIndex = text.find(')', startIndex + 1)
            values.append(text[startIndex + 1:endIndex])
            startIndex = text.find('(', endIndex + 1)
        return values

    def viewerDetailUrl(self, params):
        return 'http://dart.fss.or.kr/report/viewer.do?rcpNo=%s&dcmNo=%s&eleId=%s&offset=%s&length=%s&dtd=%s' % (params[0], params[1], params[2], params[3], params[4], params[5])

    def getViewerHTML(self,params):
        if len(params) < 6:
            print('no Params:', params)
            return None
        viewerDetailUrl = self.viewerDetailUrl(params)
        r = http.request('GET', viewerDetailUrl, timeout=10, retries=10)
        text = r.data.decode('utf-8')
        return text
       
    def crawling(self):
        jsonData = self.getJsonData(1)
        totalPageNo = jsonData['total_page']
        infoList = []
        infoList += self.getInfo(jsonData)
        if int(totalPageNo) >= 2:
            for pno in range(2, int(totalPageNo) + 1):
                jsonData = self.getJsonData(pno)
                infoList += self.getInfo(jsonData)
        results = []
        for rcpNo, rptNm in infoList:
            stockNum = ''
            total=''
            profit=''
            html = self.getViewerHTML(self.getViewerParam(rcpNo, ['주식의 총수']))
            if html:
                stockNum = self.getStockNum(html)
            html = self.getViewerHTML(self.getViewerParam(rcpNo, ['요약재무정보', '재무에 관한 사항']))
            if html:
                total, profit = self.getTotal(html)
            results.append({'Code':self.code, 'Name':self.name ,'date':rptNm[0],'stockNum':stockNum, 'total':total, 'profit':profit})
        return results
        # htmlFile = open('finhtml/'+self.name+'_'+rcpNo[0]+'.html', 'w')
        # htmlFile.write(str(html))
        # htmlFile.close()
    def getStockNum(self, html):
        if html.find('table') == -1 and html.find('TABLE') == -1:
            return None
        dfs = pd.read_html(html)
        stockNum = None
        filters = ['구 분', ('구 분', '구 분')]
        for df in dfs:
            for filterVal in filters:
                if filterVal in list(df.columns):
                    index = df[filterVal][df[filterVal]=='Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)'].index
                    if len(index) > 0:
                        if '합계' in list(df.iloc[index[0]]['주식의 종류'].index):
                            stockNum = df.iloc[index[0]]['주식의 종류']['합계']
                        if '합 계' in list(df.iloc[index[0]]['주식의 종류'].index):
                            stockNum = df.iloc[index[0]]['주식의 종류']['합 계']
                        
        return stockNum
    def getTotal(self, html):
        if html.find('table') == -1 and html.find('TABLE') == -1:
            return None, None
        dfs = pd.read_html(html)
        total = None
        profit = None
        filters = ['구 분', ('구 분', '구 분')]
        totalFilter = ['자본총계', '자 본 총 계', '자본 총계']
        profitFilter = ['당기순이익','[당기순이익]','당기순이익(손실)', 'Ⅳ.당기순이익', 'Ⅴ.당기순이익', '분기(당기)순이익', 'Ⅵ.당기순이익', 'XIII. 당기순이익(손실)', '당기순이익(당기순손실)', 'XIII. 당기순이익']
        for df in dfs:
            for filterVal in filters:
                #헤더에 있을 때
                if filterVal in list(df.columns):
                    for compVal in totalFilter:
                        index1 = df[filterVal][df[filterVal]==compVal].index
                        if len(index1) != 0:
                            break 
                    if len(index1) == 0:
                        continue
                    index2 = []
                    for compVal in profitFilter:
                        index2 = df[filterVal][df[filterVal]==compVal].index
                        if len(index2) != 0:
                            break
                    if len(index2) == 0:
                        continue
                    # print(df)
                    total = str(df.iloc[index1[0]].iloc[1]).replace('(','').replace(')','').replace(',','')
                    profit = str(df.iloc[index2[0]].iloc[1]).replace('(','').replace(')','').replace(',','')
                    break
                #바디에 있을 때
                if filterVal in list(df.values)[0]:
                    for value in df.values:
                        for compVal in totalFilter:
                            if compVal == str(value[0]):
                                total = str(value[1]).replace('(','').replace(')','').replace(',','')
                                break
                    for value in df.values:
                        for compVal in profitFilter:
                            if compVal == str(value[0]):
                                profit = str(value[1]).replace('(','').replace(')','').replace(',','')
                                break

        if total == None or profit == None:
            for df in dfs:
                for value in df.values:
                    for compVal in totalFilter:
                        if compVal == str(value[0]):
                            total = str(value[1]).replace('(','').replace(')','').replace(',','')
                            break
                for value in df.values:
                    for compVal in profitFilter:
                        if compVal == str(value[0]):
                            profit = str(value[1]).replace('(','').replace(')','').replace(',','')
                            break
            
        return total, profit



# if __name__ == "__main__":
    # 현대중공업지주267250
# dartCrawler = DartCrawler.create({'Name':'삼성전자','Code':'005930'}, '2007-01-01', '2019-12-31')
# data = dartCrawler.crawling()
# print(data)

# df['구 분'][df['구 분']=='자본총계':df['구 분']=='매출액']

# In[1]
# df['합계']
# df['Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)']
# df.query('Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)')
# df['구 분'][df['구 분'] == 'Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)']
# df['Ⅳ. 발행주식의 총수 (Ⅱ-Ⅲ)','합계']
# print(dfs[1]['합계'])

# In[23]: 크롤링
           


#%%
