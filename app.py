import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
# COHORT FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
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

workbook_path = COHORT_FILES[selected_cohort]
try:
    sheets = load_workbook(workbook_path)
except FileNotFoundError:
    st.error(
        f"Could not find '{workbook_path}' in the repo. "
        "Add it to the same folder as app.py (or update COHORT_FILES paths) and redeploy."
    )
    st.stop()

st.title(f"{selected_cohort}")

# ============================================================
# SCHEMA DETECTION
# ============================================================
is_cohort4 = ("Attendance_New" in sheets and "Test Scores" in sheets and "Application Status" in sheets)
is_cohort5 = ("Sheet1" in sheets and not is_cohort4)

# ============================================================
# COHORT 4 — INDIVIDUAL FELLOW REPORT ONLY
# ============================================================
if is_cohort4:
    df_attendance = sheets["Attendance_New"].copy()
    df_scores = sheets["Test Scores"].copy()
    df_app = sheets["Application Status"].copy()

    # Full names
    df_attendance["Full Name"] = df_attendance["First"].astype(str).str.strip() + " " + df_attendance["Last"].astype(str).str.strip()
    df_scores["Full Name"] = df_scores["Fellow First"].astype(str).str.strip() + " " + df_scores["Fellow Last"].astype(str).str.strip()
    df_app["Full Name"] = df_app["First"].astype(str).str.strip() + " " + df_app["Last"].astype(str).str.strip()

    # Attendance columns
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

    # LSAT columns
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

    # Sidebar fellow picker
    fellows = sorted(df_scores["Full Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.markdown("**Legend:** FSG = Fall Small Group, SSG = Spring Small Group, SA = Saturday Academy")

    # LSAT trend
    st.subheader("LSAT Score Trend")
    indiv_scores = scores_long[scores_long["Full Name"] == selected]
    fig_indiv = px.line(
        indiv_scores, x="Test", y="Score", markers=True,
        title=f"LSAT Scores for {selected}",
        color_discrete_sequence=["#00356b"]
    )
    st.plotly_chart(style_chart(fig_indiv), use_container_width=True)

    # Attendance overview
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

    # Application Status chart
    render_application_status_chart(selected)

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
# COHORT 5 — STRAIGHTFORWARD PROFILE VIEW (NO BAR GRAPHS)
# ============================================================
elif is_cohort5:
    df = sheets["Sheet1"].copy()

    # Expected columns based on your uploaded workbook
    # ['Unnamed: 0', 'First-Gen', 'Age', 'Undergraduate GPA',
    #  'Undergraduate Instituion', 'Graduate GPA', 'Graduate Institution',
    #  'Previous Official LSAT', 'Diagnostic LSAT']
    name_col = "Unnamed: 0"
    if name_col not in df.columns:
        st.error("Cohort 5 file: expected name column 'Unnamed: 0' not found.")
        st.stop()

    df["Full Name"] = df[name_col].astype(str).str.strip()

    # Numeric conversions
    numeric_cols = ["Age", "Undergraduate GPA", "Graduate GPA", "Previous Official LSAT", "Diagnostic LSAT"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    fellows = sorted(df["Full Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")

    row = df[df["Full Name"] == selected]
    if row.empty:
        st.error("Selected fellow not found in Cohort 5 data.")
        st.stop()

    row = row.iloc[0]

    # Top metrics row (straightforward)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Age", "" if pd.isna(row.get("Age")) else f"{int(row.get('Age'))}")
    c2.metric("Undergraduate GPA", "" if pd.isna(row.get("Undergraduate GPA")) else f"{row.get('Undergraduate GPA'):.2f}")
    c3.metric("Graduate GPA", "" if pd.isna(row.get("Graduate GPA")) else f"{row.get('Graduate GPA'):.2f}")
    c4.metric("Previous Official LSAT", "" if pd.isna(row.get("Previous Official LSAT")) else f"{int(row.get('Previous Official LSAT'))}")
    c5.metric("Diagnostic LSAT", "" if pd.isna(row.get("Diagnostic LSAT")) else f"{int(row.get('Diagnostic LSAT'))}")

    # Clean “First-Gen” display
    st.subheader("Background")
    first_gen = row.get("First-Gen")
    if pd.isna(first_gen) or str(first_gen).strip() == "":
        st.write("**First-Gen:** (missing)")
    else:
        st.write(f"**First-Gen:** {str(first_gen).strip()}")

    # Institutions (plain text)
    ug_inst = row.get("Undergraduate Instituion")
    grad_inst = row.get("Graduate Institution")

    st.subheader("Education")
    st.write(f"**Undergraduate Institution:** {'' if pd.isna(ug_inst) else str(ug_inst).strip()}")
    st.write(f"**Graduate Institution:** {'' if pd.isna(grad_inst) else str(grad_inst).strip()}")

    # Downloads
    st.download_button(
        "Download Cohort 5 Fellow Row (CSV)",
        convert_df(df[df["Full Name"] == selected]),
        f"{selected}_cohort5.csv",
        "text/csv"
    )
    st.download_button(
        "Download Cohort 5 Full Data (CSV)",
        convert_df(df),
        "cohort5_full.csv",
        "text/csv"
    )

else:
    st.error(
        "This workbook doesn’t match Cohort 4 (Attendance/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1 updated stats) schemas."
    )
    st.stop()
