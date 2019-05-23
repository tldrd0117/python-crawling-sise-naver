class NaverWorldResultData:
    @staticmethod
    def create(date='', close='', diff='', open='', high='', low=''):
        newData = NaverWorldResultData()
        newData.date = date
        newData.close = newData.format(close)
        newData.diff = newData.format(diff)
        newData.open = newData.format(open)
        newData.high = newData.format(high)
        newData.low = newData.format(low)
        return newData
    def format(self, value):
        return float(value.replace(',', '').replace('%',''))
    def __str__(self):
        return f'date:{self.date}, close:{self.close}, diff:{self.diff} rate:{self.open}, volume:{self.high}, price:{self.low}'