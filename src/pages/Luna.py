import streamlit as st
import pandas as pd
import requests
from io import StringIO
from io import BytesIO
import json
import streamlit as st
import base64
import numpy as np
import datetime
from datetime import timedelta
import time
import inspect

import os
import sys

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(src_path)
from utils.__pycache__.functions import *

input,processing,summary_portfolio, analysis=st.tabs(['QA and Processing Data','Processing Output','Summary Portfolio', '_In Development_'])

with input:
    read_data,show_data,data_quality=st.tabs(['Read and Processing Data','Show Raw Data','Raw Data Quality (upcoming)'])
    with read_data:
        company_finance_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYEkqnTC-DIdP79KlA?e=lHLNjv',name="Company Finance")
        input_link='https://1drv.ms/x/s!Agfa0F4-51TwhvJZtNzfBoKeAwfxOg?e=ZsJ38E'
        stock_action_df=read_onedrive_excel(input_link,'Stock Action')
        cash_action_df=read_onedrive_excel(input_link,"Cash Action")
        planner_df=read_onedrive_excel(input_link,"Planner")
        #latest_price_df = read_onedrive_csv("https://1drv.ms/u/s!Agfa0F4-51TwhvBoOkPKo2Ni8xCwyQ?e=jgPw56",name ='Latest Price')
        fund_input_price_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51Twh4U2ByyKzHQG5d8Qfg?e=ajc9Hf',name="Fund Input Price")
        diluted_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51Twh4U3c2DdkW6MUcLG7Q?e=5Bzfpe',name="Dilution Factor")
        company_industry_df=read_onedrive_excel('https://1drv.ms/x/s!Agfa0F4-51TwhvBYN69gaO7iPbqPjg?e=aMP8BI',sheet_name="Sheet1")
        vn_index=read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51Twh4UO5ao7qsqTQE0tdg?e=hT6z2H',name="VNINDEX")
        customer_info = read_onedrive_excel('https://1drv.ms/x/s!Agfa0F4-51Twh4YoXRYKc0aY5Tuk8w?e=pcdrgh',sheet_name='OfficeForms Table')
        # Apply the conversion function
        fund_input_price_df['time'] = convert_to_datetime(fund_input_price_df['time'])
        price_latest_update_date=fund_input_price_df['time'].max().strftime('%Y-%m-%d')
        fund_input_price_df = fund_input_price_df.sort_values(by='time')
        
        # Convert the 'time' column in index_price_history to a datetime format
        # index_price_history = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51Twh4ZmBgqKuZ6Tk6sfBQ?e=d3PF0m')
        # index_price_history['date'] = pd.to_datetime(index_price_history['time'], format='%Y%m%d')

        # # Create the new dataframe in the format of 'vnindex (tạm)' with the required columns
        # new_df = index_price_history[['date', 'priceClose']].copy()
        # new_df.rename(columns={'priceClose': 'close'}, inplace=True)
        # new_df['ticker'] = "VNINDEX"
        
        # st.dataframe(vn_index)
        # st.dataframe(new_df)
        st.header("Customer Info")
        st.dataframe(customer_info)
        
        first_transaction_date = min(pd.to_datetime(cash_action_df['Change Date'].min()), pd.to_datetime(stock_action_df['Change_Date'].min()))
        last_transaction_date = max(pd.to_datetime(cash_action_df['Change Date'].max()),pd.to_datetime(stock_action_df['Change_Date'].max()),fund_input_price_df['time'].max())
        # Function to generate missing data for a given ticker
        def generate_missing_data(ticker_data):
            ticker_data['time'] = pd.to_datetime(ticker_data['time'])
            last_date = ticker_data['time'].max()
            today = datetime.date.today()

            # Generate date range excluding weekends
            date_range = pd.date_range(start=last_date + timedelta(days=1), end=today, freq='B')
            if not date_range.empty:
                mean_return = 0.001
                volatility = 0.02
                last_close = ticker_data['close'].iloc[-1]
                prices = [last_close]

                for _ in range(len(date_range)):
                    shock = np.random.normal(loc=mean_return, scale=volatility)
                    last_close = last_close * (1 + shock)
                    prices.append(last_close)

                # Create new dataframe with generated data
                new_data = pd.DataFrame({
                    'time': date_range,
                    'ticker': ticker_data['ticker'].iloc[0],
                    'close': prices[1:]
                })
                return new_data
            return pd.DataFrame()

        @timeit
        def generate_missing_data_index(index_data):
            index_data['date'] = pd.to_datetime(index_data['date'], dayfirst=True)
            last_date = index_data['date'].max().date()
            today = datetime.date.today()

            # Generate complete date range including weekends
            complete_date_range = pd.date_range(start=index_data['date'].min(), end=today, freq='D')
            complete_date_range = complete_date_range.to_frame(index=False, name='date')

            # Merge with original data to identify missing dates
            merged_data = complete_date_range.merge(index_data, on='date', how='left')
            
            # Forward fill missing close values
            merged_data['close'] = merged_data['close'].fillna(method='ffill')

            # Now merged_data includes all dates filled with the last known value
            return merged_data
        @timeit
        def process_vn_index(vn_index):
            vn_index = generate_missing_data_index(vn_index)
            vn_index['date'] = pd.to_datetime(vn_index['date'], format='%d/%m/%Y')
            vn_index = vn_index.sort_values(by='date').reset_index(drop=True)
            vn_index['close'] = pd.to_numeric(vn_index['close'].str.replace(',', ''))
            vn_index['Change_L30D'] = vn_index['close'].pct_change(periods=30)
            vn_index['Change_L90D'] = vn_index['close'].pct_change(periods=90)

            start_of_year = pd.Timestamp(year=pd.Timestamp.today().year, month=1, day=1)
            start_of_year_close = vn_index[vn_index['date'] == start_of_year]['close']
            if start_of_year_close.empty:
                start_of_year_close = vn_index[vn_index['date'] >= start_of_year].iloc[0]['close']
            else:
                start_of_year_close = start_of_year_close.values[0]

            vn_index['Change_YTD'] = vn_index['close'].astype(float) / start_of_year_close - 1
            vn_index['Change_L30D'] = vn_index['Change_L30D'].map(lambda x: f'{x:.2%}')
            vn_index['Change_L90D'] = vn_index['Change_L90D'].map(lambda x: f'{x:.2%}')
            vn_index['Change_YTD'] = vn_index['Change_YTD'].map(lambda x: f'{x:.2%}')
            st.dataframe(vn_index)
            return vn_index

        vn_index = process_vn_index(vn_index)
        
        def process_missing_data_tickers_and_merge(fund_input_price_df, diluted_df, stock_action_df, first_transaction_date,last_transaction_date):
            # Filter the relevant tickers
            relevant_tickers = stock_action_df['Asset'].unique()
            fund_input_price_df = fund_input_price_df[fund_input_price_df['ticker'].isin(relevant_tickers)]

            # Convert Date columns to datetime
            diluted_df['Date'] = pd.to_datetime(diluted_df['Date'])
            fund_input_price_df['time'] = pd.to_datetime(fund_input_price_df['time'])

            # Melt the diluted_df for easier merging
            diluted_df_melted = diluted_df.melt(id_vars=['Date'], var_name='ticker', value_name='dilution_factor')
            st.dataframe(diluted_df_melted)
            # Merge the fund_input_price_df with diluted_df_melted
            merged_df = pd.merge(fund_input_price_df, diluted_df_melted, left_on=['ticker', 'time'], right_on=['ticker', 'Date'], how='left')

            # Fill missing dilution factors with 1 (no dilution)
            merged_df['dilution_factor'].fillna(1, inplace=True)

            # Calculate the diluted price
            merged_df['diluted_price'] = merged_df['close']
            merged_df['close'] = merged_df['close'] * merged_df['dilution_factor']

            # Drop the now redundant 'Date' and 'dilution_factor' columns
            merged_df.drop(columns=['Date'], inplace=True)

            
            # Generate a date range from the first transaction date to the current date
            date_range = pd.date_range(start=first_transaction_date, end=last_transaction_date)

            # Filter the merged_df to include only rows within the relevant date range
            merged_df = merged_df[merged_df['time'].isin(date_range)]

            # Generate missing data for all tickers in a vectorized manner
            def generate_missing_data_vectorized(group):
                group = group.sort_values(by='time')
                last_date = group['time'].max()
                today = pd.Timestamp.today()

                date_range = pd.date_range(start=last_date + pd.Timedelta(days=1), end=today, freq='B')
                if not date_range.empty:
                    mean_return = 0.001
                    volatility = 0.02
                    last_close = group['close'].iloc[-1]
                    prices = [last_close]

                    for _ in range(len(date_range)):
                        shock = np.random.normal(loc=mean_return, scale=volatility)
                        last_close = last_close * (1 + shock)
                        prices.append(last_close)

                    new_data = pd.DataFrame({
                        'time': date_range,
                        'ticker': group['ticker'].iloc[0],
                        'close': prices[1:]
                    })
                    return pd.concat([group, new_data], ignore_index=True)
                return group

            # Apply the missing data generation function to each group
            updated_data = merged_df.groupby('ticker').apply(generate_missing_data_vectorized).reset_index(drop=True)
            return updated_data

        # Combine all data
        fund_input_price_df = process_missing_data_tickers_and_merge(fund_input_price_df, diluted_df, stock_action_df, first_transaction_date,last_transaction_date)

        @timeit
        def process_latest_price(fund_input_price_df,last_transaction_date):
            # Convert 'time' column to datetime if it's not already in datetime format
            fund_input_price_df['time'] = pd.to_datetime(fund_input_price_df['time'])

            # Extract the latest price for each ticker
            latest_price_df = fund_input_price_df[fund_input_price_df['time'] == last_transaction_date]
            
            # Select only the 'ticker' and 'close' columns
            #latest_price_df = latest_price_df[['ticker', 'close']]
            return latest_price_df
        
        latest_price_df=process_latest_price(fund_input_price_df,last_transaction_date)
        
        st.header("Processed Input Price")
        st.dataframe(fund_input_price_df)
        
        #LEVEL 1
        # Function to convert Excel-style dates
        def convert_excel_date(excel_date):
            if isinstance(excel_date, int) or isinstance(excel_date, float):
                return pd.to_datetime('1899-12-30') + pd.to_timedelta(excel_date, 'D')
            return pd.to_datetime(excel_date, format='%d/%m/%Y')

        @timeit
        def process_stock_action(stock_action_df):
            # Applying the conversion function to the Change_Date column
            stock_action_df['Change_Date'] = stock_action_df['Change_Date'].apply(convert_excel_date)
            stock_action_df['Asset'] = stock_action_df['Asset'].astype(str)
            stock_action_df['Action'] = pd.to_numeric(stock_action_df['Action'], errors='coerce').fillna(0).astype(int)
            stock_action_df['Action'] = stock_action_df['Action'].astype('int64')
            stock_action_df['Change_Quantity'] = stock_action_df['Change_Quantity'].astype('int64')
            stock_action_df['Change_Price'] = stock_action_df['Change_Price'].fillna(0).astype('int64')
            stock_action_df['Total Change'] = stock_action_df['Total Change'].astype('int64')
            stock_action_df['Net Change'] = stock_action_df['Net Change'].astype('int64')
            # Add 'Q_Change' column
            stock_action_df['Q_Change'] = stock_action_df.apply(lambda row: row['Change_Quantity'] if row['Action'] >= 0 else -row['Change_Quantity'], axis=1)
            stock_action_df["Target Price"] = stock_action_df["Target Price"].fillna(10000).astype("int64")
            # Add 'Action_Cash' column
            stock_action_df['Action_Cash'] = stock_action_df.apply(lambda row: -row['Total Change']*(row['Action']+row['T&F']) if abs(row['Action']) == 1 else (0), axis=1)
            return stock_action_df
        stock_action_df = process_stock_action(stock_action_df)

        @timeit
        def process_cash_action(cash_action_df):
            cash_action_df['Change Date'] = pd.to_datetime(cash_action_df['Change Date'], format ='%d/%m/%Y')
            return cash_action_df

        cash_action_df = process_cash_action(cash_action_df)

        #PLANNER DATA
        @timeit
        def process_planner(planner_df):
            planner_df["Change_Date"] = pd.to_datetime(planner_df["Change_Date"], format ='%d/%m/%Y')
            planner_df["Q_Change"] = planner_df.apply(lambda row: -row["Action"] * row["Change_Quantity"] if row["Action"] == -1 else row["Action"] * row["Change_Quantity"], axis=1)
            planner_df["Action_Cash"] = planner_df.apply(lambda row: -row["Total Change"] if row["Action"] == 1 else row["Total Change"], axis=1)
            planner_df["Asset"] = planner_df["Asset"].str.upper()
            return planner_df

        planner_df = process_planner(planner_df)

