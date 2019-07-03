# In[3]: 제조업 per
import pandas as pd

upCodes = ['제조업', '은행업', '증권업', '보험업', '종합금융업', '여신전문금융업', '신용금고']
factors = ['per', 'pcr', 'pbr', 'roe', '당기순이익', '영업활동으로인한현금흐름', '투자활동으로인한현금흐름', '재무활동으로인한현금흐름']
names = []
for upCode in upCodes:
    for factor in factors:
        names.append('fin/'+upCode+'_'+factor+'.xlsx')
for name in names:
    df = pd.read_excel(name,sheet_name='계정별 기업 비교 - 특정계정과목', skiprows=8)
    df.columns = list(df.iloc[0])
    df.drop([0])
    df = df.set_index("종목코드")
    print(df)
# df.index


#%%