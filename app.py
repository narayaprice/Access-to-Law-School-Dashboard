
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

   # --- COHORT OVERVIEW ---
if page == "Cohort Overview":
    st.title("YA2LS 2024 Fellows - Cohort Overview")

    attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']

    # Attendance Metrics
    st.header("Attendance Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg. Total Attendance %", f"{attendance_df['%Total Attendance'].mean():.1f}%")
    col2.metric("Avg. Small Group Attendance %", f"{attendance_df['% Small Group Attendance'].mean():.1f}%")
    col3.metric("Avg. Practice Test Attendance %", f"{attendance_df['% Practice Test Attendance'].mean():.1f}%")

    # Bar chart - Total Attendance
    st.subheader("Total Attendance by Fellow")
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    sorted_total = attendance_df.sort_values('%Total Attendance', ascending=True)
    ax1.barh(sorted_total['Full Name'], sorted_total['%Total Attendance'], color='skyblue')
    ax1.set_xlabel('% Attendance')
    ax1.set_title('Total Attendance by Fellow')
    st.pyplot(fig1)

    # Bar chart - Small Group Attendance
    st.subheader("Small Group Attendance by Fellow")
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    sorted_sg = attendance_df.sort_values('% Small Group Attendance', ascending=True)
    ax2.barh(sorted_sg['Full Name'], sorted_sg['% Small Group Attendance'], color='orange')
    ax2.set_xlabel('% Attendance')
    ax2.set_title('Small Group Attendance by Fellow')
    st.pyplot(fig2)

    # Test Score Summary
    st.header("Test Score Summary")
    scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']
    scores_df.rename(columns={'Diagnostic ': 'Diagnostic', 'Approx PB': 'PB'}, inplace=True)

    col4, col5 = st.columns(2)
    col4.metric("Average Diagnostic Score", f"{scores_df['Diagnostic'].mean():.1f}")
    col5.metric("Average PB Score", f"{scores_df['PB'].mean():.1f}")

    # Bar chart - Personal Best Scores
    st.subheader("Personal Best Scores by Fellow")
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    sorted_scores = scores_df.sort_values('PB', ascending=True)
    ax3.barh(sorted_scores['Name'], sorted_scores['PB'], color='green')
    ax3.set_xlabel('Score')
    ax3.set_title('Personal Best (PB) Scores')
    st.pyplot(fig3)


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