# with simulation:
#     st.header('Planner')
#     st.dataframe(planner_df)

#     # Add new row form
#     st.write("Add a New Row")
#     # Extract asset list from the latest_price_df
#     asset_list = latest_price_df["ticker"].str.upper().tolist()
#     with st.form("add_row_form"):
#         change_date = st.date_input("Change Date")
#         asset = st.selectbox("Asset", asset_list)
#         action = st.selectbox("Action", [-1, 1])

#         change_quantity = st.number_input("Change Quantity", step=1)
#         target_price = st.number_input("Target Price",step=1000)
#         notes = st.text_area("Notes")
#         # Fetch the close price for the selected asset
#         change_price = latest_price_df[latest_price_df["ticker"].str.upper() == asset]["close"].values[0]
#         total_change = change_quantity * change_price
        
#         st.write(f"Change Price: {change_price}")
#         st.write(f"Total Change: {total_change}")
        
#         # Submit button
#         submit_button = st.form_submit_button(label="Add Row")
    
#     # Function to add a new change to changes_df
#     def add_change(change_date, asset, action, change_quantity, change_price, target_price, notes, changes_df):
#         total_change = change_quantity * change_price
#         new_row = pd.DataFrame({
#             "Change_Date": pd.to_datetime(change_date),
#             "Asset": asset,
#             "Action": action,
#             "Change_Quantity": change_quantity,
#             "Change_Price": change_price,
#             "Target Price": target_price,
#             "Notes": notes,
#             "Total Change": total_change
#         }, index=[0])
#         changes_df = pd.concat([changes_df, new_row], ignore_index=True)
#         changes_df["Q_Change"] = changes_df.apply(lambda row: -row["Action"] * row["Change_Quantity"] if row["Action"] == -1 else row["Action"] * row["Change_Quantity"], axis=1)
#         changes_df["Action_Cash"] = changes_df.apply(lambda row: -row["Total Change"] if row["Action"] == 1 else row["Total Change"], axis=1)
#         return changes_df
#     # Function to delete a change from changes_df
#     def delete_change(index):
#         changes_df = st.session_state.changes_df.drop(index)
#         changes_df.reset_index(drop=True, inplace=True)
#         st.session_state.changes_df = changes_df
#     # Add the new row to the dataframe
    
