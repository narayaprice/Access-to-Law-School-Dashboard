import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# YALE-STYLE THEME (use st.html so CSS never prints as text)
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
if hasattr(st, "html"):
    st.html(CSS)
else:
    st.markdown(CSS, unsafe_allow_html=True)

YALE_BLUES = ["#00356b", "#286dc0", "#7aa6de"]

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
    fig.update_xaxes(gridcolor=light_grid, linecolor=light_grid, zerolinecolor=light_grid)
    fig.update_yaxes(gridcolor=light_grid, linecolor=light_grid, zerolinecolor=light_grid)
    return fig

def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

@st.cache_data
def load_workbook(path: str) -> dict:
    sheets = pd.read_excel(path, sheet_name=None)
    for df in sheets.values():
        df.columns = df.columns.astype(str).str.strip()
    return sheets

# ============================================================
# COHORT FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}

# ============================================================
# SIDEBAR (NO REPORTING OVERVIEW RADIO ANYMORE)
# ============================================================
st.sidebar.markdown(
    '<div class="sidebar-title">Access to Law School Cohort Data Dashboard</div>',
    unsafe_allow_html=True
)
st.sidebar.image("sidebar_photo.jpg", use_container_width=True)

selected_cohort = st.sidebar.selectbox(
    "Select Cohort",
    list(COHORT_FILES.keys()),
    index=0
)
selected_cohort = st.sidebar.selectbox("Select Cohort", list(COHORT_FILES.keys()), index=0))

workbook_path = COHORT_FILES[selected_cohort]
try:
    sheets = load_workbook(workbook_path)
except FileNotFoundError:
    st.error(
        f"Could not find '{workbook_path}' in the repo. "
        "Add it next to app.py (or update COHORT_FILES) and redeploy."
    )
    st.stop()

# Main title (keep simple)
st.title(f"{selected_cohort}")

# ============================================================
# SCHEMA DETECTION
# ============================================================
is_cohort4 = ("Attendance_New" in sheets and "Test Scores" in sheets and "Application Status" in sheets)
is_cohort5 = ("Sheet1" in sheets and not is_cohort4)

