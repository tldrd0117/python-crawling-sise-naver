import datetime
class NaverDate:
    @staticmethod
    def create(startDate='', endDate=datetime.date.today()):
        newData = NaverDate()
        newData.startDate = NaverDate.formatDate(startDate)
        newData.endDate = NaverDate.formatDate(endDate)
        return newData
    
    @staticmethod
    def formatDate(date = ''):
        if date:
            d = str(date).replace('-', '.').split('.')
            year = int(d[0])
            month = int(d[1])
            day = int(d[2])
            date = datetime.date(year, month, day)
            return date
        else:
            return datetime.date.today()
        