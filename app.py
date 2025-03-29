import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

# Apply Yale Law styling
css = """
<link href="https://fonts.googleapis.com/css2?family=Merriweather&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  {
    font-family: 'Merriweather', Georgia, serif !important;
    color: #00356B !important;
}
h1, h2, h3, h4, h5, h6, .stText, .stMarkdown, .stMetric, .stDataFrame {
    color: #00356B !important;
    font-family: 'Merriweather', Georgia, serif !important;
}
[data-testid="stSidebar"] {
    background-color: #00356B;
    padding: 1rem;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-family: 'Merriweather', Georgia, serif !important;
}
</style>
"""
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
scores_df = scores_df.apply(pd.to_numeric, errors='ignore')

st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
st.sidebar.title("Access to Law School Cohort 4 Data Dashboard")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

if view == "Cohort Overview":
    st.title("Cohort Overview")
    st.subheader("Attendance Summary")

    # Defensive attendance chart (stacked barh)
    desired_cols = [
        'Full Name', 'Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %', 'Total Attendance%'
    ]
    existing_cols = [col for col in desired_cols if col in attendance_df.columns]
    missing = set(desired_cols) - set(existing_cols)

    if missing:
        st.warning(f"Missing columns: {missing}")

    try:
        if all(col in attendance_df.columns for col in ['Full Name', 'Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %']):
            chart_df = attendance_df[['Full Name', 'Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %']].set_index('Full Name')
            fig, ax = plt.subplots(figsize=(10, 8))
            chart_df.plot(kind='barh', stacked=True, ax=ax, color=['#004080', '#0059b3', '#3399ff'])
            ax.set_title("Fellow Attendance by Category")
            ax.set_xlabel("Attendance (%)")
            ax.invert_yaxis()
            st.pyplot(fig)
        else:
            st.warning("Could not display attendance chart: required columns are missing.")
    except Exception as e:
        st.error(f"Failed to render attendance chart: {e}")

elif view == "Individual Fellow Report":
    st.title("Individual Fellow Report")
    selected_fellow = st.selectbox("Select Fellow", sorted(attendance_df['Full Name'].unique()))
    fellow_attendance = attendance_df[attendance_df['Full Name'] == selected_fellow]

    st.subheader("Attendance Breakdown")
    desired = ['Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %']
    try:
        present = [col for col in desired if col in fellow_attendance.columns]
        values = fellow_attendance[present].iloc[0]
        fig, ax = plt.subplots()
        ax.bar(present, values, color=['#004080', '#0059b3', '#3399ff'])
        ax.set_ylim(0, 100)
        ax.set_ylabel("% Attendance")
        ax.set_title("Attendance by Session Type")
        st.pyplot(fig)
    except:
        st.warning("Attendance chart unavailable for this fellow.")




