import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------- Styling --------------------
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Merriweather', Georgia, serif !important;
        color: #0a2240 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #0a2240 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0a2240;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------- Load Data --------------------
@st.cache_data
def load_data():
    path = "YA2LS Cohort 4 Data (2024 Fellows).xlsx"
    sheets = pd.read_excel(path, sheet_name=None)
    for df in sheets.values():
        df.columns = df.columns.str.strip()
    return sheets

sheets = load_data()
df_attendance = sheets["Attendance_New"]
df_scores = sheets["Test Scores"]
df_app = sheets["Application Status"]

df_attendance["Full Name"] = df_attendance["First"].str.strip() + " " + df_attendance["Last"].str.strip()
df_scores["Full Name"] = df_scores["Fellow First"].str.strip() + " " + df_scores["Fellow Last"].str.strip()
df_app["Full Name"] = df_app["First"].str.strip() + " " + df_app["Last"].str.strip()

# -------------------- LSAT Scores --------------------
lsat_cols = [
    "Diagnostic", "PT 73", "PT 136", "PT 137", "PT 138", "PT 139", "PT 140", "PT 141",
    "PT 144", "PT 145", "PT 146", "PT 147", "PT 148", "PT 149", "PT 150", "PT 151"
]
existing_lsat_cols = [col for col in lsat_cols if col in df_scores.columns]
for col in existing_lsat_cols:
    df_scores[col] = pd.to_numeric(df_scores[col], errors="coerce")

df_scores["Score_Improvement"] = df_scores.get("PT 149", pd.NA) - df_scores.get("Diagnostic", pd.NA)

scores_long = pd.melt(
    df_scores,
    id_vars=["Full Name"],
    value_vars=existing_lsat_cols,
    var_name="Test",
    value_name="Score"
)
scores_long.dropna(subset=["Score"], inplace=True)
scores_long["Test"] = pd.Categorical(scores_long["Test"], categories=lsat_cols, ordered=True)
scores_long = scores_long.sort_values(by=["Test", "Full Name"])

# -------------------- Attendance --------------------
fall_col = "Fall Small Group % Attendance"
spring_col = "Spring Small Group % Attendance"
sa_col = "Saturday Academy % Attendance"
total_col = "Total Small Group Attendance %"

df_attendance[total_col] = pd.to_numeric(df_attendance[total_col], errors="coerce")

attendance_chart_df = pd.melt(
    df_attendance,
    id_vars=["Full Name"],
    value_vars=[fall_col, spring_col, sa_col],
    var_name="Attendance Type",
    value_name="Attendance"
)
attendance_chart_df["Attendance Type"] = attendance_chart_df["Attendance Type"].map({
    fall_col: "FSG = Fall Small Group",
    spring_col: "SSG = Spring Small Group",
    sa_col: "SA = Saturday Academy"
})

# -------------------- App Status --------------------
def render_application_status(fellow_name):
    st.subheader("Application Status Overview")
    row = df_app[df_app["Full Name"] == fellow_name]
    if row.empty:
        st.info("No application status data available for this fellow.")
        return
    display = row.drop(columns=["First", "Last"]).T.reset_index()
    display.columns = ["Field", "Value"]
    st.dataframe(display, use_container_width=True, hide_index=True)

# -------------------- Utilities --------------------
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

def style_chart(fig):
    fig.update_layout(
        title_font=dict(family="Merriweather", color="#0a2240"),
        font=dict(family="Merriweather", color="#0a2240")
    )
    return fig

# -------------------- Sidebar --------------------
st.sidebar.title("Access to Law School Cohort 4")
st.sidebar.image("https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv", use_container_width=True)
mode = st.sidebar.radio("View Mode", ["Cohort Overview", "Individual Fellow Report"])

st.title("YA2LS Dashboard: LSAT Trends, Attendance & Applications")