#     # Changes DataFrame
#     if "changes_df" not in st.session_state:
#         st.session_state.changes_df = pd.DataFrame({
#             "Change_Date": [],
#             "Asset": [],
#             "Action": [],
#             "Change_Quantity": [],
#             "Change_Price": [],
#             "Target Price": [],
#             "Notes": [],
#             "Total Change": []
#         })
#     if submit_button:
#         st.session_state.changes_df = add_change(change_date, asset, action, change_quantity, change_price, target_price, notes, st.session_state.changes_df)
#         st.success("New change added successfully!")
#         st.experimental_rerun()
        
#     # Display the changes DataFrame
#     st.write("Changes Data")
#     #st.dataframe(changes_df)
#     changes_df = st.session_state.changes_df
#     # Display each row with a delete button
#     # Create a unique identifier for each row to avoid Streamlit's button ID conflict
#     for i in range(len(changes_df)):
#         col1, col2 = st.columns([9, 1])
#         with col1:
#             st.write(changes_df.iloc[i].to_frame().T)
#         with col2:
#             if st.button("Delete", key=f"delete_{i}"):
#                 delete_change(i)
#                 st.experimental_rerun()

#     # To get the final planner DataFrame with all changes applied:
#     planner_df = pd.concat([planner_df, st.session_state.changes_df], ignore_index=True)
    
#     st.write("Final Planner Data with all changes applied:")
#     st.dataframe(planner_df)

#     st.title("Write to OneDrive Excel Sheet")
#     # Function to convert DataFrame to Excel
#     def convert_df_to_excel(df):
#         output = BytesIO()
#         with pd.ExcelWriter(output, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False, sheet_name='Planner Data')
#         processed_data = output.getvalue()
#         return processed_data
#     # Add a download button
#     excel = convert_df_to_excel(planner_df)
#     st.download_button(
#         label='Download Updated Planner as Excel File',
#         data=excel,
#         file_name='planner_df.xlsx',
#         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )

