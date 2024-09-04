import streamlit as st


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
bank_name = st.selectbox("Choose your bank", list(banks.keys()))

# User inputs
account_no = st.text_input("Enter your bank account number")
amount = st.text_input("Enter the amount")
description = st.text_input("Enter the description")
account_name = st.text_input("Enter your account name")

# Generate URL
if st.button("Generate QR Link"):
    bank_id = banks[bank_name]
    template = "print"
    url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png?amount={amount}&addInfo={description}&accountName={account_name}"
    st.write("Your QR link:")
    st.write(url)
    st.markdown(f"[Click here to view the QR image]({url})")

    # Display the QR code image
    st.image(url, caption="Your VietQR Code", use_column_width=True)

