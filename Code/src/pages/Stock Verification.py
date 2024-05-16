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

# Create tabs
list_tabs=["Basic Info", "Financial Statements","Deal And Events","Calculation",'Trading Data','Full Data',"QA"]
basic_info, finance, events,calculation,trading_data,full_data,QA_data = st.tabs(list_tabs)

#Set up parameter
risk_free_rate=7/100
income_tax=20/100

indicator_range_max=1.1
indicator_range_min=0.5
score_modifier_max=0.8
score_modifier_min=0.5

#Data 
profile_url = ' https://raw.githubusercontent.com/penthousecompany/master/main/curated/curated_company_profile.csv'
income_url_yearly = 'https://raw.githubusercontent.com/penthousecompany/master/main/raw/financial_report_incomestatement_yearly_final/financial_report_incomestatement_yearly_final.csv'
income_url_quarterly = 'https://1drv.ms/u/s!Agfa0F4-51Tw9zDy33ngzmL0I1YO?e=kbYvsQ'
bs_url_quarterly = 'https://1drv.ms/u/s!Agfa0F4-51Tw9zU8x1-kPUZnvv5g?e=y4tWat'

direct_cash_flow_url_yearly = r'data/raw/financial_report_cashflow_direct_yearly_final.csv'
indirect_cash_flow_url_yearly = r'data/raw/financial_report_cashflow_indirect_yearly_final.csv'

def finance_dict_to_dataframe(ticker_data_dict):
    # Initialize a list to store the data and a set for unique accounts
    data_for_df = []
    ordered_accounts = []
    
    # Iterate over each year in the dictionary
    for year, accounts in ticker_data_dict.items():
        if year != "Appendix":  # Exclude the appendix
            for account, value in accounts.items():
                # Append data for DataFrame
                data_for_df.append({"Year": year, "Account": account, "Value": value})
                # Keep track of the order of accounts
                if account not in ordered_accounts:
                    ordered_accounts.append(account)
    
    # Create a DataFrame
    df = pd.DataFrame(data_for_df)
    
    # Reshape the DataFrame to have years as columns and accounts as rows
    try:
        df_pivoted = df.pivot(index="Account", columns="Year", values="Value").reset_index()
    except KeyError as e:
        print(f"KeyError occurred: {e}")
        st.write("Data doesn't exist or Error")
        # Handle the error or debug further
        return pd.DataFrame()  # Or return None, based on your use case
    # Reorder the DataFrame rows based on the original account order
    df_ordered = df_pivoted.set_index("Account").reindex(ordered_accounts).reset_index()
    
    return df_ordered

def select_ticker(ticker_list):
    user_input_ticker = st.selectbox('Select a Ticker', ticker_list)

    # Function to handle option selection
    # Process input
    if user_input_ticker:
        # Normalize input and company display names to lowercase for case-insensitive matching
        st.session_state['selected_company']=user_input_ticker
    else:
        st.write("There's no company matching")
    if st.session_state.get('selected_company'):
        selected_option = st.session_state['selected_company']
        selected_ticker = selected_option.split(' - ')[0]
    return selected_ticker

def calculate_weighted_averages(df, level):
    """
    Calculates weighted averages of specified metrics by Gross Revenue for top 5 companies in each industry level.

    Args:
    - df: DataFrame containing company financials and rankings.
    - level: Industry level ('L1N', 'L2N', 'L3N', 'L4N').

    Returns:
    - DataFrame with industry name, level, and calculated weighted averages of metrics.
    """
    # Define the metrics for which to calculate weighted averages
    metrics = ['ROE', 'ROA', 'Receivable Turnover', 'Inventory Turnover', 'CA Turnover',
               'TA Turnover', 'Current Ratio', 'Interest Coverage Ratio', 'Leverage',
               'Short-term/Total Liabilities', 'P/S', 'P/B']
    
    # Filter top 5 companies based on rank within each industry level
    top_5_df = df[df[f'Rank {level}'] <= 5]
    
    # Calculate weighted averages
    weighted_avgs = top_5_df.groupby(level).apply(
        lambda x: pd.Series(
            {metric: np.average(x[metric], weights=x['Gross Revenue']) for metric in metrics}
        )
    ).reset_index()
    
    # Add industry level to the DataFrame
    weighted_avgs['Industry Level'] = level
    
    # Rename columns if necessary and reorder
    weighted_avgs = weighted_avgs.rename(columns={level: 'Industry Name'})
    weighted_avgs = weighted_avgs[['Industry Name', 'Industry Level'] + metrics]
    
    return weighted_avgs

