import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# YALE-STYLE THEME (IMPORTANT: use st.html so CSS NEVER prints)
# ============================================================
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">

<style>
  :root{
    --yale-blue: #00356b;
    --yale-blue-2: #286dc0;
    --bg: #ffffff;
  }

  /* Sidebar */
  [data-testid="stSidebar"]{
    background-color: var(--yale-blue) !important;
  }
  [data-testid="stSidebar"] *{
    color: #ffffff !important;
    font-family: "Source Sans 3", Arial, sans-serif !important;
  }

  /* Sidebar title */
  .sidebar-title{
    color: #ffffff !important;
    font-family: "Source Sans 3", Arial, sans-serif !important;
    font-weight: 700;
    font-size: 20px;
    line-height: 1.2;
    margin: 6px 0 12px 0;
  }

  /* Main page ONLY */
  [data-testid="stAppViewContainer"]{
    background: var(--bg) !important;
  }
  [data-testid="stAppViewContainer"] .main,
  [data-testid="stAppViewContainer"] .main *{
    color: var(--yale-blue) !important;
    font-family: "Libre Baskerville", Georgia, serif !important;
  }

  /* Main labels / small UI text */
  [data-testid="stAppViewContainer"] .main label,
  [data-testid="stAppViewContainer"] .main .stMarkdown p,
  [data-testid="stAppViewContainer"] .main .stMarkdown li{
    font-family: "Source Sans 3", Arial, sans-serif !important;
  }

  /* Buttons */
  .stButton>button, .stDownloadButton>button{
    background: var(--yale-blue) !important;
    color: #ffffff !important;
    border: 1px solid var(--yale-blue) !important;
  }
  .stButton>button:hover, .stDownloadButton>button:hover{
    background: var(--yale-blue-2) !important;
    border-color: var(--yale-blue-2) !important;
  }
