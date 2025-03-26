
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load Excel file
@st.cache_data
def load_data():
    xls = pd.ExcelFile("YA2LS Cohort 4 Data (2024 Fellows).xlsx")
    attendance_df = xls.parse("Attendance")
    scores_df = xls.parse("Test Scores")
    return attendance_df, scores_df

attendance_df, scores_df = load_data()

# Clean column names
attendance_df.columns = attendance_df.columns.str.strip()
scores_df.columns = scores_df.columns.str.strip()

# Sidebar navigation
page = st.sidebar.selectbox("Select View", ["Cohort Overview", "Individual Fellow Report"])

# --- COHORT OVERVIEW ---
if page == "Cohort Overview":
    st.title("YA2LS 2024 Fellows - Cohort Overview")

    # Attendance Overview
    st.header("Attendance Summary")
    attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
    st.metric("Average Total Attendance %", f"{attendance_df['%Total Attendance'].mean():.1f}%")
    st.metric("Average Small Group Attendance %", f"{attendance_df['% Small Group Attendance'].mean():.1f}%")

    # Bar chart - Total Attendance
    st.subheader("Total Attendance by Fellow")
    att_plot = attendance_df[['Full Name', '%Total Attendance']].sort_values('%Total Attendance', ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(att_plot['Full Name'], att_plot['%Total Attendance'])
    ax.invert_yaxis()
    ax.set_xlabel('% Attendance')
    ax.set_title('Total Attendance % by Fellow')
    st.pyplot(fig)

    # Test Score Summary
    st.header("Test Score Summary")
    scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']
    scores_df = scores_df.rename(columns={'Diagnostic ': 'Diagnostic', 'Approx PB': 'PB'})
    st.metric("Average Diagnostic Score", f"{scores_df['Diagnostic'].mean():.1f}")
    st.metric("Average PB Score", f"{scores_df['PB'].mean():.1f}")

# --- INDIVIDUAL FELLOW REPORT ---
elif page == "Individual Fellow Report":
    st.title("Fellow Report")
    fellows = attendance_df['First'] + ' ' + attendance_df['Last']
    selected = st.selectbox("Select a Fellow", fellows)

    att_row = attendance_df[attendance_df['Full Name'] == selected].iloc[0]
    score_row = scores_df[scores_df['Name'] == selected].iloc[0] if selected in scores_df['Name'].values else None

    st.subheader("Attendance")
    st.write(f"**Total Attendance:** {att_row['%Total Attendance']}% ({att_row['Count Attendance']} sessions)")
    st.write(f"**Small Group Attendance:** {att_row['% Small Group Attendance']}%")
    st.write(f"**Practice Test Attendance:** {att_row['% Practice Test Attendance']}%")

    if score_row is not None:
        st.subheader("Test Scores")
        st.write(f"**Diagnostic:** {score_row['Diagnostic']}")
        st.write(f"**Personal Best (PB):** {score_row['PB']}")
        pt_scores = score_row[[col for col in scores_df.columns if "PT" in col and "Unnamed" not in col]].dropna()

        st.line_chart(pt_scores.T.rename(columns={pt_scores.name: 'Score'}))
    else:
        st.write("No score data available for this fellow.")
