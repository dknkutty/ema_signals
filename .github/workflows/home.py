import streamlit as st
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from datetime import timedelta

import yfinance as yf
from pandas import ExcelWriter
st.set_page_config(layout="wide")
db = st.radio("Choose a database",["NS","BO","Holdings"])
path = r"D:\Stock Market\Data\HiCAGR_Screener.xlsx"
if db=="NS":
   df = pd.read_excel(path,sheet_name='Screener_NS')  
   file = "NS" 
elif db=="Holdings":
   df = pd.read_excel(path,sheet_name='Holdings')  
   file = "Holdings"       
else:
   df = pd.read_excel(path,sheet_name='Screener_BO')  
   file = "BO"
# set start and end dates 
lookback_period = 365
# Set the end date as the current date
end_date = datetime.date.today().strftime('%Y-%m-%d')
start_date = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - datetime.timedelta(days=lookback_period)).strftime('%Y-%m-%d')

#end = dt.today() + datetime.timedelta(days=1)
#start = end - timedelta(days=365)

tickers = df.ticker.to_list()
#stocks = df.stock.to_list()
if file == "BO": 
   tickers = [f'{ticker}.BO' for ticker in tickers]
else:   
   tickers = [f'{ticker}.NS' for ticker in tickers]
col_values = []

for ticker in tickers:
    ticker = str(ticker)
    #symbol = df.at[df.iloc[:,1]==ticker,'symbol']
           
    stock = yf.Ticker(ticker)
    info = stock.info
    longName = info.get('longName','N/A')
    df = yf.download(ticker, start = start_date, end = end_date)['Close']
    df.columns = {'Close Price'}
    
# Create 20 days exponential moving average column
    df['20_EMA'] = df['Close Price'].ewm(span = 20, adjust = False).mean()
# Create 50 days exponential moving average column
    df['50_EMA'] = df['Close Price'].ewm(span = 50, adjust = False).mean()
# create a new column 'Signal' such that if 20-day EMA is greater   # than 50-day EMA then set Signal as 1 else 0
    df['Signal'] = 0.0  
    df['Signal'] = np.where(df['20_EMA'] > df['50_EMA'], 1.0, 0.0)
# create a new column 'Position' which is a day-to-day difference of # the 'Signal' column
    df['Position'] = df['Signal'].diff()
    df_ema = df.loc[df['Position'] == 1]
    df_ema_buy = df_ema['Close Price'].tail(1)
    try:
      buy_dt = f'{df_ema_buy.index.tolist()[0]:%Y-%m-%d}'
      buy_price = f'{df_ema.iat[0,0]:.1f}'
    except:
      buy_dt = "N/A"  
      buy_price = "N/A"  
    df_ema = df.loc[df['Position'] == -1]
    df_ema_sell = df_ema['Close Price'].tail(1)
    try:
      sell_dt = f'{df_ema_sell.index.tolist()[0]:%Y-%m-%d}'
      sell_price = f'{df_ema.iat[0,0]:.1f}'
    except:
      sell_dt = "N/A"  
      sell_price = "N/A"  
    row_values = {'Symbol':f'{ticker[:-3]}','Date EMA_BUY':f'{buy_dt}','Price EMA_BUY':f'{buy_price}','Date EMA_SELL':f'{sell_dt}','Price EMA_SELL':f'{sell_price}','Stock Name':f'{longName}'}
    #row_values = {'Symbol':f'{ticker[:-3]}','Price SMA_BUY':f'{df_sma_buy}','Price SMA_SELL':f'{df_sma_sell}','Price EMA_BUY':f'{df_ema_buy}','Price EMA_SELL':f'{df_ema_sell}','Short Name':f'{longName}'}
    col_values.append(row_values)
    
df_ma = pd.DataFrame.from_dict(col_values) 
st.write("Last Buy/Sell signals generated from SMA/EMA") 
df_ma
file_ma = f'D:/Stock Market/Data/MA_{file}.xlsx'
writer = ExcelWriter(file_ma)
df_ma.to_excel(writer,index = False, header=True)
writer.close()

ticker1 = st.text_input("Type a Stock with exchange(.NS or .BO )",value="")
if len(ticker1)==0:
    exit
else:    
    stock1 = yf.Ticker(ticker1)     
    #Get price data
    end_date = datetime.date.today() 
    start_date = end_date-timedelta(days=365) #Get 1yr data
    price_data =  stock1.history(start=start_date,end=end_date)

    latest_price = price_data.iloc[-1]
    ltp=latest_price['Close']
    price_lastYr = price_data.iloc[0]
    close_lastYr = price_lastYr['Close']
        
    #Calculate percentage changes
    daily_change = (ltp-price_data.iloc[-2]['Close'])/price_data.iloc[-2]['Close']*100
    weekly_change = (ltp-price_data.iloc[-6]['Close'])/price_data.iloc[-6]['Close']*100
    monthly_change = (ltp-price_data.iloc[-23]['Close'])/price_data.iloc[-23]['Close']*100
    #Get fundamental data
    info = stock1.info
    st.subheader("Stock Name :" f'{info.get('longName','N/A')}' )
    st.write('Sector :' f'{info.get('sector','N/A')}')

    col1,col2,col3 = st.columns(3)
    with col1:
        st.write("Current Price : Rs. " f'{ltp:.1f}')
        st.write("Day Change  :" f'{daily_change:.1f}'"%")
        st.write("Week Change :" f'{weekly_change:.1f}'"%")
        st.write("Month Change :"f'{monthly_change:.1f}'"%")
    with col2:
        st.write("Yr. High :"f'{info.get("fiftyTwoWeekHigh",0):.1f}' )
        st.write("Dicount :"f'{(info.get("fiftyTwoWeekHigh",0)-ltp)/info.get("fiftyTwoWeekHigh","N/A")*100:.1f}'"%" )
        st.write("50 DMA :"f'{info.get("fiftyDayAverage",0):.1f}' )
        st.write("200 DMA :"f'{info.get("twoHundredDayAverage",0):.1f}' )
        st.write("Market Cap, Rs(Cr): " f'{info.get("marketCap",0)/10000000:.1f}')
    with col3:
        st.write("PE Ratio :" f'{info.get("forwardPE",0):.1f}' )
        st.write("EPS :" f'{info.get("forwardEps",0):.1f}')
        st.write("Profit Margin :" f'{info.get("profitMargins",0)*100:.1f}')
        st.write("Earnings Growth :" f'{info.get("earningsGrowth",0)*100:.1f}')

    st.write("Company Brief :" f'{info.get('longBusinessSummary','N/A')}')