</style>
"""

# Streamlit 1.44+ supports st.html; fallback to markdown if needed
if hasattr(st, "html"):
    st.html(CSS)
else:
    st.markdown(CSS, unsafe_allow_html=True)

YALE_BLUES = ["#00356b", "#286dc0", "#4f83cc", "#7aa6de", "#a7c3ea"]

def style_chart(fig):
    yale_blue = "#00356b"
    light_grid = "rgba(0,53,107,0.12)"
    fig.update_layout(
        font=dict(family="Libre Baskerville, Georgia, serif", color=yale_blue),
        title=dict(font=dict(family="Libre Baskerville, Georgia, serif", color=yale_blue)),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(font=dict(color=yale_blue), title_font=dict(color=yale_blue)),
        hoverlabel=dict(font=dict(color="white"), bgcolor=yale_blue),
        margin=dict(l=40, r=20, t=60, b=40),
        colorway=YALE_BLUES
    )
    fig.update_xaxes(
        gridcolor=light_grid,
        linecolor=light_grid,
        zerolinecolor=light_grid,
        title_font=dict(color=yale_blue),
        tickfont=dict(color=yale_blue)
    )
    fig.update_yaxes(
        gridcolor=light_grid,
        linecolor=light_grid,
        zerolinecolor=light_grid,
        title_font=dict(color=yale_blue),
        tickfont=dict(color=yale_blue)
    )
    return fig

def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ============================================================
# MULTI-COHORT FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats-2.xlsx",
}

@st.cache_data
def load_workbook(path: str) -> dict:
    sheets = pd.read_excel(path, sheet_name=None)
    for df in sheets.values():
        df.columns = df.columns.astype(str).str.strip()
    return sheets

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(
    '<div class="sidebar-title">Access to Law School Cohort Data Dashboard</div>',
    unsafe_allow_html=True
)

st.sidebar.image(
    "https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv",
    use_container_width=True
)

selected_cohort = st.sidebar.selectbox("Select Cohort", list(COHORT_FILES.keys()), index=0)
mode = st.sidebar.radio("Reporting Overview", ["Cohort Overview", "Individual Fellow Report"], index=0)

workbook_path = COHORT_FILES[selected_cohort]
try:
    sheets = load_workbook(workbook_path)
except FileNotFoundError:
    st.error(
        f"Could not find '{workbook_path}' in the repo. "
        "Add it to the same folder as app.py (or update COHORT_FILES paths) and redeploy."
    )
    st.stop()

# ✅ TITLE FIX: not “Dashboard”
st.title(f"{selected_cohort}")

# ============================================================
# SCHEMA DETECTION
# ============================================================
has_cohort4_schema = ("Attendance_New" in sheets and "Test Scores" in sheets and "Application Status" in sheets)
has_cohort5_schema = ("Sheet1" in sheets and not has_cohort4_schema)

# ============================================================
# COHORT 4
# ============================================================
if has_cohort4_schema:
    df_attendance = sheets["Attendance_New"].copy()
    df_scores = sheets["Test Scores"].copy()
    df_app = sheets["Application Status"].copy()

    # Full name fields
    df_attendance["Full Name"] = df_attendance["First"].astype(str).str.strip() + " " + df_attendance["Last"].astype(str).str.strip()
    df_scores["Full Name"] = df_scores["Fellow First"].astype(str).str.strip() + " " + df_scores["Fellow Last"].astype(str).str.strip()
    df_app["Full Name"] = df_app["First"].astype(str).str.strip() + " " + df_app["Last"].astype(str).str.strip()

    # LSAT scores
    lsat_cols = [
        "Diagnostic", "PT 73", "PT 136", "PT 137", "PT 138", "PT 139", "PT 140", "PT 141",
        "PT 144", "PT 145", "PT 146", "PT 147", "PT 148", "PT 149", "PT 150", "PT 151"
    ]
    existing_lsat_cols = [c for c in lsat_cols if c in df_scores.columns]
    for c in existing_lsat_cols:
        df_scores[c] = pd.to_numeric(df_scores[c], errors="coerce")

    df_scores["Score_Improvement"] = df_scores.get("PT 149", pd.NA) - df_scores.get("Diagnostic", pd.NA)

    scores_long = pd.melt(
        df_scores,
        id_vars=["Full Name"],
        value_vars=existing_lsat_cols,
        var_name="Test",
        value_name="Score"
    ).dropna(subset=["Score"])

    scores_long["Test"] = pd.Categorical(scores_long["Test"], categories=lsat_cols, ordered=True)
    scores_long = scores_long.sort_values(by=["Full Name", "Test"])

    # Attendance
    fall_col = "Fall Small Group % Attendance"
    spring_col = "Spring Small Group % Attendance"
    sa_col = "Saturday Academy % Attendance"
    total_col = "Total Small Group Attendance %"

    for c in [fall_col, spring_col, sa_col, total_col]:
        if c not in df_attendance.columns:
            st.error(f"Missing required attendance column in Cohort 4 workbook: '{c}'")
            st.stop()

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
    attendance_order = ["FSG = Fall Small Group", "SSG = Spring Small Group", "SA = Saturday Academy"]
    attendance_chart_df["Attendance Type"] = pd.Categorical(attendance_chart_df["Attendance Type"], categories=attendance_order, ordered=True)

    def render_application_status_chart(fellow_name: str):
        st.subheader("Application Status Overview")
        row = df_app[df_app["Full Name"] == fellow_name]
        if row.empty:
            st.info("No application status data available for this fellow.")
            return

        data = row.drop(columns=["First", "Last"], errors="ignore").iloc[0].to_dict()
        fields, values = [], []
        for k, v in data.items():
            if k == "Full Name":
                continue
            fields.append(k)
            values.append(0 if pd.isna(v) or str(v).strip() == "" else 1)

        app_df = pd.DataFrame({"Field": fields, "Has Data": values})
        fig = px.bar(
            app_df,
            x="Field",
            y="Has Data",
            title="Application Fields Present (1=present, 0=missing)",
            color_discrete_sequence=["#286dc0"]
        )
        fig.update_yaxes(title_text="Indicator")
        st.plotly_chart(style_chart(fig), use_container_width=True)

    # -------------------- Cohort Overview --------------------
    if mode == "Cohort Overview":
        st.header("Cohort Overview")

        st.subheader("LSAT Trajectories (Hover for Fellow Name)")

        fellow_options = sorted(scores_long["Full Name"].dropna().unique())
        fellow_filter = st.multiselect("Filter by Fellow(s)", options=fellow_options, default=fellow_options)

        pt_filter = st.multiselect("Filter by Test(s)", options=lsat_cols, default=lsat_cols)

        filtered = scores_long[
            scores_long["Full Name"].isin(fellow_filter) &
            scores_long["Test"].isin(pt_filter)
        ]

        avg_df = filtered.groupby("Test", as_index=False)["Score"].mean()

        fig = px.line(filtered, x="Test", y="Score", color="Full Name",
                      title="LSAT Trajectories", markers=True)
        fig.add_trace(go.Scatter(
            x=avg_df["Test"],
            y=avg_df["Score"],
            name="Cohort Avg",
            mode="lines+markers",
            line=dict(color="#00356b", width=4)
        ))
        st.plotly_chart(style_chart(fig), use_container_width=True)

        st.subheader("LSAT Growth for Fellows with >75% Total Attendance")
        high_attendance = df_attendance[df_attendance[total_col] > 75]
        joined_scores = pd.merge(
            high_attendance[["Full Name", total_col]],
            df_scores[["Full Name", "Score_Improvement"]],
            on="Full Name",
            how="left"
        ).dropna(subset=["Score_Improvement"])

        fig_growth = px.bar(
            joined_scores,
            x="Full Name",
            y="Score_Improvement",
            text_auto=True,
            title="Score Improvement (PT149 - Diagnostic) — Fellows >75% Attendance",
            color_discrete_sequence=["#286dc0"]
        )
        fig_growth.update_yaxes(title_text="Score Improvement (points)")
        st.plotly_chart(style_chart(fig_growth), use_container_width=True)

        st.subheader("Attendance by Fellow (Grouped)")
        fig_grouped = px.bar(
            attendance_chart_df,
            x="Full Name",
            y="Attendance",
            color="Attendance Type",
            barmode="group",
            category_orders={"Attendance Type": attendance_order},
            color_discrete_sequence=["#00356b", "#286dc0", "#7aa6de"]
        )
        fig_grouped.update_yaxes(title_text="Attendance Percent out of 100%")
        st.plotly_chart(style_chart(fig_grouped), use_container_width=True)

        st.subheader("Attendance by Fellow (Stacked)")
        fig_stacked = px.bar(
            attendance_chart_df,
            x="Full Name",
            y="Attendance",
            color="Attendance Type",
            barmode="stack",
            category_orders={"Attendance Type": attendance_order},
            color_discrete_sequence=["#00356b", "#286dc0", "#7aa6de"]
        )
        fig_stacked.update_yaxes(title_text="Attendance Percent out of 100%")
        st.plotly_chart(style_chart(fig_stacked), use_container_width=True)

        st.download_button("Download Attendance (CSV)", convert_df(df_attendance), "attendance.csv", "text/csv")
        st.download_button("Download LSAT Scores (CSV)", convert_df(df_scores), "lsat_scores.csv", "text/csv")
        st.download_button("Download Application Status (CSV)", convert_df(df_app), "application_status.csv", "text/csv")

    # -------------------- Individual Fellow Report --------------------
    else:
        st.header("Individual Fellow Report")

        fellows = sorted(df_scores["Full Name"].dropna().unique())
        selected = st.selectbox("Select Fellow", fellows)

        st.markdown("**Legend:** FSG = Fall Small Group, SSG = Spring Small Group, SA = Saturday Academy")

        st.subheader("LSAT Score Trend")
        indiv_scores = scores_long[scores_long["Full Name"] == selected]

        fig_indiv = px.line(indiv_scores, x="Test", y="Score", markers=True,
                            title=f"LSAT Scores for {selected}", color_discrete_sequence=["#00356b"])
        st.plotly_chart(style_chart(fig_indiv), use_container_width=True)

        st.subheader("Attendance Overview")
        indiv_att = attendance_chart_df[attendance_chart_df["Full Name"] == selected]
        fig_att = px.bar(
            indiv_att,
            x="Attendance Type",
            y="Attendance",
            color="Attendance Type",
            category_orders={"Attendance Type": attendance_order},
            title=f"Attendance for {selected}",
            color_discrete_sequence=["#00356b", "#286dc0", "#7aa6de"]
        )
        fig_att.update_xaxes(title_text="Attendance Type")
        fig_att.update_yaxes(title_text="Attendance Percent out of 100%")
        st.plotly_chart(style_chart(fig_att), use_container_width=True)

        render_application_status_chart(selected)

        st.download_button(
            "Download Fellow Attendance (CSV)",
            convert_df(df_attendance[df_attendance["Full Name"] == selected]),
            f"{selected}_attendance.csv",
            "text/csv"
        )
        st.download_button(
            "Download Fellow Scores (CSV)",
            convert_df(df_scores[df_scores["Full Name"] == selected]),
            f"{selected}_scores.csv",
            "text/csv"
        )
        st.download_button(
            "Download Fellow Application Status (CSV)",
            convert_df(df_app[df_app["Full Name"] == selected]),
            f"{selected}_application_status.csv",
            "text/csv"
        )

# ============================================================
# COHORT 5 (Demographics / Background)
# ============================================================
elif has_cohort5_schema:
    df = sheets["Sheet1"].copy()

    name_col = "Unnamed: 0"
    if name_col not in df.columns:
        st.error("Cohort 5 file: expected fellow name column 'Unnamed: 0' not found.")
        st.stop()

    df["Full Name"] = df[name_col].astype(str).str.strip()

    # Clean numeric columns
    for c in ["Age", "GPA"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    yn_cols = [c for c in ["First-Gen", "Syst Impacted", "Strong Ties", "LGBTQIA+"] if c in df.columns]
    for c in yn_cols:
        df[c] = df[c].astype(str).str.strip().replace({"nan": pd.NA, "": pd.NA})

    if mode == "Cohort Overview":
        st.header("Cohort Overview")

        for c in yn_cols:
            counts = df[c].fillna("Missing").value_counts().reset_index()
            counts.columns = [c, "Count"]
            fig = px.bar(counts, x=c, y="Count", title=f"{c} Distribution",
                         color_discrete_sequence=["#286dc0"])
            st.plotly_chart(style_chart(fig), use_container_width=True)

        if "GPA" in df.columns:
            fig_gpa = px.histogram(
                df.dropna(subset=["GPA"]),
                x="GPA",
                nbins=10,
                title="GPA Distribution",
                color_discrete_sequence=["#00356b"]
            )
            st.plotly_chart(style_chart(fig_gpa), use_container_width=True)

        if "Age" in df.columns:
            fig_age = px.histogram(
                df.dropna(subset=["Age"]),
                x="Age",
                nbins=10,
                title="Age Distribution",
                color_discrete_sequence=["#7aa6de"]
            )
            st.plotly_chart(style_chart(fig_age), use_container_width=True)

        if "Gender Identity" in df.columns:
            g = df["Gender Identity"].fillna("Missing").value_counts().reset_index()
            g.columns = ["Gender Identity", "Count"]
            fig_gender = px.bar(
                g,
                x="Gender Identity",
                y="Count",
                title="Gender Identity Distribution",
                color_discrete_sequence=["#286dc0"]
            )
            st.plotly_chart(style_chart(fig_gender), use_container_width=True)

        st.download_button("Download Cohort 5 Data (CSV)", convert_df(df), "cohort5.csv", "text/csv")

    else:
        st.header("Individual Fellow Report")

        fellows = sorted(df["Full Name"].dropna().unique())
        selected = st.selectbox("Select Fellow", fellows)

        row = df[df["Full Name"] == selected].iloc[0]

        profile_fields, profile_vals = [], []
        for c in yn_cols:
            v = str(row.get(c, "")).strip().lower()
            if v in ("yes", "y", "true", "1"):
                profile_fields.append(c)
                profile_vals.append(1)
            elif v in ("no", "n", "false", "0"):
                profile_fields.append(c)
                profile_vals.append(0)

        prof = pd.DataFrame({"Field": profile_fields, "Value": profile_vals})
        if not prof.empty:
            fig_prof = px.bar(
                prof,
                x="Field",
                y="Value",
                title=f"Profile Indicators for {selected} (1=Yes, 0=No)",
                color_discrete_sequence=["#00356b"]
            )
            fig_prof.update_yaxes(title_text="Indicator", range=[0, 1])
            st.plotly_chart(style_chart(fig_prof), use_container_width=True)

        cols = st.columns(2)
        if "GPA" in df.columns and pd.notnull(row.get("GPA")):
            cols[0].metric("GPA", f"{row.get('GPA'):.2f}")
        if "Age" in df.columns and pd.notnull(row.get("Age")):
            cols[1].metric("Age", f"{int(row.get('Age'))}")

        if "Hometown" in df.columns:
            st.subheader("Hometown")
            st.write(str(row.get("Hometown", "")))

        if "Strong Ties" in df.columns:
            st.subheader("Strong Ties")
            st.write(str(row.get("Strong Ties", "")))

        if "Graduated from Bachelors Program" in df.columns:
            st.subheader("Graduated from Bachelors Program")
            st.write(str(row.get("Graduated from Bachelors Program", "")))

        st.download_button(
            "Download Fellow Row (CSV)",
            convert_df(df[df["Full Name"] == selected]),
            f"{selected}_cohort5.csv",
            "text/csv"
        )

# ============================================================
# UNKNOWN SCHEMA
# ============================================================
else:
    st.error(
        "This workbook doesn’t match Cohort 4 (Attendance/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1 demographics) schemas."
    )
    st.stop()
