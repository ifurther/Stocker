import requests
from io import StringIO
import pandas as pd
import pandas_ta as ta
import numpy as np
import datetime
import time
import sqlite3

class Stocker:
  def __init__(self, n_days, db_name):
    #self.name = name
    self.today = datetime.datetime.now()
    self.country = "TW"
    self.source = "TWSE"
    self.rank = ""
    self.data = None
    self.data_ta = None
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
      data_ = pd.concat(data)
      data_ = self.correct_data(data=data_,get_data=True)
      if self.data is not None:
         newdata = [self.data, data_]
         self.data = pd.concat(newdata).drop_duplicates()
      else:
         self.data = data_

  def get_data(self) -> pd.DataFrame:
    self.data = pd.concat(self.get_twse_stocker_date_range_date(n_days=self.n_days))

  def get_data_ta(self):
    self.data_ta = self.data[['開盤價', '最高價', '最低價', '收盤價', '成交股數']].copy()       
    self.data_ta.columns = ['open', 'high', 'low', 'close', 'volume']
    self.data_ta = self.data_ta.swaplevel('交易日', '證券代號').sort_index()

  def add_indicators(self, df_group):
    df_group_ = df_group.copy()
    df_group_.ta.sma(length=20,append=True)
    df_group_.ta.rsi(length=14,append=True)
    #macd = df_group_.ta.macd()
    df_group_.ta.macd(append=True)
    #df_group_['MACD'] = macd['MACD_12_26_9']
    #df_group_['MACDh'] = macd['MACDh_12_26_9']
    #df_group_['MACDs'] = macd['MACDs_12_26_9']
    df_group_.ta.stoch(append=True)
    #kd = df_group_.ta.stoch()
    #df_group_['K'] = kd['STOCHk_14_3_3']
    #df_group_['D'] = kd['STOCHd_14_3_3']
    return df_group_ 

  def cal_data(self):
     self.data_ta = self.data_ta.groupby(level=0, group_keys=False).apply(self.add_indicators)
     self.data_ta.columns = ['open', 'high', 'low', 'close', 'volume', 'SMA_20', 'RSI_14',
       'MACD', 'MACDh', 'MACDs', 'K',
       'D', 'STOCHh_14_3_3']

  def correct_data(self, data=None, get_data=None):
    flaot_cols = ['開盤價', '最高價', '最低價', '收盤價', '最後揭示買價', '本益比']
    int_cols = ['成交股數',	'成交筆數',	'成交金額']
    if data is None:
       data = self.data
    data.index.names=['交易日','證券代號']
    data[flaot_cols] = data[flaot_cols].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    data[int_cols] = data[int_cols].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    data.index=data.index.set_levels(pd.to_datetime(data.index.levels[0]), level='交易日')
    data.index=data.index.set_levels(data.index.levels[1].astype(pd.StringDtype), level='證券代號')
    if get_data is not None:
       return data
  def save_db(self, data, db_name) -> None:
    conn = sqlite3.connect('stocker.db')  #建立資料庫
    cursor = conn.cursor()
    self.data = self.data.drop(['level_0','交易日'],axis=1)
    if self.data is not None:
      self.data.to_sql('Stocker', conn, if_exists='append', index=True)
    if self.data_ta is not None:
      self.data_ta.to_sql('Stocker_ta', conn, if_exists='append', index=True)
 
  def load_db_data(self, db_nmae) -> None:
    with sqlite3.connect('stocker.db') as conn:  #建立資料庫
      data = pd.read_sql('SELECT * FROM Stocker', conn, index_col=['交易日','證券代號'])
    self.correct_data()
    self.data=data
  
  def load_db_data_ta(self, db_nmae) -> None:
    with sqlite3.connect('stocker.db') as conn:  #建立資料庫
      data = pd.read_sql('SELECT * FROM Stocker_ta', conn, index_col=['交易日','證券代號'])
    self.correct_data()
    self.data=data