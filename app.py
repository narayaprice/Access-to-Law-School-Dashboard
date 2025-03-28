import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

# Define CSS styles in a variable
css = """
<link href="https://fonts.googleapis.com/css2?family=Merriweather&display=swap" rel="stylesheet">
<style>
body {
    background-color: #f5f5f5;
    font-family: 'Merriweather', Georgia, serif;
    color: #00356B;
}
h1, h2, h3, h4, .stMarkdown, .stText, .css-10trblm, .css-1d391kg {
    color: #00356B !important;
    font-family: 'Merriweather', Georgia, serif !important;
}
.stApp {
    padding: 2rem;
}
[data-testid="stSidebar"] {
    background-color: #00356B;
    padding: 1rem;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .css-1v3fvcr {
    color: white !important;
    font-family: 'Merriweather', Georgia, serif !important;
}
.stButton > button {
    background-color: #00356B;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 0.5rem 1rem;
}
.stDownloadButton > button {
    background-color: #286DC0;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    padding: 0.5rem 1rem;
}
.section {
    background-color: white;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.block-container {
    padding-top: 1rem;
}
</style>
"""

# Apply the CSS styles
st.markdown(css, unsafe_allow_html=True)

@st.cache_data
def load_data():
    xls = pd.ExcelFile("YA2LS Cohort 4 Data (2024 Fellows).xlsx")
    attendance = xls.parse("Attendance_New")
    scores = xls.parse("Test Scores")
    return attendance, scores

attendance_df, scores_df = load_data()

attendance_df.columns = attendance_df.columns.str.strip()
scores_df.columns = scores_df.columns.str.strip()
attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']

st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
st.sidebar.title("Access to Law School Cohort 4 Data Dashboard")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

# Remaining code continues unchanged...
