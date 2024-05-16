import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import pandas as pd

st.set_page_config(
    page_title = "Pages for easy development",
    page_icon = None
)

# Configuration for Outlook email server
EMAIL_ADDRESS = 'binh.damduc@fico-ytl.com'
EMAIL_PASSWORD = 'Ddb20112001@'
SMTP_SERVER = 'smtp.office365.com'
SMTP_PORT = 587

if 'otp' in st.session_state:
    try:
        st.write("Cảm ơn anh chị đã sử dụng dịch vụ của Lucid")
        st.write("Anh chị đã sở hữu thành công 1000 Chứng chỉ Quỹ Lucid tương đương với 100 triệu đồng")
        st.write(user.full_name)
    except:
        pass
# Store this in session to persist state across interactions
if 'otp' not in st.session_state:
    st.session_state['otp'] = None

def send_otp_email(email):
    otp = secrets.randbelow(999999)  # Generate a 6-digit OTP
    st.session_state['otp'] = str(otp).zfill(6)  # Store the OTP in session state

    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = 'Your OTP to Pricing Analyst Application'
    message = f'''Your OTP is {st.session_state["otp"]}/n
    Thanks for using our services'''
    msg.attach(MIMEText(message, 'plain'))

    # Send email
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    text = msg.as_string()
    server.sendmail(EMAIL_ADDRESS, email, text)
    server.quit()

def verify_otp(input_otp):
    if input_otp == st.session_state['otp']:
        st.success("OTP verified successfully!")
        # Proceed with your application logic here
    else:
        st.error("Invalid OTP, please try again.")

# User Interface
st.write("OTP Authentication")
email = st.text_input("Enter your email to receive an OTP:")
if st.button("Send OTP"):
    send_otp_email(email)

input_otp = st.text_input("Enter your OTP:")
if st.button("Verify OTP"):
    verify_otp(input_otp)

class People:
    def __init__(self, full_name, dear_name, position, email, sex):
        self.full_name = full_name
        self.dear_name = dear_name
        self.position = position
        self.first_name = self.full_name.split(' ')[-1]
        self.email = email
        self.sex = sex
        if sex=='Female':
            self.contraction= "Ms"
        else:
            self.contraction= "Mr"


def find_people(df, group=None, regions=None, position=None, email=None):
    """
    Searches the DataFrame for people belonging to a specific group, region, position, and email.
    Parameters:
    - df: pandas.DataFrame containing people information.
    - group: The group to filter by (e.g., "MBI").
    - regions: A list of regions to include (e.g., ["Mekong", "HCM_LAN"]).
    - position: The position to filter by (e.g., "Manager").
    - email: The email address to filter by.
    Returns:
    - A single People instance if one match is found,
    - A list of People instances if multiple matches are found,
    - None if no matches are found.
    """
    filtered_people = df.copy()
    
    if group is not None:
        filtered_people = filtered_people[filtered_people['Group'] == group]
    
    if regions is None:
        filtered_people = filtered_people[filtered_people['Region'].isna()]
    else:
        if isinstance(regions, str):
            regions = [regions]
        filtered_people = filtered_people[(filtered_people['Group'] == group) & (filtered_people['Region'].isin(regions))]
    
    if position is not None:
        filtered_people = filtered_people[filtered_people['Position'] == position]
    
    if email is not None:
        filtered_people = filtered_people[filtered_people['Email'] == email]
    
    num_matches = len(filtered_people)
    
    if num_matches == 1:
        # One match, create and return a single People instance
        row = filtered_people.iloc[0]
        return People(
            full_name=row['Full Name'],
            dear_name=row['Dear'],
            email=row['Email'],
            sex=row['Giới tính'],
            position=row['Position']
        )
    elif num_matches > 1:
        # Multiple matches, convert results to a list of People instances
        people_list = []
        for index, row in filtered_people.iterrows():
            people_list.append(People(
                full_name=row['Full Name'],
                dear_name=row['Dear'],
                email=row['Email'],
                sex=row['Giới tính'],
                position=row['Position']
            ))
        return people_list
    else:
        # No matches found
        return None
