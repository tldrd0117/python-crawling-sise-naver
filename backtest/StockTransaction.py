import pandas as pd

class StockTransaction:
    @staticmethod
    def create():
        st = StockTransaction()
        return st
    
    def getMomentumMean(self, current, df, mNum, mUnit):
        mdf = df.resample('M').mean()
        beforeMomentumDate = current + pd.Timedelta(-mNum, unit=mUnit)
        start = mdf.index.get_loc(beforeMomentumDate, method='nearest')
        end = mdf.index.get_loc(current, method='nearest')
        oneYearDf = mdf.iloc[start:end+1]
        momentum = oneYearDf.iloc[-1] - oneYearDf
        momentumScore = momentum.applymap(lambda val: 1 if val > 0 else 0 )
        return momentumScore.mean()

    def getMomentumInvestRate(self, momentumScoreMean, shareNum, cashRate):
        sortValue = momentumScoreMean.sort_values(ascending=False)
        share = sortValue.head(shareNum)
        distMoney = share / (share + cashRate)
        sumMoney = distMoney.sum()
        return {'invest':distMoney / sumMoney, 'perMoney':sumMoney / share.size if share.size != 0 else 0}

    def setMonmentumRate(self, shares, current, topdf, cashRate, mNum, mUnit):
        momentumScoreMean = self.getMomentumMean(current, topdf, mNum=mNum, mUnit=mUnit)
        rate = self.getMomentumInvestRate(momentumScoreMean[shares.shareList], shareNum=shares.shareNum, cashRate=cashRate)
        shares.investRate = rate['invest']
        shares.perMoneyRate = rate['perMoney']
