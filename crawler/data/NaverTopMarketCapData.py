class NaverTopMarketCapData:
    @staticmethod
    def create(rank='', name='', code='', price='', diff='', rate='', parValue='', marketCap='',  listedShares='', foreignerRate='', volume='', per='', roe=''):
        newData = NaverTopMarketCapData()
        newData.rank = int(rank)
        newData.name = name
        newData.code = code
        newData.price = newData.format(price)
        newData.diff = newData.format(diff)
        newData.rate = newData.format(rate)
        newData.parValue = newData.format(parValue)
        newData.marketCap = newData.format(marketCap)
        newData.listedShares = newData.format(listedShares)
        newData.foreignerRate = newData.format(foreignerRate)
        newData.volume = newData.format(volume)
        newData.per = newData.format(per)
        newData.roe = newData.format(roe)
        return newData
    def format(self, value):
        return float(value.replace(',', '').replace('%','').replace('N/A','0'))
    def __str__(self):
        return f'rank:{self.rank}, code:{self.code}, name:{self.name}, price:{self.price} diff:{self.diff}, rate:{self.rate}, parValue:{self.parValue}, marketCap:{self.marketCap}, listedShares:{self.listedShares}, foreignerRate:{self.foreignerRate}, volume:{self.volume}, per:{self.per}, roe:{self.roe}'