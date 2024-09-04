import streamlit as st
from utils.__pycache__.functions import *

# Bank data extracted from the provided bank.js file
banks = {
    "VietinBank": "ICB",
    "Vietcombank": "VCB",
    "BIDV": "BIDV",
    "Agribank": "VBA",
    "OCB": "OCB",
    "MBBank": "MB",
    "Techcombank": "TCB",
    "ACB": "ACB",
    "VPBank": "VPB",
    "TPBank": "TPB",
    "Sacombank": "STB",
    "HDBank": "HDB",
    "VietCapitalBank": "VCCB",
    "SCB": "SCB",
    "VIB": "VIB",
    "SHB": "SHB",
    "Eximbank": "EIB",
    "MSB": "MSB",
    "CAKE": "CAKE",
    "Ubank": "Ubank",
    "Timo": "TIMO",
    "ViettelMoney": "VTLMONEY",
    "VNPTMoney": "VNPTMONEY",
    "SaigonBank": "SGICB",
    "BacABank": "BAB",
    "PVcomBank": "PVCB",
    "Oceanbank": "Oceanbank",
    "NCB": "NCB",
    "ShinhanBank": "SHBVN",
    "ABBANK": "ABB",
    "VietABank": "VAB",
    "NamABank": "NAB",
    "PGBank": "PGB",
    "VietBank": "VIETBANK",
    "BaoVietBank": "BVB",
    "SeABank": "SEAB",
    "COOPBANK": "COOPBANK",
    "LienVietPostBank": "LPB",
    "KienLongBank": "KLB",
    "KBank": "KBank",
    "KookminHN": "KBHN",
    "KEBHanaHCM": "KEBHANAHCM",
    "KEBHanaHN": "KEBHANAHN",
    "MAFC": "MAFC",
    "Citibank": "CITIBANK",
    "KookminHCM": "KBHCM",
    "VBSP": "VBSP",
    "Woori": "WVN",
    "VRB": "VRB",
    "UnitedOverseas": "UOB",
    "StandardChartered": "SCVN",
    "PublicBank": "PBVN",
    "Nonghyup": "NHB HN",
    "IndovinaBank": "IVB",
    "IBKHCM": "IBK - HCM",
    "IBKHN": "IBK - HN",
    "HSBC": "HSBC",
    "HongLeong": "HLBVN",
    "GPBank": "GPB",
    "DongABank": "DOB",
    "DBSBank": "DBS",
    "CIMB": "CIMB",
    "CBBank": "CBB",
}

# Streamlit UI
st.title('VietQR Link Generator')

# Bank selection
bank_name = 'MBBank'

type_of_customer={'Cá nhân/Individual':'CN',"Doanh nghiệp/Business":"DN"}
# User inputs
account_no = 8820231001
customer_type = st.selectbox("Customer Type", list(type_of_customer.keys()))
import urllib.parse
customer_id = st.text_input("Enter customer ID (sau này mỗi khách hàng đăng nhập sẽ có một ID, ko cần nhập)")
amount = st.text_input("Enter the amount")
#description = f"{type_of_customer[customer_type]}-{customer_id}-TT"
description = urllib.parse.quote(type_of_customer[customer_type] + ' - ' + customer_id + "- TT")
account_name = "Cao Phúc Đạt"
st.write(description)

# Generate URL
if st.button("Generate QR Link"):
    bank_id = banks[bank_name]
    template = "print"
    url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png?amount={amount}&addInfo={description}&accountName={account_name}"
    st.write("Your QR link:")
    st.write(url)

    # Display the QR code image
    st.markdown(f"<div style='text-align: center;'><img src='{url}' width='300' alt='Your VietQR Code'></div>", unsafe_allow_html=True)