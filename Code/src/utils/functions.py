link='https://raw.githubusercontent.com/asset-management-product/asset-management/main'
import pandas as pd
import requests
from io import StringIO
from io import BytesIO
import json
import streamlit as st
import base64

@st.cache_data
def get_data_csv(url):
    response=requests.get(url)
    response.raise_for_status()
    data_raw = StringIO(response.text)
    data = pd.read_csv(data_raw)
    return data

@st.cache_data
def get_data_excel(url):
    """Fetches data from a URL as Excel and returns a pandas DataFrame.

    Args:
        url (str): The URL of the Excel file.

    Returns:
        pd.DataFrame: The pandas DataFrame containing the data.

    Raises:
        requests.exceptions.RequestException: If there's an error fetching the data.
    """

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return pd.read_excel(BytesIO(response.content))  # Use BytesIO for binary data
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching data from URL: {url}") from e

@st.cache_data
def read_github(file_name,database=None,file_path=None):
    if file_path!=None:
        file_path=file_path
        try:
            df=get_data_csv(file_path)
        except:
            df=pd.read_excel(file_path)
    else:
        if database==None:
            folder_path=''
        else:
            folder_path=f'{link}/data/{database}'
        try:
            file_path=f'{folder_path}/{file_name}.csv'
            df=get_data_csv(file_path)
        except:
            try:
                file_path=f'{folder_path}/{file_name}/{file_name}.csv'
                df=get_data_csv(file_path)
            except:
                file_path=folder_path+file_name+'xlsx'
                df=pd.read_excel(file_path)
    return df

@st.cache_data
def read_onedrive_csv (onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    df=pd.read_csv(resultUrl)
    return df

@st.cache_data
def read_onedrive_excel (onedrive_link,sheet_name=None):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    if sheet_name == None:
        st.write(pd.read_excel(resultUrl).keys())
        df=pd.read_excel(resultUrl,sheet_name=sheet_name)
    else:
        df=pd.read_excel(resultUrl,sheet_name=sheet_name)
    return df

@st.cache_data
def read_onedrive_json(onedrive_link):
    # Encode the OneDrive link into base64
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip("=")
    # Create the URL for accessing the file
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    # Request the content of the file
    response = requests.get(resultUrl)
    # Check if the request was successful
    if response.status_code == 200:
        # Convert the fetched JSON data to a dictionary
        data = response.json()
        return data
    else:
        # Return an error message if the request was unsuccessful
        return f"Failed to retrieve data. Status code: {response.status_code}"

@st.cache_data
def organize_data(data):
    data_dict = {}
    for index, row in data.iterrows():
        ticker = row['ticker']
        try:
            response = json.loads(row['response'])
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for ticker {ticker} at row {index}: {e}")
            continue

        # Initialize the structure for the current ticker
        if ticker not in data_dict:
            data_dict[ticker] = {}
        # Check if 'Appendix' exists
        if 'Appendix' in response:
            # Append the appendix to the ticker's data
            data_dict[ticker]['Appendix'] = response['Appendix']

            # Iterate over the years and metrics in the response, excluding the Appendix
            for key, metrics in response.items():
                if key != "Appendix":
                    if key not in data_dict[ticker]:
                        data_dict[ticker][key] = {}
                    for metric_index, value in metrics.items():
                        # Use the appendix to get the metric name, if possible
                        metric_name = response['Appendix'].get(metric_index, f"Unknown Metric {metric_index}")
                        data_dict[ticker][key][metric_name] = value
        else:
            print(f"No 'Appendix' found for ticker {ticker} at row {index}")
            # Handle the case where there's no Appendix separately if needed
            # For example, you might want to simply copy the data as-is
            for key, metrics in response.items():
                data_dict[ticker][key] = metrics

    return data_dict