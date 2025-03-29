import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

# Define the CSS in a variable
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

# Clean and validate columns
attendance_df.columns = attendance_df.columns.str.strip()
scores_df.columns = scores_df.columns.str.strip()

attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']
scores_df = scores_df.apply(pd.to_numeric, errors='ignore')

st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
st.sidebar.title("Access to Law School Cohort 4 Data Dashboard")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

if view == "Cohort Overview":
    st.markdown("""
    <div style='margin-bottom: 2rem;'>
        <h2>Cohort Overview</h2>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("### Attendance Summary", unsafe_allow_html=True)
        attendance_summary = attendance_df.groupby('Full Name').agg({
            'Session Date': pd.Series.nunique,
            'Attended': lambda x: (x == 'Yes').sum()
        }).rename(columns={'Session Date': 'Total Sessions', 'Attended': 'Sessions Attended'})
        attendance_summary['Attendance Rate (%)'] = (attendance_summary['Sessions Attended'] / attendance_summary['Total Sessions'] * 100).round(1)

        st.metric("Average Attendance Rate", f"{attendance_summary['Attendance Rate (%)'].mean():.1f}%")
        st.dataframe(attendance_summary.sort_values(by="Attendance Rate (%)", ascending=False), use_container_width=True)

    with st.container():
        st.markdown("### Test Score Trends", unsafe_allow_html=True)
        test_long = pd.melt(scores_df, id_vars=['Name'], var_name='Test', value_name='Score')
        test_long = test_long[pd.to_numeric(test_long['Score'], errors='coerce').notnull()]
        avg_scores = test_long.groupby('Test')['Score'].mean().reset_index()
        fig, ax = plt.subplots()
        sns.barplot(data=avg_scores, x='Test', y='Score', ax=ax)
        ax.set_title('Average Test Scores by Category')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        st.pyplot(fig)

    with st.container():
        st.markdown("### Download Attendance Summary", unsafe_allow_html=True)
        st.download_button(
            label="Download Cohort Summary as CSV",
            data=attendance_summary.to_csv(index=True).encode('utf-8'),
            file_name="cohort_attendance_summary.csv",
            mime="text/csv"
        )

elif view == "Individual Fellow Report":
    st.markdown("## Individual Fellow Report", unsafe_allow_html=True)
    selected_fellow = st.selectbox("Select Fellow", sorted(attendance_df['Full Name'].unique()))

    fellow_attendance = attendance_df[attendance_df['Full Name'] == selected_fellow]
    fellow_scores = scores_df[scores_df['Name'] == selected_fellow]

    with st.container():
        st.markdown(f"### Attendance for {selected_fellow}", unsafe_allow_html=True)
        st.dataframe(fellow_attendance[['Session Date', 'Attended']], use_container_width=True)
        total_sessions = fellow_attendance['Session Date'].nunique()
        attended_sessions = (fellow_attendance['Attended'] == 'Yes').sum()
        attendance_rate = round((attended_sessions / total_sessions) * 100, 1) if total_sessions > 0 else 0
        st.metric(label="Attendance Rate (%)", value=attendance_rate)

    with st.container():
        st.markdown(f"### Test Scores for {selected_fellow}", unsafe_allow_html=True)
        fellow_scores_melted = pd.melt(fellow_scores, id_vars=['Name'], var_name='Test', value_name='Score')
        fellow_scores_melted = fellow_scores_melted[pd.to_numeric(fellow_scores_melted['Score'], errors='coerce').notnull()]
        fig2, ax2 = plt.subplots()
        sns.barplot(data=fellow_scores_melted, x='Test', y='Score', ax=ax2)
        ax2.set_title(f"{selected_fellow}'s Test Scores")
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha='right')
        st.pyplot(fig2)

    with st.container():
        st.markdown("### Download Fellow Report", unsafe_allow_html=True)
        output_df = pd.merge(
            fellow_attendance[['Session Date', 'Attended']].reset_index(drop=True),
            fellow_scores_melted[['Test', 'Score']].reset_index(drop=True),
            how='outer',
            left_index=True, right_index=True
        )
        st.download_button(
            label="Download Report as CSV",
            data=output_df.to_csv(index=False).encode('utf-8'),
            file_name=f"{selected_fellow}_report.csv",
            mime="text/csv"
        )