def period_to_datetime(period):
    try:
        # For "YYYY" format
        return datetime(year=int(period.strip()), month=1, day=1)
    except ValueError:
        try:
            # For "Quý X- YYYY" format
            quarter, year = period.split('-')
            quarter_number = int(quarter.split(' ')[1])
            start_month = (quarter_number - 1) * 3 + 1
            return datetime(year=int(year.strip()), month=start_month, day=1)
        except ValueError:
            # If the period doesn't conform to expected formats, return None
            return None

def transform_to_dataframe(health_data, health_groups):
    ticker=list(health_data.keys())[0]
    # Prepare the multi-index for columns
    tuples = [(group, metric) for group, metrics in health_groups.items() for metric in metrics]
    multi_index = pd.MultiIndex.from_tuples(tuples, names=['Health Valuation', 'Metric'])

    # Prepare the data for the DataFrame
    # Rows will contain data for Ticker, Benchmark, and Score in that order
    data = {
        ticker: [],
        'Benchmark': [],
        'Score': []
    }

    for group, metrics in health_groups.items():
        for metric in metrics:
            data[ticker].append(health_data[ticker].get(metric, None))
            data['Benchmark'].append(health_data['Benchmark'].get(metric, None))
            data['Score'].append(health_data['Score'].get(metric, None))

    # Create the DataFrame with a list of the data dictionaries
    df = pd.DataFrame([data[ticker], data['Benchmark'], data['Score']], 
                      index=[ticker, 'Benchmark', 'Score'],
                      columns=multi_index)
    return df

@st.cache_data
def build_company_metrics_dataframe(ticker, company_finance_df, industry_summary_df):
    # Group the metrics columns
    global groups

    # Flatten the group structure for easier data retrieval
    metrics_columns = [metric for group in groups.values() for metric in group]

    final_dataframe_list = []

    # Retrieve the row for the input ticker to get industry levels and names
    company_row = company_finance_df.loc[company_finance_df['ticker'] == ticker]

    if company_row.empty:
        print(f"No data found for ticker {ticker}.")
        return None

    industry_info = company_row[['L1N', 'L2N', 'L3N', 'L4N']].iloc[0]

    for level, industry_name in industry_info.dropna().items():
        # Get all companies in the industry to calculate the total industry Gross Revenue
        full_industry_df = company_finance_df[company_finance_df[level] == industry_name]
        total_industry_revenue = full_industry_df['Gross Revenue'].sum()

        # Get the top 5 companies and their detailed data
        top_industry_df = full_industry_df.nsmallest(5, f'Rank {level}')
        
        # Calculate Sales Share for each top company
        top_industry_df['Sales Share'] = top_industry_df['Gross Revenue'] / total_industry_revenue
        top_industry_df['Receivable Turnover'] = top_industry_df['Receivable Turnover'].clip(upper=50)
        top_industry_df['Inventory Turnover'] = top_industry_df['Inventory Turnover'].clip(upper=50)
        top_industry_df['Interest Coverage Ratio'] = top_industry_df['Interest Coverage Ratio'].clip(upper=100)
        # Get the list of top 5 company tickers
        top_companies = top_industry_df['ticker'].tolist()
        
        multi_index = pd.MultiIndex.from_product(
            [[level[-2]], [industry_name], ['Industry Average'] + top_companies],
            names=['Level', 'Industry', 'Company']
        )
        
        # Retrieve metrics for the top companies and calculate industry average
        metrics_columns_with_share = ['Sales Share'] + metrics_columns
        metrics_data = top_industry_df[metrics_columns_with_share]
        industry_average_metrics = metrics_data.mean().round(2)  # Get average metrics including averaged Sales Share

        # Create a MultiIndex for groups and metrics including 'Sales Share'
        tuples = [('Sales Share', 'Sales Share')] + [(group, metric) for group in groups for metric in groups[group]]
        multi_column = pd.MultiIndex.from_tuples(tuples, names=['Group', 'Metric'])

        # Initialize an empty DataFrame to hold reordered metrics with MultiIndex
        metrics_data_reordered = pd.DataFrame(columns=multi_column, index=metrics_data.index)
        
        # Populate the DataFrame
        metrics_data_reordered[('Sales Share', 'Sales Share')] = metrics_data['Sales Share']
        for group, metrics in groups.items():
            for metric in metrics:
                metrics_data_reordered[(group, metric)] = metrics_data[metric]
        
        # Add the industry average metrics to the DataFrame
        industry_average_df = pd.DataFrame([industry_average_metrics.values], columns=pd.MultiIndex.from_tuples([('Sales Share', 'Sales Share')] + [(group, metric) for group in groups for metric in groups[group]]))
        combined_metrics_df = pd.concat([industry_average_df, metrics_data_reordered])

        combined_metrics_df.index = multi_index
        
        final_dataframe_list.append(combined_metrics_df)

    final_df = pd.concat(final_dataframe_list)
    return final_df