#LEVEL 2

        @timeit
        def process_cash_from_action(stock_action_df):
            #CURRENT CASH FROM STOCK ACTION
            current_cash_from_stock_action = stock_action_df.groupby('Change_Date')['Action_Cash'].sum().reset_index()
            #current_cash_from_stock_action['Change_Date'] = pd.to_datetime(current_cash_from_stock_action['Change_Date'], errors='coerce')
            # Rename the column to 'Cash_Change' for clarity
            current_cash_from_stock_action.rename(columns={'Action_Cash': 'Cash_Change'}, inplace=True)
            current_cash_from_stock_action = current_cash_from_stock_action.sort_values(by='Change_Date')
            current_cash_from_stock_action['Change_Date'] = pd.to_datetime(current_cash_from_stock_action['Change_Date'])
            
            return current_cash_from_stock_action

        current_cash_from_stock_action = process_cash_from_action(stock_action_df)

        #PLANNER TO STOCK ACTION
        planner_to_stock_action = pd.concat([planner_df, stock_action_df], ignore_index=True)

        #LEVEL 3
        #CURRENT CASH HISTORY
        @timeit
        def process_current_cash_history(cash_action_df,current_cash_from_stock_action):
            # Merge the dataframes
            merged_df = pd.merge(cash_action_df[['Change Date','Asset','Net Change']].groupby(['Change Date', 'Asset'], as_index=False)['Net Change'].sum(), current_cash_from_stock_action, how='outer', left_on='Change Date', right_on='Change_Date')
            # Replace null values in 'Asset' column with 'Trading'
            merged_df['Asset'].fillna('Trading', inplace=True)
            # Create 'Cash_Change_Date' column
            merged_df['Cash_Change_Date'] = merged_df['Change Date'].combine_first(merged_df['Change_Date'])
            # Replace null values in 'Net Change' and 'Cash_Change' columns with 0
            merged_df['Net Change'].fillna(0, inplace=True)
            merged_df['Cash_Change'].fillna(0, inplace=True)
            # Create 'Portfolio Change' column
            merged_df['Portfolio Change'] = merged_df['Net Change'] + merged_df['Cash_Change']
            # Group by 'Cash_Change_Date' and sum 'Portfolio Change'
            grouped_df = merged_df.groupby('Cash_Change_Date')['Portfolio Change'].sum().reset_index()
            # Rename columns for clarity
            grouped_df.rename(columns={'Cash_Change_Date': 'Date_Change', 'Portfolio Change': 'Cash_Change'}, inplace=True)
            # Add 'Asset' column with value 'Cash'
            grouped_df['Asset'] = 'Cash'

            # Reorder columns
            current_cash_history = grouped_df[['Asset', 'Date_Change', 'Cash_Change']].sort_values('Date_Change').reset_index(drop=True)
            return current_cash_history

        current_cash_history = process_current_cash_history(cash_action_df,current_cash_from_stock_action)

        @timeit
        def process_planner_cash_from_stock_action(planner_to_stock_action):
            # Planner_Cash_from_Stock_Action
            # Grouping the rows by "Change_Date" and summing the "Action_Cash" values
            Planner_Cash_from_Stock_Action = planner_to_stock_action.groupby('Change_Date', as_index=False).agg({'Action_Cash': 'sum'})

            # Renaming the column to match the desired output
            Planner_Cash_from_Stock_Action.rename(columns={'Action_Cash': 'Cash_from_StockAction'}, inplace=True)
            return Planner_Cash_from_Stock_Action

        Planner_Cash_from_Stock_Action = process_planner_cash_from_stock_action(planner_to_stock_action)

        #LEVEL 4:

        @timeit
        def process_current_cash_balance(current_cash_history):
            #CURRENT CASH BALANCE
            # Grouping by 'Asset' and summing 'Cash_Change'
            grouped_df = current_cash_history.groupby('Asset')['Cash_Change'].sum().reset_index()
            # Dividing 'Cash_Change' column values by 10000
            grouped_df['C_Quantity'] = grouped_df['Cash_Change'] / 10000

            # Adding 'C_CapitalCost' column
            grouped_df['C_CapitalCost'] = grouped_df['C_Quantity'] * 10000

            # Adding 'C_Price' column
            grouped_df['C_Price'] = 10000

            # Adding 'C_Target' column
            grouped_df['C_Target'] = 10000

            # Reordering columns
            current_cash_balance_df = grouped_df[['Asset', 'C_Quantity', 'C_CapitalCost', 'C_Target', 'C_Price']]
            return current_cash_balance_df

        current_cash_balance_df = process_current_cash_balance(current_cash_history)
        @timeit
        def process_planner_cash_balance(cash_action_df, Planner_Cash_from_Stock_Action):
            #PLANNER CASH BALANCE
            #Merging the DataFrames
            merged_df = pd.merge(cash_action_df[['Change Date','Asset','Net Change']].groupby(['Change Date', 'Asset'], as_index=False)['Net Change'].sum(), 
                                Planner_Cash_from_Stock_Action, 
                                left_on='Change Date', 
                                right_on='Change_Date', 
                                how='outer')
            # Creating the 'Date_Change' column
            merged_df['Date_Change'] = merged_df.apply(
                lambda row: row['Change Date'] if pd.notnull(row['Change Date']) else row['Change_Date'], 
                axis=1
            )
            # Replacing NaN values with 0 in 'Net Change' and 'Cash_from_StockAction' columns
            merged_df['Net Change'].fillna(0, inplace=True)
            merged_df['Cash_from_StockAction'].fillna(0, inplace=True)
            # Creating the 'Cash_Change' column
            merged_df['Cash_Change'] = merged_df['Net Change'] + merged_df['Cash_from_StockAction']
            # Grouping by 'Date_Change' and summing the 'Cash_Change' values
            grouped_df = merged_df.groupby('Date_Change')['Cash_Change'].sum().reset_index()
            # Adding the 'Asset' column
            grouped_df['Asset'] = 'Cash'
            # Grouping by 'Asset' and summing the 'Cash_Change' values
            final_grouped_df = grouped_df.groupby('Asset')['Cash_Change'].sum().reset_index()
            # Dividing 'Cash_Change' by 10000 to get 'P_Quantity'
            final_grouped_df['P_Quantity'] = final_grouped_df['Cash_Change'] / 10000
            # Creating the 'P_CapitalCost' column
            final_grouped_df['P_CapitalCost'] = final_grouped_df['P_Quantity'] * 10000
            # Adding the 'P_Target' column
            final_grouped_df['P_Target'] = 10000
            # Changing the data types
            final_grouped_df = final_grouped_df.astype({
                'P_Quantity': 'int64',
                'P_CapitalCost': 'int64',
                'P_Target': 'int64'
            })
            # Reordering the columns
            planner_cash_balance_df = final_grouped_df[['Asset', 'P_Quantity', 'P_CapitalCost', 'P_Target']]
            return planner_cash_balance_df
        planner_cash_balance_df = process_planner_cash_balance(cash_action_df, Planner_Cash_from_Stock_Action)
        #LEVEL 5

        @timeit
        def process_planner_cash_history(cash_action_df, Planner_Cash_from_Stock_Action):
            #PLANNER_CASH_HISTORY
            # Merging the tables
            Merged_Queries = pd.merge(cash_action_df[['Change Date','Asset','Net Change']].groupby(['Change Date', 'Asset'], as_index=False)['Net Change'].sum(), Planner_Cash_from_Stock_Action, left_on='Change Date', right_on='Change_Date', how='outer')

            # Adding 'Date_Change' column
            Merged_Queries['Date_Change'] = Merged_Queries['Change Date'].combine_first(Merged_Queries['Change_Date'])
            # Reordering columns
            Merged_Queries = Merged_Queries[['Date_Change', 'Asset', 'Change Date', 'Net Change', 'Change_Date', 'Cash_from_StockAction']]
            # Replacing null values
            Merged_Queries['Net Change'].fillna(0, inplace=True)
            Merged_Queries['Cash_from_StockAction'].fillna(0, inplace=True)
            # Adding 'Cash_Change' column
            Merged_Queries['Cash_Change'] = Merged_Queries['Net Change'] + Merged_Queries['Cash_from_StockAction']
            # Reordering columns again
            Merged_Queries = Merged_Queries[['Date_Change', 'Cash_Change', 'Asset', 'Change Date', 'Net Change', 'Change_Date', 'Cash_from_StockAction']]
            # Grouping by 'Date_Change' and summing 'Cash_Change'
            Grouped_Rows = Merged_Queries.groupby('Date_Change', as_index=False).agg({'Cash_Change': 'sum'})
            # Changing type of 'Date_Change' to date
            Grouped_Rows['Date_Change'] = pd.to_datetime(Grouped_Rows['Date_Change'])
            # Adding 'Asset' column with a constant value 'Cash'
            Grouped_Rows['Asset'] = 'Cash'
            # Reordering columns again
            Grouped_Rows = Grouped_Rows[['Asset', 'Date_Change', 'Cash_Change']]
            # Grouping by 'Asset' and summing 'Cash_Change'
            Grouped_Rows1 = Grouped_Rows.groupby('Asset', as_index=False).agg({'Cash_Change': 'sum'}).rename(columns={'Cash_Change': 'P_Quantity'})
            # Dividing 'P_Quantity' by 10000
            Grouped_Rows1['P_Quantity'] = Grouped_Rows1['P_Quantity'] / 10000
            # Adding 'P_CapitalCost' column
            Grouped_Rows1['P_CapitalCost'] = Grouped_Rows1['P_Quantity'] * 10000
            # Changing types
            Grouped_Rows1['P_Quantity'] = Grouped_Rows1['P_Quantity'].astype(np.int64)
            Grouped_Rows1['P_CapitalCost'] = Grouped_Rows1['P_CapitalCost'].astype(np.int64)

            # Adding 'P_Target' column
            Grouped_Rows1['P_Target'] = 10000
            # Changing type of 'P_Target'
            Grouped_Rows1['P_Target'] = Grouped_Rows1['P_Target'].astype(np.int64)
            planner_cash_history = Grouped_Rows1
            return planner_cash_history

        planner_cash_history = process_planner_cash_history(cash_action_df, Planner_Cash_from_Stock_Action)

        @timeit
        def process_current_stock_view(stock_action_df, latest_price_df, current_cash_balance_df):
            grouped_df = stock_action_df.groupby("Asset").agg(
                P_Quantity=pd.NamedAgg(column="Q_Change", aggfunc="sum"),
                P_CapitalCost=pd.NamedAgg(column="Action_Cash", aggfunc=lambda x: -sum(x)),
                P_Target=pd.NamedAgg(column="Target Price", aggfunc="mean")
            ).reset_index()

            # Merge with latest price data
            merged_df = pd.merge(grouped_df, latest_price_df.rename(columns={'close':"C_Price"})[['ticker','C_Price']], left_on="Asset", right_on="ticker", how="left")
            merged_df.drop("ticker", axis=1,inplace=True)

            # Rename columns
            merged_df = merged_df.rename(columns={"close": "C_Price", "P_Target": "C_Target", "P_CapitalCost": "C_CapitalCost", "P_Quantity": "C_Quantity"})


            merged_df = pd.concat([merged_df, current_cash_balance_df], ignore_index=True)


            merged_df["C_Price"] = merged_df["C_Price"].fillna(0).astype("int64")
            merged_df["C_Quantity"] = merged_df["C_Quantity"].fillna(0).astype("int64")

            # Adding custom columns
            merged_df["UnitCost"] = merged_df.apply(lambda row: row["C_CapitalCost"] / row["C_Quantity"] if row["C_Quantity"] > 0 else 0, axis=1)
            merged_df["UnitCost"] = merged_df["UnitCost"].fillna(0).astype("int64")
            merged_df["C_Amount"] = merged_df["C_Quantity"] * merged_df["C_Price"]
            merged_df["C_Amount"] = merged_df["C_Amount"].fillna(0).astype("int64")

            # # Merge with company industry data
            merged_df = pd.merge(merged_df, company_industry_df, left_on="Asset", right_on='Stock', how="left")

            # Adding more custom columns
            merged_df["C_PL"] = merged_df.apply(lambda row: row["C_Price"] / row["UnitCost"] - 1 if row["C_Quantity"] > 0 else 0, axis=1)
            merged_df["C_Upside"] = merged_df.apply(lambda row: row["C_Target"] / row["C_Price"] - 1 if row["C_Quantity"] > 0 else 0, axis=1)

            # # Ensure C_PL and C_Upside are of type float64
            merged_df["C_PL"] = merged_df["C_PL"].astype("float64")
            merged_df["C_Upside"] = merged_df["C_Upside"].astype("float64")

            # Reorder columns
            columns_order = ["Asset", "C_Quantity", "C_CapitalCost", "C_Target", "C_Price", "UnitCost", "C_Amount", "C_PL", "C_Upside", "L4N", "L3N", "L2N", "L1N"]
            current_stock_view_df = merged_df[columns_order]
            return current_stock_view_df

        current_stock_view_df = process_current_stock_view(stock_action_df, latest_price_df, current_cash_balance_df)

        @timeit
        def process_planner_cash_balance(planner_to_stock_action, planner_cash_balance_df,company_industry_df, latest_price_df):
            #PLANNER STOCKVIEW
            # Group by "Asset" and aggregate
            grouped_df = planner_to_stock_action.groupby("Asset").agg(
                P_Quantity=pd.NamedAgg(column="Q_Change", aggfunc="sum"),
                P_CapitalCost=pd.NamedAgg(column="Total Change", aggfunc="sum"),
                P_Target=pd.NamedAgg(column="Target Price", aggfunc="mean")
            ).reset_index()

            # Append planner cash balance (assuming planner_cash_balance_df is your dataframe)
            # planner_cash_balance_df should be defined or replace it with the correct dataframe
            # Append current planner cash balance
            appended_df = pd.concat([grouped_df, planner_cash_balance_df], ignore_index=True)

            # Merge with latest price data
            merged_df = pd.merge(appended_df, latest_price_df, left_on="Asset", right_on="ticker", how="left")

            # Replace null values in "Price_Current" with 10000
            merged_df["close"].fillna(10000, inplace=True)

            # Rename columns
            merged_df = merged_df.rename(columns={"close": "P_Price"})

            # Adding custom columns
            merged_df["UnitCost"] = merged_df.apply(lambda row: row["P_CapitalCost"] / row["P_Quantity"] if row["P_Quantity"] != 0 else 0, axis=1)
            merged_df["P_Amount"] = merged_df["P_Quantity"] * merged_df["P_Price"]

            # Change types
            merged_df = merged_df.astype({"UnitCost": "int64", "P_Amount": "int64"})

            # Adding custom columns
            merged_df["P_Upside"] = merged_df.apply(lambda row: row["P_Target"] / row["P_Price"] - 1 if row["P_Quantity"] > 0 else 0, axis=1)

            # Merge with company industry data
            merged_df = pd.merge(merged_df, company_industry_df, left_on="Asset", right_on="Stock", how="left")

            # Reorder columns
            columns_order = ["Asset", "P_Quantity", "P_CapitalCost", "P_Target", "P_Price", "P_Upside", "L4N", "L3N", "L2N", "L1N", "UnitCost", "P_Amount"]
            planner_stock_view_df = merged_df[columns_order]
            return planner_stock_view_df

        planner_stock_view_df = process_planner_cash_balance(planner_to_stock_action, planner_cash_balance_df,company_industry_df, latest_price_df)

        # LEVEL 6
        @timeit
        def calculate_daily_positions(cash_action_df, stock_action_df, fund_input_price_df):
            # Identify the first transaction date
            first_transaction_date = min(cash_action_df['Change Date'].min(), stock_action_df['Change_Date'].min())

            # Generate a date range from the first transaction date to the current date
            date_range = pd.date_range(start=first_transaction_date, end=pd.Timestamp.today())

            # Initialize an empty list to hold the daily stock view
            daily_stock_view = []

            # Initialize current holdings
            current_holdings = {}

            # Initialize cash balance
            cash_balance = 0

            # Initialize fund certificate data
            fund_certificate_data = []
            ccq_price = 10000
            total_asset_value_closing_previous_day = 0
            closing_ccq_price_previous_day = ccq_price
            
            # Initialize customer CCQ data and issuance history
            customer_ccq = []
            ccq_issuance_history = []
            customer_balances = {}

            # Precompute daily cash actions and stock transactions to avoid repeated filtering
            daily_cash_actions_dict = {date: cash_action_df[cash_action_df['Change Date'] == date] for date in date_range}
            daily_transactions_dict = {date: stock_action_df[stock_action_df['Change_Date'] == date] for date in date_range}

            # Precompute the latest price for each asset at each date to avoid repeated lookups
            fund_input_price_df[fund_input_price_df['ticker'].isin(stock_action_df['Asset'].unique())]
            fund_input_price_df = fund_input_price_df.sort_values(by=['ticker', 'time'])
            fund_input_price_dict = fund_input_price_df.groupby('ticker').apply(lambda x: dict(zip(x['time'], x['close']))).to_dict()

            # Function to get the latest available price before the given date
            def get_latest_price(date, price_dict):
                dates = [d for d in price_dict.keys() if d <= date]
                if dates:
                    latest_date = max(dates)
                    return price_dict[latest_date]
                return np.nan

            # Process daily positions
            for date in date_range:
                
                # Set initial balances
                for asset in list(current_holdings.keys()):
                    current_holdings[asset]['Start_Balance'] = current_holdings[asset]['End_Balance']
                    current_holdings[asset]['Change_Quantity'] = 0
                
                # Track starting cash balance at the beginning of the day
                start_cash_balance = cash_balance
                
                # Update cash actions for the current date
                daily_cash_actions = daily_cash_actions_dict.get(date, pd.DataFrame())
                net_cash_flow = 0
                value_issued = 0
                for _, cash_action in daily_cash_actions.iterrows():
                    action = cash_action['Action']
                    asset = cash_action['Asset']
                    net_change = cash_action['Net Change']
                    customer = cash_action['Customer']
                    cash_balance += net_change
                    
                    if asset == "Cash":
                        # Only issue or buy back CCQs if the asset is "Cash"
                        net_cash_flow += net_change
                        value_issued += net_change
                        
                        if customer not in customer_balances:
                            customer_balances[customer] = {'Opening_Balance': 0, 'CCQ_Balance': 0, 'Total_Capital_Cost': 0}
                        
                        ccq_change_quantity = round(net_change / closing_ccq_price_previous_day, 1) if closing_ccq_price_previous_day != 0 else 0
                        ccq_change_value = net_change
                        customer_balances[customer]['CCQ_Balance'] += ccq_change_quantity
                        customer_balances[customer]['Total_Capital_Cost'] += net_change
                        
                        ccq_issuance_history.append({
                            'Transaction Date': date,
                            'Customer': customer,
                            'Change Quantity': abs(ccq_change_quantity),
                            'Type': 1 if net_change > 0 else -1,
                            'CCQ Change Price': closing_ccq_price_previous_day,
                            'Total Change': net_change
                        })
                
                # Update stock transactions for the current date
                daily_transactions = daily_transactions_dict.get(date, pd.DataFrame())
                for _, transaction in daily_transactions.iterrows():
                    asset = transaction['Asset']
                    action = transaction['Action']
                    quantity_change = transaction['Q_Change']
                    price = transaction['Change_Price']
                    value_change = transaction['Total Change']

                    if asset not in current_holdings:
                        current_holdings[asset] = {'Start_Balance': 0, 'End_Balance': 0, 'Change_Price': 0, 'Change_Quantity': 0}

                    current_holdings[asset]['Change_Quantity'] += quantity_change
                    current_holdings[asset]['Change_Price'] = price
                    current_holdings[asset]['End_Balance'] += quantity_change

                    if action == 1:  # Buy
                        cash_balance -= (value_change + (value_change * 0.001))  # Deduct cash with fee
                    elif action == -1:  # Sell
                        cash_balance += (value_change - (value_change * 0.001))  # Add cash minus fee
                
                # Calculate daily stock values
                total_asset_value_opening = total_asset_value_closing_previous_day
                total_asset_value_closing = 0
                assets_to_remove = []
                for asset in list(current_holdings.keys()):
                    start_balance = current_holdings[asset]['Start_Balance']
                    end_balance = current_holdings[asset]['End_Balance']
                    change_quantity = current_holdings[asset]['Change_Quantity']
                    change_price = current_holdings[asset]['Change_Price']
                    
                    # Get current price from fund_input_price_df
                    current_price = get_latest_price(date, fund_input_price_dict.get(asset, {}))
                    
                    current_total_value = end_balance * current_price
                    total_asset_value_closing += current_total_value
                    
                    daily_stock_view.append({
                        'Date': date,
                        'Asset': asset,
                        'Start_Balance': start_balance,
                        'Change_Quantity': change_quantity,
                        'End_Balance': end_balance,
                        'Change_Price': change_price if change_quantity != 0 else np.nan, # Only set Change_Price if there was a transaction
                        'Current_Price': current_price,
                        'Current_Total_Value': current_total_value
                    })
                    
                    current_holdings[asset]['Current_Price'] = current_price

                    # Remove asset if end balance is 0
                    if end_balance == 0:
                        assets_to_remove.append(asset)
                        
                # Remove assets with end balance 0
                for asset in assets_to_remove:
                    del current_holdings[asset]
                # Append cash data
                total_asset_value_closing += cash_balance
                daily_stock_view.append({
                    'Date': date,
                    'Asset': 'Cash',
                    'Start_Balance': start_cash_balance,
                    'Change_Quantity': cash_balance - start_cash_balance,
                    'End_Balance': cash_balance,
                    'Change_Price': np.nan,
                    'Current_Price': 1,
                    'Current_Total_Value': cash_balance
                })
                
                # Calculate fund certificate data
                if len(fund_certificate_data) == 0:
                    start_ccq_balance = 0
                    ccq_issued = 0
                    closing_ccq_price = ccq_price if total_asset_value_closing != 0 else 0
                else:
                    start_ccq_balance = fund_certificate_data[-1]['End_CCQ_Balance']
                    closing_ccq_price = closing_ccq_price_previous_day
                
                opening_ccq_price = closing_ccq_price
                
                # Prevent division by zero error
                if opening_ccq_price != 0:
                    ccq_issued = round(value_issued / opening_ccq_price, 1)
                else:
                    ccq_issued = 0
                
                end_ccq_balance = start_ccq_balance + ccq_issued
                closing_ccq_price = round(total_asset_value_closing / end_ccq_balance if end_ccq_balance != 0 else 0, 1)
                
                # Calculate the current cash ratio for the day
                current_cash_ratio = (cash_balance / total_asset_value_closing) * 100
                
                fund_certificate_data.append({
                    'Date': date,
                    'Total_Asset_Value_Opening': total_asset_value_opening,
                    'Start_CCQ_Balance': start_ccq_balance,
                    'Opening_CCQ_Price': opening_ccq_price,
                    'Value_Issued': value_issued,
                    'CCQ_Issued': ccq_issued,
                    'End_CCQ_Balance': end_ccq_balance,
                    'Total_Asset_Value_Closing': total_asset_value_closing,
                    'Closing_CCQ_Price': closing_ccq_price,
                    'Current_Cash_Ratio': current_cash_ratio
                })
                
                # Update previous day's values for next iteration
                total_asset_value_closing_previous_day = total_asset_value_closing
                closing_ccq_price_previous_day = closing_ccq_price

                # Update daily customer CCQ balances
                for customer, balance in customer_balances.items():
                    opening_balance = balance['Opening_Balance']
                    ccq_balance = balance['CCQ_Balance']
                    total_capital_cost = balance['Total_Capital_Cost']
                    
                    # Determine if there was a change on this day
                    daily_cash_action = daily_cash_actions[daily_cash_actions['Customer'] == customer]
                    if not daily_cash_action.empty:
                        net_change = daily_cash_action['Net Change'].sum()
                        ccq_change_quantity = daily_cash_action.apply(lambda x: round(x['Net Change'] / closing_ccq_price_previous_day, 1) if closing_ccq_price_previous_day != 0 else 0, axis=1).sum()
                        ccq_change_value = net_change
                        change_type = 'Issue' if net_change > 0 else 'Redeem'
                    else:
                        ccq_change_quantity = 0
                        ccq_change_value = 0
                        change_type = ''
                    
                    customer_ccq.append({
                        'Date': date,
                        'Customer': customer,
                        'Opening balance': opening_balance,
                        'Opening asset value': opening_balance * closing_ccq_price_previous_day,
                        'Change Type': change_type,
                        'CCQ Change Quantity': ccq_change_quantity,
                        'CCQ Change Price': closing_ccq_price_previous_day,
                        'CCQ Change Value': ccq_change_value,
                        'Ending balance': ccq_balance,
                        'Ending asset value': ccq_balance * closing_ccq_price_previous_day,
                        'Total Capital Cost': total_capital_cost,
                        'Average cost of CCQ': total_capital_cost / ccq_balance if ccq_balance != 0 else 0
                    })
                    
                    # Update the opening balance for the next day
                    balance['Opening_Balance'] = ccq_balance

            # Convert the list of dictionaries to DataFrames
            daily_stock_view_df = pd.DataFrame(daily_stock_view)
            fund_certificate_df = pd.DataFrame(fund_certificate_data)
            customer_ccq_df = pd.DataFrame(customer_ccq)
            ccq_issuance_history_df = pd.DataFrame(ccq_issuance_history)

            # Calculate changes in price
            fund_certificate_df['Change_L30D'] = fund_certificate_df['Closing_CCQ_Price'].pct_change(periods=30)
            fund_certificate_df['Change_L90D'] = fund_certificate_df['Closing_CCQ_Price'].pct_change(periods=90)

            # Calculate Change_YTD
            start_of_year = pd.Timestamp(year=pd.Timestamp.today().year, month=1, day=1)
            fund_start_date = max(start_of_year, fund_certificate_df['Date'].min())
            initial_price = fund_certificate_df[fund_certificate_df['Date'] == fund_start_date]['Closing_CCQ_Price'].values[0]
            fund_certificate_df['Change_YTD'] = fund_certificate_df['Closing_CCQ_Price'] / initial_price - 1

            return daily_stock_view_df, fund_certificate_df, customer_ccq_df, ccq_issuance_history_df

        daily_stock_view_df, fund_certificate_df, customer_ccq_df, ccq_issuance_history_df = calculate_daily_positions(cash_action_df, stock_action_df, fund_input_price_df)

        @timeit
        def calculate_fund_allocation(current_stock_view_df):
            filtered_stock_view_df = current_stock_view_df[current_stock_view_df['L1N'].notna() & (current_stock_view_df['L1N'] != '')]

            # Sidebar for filtering
            selected_L1N = st.multiselect('Select L1N values:', options=filtered_stock_view_df['L1N'].unique(), default=filtered_stock_view_df['L1N'].unique())

            # Filter the dataframe based on selected L1N values
            filtered_stock_view_df = filtered_stock_view_df[filtered_stock_view_df['L1N'].isin(selected_L1N)]

            # Group by L1N and sum C_Amount
            fund_allocation = filtered_stock_view_df.groupby('L1N')['C_Amount'].sum().reset_index()

            # Recalculate the percentages for the grouped data
            total_amount = fund_allocation['C_Amount'].sum()
            fund_allocation['C_Amount (%)'] = (fund_allocation['C_Amount'] / total_amount) * 100

            # Keep only L1N and C_Amount (%) columns
            fund_allocation = fund_allocation[['L1N', 'C_Amount (%)']]
            # Sort the dataframe by C_Amount (%) in ascending order
            fund_allocation = fund_allocation.sort_values(by='C_Amount (%)', ascending=False)
            fund_allocation = fund_allocation[fund_allocation['C_Amount (%)'] != 0]
            # Format the percentages
            fund_allocation['C_Amount (%)'] = fund_allocation['C_Amount (%)'].map("{:.2f}%".format)

            return fund_allocation
    with show_data:
        st.header("Latest Price Data")
        st.dataframe(latest_price_df)

        st.header("Stock Action Data")
        st.dataframe(stock_action_df)

        st.header("Cash Action Data")
        st.dataframe(cash_action_df)

        st.header('Planner')
        st.dataframe(planner_df)
        
        st.header("Reference")
        st.dataframe(company_industry_df)
        
        st.header("Full Price Data")
        st.dataframe(fund_input_price_df)
        
        st.header("Dilution Factor")
        st.dataframe(diluted_df)
        
        st.header("VNINDEX")
        st.dataframe(vn_index)

