import streamlit as st
from PIL import Image
from utils.__pycache__.functions import *
import qrcode

# Streamlit UI
st.title('VietQR Link Generator')

bank_js=read_onedrive_json('https://1drv.ms/u/s!Agfa0F4-51Twh4cyLAtS_Ij9qdyCKA?e=vXUF6a')
bank_dict = {item['short_name']: item for item in bank_js['data']}
logo=read_onedrive_image('https://1drv.ms/i/s!Agfa0F4-51Twh4c0M1taixPC4bAlyg?e=Ckydol')

class VietQR:
    def __init__(self):
        self.payload_format_indicator = "000201"
        self.point_of_initiation_method = "010212"
        self.consumer_account_information = ""
        self.guid = "0010A000000727"
        self.service_code = "0208QRIBFTTA"
        self.transaction_currency = "5303704"
        self.transaction_amount = ""
        self.country_code = "5802VN"
        self.additional_data_field_template = ""
        self.crc = ""

    def convert_length(self, value):
        length = len(value)
        return f"{length:02}"

    def set_transaction_amount(self, money):
        length = self.convert_length(money)
        self.transaction_amount = f"54{length}{money}"
        return self

    def set_beneficiary_organization(self, acquirer_id, consumer_id):
        acquirer_length = self.convert_length(acquirer_id)
        acquirer = f"00{acquirer_length}{acquirer_id}"
        consumer_length = self.convert_length(consumer_id)
        consumer = f"01{consumer_length}{consumer_id}"
        # Calculate the total length of the GUID, acquirer, consumer, and service code
        consumer_account_information_length = len(self.guid)+ 4 + len(acquirer) + len(consumer) + len(self.service_code)
        
        beneficiary_organization_length = self.convert_length(acquirer + consumer)

        self.consumer_account_information = (
            f"38{consumer_account_information_length}{self.guid}01"
            f"{beneficiary_organization_length}{acquirer}{consumer}0208QRIBFTTA"
        )
        
        return self

    def set_additional_data_field_template(self, content):
        content_length = self.convert_length(content)
        
        additional_data_field_template_length = (str(int(content_length) + 4)).zfill(2)
        self.additional_data_field_template = f"62{additional_data_field_template_length}08{content_length}{content}"
        return self

    def calc_crc(self, string):
        crc_table = [
            0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, 0x8108,
            0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef, 0x1231, 0x0210,
            0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6, 0x9339, 0x8318, 0xb37b,
            0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de, 0x2462, 0x3443, 0x0420, 0x1401,
            0x64e6, 0x74c7, 0x44a4, 0x5485, 0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee,
            0xf5cf, 0xc5ac, 0xd58d, 0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6,
            0x5695, 0x46b4, 0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d,
            0xc7bc, 0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b, 0x5af5,
            0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12, 0xdbfd, 0xcbdc,
            0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a, 0x6ca6, 0x7c87, 0x4ce4,
            0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41, 0xedae, 0xfd8f, 0xcdec, 0xddcd,
            0xad2a, 0xbd0b, 0x8d68, 0x9d49, 0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13,
            0x2e32, 0x1e51, 0x0e70, 0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a,
            0x9f59, 0x8f78, 0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e,
            0xe16f, 0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e, 0x02b1,
            0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256, 0xb5ea, 0xa5cb,
            0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d, 0x34e2, 0x24c3, 0x14a0,
            0x0481, 0x7466, 0x6447, 0x5424, 0x4405, 0xa7db, 0xb7fa, 0x8799, 0x97b8,
            0xe75f, 0xf77e, 0xc71d, 0xd73c, 0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657,
            0x7676, 0x4615, 0x5634, 0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9,
            0xb98a, 0xa9ab, 0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882,
            0x28a3, 0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92, 0xfd2e,
            0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9, 0x7c26, 0x6c07,
            0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1, 0xef1f, 0xff3e, 0xcf5d,
            0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8, 0x6e17, 0x7e36, 0x4e55, 0x5e74,
            0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
        ]

        crc = 0xffff
        for char in string:
            c = ord(char)
            if c > 255:
                raise ValueError("Character code out of range.")
            j = (c ^ (crc >> 8)) & 0xff
            crc = crc_table[j] ^ (crc << 8)
        crc = (crc ^ 0) & 0xffff
        return crc

    def build(self):
        content_qr = (
            f"{self.payload_format_indicator}{self.point_of_initiation_method}"
            f"{self.consumer_account_information}{self.transaction_currency}"
            f"{self.transaction_amount}{self.country_code}{self.additional_data_field_template}6304"
        )
        crc = hex(self.calc_crc(content_qr.replace("\n", "")))[2:].upper().zfill(4)
        return f"{content_qr}{crc}"

# Bank selection
bank_name = "MBBank"
type_of_customer={'Cá nhân/Individual':'CN',"Doanh nghiệp/Business":"DN"}
# User inputs
account_no = 8820231001
customer_type = st.selectbox("Customer Type", list(type_of_customer.keys()))
import urllib.parse
customer_id = st.text_input("Enter customer ID (sau này mỗi khách hàng đăng nhập sẽ có một ID, ko cần nhập)")

# Function to format the number with commas
def format_number(value):
    try:
        # Convert the input to a float and format it with commas
        formatted_value = f"{int(value):,}"
    except ValueError:
        # If input is not a valid number, return the original value
        formatted_value = value
    return formatted_value

# Text input
amount = st.text_input("Enter the amount", "")

# If the user has entered something, format it
if amount:
    formatted_amount = format_number(amount)
    st.write(f"Formatted amount: {formatted_amount}")
#description = f"{type_of_customer[customer_type]}-{customer_id}-TT"
description = type_of_customer[customer_type] + '-' + customer_id + "-TT"
account_name = "Cao Phúc Đạt"

if st.button("Invest"):
    bank_id = bank_dict[bank_name]['bin']
    
    # Usage example
    viet_qr = VietQR()
    viet_qr.set_beneficiary_organization("970422", "8820231001")
    viet_qr.set_transaction_amount(amount)
    viet_qr.set_additional_data_field_template(description)

    st.write(viet_qr.build())  # This should output the correct CRC code and the final string

    # Create the QR code
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(viet_qr.build())
    qr.make()
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Ensure the logo has an alpha channel
    logo = logo.convert("RGBA")

    # Calculate the size of the logo while keeping the aspect ratio
    qr_size = qr_img.size[0]
    logo_ratio = min(qr_size // 4 / logo.width, qr_size // 4 / logo.height)
    new_logo_size = (int(logo.width * logo_ratio)*3, int(logo.height * logo_ratio)*3)
    logo = logo.resize(new_logo_size, Image.Resampling.LANCZOS)

    # Calculate the position to place the logo
    logo_position = ((qr_img.size[0] - logo.width) // 2, (qr_img.size[1] - logo.height) // 2)

    # Create a mask using the alpha channel of the logo
    mask = logo.split()[3]

    # Overlay the logo onto the QR code
    qr_img.paste(logo, logo_position, mask)
    # Display the image in Streamlit
    #st.image(qr_img,width=150)
    # Convert image to base64
    import io
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Display the image in Streamlit with HTML for centering
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{img_str}" width="250">
        </div>
        """,
        unsafe_allow_html=True
    )