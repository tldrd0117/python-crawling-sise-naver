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

    def buy(shares, wallet, buyDate, valuedf):
        money = shares.investMoney
        rateMoney = shares.investRate * shares.investMoney
        stockWallet = wallet.stockWallet
        stockValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][rateMoney.index]
        rowdf = pd.DataFrame(data=[[0]*len(rateMoney.index)], index=[buyDate], columns=rateMoney.index)
        intersect = list(set(stockWallet.columns) & set(rowdf.columns))
        if buyDate not in stockWallet.index:
            stockWallet = pd.concat([stockWallet, rowdf], axis=0)
        else:
            if len(intersect) > 0:
                stockWallet.loc[buyDate, intersect] = 0
                rowdf = rowdf.drop(columns=intersect)
                stockWallet = pd.concat([stockWallet, rowdf], axis=1)
            else:
                stockWallet = pd.concat([stockWallet, rowdf], axis=1)
        for col in rateMoney.index:
            rMoney = rateMoney[col]
            sValue = stockValue[col]
            while (rMoney - sValue) > 0:
                if col in stockWallet.columns and buyDate in stockWallet.index:
                    stockWallet[col][buyDate] = stockWallet[col][buyDate] + 1
                money -= sValue
                rMoney -= sValue
        wallet.stockWallet = wallet
        shares.restMoney += money

    def restInvestBuy(buyDate, valuedf, money, wallet):
        bondValue = valuedf.iloc[valuedf.index.get_loc(buyDate, method='nearest')][restBond]
        stockNum = 0
        while bondValue < money:
            money -= bondValue
            stockNum += 1
        wallet.bondNum = stockNum
        wallet.restMoney += money
