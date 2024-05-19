import streamlit as st
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, 'pages')

st.title("Main Page")

st.header("# Welcome to The Lucid Fund! 👋")

st.write("Objective of today: Walkthrough and Testing")
st.markdown("""
Objective: Internal team understand product
How it works (Input Output)
Result & Demo


Outline

- Overview về Stock Master
    + Các component, feature
    + Data Flow
- Cụ thể từng component
    + Với từng component sẽ grow through
    + Input (brief qua)
    + Logic (brief)
    + Output cho các internal stakeholder
    + Example
    + Demo + Hướng dẫn sử dụng""")

st.write("Requirement is updated in this file: https://1drv.ms/p/s!Agfa0F4-51Tw6DXYCqd6kQA3hpEA?e=cMOoaA")