# -------------------- Cohort Overview --------------------
if mode == "Cohort Overview":
    st.header("LSAT Score Trajectories")

    fellow_options = sorted(scores_long["Full Name"].unique())
    fellow_filter = st.multiselect("Filter by Fellow(s):", options=fellow_options, default=fellow_options)

    pt_filter = st.multiselect("Filter by Test(s):", options=lsat_cols, default=lsat_cols)

    filtered = scores_long[
        scores_long["Full Name"].isin(fellow_filter) &
        scores_long["Test"].isin(pt_filter)
    ]

    avg_df = filtered.groupby("Test", as_index=False)["Score"].mean()

    fig = px.line(filtered, x="Test", y="Score", color="Full Name", title="LSAT Trajectories", markers=True)
    fig.add_trace(go.Scatter(x=avg_df["Test"], y=avg_df["Score"], name="Cohort Avg", mode="lines+markers", line=dict(color="#004c99")))
    st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("LSAT Score Improvement by Fellows with >75% Attendance")
    high_attendance = df_attendance[df_attendance[total_col] > 75]
    joined_scores = pd.merge(
        high_attendance[["Full Name", total_col]],
        df_scores[["Full Name", "Score_Improvement"]],
        on="Full Name",
        how="left"
    ).dropna(subset=["Score_Improvement"])

    fig_growth = px.bar(joined_scores, x="Full Name", y="Score_Improvement", title="Score Improvement vs Attendance", text_auto=True)
    st.plotly_chart(style_chart(fig_growth), use_container_width=True)

    st.subheader("Average LSAT Scores Over Time")
    fig_avg = px.line(avg_df, x="Test", y="Score", markers=True, title="Cohort Average Scores", color_discrete_sequence=["#004c99"])
    st.plotly_chart(style_chart(fig_avg), use_container_width=True)

    st.subheader("Attendance by Fellow (Grouped)")
    fig_grouped = px.bar(attendance_chart_df, x="Full Name", y="Attendance", color="Attendance Type", barmode="group")
    st.plotly_chart(style_chart(fig_grouped), use_container_width=True)

    st.subheader("Attendance by Fellow (Stacked)")
    fig_stacked = px.bar(attendance_chart_df, x="Full Name", y="Attendance", color="Attendance Type", barmode="stack")
    st.plotly_chart(style_chart(fig_stacked), use_container_width=True)

    st.download_button("Download Attendance", convert_df(df_attendance), "attendance.csv", "text/csv")
    st.download_button("Download LSAT Scores", convert_df(df_scores), "lsat_scores.csv", "text/csv")

# -------------------- Individual Fellow Report --------------------
else:
    st.header("Individual Fellow Report")
    fellows = sorted(df_scores["Full Name"].dropna().unique())
    selected = st.selectbox("Select Fellow", fellows)

    render_application_status(selected)

    st.subheader("LSAT Score Trend")
    indiv_scores = scores_long[scores_long["Full Name"] == selected]
    completed_tests = indiv_scores["Test"].tolist()
    st.markdown(f"**Tests Completed:** {' → '.join(completed_tests)}")

    fig = px.line(indiv_scores, x="Test", y="Score", title=f"LSAT Scores for {selected}", markers=True)
    st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Score Improvement Summary")
    improvement = df_scores[df_scores["Full Name"] == selected]["Score_Improvement"].values[0]
    if pd.notnull(improvement):
        st.metric("Score Improvement (PT 149 - Diagnostic)", value=f"{improvement:.1f}")
    else:
        st.info("Score improvement data not available for this fellow.")

    st.subheader("Attendance Overview")
    indiv_att = attendance_chart_df[attendance_chart_df["Full Name"] == selected]
    fig_att = px.bar(indiv_att, x="Attendance Type", y="Attendance", title=f"Attendance for {selected}", color="Attendance Type")
    st.plotly_chart(style_chart(fig_att), use_container_width=True)

    cohort_median_att = df_attendance[total_col].median()
    cohort_median_imp = df_scores["Score_Improvement"].median()

    joined = pd.merge(
        df_attendance[df_attendance["Full Name"] == selected][["Full Name", total_col]],
        df_scores[df_scores["Full Name"] == selected][["Full Name", "Score_Improvement"]],
        on="Full Name", how="left"
    ).iloc[0]

    comp_df = pd.DataFrame({
        "Metric": ["Total Attendance %", "LSAT Score Improvement"],
        "Fellow": [joined[total_col], joined["Score_Improvement"]],
        "Cohort Median": [cohort_median_att, cohort_median_imp]
    })
    fig_comp = px.bar(comp_df, x="Metric", y=["Fellow", "Cohort Median"], barmode="group", title="Fellow vs. Cohort Comparison")
    st.plotly_chart(style_chart(fig_comp), use_container_width=True)

    st.download_button("Download Fellow Attendance", convert_df(df_attendance[df_attendance["Full Name"] == selected]), f"{selected}_attendance.csv", "text/csv")
    st.download_button("Download Fellow Scores", convert_df(df_scores[df_scores["Full Name"] == selected]), f"{selected}_scores.csv", "text/csv")