@st.cache_data
def industry_benchmark_dataframe_to_html(df, base_color_hex="#36454F"):  # Header color: charcoal
    # Define a light color for data rows and adjust lightness based on level
    def adjust_row_color(base_color, level):
        base_lightness = 245  # Start light for data rows (light greyish)
        lightness_adjustment = 10 * int(level)
        return f"rgb(255, {base_lightness - lightness_adjustment}, {base_lightness - lightness_adjustment})"

    header_color = base_color_hex
    text_color = "#FFFFFF"  # White text for headers
    row_text_color = "#000000"  # Black text for data

    html = (
        f"<style>"
        f"table {{ width: 100%; border-collapse: collapse; border: 3px solid black; }}"  # Border for the table
        f"th, td {{ padding: 10px 5px; text-align: center; font-size: 14px; }}"
        f".thick-border {{ background-color: {header_color}; color: {text_color}; border: 3px solid black; }}"  # Class for thick borders on headers
        f"tr:nth-child(even) {{ background-color: #F8F8F8; }}"  # Light grey for even rows
        f".industry-average {{ font-weight: bold; }}"
        f".pre-industry-average {{ border-bottom: 3px solid black; }}"
        f"</style>"
        f"<table>"
        f"<thead>"
        f"<tr>"
        f"<th rowspan='2' class='thick-border'>Level</th><th rowspan='2' class='thick-border'>Industry</th><th rowspan='2' class='thick-border'>Company</th>"
    )

    # Group header generation for categories
    categories = df.columns.get_level_values(0).unique()
    for category in categories:
        count = sum(1 for cat in df.columns.get_level_values(0) if cat == category)
        html += f"<th colspan='{count}' class='thick-border'>{category}</th>"
    html += "</tr><tr>"

    # Sub-header generation for individual metrics
    for category in categories:
        metrics = df.columns[df.columns.get_level_values(0) == category].get_level_values(1)
        for metric in metrics:
            html += f"<th class='thick-border'>{metric}</th>"
    html += "</tr></thead><tbody>"

    # Generate data rows with adjusted colors based on level
    df_iter = df.iterrows()
    try:
        index, row = next(df_iter)  # Get the first row to start the loop
        while True:
            next_index, next_row = next(df_iter)
            row_color = adjust_row_color(base_color_hex, index[0])
            row_class = "industry-average" if index[2] == "Industry Average" else ""
            if next_index[2] == "Industry Average":
                row_class += " pre-industry-average"  # Add class if next row is Industry Average
            html += f"<tr class='{row_class.strip()}' style='background-color: {row_color}; color: {row_text_color};'><td>{index[0]}</td><td>{index[1]}</td><td>{index[2]}</td>"
            for val in row:
                formatted_val = f"{val:.2f}" if isinstance(val, float) and not pd.isna(val) else val
                html += f"<td>{formatted_val}</td>"
            html += "</tr>"
            index, row = next_index, next_row  # Update current row to next
    except StopIteration:
        # Handle the last row outside the loop, as it has no next row
        row_color = adjust_row_color(base_color_hex, index[0])
        row_class = "industry-average" if index[2] == "Industry Average" else ""
        html += f"<tr class='{row_class.strip()}' style='background-color: {row_color}; color: {row_text_color};'><td>{index[0]}</td><td>{index[1]}</td><td>{index[2]}</td>"
        for val in row:
            formatted_val = f"{val:.2f}" if isinstance(val, float) and not pd.isna(val) else val
            html += f"<td>{formatted_val}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html

