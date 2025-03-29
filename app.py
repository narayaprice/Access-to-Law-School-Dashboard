import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

# Apply Yale Law styling
css = """
<link href="https://fonts.googleapis.com/css2?family=Merriweather&display=swap" rel="stylesheet">
<style>
body {
    background-color: #f5f5f5;
    font-family: 'Merriweather', Georgia, serif;
    color: #00356B;
}
.stApp { padding: 2rem; }
[data-testid="stSidebar"] {
    background-color: #00356B;
    padding: 1rem;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-family: 'Merriweather', Georgia, serif !important;
}
.stButton > button, .stDownloadButton > button {
    background-color: #00356B;
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
.block-container { padding-top: 1rem; }
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

# Sidebar
st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
st.sidebar.title("Access to Law School Cohort 4 Data Dashboard")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

# Filtered test columns
test_order = [
    "Diagnostic", "PT 71", "PT 73", "PT 136", "PT 137", "PT 138", "PT 139",
    "PT 140", "PT 141", "PT 144", "PT 145", "PT 146", "PT 147", "PT 148", "PT 149"
]

if view == "Cohort Overview":
    st.title("Cohort Overview")

    # Defensive attendance summary block
    st.subheader("Attendance Summary")
    desired_columns = [
        'Full Name',
        'Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %',
        'Total Attendance%'
    ]
    existing_columns = [col for col in desired_columns if col in attendance_df.columns]
    missing = set(desired_columns) - set(existing_columns)
    if missing:
        st.warning(f"Missing columns in Attendance sheet: {missing}")
    if existing_columns:
        attendance_summary = attendance_df[existing_columns].copy()
        st.dataframe(attendance_summary)
    else:
        st.error("Could not generate attendance summary — required columns are missing.")

elif view == "Individual Fellow Report":
    st.title("Individual Fellow Report")
    selected_fellow = st.selectbox("Select Fellow", sorted(attendance_df['Full Name'].unique()))
    fellow_attendance = attendance_df[attendance_df['Full Name'] == selected_fellow]
    fellow_scores = scores_df[scores_df['Name'] == selected_fellow]

    st.subheader("Attendance Summary")
    desired_columns = [
        'Fall Small Groups %', 'Spring Small Groups %', 'Saturday Academies %',
        'Total Attendance%'
    ]
    existing_columns = [col for col in desired_columns if col in fellow_attendance.columns]
    missing = set(desired_columns) - set(existing_columns)
    if missing:
        st.warning(f"Missing columns in fellow attendance: {missing}")
    if existing_columns:
        details = fellow_attendance[existing_columns].T
        details.columns = ["%"]
        st.dataframe(details)
    else:
        st.error("Could not display attendance details — missing fields.")

    st.subheader("Test Score Trend")
    try:
        melted = pd.melt(fellow_scores, id_vars='Name', value_vars=[col for col in test_order if col in fellow_scores.columns], var_name='Test', value_name='Score')
        melted = melted[pd.to_numeric(melted['Score'], errors='coerce').notnull()]
        fig, ax = plt.subplots()
        sns.lineplot(data=melted, x='Test', y='Score', marker='o', ax=ax)
        ax.set_title(f"{selected_fellow}'s Test Score Trend")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        st.pyplot(fig)
    except:
        st.warning("Could not plot score trend.")



