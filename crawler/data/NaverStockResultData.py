class NaverStockResultData:
    @staticmethod
    def create(date='', close='', diff='', open='', high='', low='', volume=''):
        newData = NaverStockResultData()
        newData.date = date
        newData.close = newData.format(close)
        newData.diff = newData.format(diff)
        newData.open = newData.format(open)
        newData.high = newData.format(high)
        newData.low = newData.format(low)
        newData.volume = newData.format(volume)
        return newData
    def format(self, value):
        return float(value.replace(',', '').replace('%',''))
    def __str__(self):
        return f'date:{self.date}, close:{self.close}, diff:{self.open} rate:{self.open}, high:{self.high}, low:{self.low}, volume:{self.volume}'