# Make a GET request to fetch the raw CSV content
# Read the data into a pandas DataFrame
company_profile_data = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYFhVNWUORgW6nxxZA?e=YCF8dQ')
income_data_yearly = get_data_csv(income_url_yearly)
bs_data_quarterly=read_onedrive_csv(bs_url_quarterly)
direct_cash_flow_data_yearly=pd.read_csv(direct_cash_flow_url_yearly)
indirect_cash_flow_data_yearly=pd.read_csv(indirect_cash_flow_url_yearly)
dividend_df=read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYFg_MlY6d71jErTug?e=DDazfC')

company_industry_df=pd.read_excel('company_industry.xlsx')
beta_df=pd.read_csv(r'beta.csv')

# Transform Data
income_data_dict_yearly = organize_data(income_data_yearly)
direct_cash_flow_data_dict_yearly = organize_data(direct_cash_flow_data_yearly)
indirect_cash_flow_data_dict_yearly = organize_data(indirect_cash_flow_data_yearly)
bs_dict_quarterly = organize_data(bs_data_quarterly)

latest_bs_data = read_onedrive_json('https://1drv.ms/u/s!Agfa0F4-51TwgYEgTHTLHf91BDUQiA?e=KcMHGU')
latest_income_data = read_onedrive_json('https://1drv.ms/u/s!Agfa0F4-51TwgYEfaq-H7ZUiriLbnw?e=QY8Krj')

company_finance_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYEkqnTC-DIdP79KlA?e=lHLNjv')
industry_summary_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYEXK7eSdQyRZdaV7Q?e=4aNPHc')
health_evaluation = read_onedrive_json('https://1drv.ms/u/s!Agfa0F4-51TwgYEBQL1XCUeiyNWLUg?e=KsIIWF')

st.dataframe(industry_summary_df)

price_df = read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51Tw_mIpC7MpdyYmRhh2?e=hDSauu')
trading_summary_df= read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYFRGPjCn0zhoL0rWg?e=Ig8CLs')
    

price_df['time'] = pd.to_datetime(price_df['time'])
latest_prices = price_df.sort_values(by='time').groupby('ticker').last().reset_index()

# We only need the ticker and the latest close price
latest_prices = latest_prices[['ticker', 'close']]

# Rename the 'close' column to 'latest_price' for the merge
latest_prices.rename(columns={'close': 'latest_price'}, inplace=True)

# Assuming company_profile_data is already loaded
company_profile_data = pd.merge(company_profile_data, latest_prices, on='ticker', how='left')


company_profile_data['display']= company_profile_data['ticker'] + ' - ' + company_profile_data['exchange'] + ' - ' + company_profile_data['shortName'] + ' - ' + company_profile_data['companyName']
company_profile_data['Market Capitalization (Mil)']= company_profile_data['latest_price']*company_profile_data['outstandingShare']

# Input widget to accept part of ticker or company name
#user_input = st.text_input('Enter Company Ticker or Name:', on_change=None, key="user_input")