with processing:
    current_portfolio_section,planner_portfolio_section=st.tabs(["Current Portfolio","Planner Portfolio"])
    with current_portfolio_section:
        st.header("Current Cash Balance")
        st.dataframe(current_cash_balance_df)
        
        st.header("Current Cash from Stock Action")
        st.dataframe(current_cash_from_stock_action)
        
        st.header("Current Cash History")
        st.dataframe(current_cash_history)
        
        st.header("Current Stock View")
        st.dataframe(current_stock_view_df)
    with planner_portfolio_section:
        st.header("Planner Cash Balance")
        st.dataframe(planner_cash_balance_df)

        st.header("Planner to Stock Action")
        st.dataframe(Planner_Cash_from_Stock_Action)
        
        st.header("Planner Cash from Stock Action")
        st.dataframe(planner_to_stock_action)

        st.header("Planner Stock View")
        st.dataframe(planner_stock_view_df)
            
        st.header("Planner Cash History")
        st.dataframe(planner_cash_history)

with summary_portfolio:
    portfolio_performance, portfolio_allocation, portfolio_details, trading_history = st.tabs(["Performance", "Portfolio Allocation",'Detailed Portfolio','Trading History'])
    
    with portfolio_performance:
        st.subheader(f"DISCLAIMER: LATEST UPDATE ON {last_transaction_date.strftime('%Y-%m-%d')}")
        selected_date = st.date_input("Select a date", last_transaction_date)
        selected_date = pd.to_datetime(selected_date)
        col1, col2 = st.columns(2)
        with col1:
            # Format the results
            fund_certificate_df['Change_L30D'] = fund_certificate_df['Change_L30D'].map(lambda x: f'{x:.2%}')
            fund_certificate_df['Change_L90D'] = fund_certificate_df['Change_L90D'].map(lambda x: f'{x:.2%}')
            fund_certificate_df['Change_YTD'] = fund_certificate_df['Change_YTD'].map(lambda x: f'{x:.2%}')
            fund_certificate_df['Current_Cash_Ratio'] = fund_certificate_df['Current_Cash_Ratio'].map(lambda x: f'{x:.2f}%')

            
            def get_value(df, date, column):
                if date in df['Date'].values:
                    return df.loc[df['Date'] == date, column].values[0]
                else:
                    return 'N/A'

            def get_value_vnindex(df, date, column):
                if date in df['date'].values:
                    return df.loc[df['date'] == date, column].values[0]
                else:
                    return 'N/A'

            # Create the summary table
            summary_table = pd.DataFrame({
                'Metric': ['Change L30D', 'Change L90D', 'Change YTD', 'Current Cash Ratio'],
                'Lucid Fund': [
                    fund_certificate_df.loc[fund_certificate_df['Date'] == selected_date, 'Change_L30D'].values[0],
                    fund_certificate_df.loc[fund_certificate_df['Date'] == selected_date, 'Change_L90D'].values[0],
                    fund_certificate_df.loc[fund_certificate_df['Date'] == selected_date, 'Change_YTD'].values[0],
                    fund_certificate_df.loc[fund_certificate_df['Date'] == selected_date, 'Current_Cash_Ratio'].values[0]
                ],
                'VNINDEX': [
                    get_value_vnindex(vn_index, selected_date, 'Change_L30D'),
                    get_value_vnindex(vn_index, selected_date, 'Change_L90D'),
                    get_value_vnindex(vn_index, selected_date, 'Change_YTD'),
                    '0%'
                ]
            })
            st.header("Summary Table:")
            st.dataframe(summary_table)
        with col2:
            st.header("History Summary")
            st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%;'><span><b>Total Portfolio Value (1) = (2) + (3):</b></span><span style='text-align: right;'>{daily_stock_view_df[daily_stock_view_df['Date']==selected_date]['Current_Total_Value'].sum():,.0f} VND</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%;'><span><b>Total Cash In Portfolio (2):</b></span><span style='text-align: right;'>{round(current_cash_balance_df['C_CapitalCost'].sum(), 0):,.0f} VND</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%;'><span><b>Total Stock Value In Portfolio (3):</b></span><span style='text-align: right;'>{round(current_stock_view_df[current_stock_view_df['Asset']!='Cash']['C_Amount'].sum(), 0):,.0f} VND</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%;'><span><b>Total Cash In (Dividend After Tax + Customer) (4) = (2) + (5):</b></span><span style='text-align: right;'>{cash_action_df['Net Change'].sum():,.0f} VND</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='display: flex; justify-content: space-between; width: 100%;'><span><b>Net Cash Buying Stock (5):</b></span><span style='text-align: right;'>{-round(current_cash_from_stock_action['Cash_Change'].sum(), 0):,.0f} VND</span></div>", unsafe_allow_html=True)
            
        st.header("Current Portfolio")
        st.dataframe(current_stock_view_df)
        
        # Display the results
        st.header("Daily Stock View:")
        st.dataframe(daily_stock_view_df)

        st.header("Fund Certificate Data")
        st.dataframe(fund_certificate_df)
        
        st.header("Customer CCQ History")
        st.dataframe(ccq_issuance_history_df)
        st.header("Customer CCQ Balance")
        st.dataframe(customer_ccq_df)


    with portfolio_allocation:
        st.header("Industry Level Allocation")
        fund_allocation=calculate_fund_allocation(current_stock_view_df)
        st.dataframe(fund_allocation)
    
    with portfolio_details:
        
        # Button to include or exclude "Cash"
        include_cash = st.checkbox("Include Cash", value=True)
        # Filter dataframes based on the button state
        if not include_cash:
            st.write("Note: Currently our portfolio details doesn't include Cash")
            current_stock_view_df = current_stock_view_df[current_stock_view_df['Asset'] != 'Cash']
            planner_stock_view_df = planner_stock_view_df[planner_stock_view_df['Asset'] != 'Cash']
        else:
            st.write("Note: Currently our portfolio details include Cash")
        # Calculate contribution of each asset
        current_stock_view_df['Contribution'] = current_stock_view_df['C_CapitalCost'] / current_stock_view_df['C_CapitalCost'].sum() * 100
        planner_stock_view_df['Contribution'] = planner_stock_view_df['P_CapitalCost'] / planner_stock_view_df['P_CapitalCost'].sum() * 100
        col1, col2 = st.columns(2)
        with col1:
            st.header("Portfolio Details")
            current_stock_view_df['C_PL'] = (current_stock_view_df['C_PL']*100).map('{:.2f}%'.format)
            current_stock_view_df['Contribution'] = current_stock_view_df['Contribution'].map('{:.2f}%'.format)

            st.dataframe(current_stock_view_df[['Asset','C_CapitalCost','C_Price','UnitCost','C_PL','Contribution']])

        with col2:
            st.header("Portfolio Details (Planner)")
            planner_stock_view_df['Contribution'] = planner_stock_view_df['Contribution'].map('{:.2f}%'.format)
            st.dataframe(planner_stock_view_df[['Asset','P_CapitalCost','P_Price','Contribution']])
            
    with trading_history:
        st.header("Trading History")
        st.write("Not Available Yet, Coming up in Beta")

with analysis:
    st.header("Pivot Table")
    from st_aggrid import AgGrid, GridOptionsBuilder
    # Create AgGrid options builder
    gb = GridOptionsBuilder.from_dataframe(current_stock_view_df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(editable=True, groupable=True, filterable=True)

    # Add pivot mode
    gb.configure_grid_options(enablePivot=True)
    # Enable column dragging
    gb.configure_default_column(enableRowGroup=True, enablePivot=True, enableValue=True)

    # Build grid options
    grid_options = gb.build()

    # Display the pivot table
    AgGrid(
        current_stock_view_df,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        update_mode='value_changed',
        height=500,
        width='100%',
        allow_unsafe_jscode=True  # Set it to True to allow JavaScript in the table
    )
    

# https://chatgpt.com/c/f1a4fd4b-739b-4c64-a736-c814ee6dfa26