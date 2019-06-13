import pandas as pd
class NaverResultData:
    @staticmethod
    def create(date='', close='', diff='', rate='', volume='', price=''):
        newData = NaverResultData()
        newData.date = date
        newData.close = newData.format(close)
        newData.diff = newData.format(diff)
        newData.rate = newData.format(rate)
        newData.volume = newData.format(volume)
        newData.price = newData.format(price)
        return newData
    def format(self, value):
        return float(value.replace(',', '').replace('%',''))
    def value(self):
        return [self.close, self.diff, self.rate, self.volume, self.price]
    def index(self):
        return pd.to_datetime(self.date, format='%Y-%m-%d')
    def __str__(self):
        return f'date:{self.date}, close:{self.close}, diff:{self.diff} rate:{self.rate}, volume:{self.volume}, price:{self.price}'