free_float_df=read_onedrive_csv('https://1drv.ms/u/s!Agfa0F4-51TwgYFddhQ_IL31zaqCWw?e=OIKMMN')
company_profile_data=pd.merge(company_profile_data,free_float_df,how='left' , on='ticker')
company_profile_data['Free Shares'] = company_profile_data['outstandingShare'] * company_profile_data['free-float rate']/100

with basic_info:
    st.header("Basic Info")
    
    selectbox_container = st.container()
    with selectbox_container:
        selected_ticker=select_ticker(company_profile_data['display'])  
    if st.session_state.get('selected_company'):
        try:
            st.subheader("Basic")
            st.dataframe(company_profile_data[company_profile_data['ticker']==selected_ticker][['shortName','exchange']].T)

            st.subheader("Shares")
            st.dataframe(company_profile_data[company_profile_data['ticker']==selected_ticker][['Market Capitalization (Mil)','outstandingShare','issueShare','Free Shares']].T)

            st.subheader("Ownership")
            st.write("Upcoming:  1. State Ownership")
            st.dataframe(company_profile_data[company_profile_data['ticker']==selected_ticker][['noShareholders','foreignPercent']].T)

            st.subheader("Business Story")
            st.dataframe(company_profile_data[company_profile_data['ticker']==selected_ticker][['companyProfile','historyDev','keyDevelopments','businessRisk','businessStrategies','companyPromise']].T)
            

        except:
            st.write("There is no Company data about this company yet")
    # Optionally display the full company data
    if st.checkbox('Show Full Company Data'):
        print("Other info")
        st.dataframe(company_profile_data[company_profile_data['ticker']==selected_ticker].T)
        st.write(company_profile_data)
    
with finance:
    income_statement_section, balance_sheet_section,cash_flow_section = st.tabs(["Income Statement", "Balance Sheet",'Cash Flow'])

    with income_statement_section:
        st.subheader("Income Statement - Báo cáo Kết quả kinh doanh")
        income_statement_section_yearly, income_statement_section_quarterly = st.tabs(["Yearly", "Quarterly"])
        with income_statement_section_yearly:    
            # Convert the nested dictionary into a DataFrame
            # Function to convert the dictionary to a DataFrame while preserving the order
            st.dataframe(finance_dict_to_dataframe(income_data_dict_yearly[selected_ticker]))
        with income_statement_section_quarterly:
            st.write("A")
    with balance_sheet_section:
        st.subheader("Balance Sheet - Bảng cân đối kế toán")

        balance_sheet_section_yearly, balance_sheet_section_quarterly = st.tabs(["Yearly", "Quarterly"])
        with balance_sheet_section_yearly:
            st.write("Coming soon")
        with balance_sheet_section_quarterly:# Your content for nested tab 2
            st.dataframe(finance_dict_to_dataframe(bs_dict_quarterly[selected_ticker]))
    with cash_flow_section:
        direct_cash_flow_section, indirect_cash_flow_section = st.tabs(["Direct Cash Flow", "Indirect Cash Flow"])
        with direct_cash_flow_section:
            st.dataframe(finance_dict_to_dataframe(direct_cash_flow_data_dict_yearly[selected_ticker]))
        with indirect_cash_flow_section:
            st.write(selected_ticker)
            st.dataframe(finance_dict_to_dataframe(indirect_cash_flow_data_dict_yearly[selected_ticker]))

with events:
    st.header(list_tabs[1])
    company_insider_deal_url = 'https://raw.githubusercontent.com/penthousecompany/master/main/structured/structured_company_insider_deals.csv'
    insider_deal=get_data_csv(company_insider_deal_url)
    st.write("Insider Deal, Lưu ý, hiện tại các ticker ở Insider Deal bị lệch nhiều so với Ticker thông thường")
    st.write(insider_deal)#[insider_deal['ticker']==selected_ticker])

