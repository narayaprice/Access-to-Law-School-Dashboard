import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------- Custom CSS & Fonts for Yale Styling --------------------
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
    /* Sidebar: Yale blue background with white text */
    [data-testid="stSidebar"] {
        background-color: #0a2240;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
        font-family: Arial, sans-serif;
    }
    /* Main content: Use Merriweather with navy blue text */
    .reportview-container .main, .reportview-container .main * {
        color: #0a2240 !important;
        font-family: 'Merriweather', Georgia, serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------- Data Loading --------------------
@st.cache_data
def load_data():
    data_file = "YA2LS Cohort 4 Data (2024 Fellows).xlsx"
    sheets = pd.read_excel(data_file, sheet_name=["Attendance_New", "Test Scores"])
    return sheets["Attendance_New"], sheets["Test Scores"]

df_attendance, df_scores = load_data()

# -------------------- Helper Function to Find a Column --------------------
def find_column(df, candidates):
    for col in df.columns:
        for candidate in candidates:
            if candidate.lower() in col.lower():
                return col
    return None

# -------------------- Identify Fellow Column --------------------
test_fellow_col = find_column(df_scores, ["Fellow", "Name"])
if test_fellow_col is None:
    st.error("Required fellow identifier column ('Fellow' or 'Name') not found in Test Scores sheet.")
    st.stop()

attendance_fellow_col = find_column(df_attendance, ["Fellow", "Name"])
if attendance_fellow_col is None:
    df_attendance["Fellow"] = df_scores[test_fellow_col]
    attendance_fellow_col = "Fellow"

# -------------------- Define Attendance Columns --------------------
fall_col = "Fall Small Group Attendance %"
spring_col = "Spring Small Group Attendance %"
sa_col = "SA %"
total_attendance_col = "Total Attendance %"

for col in [fall_col, spring_col, sa_col, total_attendance_col]:
    if col not in df_attendance.columns:
        st.error(f"Required column '{col}' not found in Attendance_New sheet.")
        st.stop()

df_attendance[total_attendance_col] = pd.to_numeric(df_attendance[total_attendance_col], errors="coerce")

# Create long-format DataFrame for the summary attendance charts.
attendance_chart_df = pd.melt(
    df_attendance,
    id_vars=[attendance_fellow_col],
    value_vars=[fall_col, spring_col, sa_col],
    var_name="Attendance Type",
    value_name="Attendance"
)
attendance_chart_df["Attendance Type"] = attendance_chart_df["Attendance Type"].map({
    fall_col: "FSG",
    spring_col: "SSG",
    sa_col: "SA"
})

# -------------------- Detailed Attendance Events --------------------
# Automatically detect additional attendance columns starting with FSG, SSG, or SA (excluding summary columns).
detailed_attendance_cols = [
    col for col in df_attendance.columns 
    if col not in [fall_col, spring_col, sa_col, total_attendance_col, attendance_fellow_col]
    and any(col.upper().startswith(prefix) for prefix in ["FSG", "SSG", "SA"])
]
if detailed_attendance_cols:
    detailed_attendance_df = df_attendance[[attendance_fellow_col] + detailed_attendance_cols]
    detailed_attendance_long = pd.melt(
        detailed_attendance_df,
        id_vars=[attendance_fellow_col],
        value_vars=detailed_attendance_cols,
        var_name="Event",
        value_name="Attendance"
    )
    # Order events if needed; here we simply sort alphabetically.
    event_order = sorted(detailed_attendance_long["Event"].unique())
    detailed_attendance_long["Event"] = pd.Categorical(detailed_attendance_long["Event"],
                                                       categories=event_order,
                                                       ordered=True)
else:
    detailed_attendance_long = None

# -------------------- Process Test Scores --------------------
score_columns_expected = ["Diagnostic", "PT 71", "PT 73", "PT136", "PT 137", "PT 138",
                          "PT 139", "PT 140", "PT 141", "PT 144", "PT 145", "PT 146",
                          "PT 147", "PT 148", "PT 149"]
for col in ["Diagnostic", "PT 149"]:
    if col not in df_scores.columns:
        st.error(f"Required test score column '{col}' not found in Test Scores sheet.")
        st.stop()

existing_score_columns = [col for col in score_columns_expected if col in df_scores.columns]
for col in existing_score_columns:
    df_scores[col] = pd.to_numeric(df_scores[col], errors="coerce")

scores_long = pd.melt(
    df_scores,
    id_vars=test_fellow_col,
    value_vars=existing_score_columns,
    var_name="Test",
    value_name="Score"
)
scores_long["Score"] = pd.to_numeric(scores_long["Score"], errors="coerce")
scores_long = scores_long.dropna(subset=["Score"])
scores_long["Test"] = pd.Categorical(scores_long["Test"], categories=existing_score_columns, ordered=True)

df_scores["Score_Improvement"] = df_scores["PT 149"] - df_scores["Diagnostic"]

# -------------------- LSAT Trajectory Chart for All Fellows --------------------
fig_trajectories = px.line(
    scores_long,
    x="Test",
    y="Score",
    color=test_fellow_col,
    title="LSAT Trajectories for All Fellows",
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Plotly
)
avg_scores_df = scores_long.groupby("Test", as_index=False)["Score"].mean()
fig_trajectories.add_trace(go.Scatter(
    x=avg_scores_df["Test"],
    y=avg_scores_df["Score"],
    mode="lines+markers",
    name="Average Trajectory",
    line=dict(color="#004c99", width=4)
))

# -------------------- LSAT Growth for Fellows with >75% Attendance --------------------
high_attendance = df_attendance[df_attendance[total_attendance_col] > 75]
high_attendance_scores = pd.merge(
    high_attendance[[attendance_fellow_col, total_attendance_col]],
    df_scores[[test_fellow_col, "Score_Improvement"]],
    left_on=attendance_fellow_col,
    right_on=test_fellow_col,
    how="inner"
)
fig_growth_high = px.bar(
    high_attendance_scores,
    x=attendance_fellow_col,
    y="Score_Improvement",
    title="LSAT Growth for Fellows with >75% Attendance",
    text_auto=True,
    color=attendance_fellow_col,
    color_discrete_sequence=px.colors.sequential.Blues
)

# -------------------- Average LSAT Scores Over Test Events --------------------
avg_scores = scores_long.groupby("Test", as_index=False)["Score"].mean()
fig_avg_scores = px.line(
    avg_scores,
    x="Test",
    y="Score",
    title="Average LSAT Scores Over Test Events",
    markers=True,
    color_discrete_sequence=["#004c99"]
)

# -------------------- Download Button Function --------------------
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# -------------------- Chart Helper Function --------------------
def style_chart(fig):
    fig.update_layout(
        title_font=dict(family="Merriweather", color="#0a2240"),
        font=dict(family="Merriweather", color="#0a2240")
    )
    return fig

# -------------------- Sidebar Setup --------------------
st.sidebar.title("Access to Law School Cohort 4 Data Dashboard")
st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
reporting_option = st.sidebar.selectbox("Select Reporting Overview", ["Cohort Overview", "Individual Fellow Reports"], index=0)

# -------------------- Main App Layout --------------------
st.title("Access to Law School Cohort 4 Data Dashboard")

if reporting_option == "Cohort Overview":
    st.header("Cohort Overview")
    
    st.subheader("Attendance by Fellow (Grouped Bar Chart)")
    fig_grouped = px.bar(
        attendance_chart_df,
        x=attendance_fellow_col,
        y="Attendance",
        color="Attendance Type",
        barmode="group",
        title="Attendance (FSG, SSG, SA) by Fellow (Grouped)",
        color_discrete_sequence=["#1f77b4", "#5dade2", "#85c1e9"]
    )
    st.plotly_chart(style_chart(fig_grouped), use_container_width=True)
    
    st.subheader("Attendance by Fellow (Stacked Bar Chart)")
    fig_stacked = px.bar(
        attendance_chart_df,
        x=attendance_fellow_col,
        y="Attendance",
        color="Attendance Type",
        barmode="stack",
        title="Attendance (FSG, SSG, SA) by Fellow (Stacked)",
        color_discrete_sequence=["#1f77b4", "#5dade2", "#85c1e9"]
    )
    st.plotly_chart(style_chart(fig_stacked), use_container_width=True)
    
    st.subheader("LSAT Trajectories")
    st.plotly_chart(style_chart(fig_trajectories), use_container_width=True)
    
    st.subheader("LSAT Growth for Fellows with >75% Attendance")
    st.plotly_chart(style_chart(fig_growth_high), use_container_width=True)
    
    st.subheader("Average LSAT Scores Over Test Events")
    st.plotly_chart(style_chart(fig_avg_scores), use_container_width=True)
    
    st.markdown("### Download Cohort Data")
    st.download_button("Download Attendance Data", convert_df(df_attendance), "attendance_data.csv", "text/csv", key='download-attendance')
    st.download_button("Download Test Scores Data", convert_df(df_scores), "test_scores_data.csv", "text/csv", key='download-scores')
    
elif reporting_option == "Individual Fellow Reports":
    st.header("Individual Fellow Reports")
    fellows = sorted(df_scores[test_fellow_col].unique())
    selected_fellow = st.selectbox("Select Fellow", fellows)
    
    st.subheader("Attendance Overview")
    fellow_attendance = attendance_chart_df[attendance_chart_df[attendance_fellow_col] == selected_fellow]
    fig_fellow_att = px.bar(
        fellow_attendance,
        x="Attendance Type",
        y="Attendance",
        title=f"Attendance for {selected_fellow}",
        color="Attendance Type",
        color_discrete_sequence=["#1f77b4", "#5dade2", "#85c1e9"]
    )
    fig_fellow_att.update_xaxes(title_text="Attendance Type")
    fig_fellow_att.update_yaxes(title_text="Attendance Percent out of 100%")
    st.plotly_chart(style_chart(fig_fellow_att), use_container_width=True)
    
    if detailed_attendance_long is not None:
        st.subheader("Detailed Attendance Events")
        fellow_detailed = detailed_attendance_long[detailed_attendance_long[attendance_fellow_col] == selected_fellow]
        if not fellow_detailed.empty:
            fig_detailed = px.bar(
                fellow_detailed,
                x="Event",
                y="Attendance",
                title=f"Detailed Attendance Events for {selected_fellow}",
                color="Event",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            st.plotly_chart(style_chart(fig_detailed), use_container_width=True)
        else:
            st.info("No detailed attendance event data available for this fellow.")
    
    st.subheader("LSAT Test Score Trend")
    fellow_scores = scores_long[scores_long[test_fellow_col] == selected_fellow]
    fig_fellow_line = px.line(
        fellow_scores,
        x="Test",
        y="Score",
        title=f"LSAT Test Score Trend for {selected_fellow}",
        markers=True
    )
    st.plotly_chart(style_chart(fig_fellow_line), use_container_width=True)
    
    st.subheader("Comparison: Selected Fellow vs. Cohort Median")
    cohort_median_attendance = df_attendance[total_attendance_col].median()
    cohort_median_improvement = df_scores["Score_Improvement"].median()
    fellow_data = pd.merge(
        df_attendance[df_attendance[attendance_fellow_col] == selected_fellow][[attendance_fellow_col, total_attendance_col]],
        df_scores[df_scores[test_fellow_col] == selected_fellow][[test_fellow_col, "Score_Improvement"]],
        left_on=attendance_fellow_col,
        right_on=test_fellow_col,
        how="left"
    ).iloc[0]
    comp_df = pd.DataFrame({
        "Metric": ["Total Attendance %", "LSAT Score Improvement"],
        "Fellow": [fellow_data[total_attendance_col], fellow_data["Score_Improvement"]],
        "Cohort Median": [cohort_median_attendance, cohort_median_improvement]
    })
    fig_comp = px.bar(comp_df, x="Metric", y=["Fellow", "Cohort Median"], barmode="group",
                      title="Comparison: Selected Fellow vs. Cohort Median")
    st.plotly_chart(style_chart(fig_comp), use_container_width=True)
    
    st.markdown("### Download Individual Fellow Data")
    st.download_button("Download Attendance Data", convert_df(df_attendance[df_attendance[attendance_fellow_col] == selected_fellow]), f"{selected_fellow}_attendance.csv", "text/csv", key='download-fellow-att')
    st.download_button("Download Test Scores Data", convert_df(df_scores[df_scores[test_fellow_col] == selected_fellow]), f"{selected_fellow}_scores.csv", "text/csv", key='download-fellow-scores')