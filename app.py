import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

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

st.sidebar.title("Access to Law School Cohort 4")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

if view == "Cohort Overview":
    # ... [unchanged cohort overview code above]
    pass

elif view == "Individual Fellow Report":
    fellow = st.selectbox("Select Fellow", attendance_df['Full Name'].unique())
    att_row = attendance_df[attendance_df['Full Name'] == fellow]
    score_row = scores_df[scores_df['Name'] == fellow]

    st.title(f"Individual Fellow Report: {fellow}")

    st.header("1. Attendance Timeline")
    # Order the sessions as FSG #, FSG attended, FSG total, SSG #, SSG attended, SSG total, SA #, SA attended, SA total
    fsg_cols = sorted([col for col in att_row.columns if col.startswith('FSG') and not col.endswith('%')])
    ssg_cols = sorted([col for col in att_row.columns if col.startswith('SSG') and not col.endswith('%')])
    sa_cols = sorted([col for col in att_row.columns if col.startswith('SA') and not col.endswith('%')])
    ordered_session_cols = fsg_cols + ssg_cols + sa_cols

    att_vals = att_row[ordered_session_cols].T.reset_index()
    att_vals.columns = ['Session', 'Attendance']
    att_vals['Group'] = att_vals['Session'].apply(lambda x: 'FSG' if x.startswith('FSG') else ('SSG' if x.startswith('SSG') else 'SA'))
    att_vals['Attendance'] = pd.to_numeric(att_vals['Attendance'], errors='coerce')
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=att_vals, x='Session', y='Attendance', hue='Group', marker='o', ax=ax)
    ax.set_title(f'{fellow} - Attendance Timeline')
    ax.set_ylabel('Present (1) / Absent (0)')
    ax.legend(title='Group')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # ... [remaining individual report code stays the same]
    # Score progression, summary, and download