#ticker,dealAnnounceDate,dealMethod,dealAction,dealQuantity,dealPrice,dealRatio

    company_events_url = 'https://raw.githubusercontent.com/penthousecompany/master/main/structured/structured_company_events.csv'
    company_events_full=get_data_csv(company_events_url)
    company_events=company_events_full[['ticker','price','priceChange','eventName','eventCode','notifyDate','exerDate','regFinalDate','exRigthDate','eventDesc','eventNote']]
    st.write("Company Event")
    st.write(company_events[company_events['ticker']==selected_ticker])
    #datime,id,ticker,price,priceChange,priceChangeRatio,priceChangeRatio1W,priceChangeRatio1M,eventName,eventCode,notifyDate,exerDate,regFinalDate,exRigthDate,eventDesc,eventNote

groups = {
    'Market': ['P/B', 'P/S'],
    'Cost Profit': ['ROE', 'ROA'],
    'Activity Indicators': ['Receivable Turnover', 'Inventory Turnover', 'CA Turnover', 'TA Turnover'],
    'Liquidity Indicators': ['Current Ratio', 'Interest Coverage Ratio'],
    'Leverage':['Leverage','Short-term/Total Liabilities']
}

health_groups={'Cost Profit': ['ROE', 'ROA'],
    'Activity Indicators': ['Receivable Turnover', 'Inventory Turnover', 'CA Turnover', 'TA Turnover'],
    'Liquidity Indicators': ['Current Ratio', 'Interest Coverage Ratio'],
    'Leverage':['Leverage','Short-term/Total Liabilities']
}

with calculation:
    company_finance_df = pd.merge(company_finance_df, latest_prices, on='ticker', how='left')
    company_finance_df['Fair Price']=(company_finance_df['Adjusted CAPM Per Share']+company_finance_df['PB Valuation']+company_finance_df['PS Valuation'])/3
    company_finance_df['Opportunity']=company_finance_df['Fair Price']/company_finance_df['latest_price']-1
    company_finance_df['Opportunity'] = company_finance_df['Opportunity'].apply(lambda x: f'{x:.2f}%')
    st.header(selected_ticker)
    st.dataframe(company_finance_df[company_finance_df['ticker']==selected_ticker])
    st.dataframe(company_finance_df[company_finance_df['ticker']==selected_ticker][['Adjusted CAPM Per Share','PB Valuation','PS Valuation','Fair Price','latest_price']].applymap(lambda x: f'{x:.0f}').T)
    st.write(company_finance_df[company_finance_df['ticker']==selected_ticker]['Opportunity'])
    st.header("Benchmark")
    # Flatten the group structure for easier data retrieval
    ticker_data_df = build_company_metrics_dataframe(selected_ticker, company_finance_df, industry_summary_df)
    html_str = industry_benchmark_dataframe_to_html(ticker_data_df)
    st.markdown(html_str, unsafe_allow_html=True)

    st.header("Ticker Health")
    company_health=transform_to_dataframe(health_evaluation[selected_ticker], health_groups)

    current_year = datetime.now().year
    # Function to calculate average dividends for a given ticker and type over the last 3 years

    # Convert dataframe to HTML with multi-level headers
    def dataframe_to_html(df):
        header_color = "#40466e"  # Dark blue header
        row_color = "#f1f1f2"    # Light grey row
        html = (
            "<style>"
                "table { width: 100%; border-collapse: collapse; border: 3px solid black; }"
                "th, td { padding: 10px 5px; text-align: center; font-size: 14px; }"
                "th { background-color: " + header_color + "; color: white; border: 1px solid black; }"
                "tr:nth-child(even) { background-color: " + row_color + "; }"
                "th.category { border-right: 3px solid black; }"  # Thick black border for category separation
                "th.last-in-category { border-right: 3px solid black; }"
                "thead { border-bottom: 3px solid black; }"
                "thead tr:first-child th { border-bottom: 3px solid black; }"
                "thead th:first-child, thead th:last-child { border-left: 3px solid black; border-right: 3px solid black; }"
            "</style>"
            "<table>"
            "<thead>"
            "<tr><th rowspan='2'>Index</th>"
        )

        # First row for categories with thick right borders
        categories = df.columns.get_level_values(0).unique()
        for category in categories:
            count = sum(1 for cat, met in df.columns if cat == category)
            html += f"<th class='category' colspan='{count}'>{category}</th>"
        html += "</tr><tr>"

        # Second row for metrics, check for last metric in category
        last_metric_indices = {cat: None for cat in categories}
        for i, (cat, met) in enumerate(df.columns):
            if cat in last_metric_indices:
                last_metric_indices[cat] = i  # Update to the latest index
        for category, metric in df.columns:
            html += f"<th class='category'>{metric}</th>"
        
        html += "</tr></thead><tbody>"

        # Generate data rows with formatting
        for index, row in df.iterrows():
            html += f"<tr><td>{index}</td>"
            for idx, val in enumerate(row):
                is_last_in_category = (idx in last_metric_indices.values())
                style_addition = "style='border-right: 3px solid black;'" if is_last_in_category else ""
                formatted_val = f"{val:.2f}" if isinstance(val, float) else f"{val}"
                html += f"<td {style_addition}>{formatted_val}</td>"
            html += "</tr>"

        html += "</tbody></table>"
        return html

    # Display HTML in Streamlit
    st.write("Current")
    html_str = dataframe_to_html(company_health)
    st.markdown(html_str, unsafe_allow_html=True)
    
    
    st.subheader("Average Dividend Data for:", selected_ticker)
    def calculate_dividend_averages(df, ticker, current_year):
        # Filter data for the selected ticker
        selected_df = df[df['ticker'] == ticker]

        # Filter data for the last 3 years
        recent_df = selected_df[selected_df['cashYear'] >= current_year - 2]

        # Calculate average cash dividend
        cash_dividends = recent_df[recent_df['issueMethod'] == 'cash']['cashDividendPercentage'].mean()

        # Calculate average stock dividend
        stock_dividends = recent_df[recent_df['issueMethod'] == 'share']['cashDividendPercentage'].mean()

        averages = {
            'Cash Dividend Avg3Y': cash_dividends,
            'Stock Dividend Avg3Y': stock_dividends
        }
        averages_df = pd.DataFrame([averages])
            # Style the DataFrame
        def style_specific(df):
            return df.style.set_table_styles(
                [{'selector': 'th',
                'props': [('background-color', 'black'), ('color', 'white')]}]
            ).set_properties(**{'border': '1.4px solid black', 'text-align': 'center'})

        styled_df = style_specific(averages_df)
        return styled_df
    st.write(calculate_dividend_averages(dividend_df,selected_ticker, current_year), unsafe_allow_html=True)
    
