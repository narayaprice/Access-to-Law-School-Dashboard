import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
st.cache_data.clear() 

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

# Create 'Full Name' and 'Name' columns early for reuse
attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']
scores_df.rename(columns={'Diagnostic ': 'Diagnostic', 'Approx PB': 'PB'}, inplace=True)

# Sidebar navigation
page = st.sidebar.selectbox("Select View", ["Cohort Overview", "Individual Fellow Report"])

# --- COHORT OVERVIEW ---
if page == "Cohort Overview":
    st.title("YA2LS 2024 Fellows - Cohort Overview")

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
    fellows = attendance_df['Full Name']
    selected = st.selectbox("Select a Fellow", fellows)

    # Get selected fellow rows
    att_match = attendance_df[attendance_df['Full Name'] == selected]
    score_match = scores_df[scores_df['Name'] == selected]

    if not att_match.empty:
        att_row = att_match.iloc[0]
        st.subheader("Attendance (Includes Small Group & Saturday Academy)")
        st.write(f"**Total Attendance:** {att_row['%Total Attendance']}% ({att_row['Count Attendance']} sessions)")
        st.write(f"**Small Group Attendance:** {att_row['% Small Group Attendance']}%")         
        st.write(f"**Practice Test Attendance:** {att_row['% Practice Test Attendance']}%")

        # --- Attendance Over Time Chart ---
        attendance_columns = [
            col for col in attendance_df.columns
            if col.startswith("FSG") or col.startswith("SSG") or col.startswith("Spring Small Group")
        ]

        raw_attendance = att_row[attendance_columns]

        # Convert attendance entries to binary (1 = Present, 0 = Absent)
        bin_attendance = raw_attendance.apply(lambda x: 1 if str(x).strip().lower() in ['yes', '1', 'present'] else 0)

        # Build DataFrame for charting
        attendance_chart = pd.DataFrame({
            "Session": bin_attendance.index,
            "Present": bin_attendance.values
        }).set_index("Session")

        st.subheader("Session Attendance Over Time")
        st.bar_chart(attendance_chart)

    else:
        st.warning("No attendance data found for this fellow.")

    if not score_match.empty:
        score_row = score_match.iloc[0]
        st.subheader("Test Scores")
        st.write(f"**Diagnostic:** {score_row['Diagnostic']}")
        st.write(f"**Personal Best (PB):** {score_row['PB']}")

        # --- Practice Test Scores Over Time ---
        pt_columns = [col for col in scores_df.columns if col.startswith("PT")]
        pt_scores = score_row[pt_columns].dropna()

        # Clean column names (remove spaces)
        pt_scores.index = [col.replace(" ", "") for col in pt_scores.index]

        if not pt_scores.empty:
            pt_chart = pd.DataFrame({
                "PT": pt_scores.index,
                "Score": pt_scores.values
            }).sort_values("PT")  # PT names like PT136, PT137, etc.

            pt_chart.set_index("PT", inplace=True)

            st.subheader("Practice Test Scores Over Time")
            st.line_chart(pt_chart)
        else:
            st.info("No practice test scores available.")
    else:
        st.info("No score data available for this fellow.")