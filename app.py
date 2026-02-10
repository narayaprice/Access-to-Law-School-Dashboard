import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# YALE-STYLE THEME (components.html prevents CSS from printing as text)
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
    margin: 8px 0 12px 0;
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
components.html(CSS, height=0, scrolling=False)

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

def normalize_value(v):
    """Normalize display values for Cohort 5: N/A -> Not Applicable; blanks -> (missing)."""
    if pd.isna(v):
        return "(missing)"
    s = str(v).strip()
    if s == "":
        return "(missing)"
    if s.upper() in {"N/A", "NA", "N.A.", "NOT APPLICABLE"}:
        return "Not Applicable"
    return s

# ============================================================
# COHORT FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(
    '<div class="sidebar-title">Access to Law School Cohort Data Dashboard</div>',
    unsafe_allow_html=True
)

# Sidebar image (local file in repo)
st.sidebar.image("sidebar_photo.jpg", use_container_width=True)

# Cohort selector (defined ONCE)
selected_cohort = st.sidebar.selectbox(
    "Select Cohort",
    list(COHORT_FILES.keys()),
    index=0
)

# Load selected cohort workbook
workbook_path = COHORT_FILES[selected_cohort]
try:
    sheets = load_workbook(workbook_path)
except FileNotFoundError:
    st.error(
        f"Could not find '{workbook_path}' next to app.py. "
        "Add it to the repo folder (same level as app.py) and redeploy."
    )
    st.stop()

# Main page title
st.title(selected_cohort)

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
    df_attendance["Full Name"] = (
        df_attendance["First"].astype(str).str.strip() + " " + df_attendance["Last"].astype(str).str.strip()
    )
    df_scores["Full Name"] = (
        df_scores["Fellow First"].astype(str).str.strip() + " " + df_scores["Fellow Last"].astype(str).str.strip()
    )
    df_app["Full Name"] = (
        df_app["First"].astype(str).str.strip() + " " + df_app["Last"].astype(str).str.strip()
    )

    fellows = sorted(df_scores["Full Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.subheader(selected)

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
            scores_long,
            x="Test",
            y="Score",
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
    st.subheader("Attendance Overview")
    if att_row.empty:
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

    # -------------------- Application Status (kept as-is) --------------------
    st.subheader("Application Status Overview")
    app_row = df_app[df_app["Full Name"] == selected].copy()
    if app_row.empty:
        st.info("No application status data available for this fellow.")
    else:
        # Straightforward display (no table): field-by-field
        data = app_row.drop(columns=["First", "Last"], errors="ignore").iloc[0].to_dict()
        for k, v in data.items():
            if k == "Full Name":
                continue
            val = "(missing)" if pd.isna(v) or str(v).strip() == "" else str(v).strip()
            st.write(f"**{k}:** {val}")

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
# COHORT 5 — INDIVIDUAL ONLY (NO CHARTS / NO TABLES)
# Uses columns: Name, First-Gen, Age, UG GPA, UG Institution, Grad GPA, Grad Institution,
# Previous Official LSAT, Diagnostic LSAT
# N/A -> Not Applicable
# ============================================================
elif is_cohort5:
    df = sheets["Sheet1"].copy()
    df.columns = df.columns.astype(str).str.strip()

    # Name column in your file appears as "Unnamed: 0" (per your upload),
    # but support "Name" too in case you renamed it.
    name_col = None
    for c in ["Name", "Full Name", "Unnamed: 0"]:
        if c in df.columns:
            name_col = c
            break
    if name_col is None:
        st.error("Cohort 5 file: could not find a name column (expected 'Name' or 'Unnamed: 0').")
        st.stop()

    df["Fellow Name"] = df[name_col].astype(str).str.strip()

    fellows = sorted(df["Fellow Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.subheader(selected)

    row_df = df[df["Fellow Name"] == selected].copy()
    if row_df.empty:
        st.error("Selected fellow not found in Cohort 5 data.")
        st.stop()
    row = row_df.iloc[0].to_dict()

    # Preferred ordering / labels (matches what you described)
    # NOTE: Your sheet uses "Undergraduate Instituion" (typo) — keep both possibilities.
    field_map = [
        ("First-Gen", "First-Gen"),
        ("Age", "Age"),
        ("Undergraduate GPA", "Undergraduate GPA"),
        ("Undergraduate Instituion", "Undergraduate Institution"),
        ("Undergraduate Institution", "Undergraduate Institution"),
        ("Graduate GPA", "Graduate GPA"),
        ("Graduate Institution", "Graduate Institution"),
        ("Previous Official LSAT", "Previous Official LSAT"),
        ("Diagnostic LSAT", "Diagnostic LSAT"),
    ]

    st.subheader("Biographical Snapshot")

    shown = set()
    for raw_col, label in field_map:
        if raw_col in row and raw_col not in shown:
            st.write(f"**{label}:** {normalize_value(row.get(raw_col))}")
            shown.add(raw_col)

    # If there are extra columns beyond the expected ones, show them too (still no tables).
    extras = [c for c in df.columns if c not in {name_col, "Fellow Name"} and c not in shown]
    if extras:
        st.subheader("Additional Fields")
        for c in extras:
            st.write(f"**{c}:** {normalize_value(row.get(c))}")

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
        "This workbook doesn’t match Cohort 4 (Attendance_New/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1) schemas."
    )
    st.stop()