with trading_data:
    st.dataframe(trading_summary_df[trading_summary_df['ticker']==selected_ticker].set_index('ticker').T)
    ticker_price_df=price_df[price_df['ticker']==selected_ticker]
    ticker_price_df.sort_values(by=['ticker', 'time'], ascending=[True, False], inplace=True)
    def calculate_indicators(group):
        # Reverse to chronological order
        reversed_group = group.iloc[::-1]

        group['5D Average Volume'] = reversed_group['volume'].rolling(window=5, min_periods=1).mean()
        group['20D Average Volume'] = reversed_group['volume'].rolling(window=20, min_periods=1).mean()
        # Calculate RSI
        delta = reversed_group['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        group['RSI'] = 100 - (100 / (1 + rs))

        # Calculate Moving Average
        group['20D MA'] = reversed_group['close'].rolling(window=20, min_periods=1).mean()

        # Calculate Bollinger Bands
        std_dev = reversed_group['close'].rolling(window=20, min_periods=1).std()
        group['Bollinger Upper'] = group['20D MA'] + (std_dev * 2)
        group['Bollinger Lower'] = group['20D MA'] - (std_dev * 2)

        return group
    ticker_price_df = ticker_price_df.groupby('ticker').apply(calculate_indicators)
    ticker_price_df.set_index('time', inplace=True)
    ticker_price_df.index = pd.to_datetime(ticker_price_df.index)
    st.write(ticker_price_df)
    # Streamlit layout
    st.title('Financial Chart Analysis')
    # User options
    chart_type = st.selectbox('Chart Type', ['Line', 'Candle'])
    interval = st.selectbox('Interval', ['1D', '1W', '1M'])
    timeframe = st.selectbox('Timeframe', ['1M', '3M', '6M', '1Y'])

    # Handle interval conversion
    if interval == '1W':
        ticker_price_df = ticker_price_df.resample('W').agg({
            'open': 'first', 
            'high': 'max', 
            'low': 'min', 
            'close': 'last',
            'volume': 'sum',
            '5D Average Volume': 'mean',
            '20D Average Volume': 'mean',
            'RSI': 'mean',
            '20D MA': 'mean',
            'Bollinger Upper': 'mean',
            'Bollinger Lower': 'mean'
        })
    elif interval == '1M':
        ticker_price_df = ticker_price_df.resample('M').agg({
            'open': 'first', 
            'high': 'max', 
            'low': 'min', 
            'close': 'last',
            'volume': 'sum',
            '5D Average Volume': 'mean',
            '20D Average Volume': 'mean',
            'RSI': 'mean',
            '20D MA': 'mean',
            'Bollinger Upper': 'mean',
            'Bollinger Lower': 'mean'
        })

    # Select timeframe
    ticker_price_df.index = pd.to_datetime(ticker_price_df.index)
    end_date = pd.to_datetime(ticker_price_df.index.max())
    if timeframe == '1M':
        start_date = end_date - pd.DateOffset(months=1)
    elif timeframe == '3M':
        start_date = end_date - pd.DateOffset(months=3)
    elif timeframe == '6M':
        start_date = end_date - pd.DateOffset(months=6)
    elif timeframe == '1Y':
        start_date = end_date - pd.DateOffset(years=1)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    ticker_price_df = ticker_price_df[ticker_price_df.index >= start_date]
    ticker_price_df = ticker_price_df[ticker_price_df.index <= end_date]

    # mplfinance plot
    apds = [mpf.make_addplot(ticker_price_df['20D MA'], color='orange', secondary_y=False),
            mpf.make_addplot(ticker_price_df[['Bollinger Upper', 'Bollinger Lower']], color='blue', secondary_y=False)]
    fig_dims = (18, 10)
    if chart_type == 'Line':
        fig, axlist = mpf.plot(ticker_price_df, type='line', style='charles',figsize=fig_dims,
                           volume=True, addplot=apds, title=f"{selected_ticker} Line Chart", returnfig=True)
        st.pyplot(fig)
    elif chart_type == 'Candle':
        fig, axlist = mpf.plot(ticker_price_df, type='candle', style='charles',figsize=fig_dims,
                           volume=True, addplot=apds, title=f"{selected_ticker} Candlestick Chart", returnfig=True)
        st.pyplot(fig)
with full_data:
    st.header("Company Finance Dataframe")
    st.dataframe(company_finance_df)

    st.header("Industry Summary")
    st.dataframe(industry_summary_df)

    st.header("Full Data Company Industry")
    st.dataframe(company_industry_df)

    st.header("Price Data")
    st.dataframe(price_df[price_df['ticker']==selected_ticker])

    st.header("Dividend Data")
    st.dataframe(dividend_df)
with QA_data:
    st.header("Data Quality")
    # Reset the index to default integer index

    # Number of areas per column
    num_areas = 16

    # Create a DataFrame where each cell is the percentage of NULL values in its area
    null_df = company_finance_df.isnull().astype(int).groupby(company_finance_df.index // (len(company_finance_df) // num_areas)).mean()

    # Create a heatmap
    plt.figure(figsize=(25,15))  # Increase figure size
    sns.heatmap(null_df, cmap='RdYlGn_r', cbar=True)#, annot=True, fmt=".1%", annot_kws={"size": 8})  # Decrease font size
    plt.title('NULL Values Density Heatmap')
    plt.xlabel('Columns')
    plt.ylabel('Area')
    plt.tight_layout()  # Adjust layout to not cut-off the title and labels
    st.pyplot(plt)