# ============================================================
# COHORT 4 — INDIVIDUAL ONLY (charts OK)
# ============================================================
if is_cohort4:
    df_attendance = sheets["Attendance_New"].copy()
    df_scores = sheets["Test Scores"].copy()
    df_app = sheets["Application Status"].copy()

    # Full names
    df_attendance["Full Name"] = df_attendance["First"].astype(str).str.strip() + " " + df_attendance["Last"].astype(str).str.strip()
    df_scores["Full Name"] = df_scores["Fellow First"].astype(str).str.strip() + " " + df_scores["Fellow Last"].astype(str).str.strip()
    df_app["Full Name"] = df_app["First"].astype(str).str.strip() + " " + df_app["Last"].astype(str).str.strip()

    # Sidebar fellow selector (THIS is the only “view selector” now)
    fellows = sorted(df_scores["Full Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.subheader(selected)  # <-- Fellow name at top

    # -------------------- LSAT Scores --------------------
    lsat_cols = [
        "Diagnostic", "PT 73", "PT 136", "PT 137", "PT 138", "PT 139", "PT 140", "PT 141",
        "PT 144", "PT 145", "PT 146", "PT 147", "PT 148", "PT 149", "PT 150", "PT 151"
    ]
    existing_lsat_cols = [c for c in lsat_cols if c in df_scores.columns]
    for c in existing_lsat_cols:
        df_scores[c] = pd.to_numeric(df_scores[c], errors="coerce")

    scores_long = pd.melt(
        df_scores,
        id_vars=["Full Name"],
        value_vars=existing_lsat_cols,
        var_name="Test",
        value_name="Score"
    ).dropna(subset=["Score"])
    scores_long = scores_long[scores_long["Full Name"] == selected].copy()
    scores_long["Test"] = pd.Categorical(scores_long["Test"], categories=lsat_cols, ordered=True)
    scores_long = scores_long.sort_values("Test")

    st.subheader("LSAT Score Trend")
    if scores_long.empty:
        st.info("No LSAT score data available for this fellow.")
    else:
        fig_lsat = px.line(
            scores_long, x="Test", y="Score",
            title=f"LSAT Scores for {selected}",
            markers=True,
            color_discrete_sequence=["#00356b"]
        )
        st.plotly_chart(style_chart(fig_lsat), use_container_width=True)

    # -------------------- Attendance --------------------
    fall_col = "Fall Small Group % Attendance"
    spring_col = "Spring Small Group % Attendance"
    sa_col = "Saturday Academy % Attendance"

    required_att_cols = [fall_col, spring_col, sa_col]
    missing = [c for c in required_att_cols if c not in df_attendance.columns]
    if missing:
        st.error(f"Missing attendance columns in Cohort 4 workbook: {missing}")
        st.stop()

    attendance_order = ["FSG = Fall Small Group", "SSG = Spring Small Group", "SA = Saturday Academy"]

    att_row = df_attendance[df_attendance["Full Name"] == selected].copy()
    if att_row.empty:
        st.subheader("Attendance Overview")
        st.info("No attendance data available for this fellow.")
    else:
        att_long = pd.melt(
            att_row,
            id_vars=["Full Name"],
            value_vars=[fall_col, spring_col, sa_col],
            var_name="Attendance Type",
            value_name="Attendance"
        )
        att_long["Attendance"] = pd.to_numeric(att_long["Attendance"], errors="coerce")
        att_long["Attendance Type"] = att_long["Attendance Type"].map({
            fall_col: "FSG = Fall Small Group",
            spring_col: "SSG = Spring Small Group",
            sa_col: "SA = Saturday Academy"
        })
        att_long["Attendance Type"] = pd.Categorical(att_long["Attendance Type"], categories=attendance_order, ordered=True)

        st.subheader("Attendance Overview")
        fig_att = px.bar(
            att_long,
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

    # -------------------- Application Status (chart is okay) --------------------
    st.subheader("Application Status Overview")
    app_row = df_app[df_app["Full Name"] == selected].copy()
    if app_row.empty:
        st.info("No application status data available for this fellow.")
    else:
        data = app_row.drop(columns=["First", "Last"], errors="ignore").iloc[0].to_dict()
        fields, values = [], []
        for k, v in data.items():
            if k == "Full Name":
                continue
            fields.append(k)
            values.append(0 if pd.isna(v) or str(v).strip() == "" else 1)

        app_df = pd.DataFrame({"Field": fields, "Has Data": values})
        fig_app = px.bar(
            app_df,
            x="Field",
            y="Has Data",
            title="Application Fields Present (1=present, 0=missing)",
            color_discrete_sequence=["#286dc0"]
        )
        fig_app.update_yaxes(title_text="Indicator")
        st.plotly_chart(style_chart(fig_app), use_container_width=True)

    # Downloads
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
# COHORT 5 — INDIVIDUAL ONLY (NO CHARTS / NO BAR GRAPHS)
# ============================================================
elif is_cohort5:
    df = sheets["Sheet1"].copy()

    # Find the fellow name column robustly
    # Prefer "Full Name" if it exists, else fall back to "Unnamed: 0"
    name_col = "Full Name" if "Full Name" in df.columns else ("Unnamed: 0" if "Unnamed: 0" in df.columns else None)
    if name_col is None:
        st.error("Cohort 5 file: could not find a name column (expected 'Full Name' or 'Unnamed: 0').")
        st.stop()

    df["Fellow Name"] = df[name_col].astype(str).str.strip()

    # Sidebar fellow selector
    fellows = sorted(df["Fellow Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.subheader(selected)

    row_df = df[df["Fellow Name"] == selected].copy()
    if row_df.empty:
        st.error("Selected fellow not found in Cohort 5 data.")
        st.stop()
    row = row_df.iloc[0].to_dict()

    # Helpful numeric parsing (quietly; if column missing, ignore)
    def to_num(x):
        try:
            return float(x)
        except Exception:
            return None

    # ---- Top “at-a-glance” metrics (only show if present) ----
    st.subheader("At-a-Glance")

    # Candidate numeric columns (based on your last file + future-proofing)
    metric_candidates = [
        "Age",
        "Undergraduate GPA", "UG GPA",
        "Graduate GPA",
        "Previous Official LSAT", "Official LSAT",
        "Diagnostic LSAT", "Diagnostic",
    ]

    # Build a list of metrics that actually exist
    present_metrics = []
    for c in metric_candidates:
        if c in row and pd.notna(row.get(c)) and str(row.get(c)).strip() != "":
            present_metrics.append(c)

    if present_metrics:
        cols = st.columns(min(5, len(present_metrics)))
        for i, c in enumerate(present_metrics[:5]):
            val = row.get(c)
            num = to_num(val)
            if num is not None and c.lower().endswith("gpa"):
                cols[i].metric(c, f"{num:.2f}")
            elif num is not None and ("lsat" in c.lower() or c.lower() == "age"):
                cols[i].metric(c, f"{int(num)}")
            else:
                cols[i].metric(c, str(val))
    else:
        st.write("No numeric snapshot fields found in this Cohort 5 workbook.")

    # ---- Full profile: show ALL columns (no charts, no tables) ----
    st.subheader("Profile (All Fields)")

    # Exclude internal name columns from repeated display
    exclude = {name_col, "Fellow Name"}
    fields = [c for c in df.columns if c not in exclude]

    # Print as clean labeled lines (straightforward, not a dataframe/table)
    for c in fields:
        v = row.get(c)
        if pd.isna(v) or str(v).strip() == "":
            display_val = "(missing)"
        else:
            display_val = str(v).strip()
        st.write(f"**{c}:** {display_val}")

    # Downloads
    st.download_button(
        "Download Fellow Row (CSV)",
        convert_df(df[df["Fellow Name"] == selected]),
        f"{selected}_cohort5.csv",
        "text/csv"
    )
    st.download_button(
        "Download Full Cohort 5 Data (CSV)",
        convert_df(df),
        "cohort5_full.csv",
        "text/csv"
    )

else:
    st.error(
        "This workbook doesn’t match Cohort 4 (Attendance/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1) schemas."
    )
    st.stop()
