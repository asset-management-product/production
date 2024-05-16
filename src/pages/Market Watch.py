import streamlit as st
import pandas as pd
import numpy as np
import json
import ast
import mplfinance as mpf


from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

import colorsys

import requests
from io import StringIO

from utils.functions import *
from statistics import mean


st.header("Market Watch")

#st.write("Currently there are three sections: Benchmark Performance, Industry View and Player View")
#st.write("In Alpha Phase")

#list_tabs=["Benchmark Performance", "Industry View", "Player View"]
#tab0, tab1, tab2 = st.tabs(list_tabs)


gold_price_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYFfvf7P74qciUDJxQ?e=DhbhpP')
gold_price_df = gold_price_df[['Date','Price']]


# Load the data
df_index = pd.read_excel('data/curated/curated_vnindex.xlsx')
df_index=df_index.iloc[:,0].str.split(',', expand=True)
# Assign the column names to the dataframe
# Define column names based on the provided information
column_names = [
    "Ngay", "GiaDieuChinh", "Giá Đóng Cửa", "Thay Đổi", "Khối Lượng Khớp Lệnh", 
    "Giá Trị Khớp Lệnh", "KL Thỏa Thuận", "GT Thỏa Thuận", "Giá Mở Cửa", 
    "Giá Cao Nhất", "Giá Thấp Nhất"
]
df_index.columns = column_names
df_index=df_index[['Ngay','GiaDieuChinh']]





list_tabs=["Benchmark","Industry View","Player View"]
benchmark, industry_view, player_view = st.tabs(list_tabs)

with industry_view:
    industry_summary_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYEXK7eSdQyRZdaV7Q?e=4aNPHc')
    st.dataframe(industry_summary_df)

with benchmark:
    # Start of Streamlit app
    st.title('Financial Data Visualization')

    st.dataframe(gold_price_df)
    
    st.dataframe(df_index)
    gold_price_df['Date'] = pd.to_datetime(gold_price_df['Date'])
    df_index['Ngay'] = pd.to_datetime(df_index['Ngay'], format='%d/%m/%Y')
    
    # Plotting Gold Price Chart
    st.header('Gold Price Trend')
    st.line_chart(gold_price_df.set_index('Date'))

    # Plotting VNINDEX Chart
    st.header('VNINDEX Trend')
    df_index=df_index[['Ngay','GiaDieuChinh']]
    st.line_chart(df_index.set_index('Ngay'))
    st.dataframe(df_index)