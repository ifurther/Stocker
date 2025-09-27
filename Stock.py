import datetime
from io import StringIO
import sqlite3
import time
import pandas as pd
import pandas_ta as ta
import matplotlib as mpf
import requests

class Stocker:
  def __init__(self, n_days, db_name):
    #self.name = name
    self.today = datetime.datetime.now()
    self.country = "TW"
    self.source = "TWSE"
    self.rank = ""
    self.data = None
    self.data-ta = None
    self.OHLCV = None
    self.n_days = n_days
    self.db_name = db_name

  def crawl_price(self, date):
    r = requests.post('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + str(date).split(' ')[0].replace('-','') + '&type=ALL')
    #ret = pd.read_csv(StringIO("\n".join([i.translate({ord(c): None for c in ' '})
    #                                    for i in r.text.split('\n')
    #                                    if len(i.split('",')) == 17 and i[0] != '='])), header=0)
    ret = pd.read_csv(StringIO(r.text.replace("=", "")),
            header=["證券代號" in l for l in r.text.split("\n")].index(True)-1)
    ret = ret.set_index('證券代號')
    ret = ret[:'備註:'][:-1]
    ret = ret.loc[:,:'本益比']
    ret['成交金額'] = ret['成交金額'].str.replace(',','')
    ret['成交股數'] = ret['成交股數'].str.replace(',','')
    ret['成交筆數'] = ret['成交筆數'].str.replace(',','')
    ret['交易日']= date.date()
    return ret


  def get_twse_stocker_date_range_date(
      self,
      startdate=datetime.datetime.now(),
      n_days=10,
      sleep_time=10,
      allow_continuous_fail_count=5,
  ):
      data = {}
      date = startdate
      fail_count = 0
      while len(data) < n_days:

          print('parsing', date)
          # 使用 crawPrice 爬資料

          try:
              if pd.to_datetime(date.date()) in self.data.index.levels[0] and self.data is not None:
                print('skip! data is already having')
                data[date.date()] = self.data.loc[[date.date()]].droplevel(level='交易日')
              else:
                # 抓資料
                data[date.date()] = self.crawl_price(date)
                print('success!')
                fail_count = 0
          except:
              # 假日爬不到
              print('fail! check the date is holiday')
              fail_count += 1
              if fail_count == allow_continuous_fail_count:
                  raise
                  break

          # 減一天
          date -= datetime.timedelta(days=1)
          time.sleep(sleep_time)
      #return data
      self.data = pd.concat(data)
  def get_data(self) -> pd.DataFrame:
    self.data = pd.concat(self.get_twse_stocker_date_range_date(n_days=self.n_days))

  def get_ta_data(self):
    self.data-ta = self.data[['開盤價', '最高價', '最低價', '收盤價', '成交股數']].copy()       
    self.data-ta.columns = ['open', 'high', 'low', 'close', 'volume']
    self.data-ta.swaplevel('交易日', '證券代號').sort_index()

  def save_db(self, data, db_name) -> None:
    conn = sqlite3.connect('stocker.db')  #建立資料庫
    cursor = conn.cursor()
    self.data.to_sql('Stocker', conn, if_exists='append', index=True)
  
  def load_db(self, db_nmae) -> None:
    conn = sqlite3.connect('stocker.db')  #建立資料庫
    cursor = conn.cursor()
    data = pd.read_sql('SELECT * FROM Stocker', conn, index_col=['交易日','證券代號'])
    data.index=data.index.set_levels(pd.to_datetime(data.index.levels[0]), level='交易日')
    data.index=data.index.set_levels(data.index.levels[1].astype(pd.StringDtype), level='證券代號')
    data[['成交股數',	'成交筆數',	'成交金額']] = data[['成交股數',	'成交筆數',	'成交金額']].astype(pd.Int64Dtype)
    self.data=data