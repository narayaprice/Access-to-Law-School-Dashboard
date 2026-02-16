import re
import pandas as pd
import streamlit as st
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# THEME CONSTANTS
# ============================================================
NAVY = "#00356b"   # Yale navy
NAVY_2 = "#286dc0"
WHITE = "#ffffff"
LIGHT_BG = "#f7f8fb"
GRID = "rgba(0,0,0,0.10)"


# ============================================================
# GLOBAL CSS (Main = white, Sidebar = navy)
# Use @import instead of <link> so Streamlit doesn't render it as text
# ============================================================
CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@400;600&display=swap');

:root {{
  --navy: {NAVY};
  --navy2: {NAVY_2};
  --white: {WHITE};
  --lightbg: {LIGHT_BG};
}}

html, body, [data-testid="stAppViewContainer"] {{
  background: var(--lightbg) !important;
}}

[data-testid="stAppViewContainer"] .main {{
  background: var(--white) !important;
  padding-top: 1rem;
}}

[data-testid="stAppViewContainer"] .main,
[data-testid="stAppViewContainer"] .main * {{
  color: var(--navy) !important;
  font-family: "Libre Baskerville", Georgia, serif !important;
}}

section[data-testid="stSidebar"] {{
  background: var(--navy) !important;
}}

section[data-testid="stSidebar"] * {{
  color: var(--white) !important;
  font-family: "Source Sans 3", Arial, sans-serif !important;
}}

.sidebar-title {{
  color: var(--white) !important;
  font-family: "Source Sans 3", Arial, sans-serif !important;
  font-weight: 700;
  font-size: 20px;
  line-height: 1.2;
  margin: 10px 0 12px 0;
}}

.stButton > button, .stDownloadButton > button {{
  background: var(--navy) !important;
  color: var(--white) !important;
  border: 1px solid var(--navy) !important;
  font-weight: 700 !important;
}}

.stButton > button:hover, .stDownloadButton > button:hover {{
  background: rgba(0,53,107,0.90) !important;
  border-color: rgba(0,53,107,0.90) !important;
}}

div[data-baseweb="select"] > div {{
  background: rgba(255,255,255,0.10) !important;
  border: 1px solid rgba(255,255,255,0.35) !important;
}}

div[data-baseweb="select"] * {{
  color: var(--white) !important;
}}

[data-testid="stHeader"] {{
  background: transparent !important;
}}

</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def convert_df(df: pd.DataFrame) -> bytes:
  return df.to_csv(index=False).encode("utf-8")


@st.cache_data
def load_workbook(path: str) -> dict:
  sheets = pd.read_excel(path, sheet_name=None)
  for df in sheets.values():
    df.columns = df.columns.astype(str).str.strip()
  return sheets


def normalize_value(v):
  """Cohort 5 bio: N/A -> Not Applicable; blanks -> (missing)."""
  if pd.isna(v):
    return "(missing)"
  s = str(v).strip()
  if s == "":
    return "(missing)"
  if s.upper() in {"N/A", "NA", "N.A.", "NOT APPLICABLE"}:
    return "Not Applicable"
  return s


def normalize_colname(c: str) -> str:
  c = str(c).strip()
  c = re.sub(r"\s+", " ", c)
  return c


def normalize_yes_no(x):
  """Map common values to Yes/No; otherwise None."""
  if pd.isna(x):
    return None
  s = str(x).strip().lower()
  if s in {"yes", "y", "attended", "present", "1", "true"}:
    return "Yes"
  if s in {"no", "n", "missed", "absent", "0", "false"}:
    return "No"
  return None


def style_plotly(fig):
  """
  Plotly 6-safe styling:
  - NO titlefont anywhere
  - White plot background, navy text
  - Visible axes + light grid
  """
  fig.update_layout(
    paper_bgcolor=WHITE,
    plot_bgcolor=WHITE,
    font=dict(color=NAVY, family="Libre Baskerville, Georgia, serif"),
    title=dict(font=dict(color=NAVY)),
    legend=dict(font=dict(color=NAVY), title_font=dict(color=NAVY)),
    margin=dict(l=70, r=30, t=80, b=70),
  )

  # Bar traces: navy fill
  fig.update_traces(marker_color=NAVY, selector=dict(type="bar"))

  # Scatter traces: navy line + markers (covers px.line etc.)
  fig.update_traces(line=dict(color=NAVY), selector=dict(type="scatter"))
  fig.update_traces(marker=dict(color=NAVY), selector=dict(type="scatter"))

  # Axes styling (Plotly 6 uses axis.title.font)
  fig.update_xaxes(
    showline=True,
    linecolor=NAVY,
    linewidth=1,
    ticks="outside",
    tickcolor=NAVY,
    tickfont=dict(color=NAVY),
    showticklabels=True,
    showgrid=True,
    gridcolor=GRID,
    zeroline=True,
    zerolinecolor=GRID,
    title=dict(font=dict(color=NAVY)),  # Plotly 6 replacement
  )
  fig.update_yaxes(
    showline=True,
    linecolor=NAVY,
    linewidth=1,
    ticks="outside",
    tickcolor=NAVY,
    tickfont=dict(color=NAVY),
    showticklabels=True,
    showgrid=True,
    gridcolor=GRID,
    zeroline=True,
    zerolinecolor=GRID,
    title=dict(font=dict(color=NAVY)),  # Plotly 6 replacement
  )

  return fig


@st.cache_data
def load_weekly_updates(path: str) -> pd.DataFrame:
  df = pd.read_excel(path)
  df.columns = [normalize_colname(c) for c in df.columns]
  return df


def attendance_bar_charts(df_long: pd.DataFrame, title_prefix: str):
  """
  df_long columns: Program, Response(Yes/No), Count
  Creates two bar charts: Yes (attended) and No (missed)
  """
  yes_df = df_long[df_long["Response"] == "Yes"].copy()
  no_df = df_long[df_long["Response"] == "No"].copy()

  st.subheader(f"{title_prefix}: Attended (Yes)")
  if yes_df.empty:
    st.info("No Yes/attended responses found yet.")
  else:
    fig_yes = px.bar(
      yes_df,
      x="Program",
      y="Count",
      title=f"{title_prefix} — Attended",
      labels={"Program": "Program Attended", "Count": "Count"},
    )
    fig_yes.update_xaxes(title_text="Program Attended", tickangle=-25)
    fig_yes.update_yaxes(title_text="Count")
    st.plotly_chart(style_plotly(fig_yes), use_container_width=True)

  st.subheader(f"{title_prefix}: Missed (No)")
  if no_df.empty:
    st.info("No No/missed responses found yet.")
  else:
    fig_no = px.bar(
      no_df,
      x="Program",
      y="Count",
      title=f"{title_prefix} — Missed",
      labels={"Program": "Program Missed", "Count": "Count"},
    )
    fig_no.update_xaxes(title_text="Program Missed", tickangle=-25)
    fig_no.update_yaxes(title_text="Count")
    st.plotly_chart(style_plotly(fig_no), use_container_width=True)


# ============================================================
# FILES
# ============================================================
COHORT_FILES = {
  "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
  "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}
WEEKLY_UPDATES_FILE = "Cohort 5 - Weekly Fellow Updates - SP26 (Responses).xlsx"
SIDEBAR_PHOTO = "sidebar_photo.jpg"


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(
  '<div class="sidebar-title">Access to Law School Cohort Data Dashboard</div>',
  unsafe_allow_html=True,
)

try:
  st.sidebar.image(SIDEBAR_PHOTO, use_container_width=True)
except Exception:
  st.sidebar.caption("(Sidebar photo not found — add sidebar_photo.jpg next to app.py)")

selected_cohort = st.sidebar.selectbox("Select Cohort", list(COHORT_FILES.keys()), index=0)

# ============================================================
# LOAD COHORT WORKBOOK
# ============================================================
workbook_path = COHORT_FILES[selected_cohort]
try:
  sheets = load_workbook(workbook_path)
except FileNotFoundError:
  st.error(
    f"Could not find '{workbook_path}' next to app.py. "
    "Add it to the repo folder (same level as app.py) and redeploy."
  )
  st.stop()

st.title(selected_cohort)

# ============================================================
# SCHEMA DETECTION
# ============================================================
is_cohort4 = ("Attendance_New" in sheets and "Test Scores" in sheets and "Application Status" in sheets)
is_cohort5 = ("Sheet1" in sheets and not is_cohort4)

# ============================================================
# COHORT 4 — INDIVIDUAL ONLY
# ============================================================
if is_cohort4:
  df_attendance = sheets["Attendance_New"].copy()
  df_scores = sheets["Test Scores"].copy()
  df_app = sheets["Application Status"].copy()

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

  # ---------- LSAT Scores ----------
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
    value_name="Score",
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
    )
    fig_lsat.update_xaxes(title_text="Test")
    fig_lsat.update_yaxes(title_text="Score")
    st.plotly_chart(style_plotly(fig_lsat), use_container_width=True)

  # ---------- Attendance ----------
  fall_col = "Fall Small Group % Attendance"
  spring_col = "Spring Small Group % Attendance"
  sa_col = "Saturday Academy % Attendance"

  required_att_cols = [fall_col, spring_col, sa_col]
  missing = [c for c in required_att_cols if c not in df_attendance.columns]
  if missing:
    st.error(f"Missing attendance columns in Cohort 4 workbook: {missing}")
    st.stop()

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
      value_name="Attendance",
    )
    att_long["Attendance"] = pd.to_numeric(att_long["Attendance"], errors="coerce")
    att_long["Attendance Type"] = att_long["Attendance Type"].map(
      {fall_col: "FSG", spring_col: "SSG", sa_col: "SA"}
    )

    fig_att = px.bar(
      att_long,
      x="Attendance Type",
      y="Attendance",
      title=f"Attendance for {selected}",
      labels={"Attendance Type": "Program", "Attendance": "Attendance %"},
    )
    fig_att.update_xaxes(title_text="Program")
    fig_att.update_yaxes(title_text="Attendance %")
    st.plotly_chart(style_plotly(fig_att), use_container_width=True)

  # ---------- Application Status ----------
  st.subheader("Application Status Overview")
  app_row = df_app[df_app["Full Name"] == selected].copy()
  if app_row.empty:
    st.info("No application status data available for this fellow.")
  else:
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
    "text/csv",
  )
  st.download_button(
    "Download Fellow Scores (CSV)",
    convert_df(df_scores[df_scores["Full Name"] == selected]),
    f"{selected}_scores.csv",
    "text/csv",
  )
  st.download_button(
    "Download Fellow Application Status (CSV)",
    convert_df(df_app[df_app["Full Name"] == selected]),
    f"{selected}_application_status.csv",
    "text/csv",
  )

# ============================================================
# COHORT 5 — BIO + WEEKLY UPDATES
# ============================================================
elif is_cohort5:
  df = sheets["Sheet1"].copy()
  df.columns = df.columns.astype(str).str.strip()

  name_col = None
  for c in ["Name", "Full Name", "Unnamed: 0"]:
    if c in df.columns:
      name_col = c
      break
  if name_col is None:
    st.error("Cohort 5 bio file: could not find a name column (expected 'Name' or 'Unnamed: 0').")
    st.stop()

  df["Fellow Name"] = df[name_col].astype(str).str.strip()
  fellows = sorted(df["Fellow Name"].dropna().unique())
  selected = st.sidebar.selectbox("Select Fellow", fellows)

  st.header("Individual Fellow Report")
  st.subheader(selected)

  # ---------- Bio Snapshot ----------
  row_df = df[df["Fellow Name"] == selected].copy()
  if row_df.empty:
    st.error("Selected fellow not found in Cohort 5 bio data.")
    st.stop()
  row = row_df.iloc[0].to_dict()

  st.subheader("Biographical Snapshot")

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

  shown = set()
  for raw_col, label in field_map:
    if raw_col in row and raw_col not in shown:
      st.write(f"**{label}:** {normalize_value(row.get(raw_col))}")
      shown.add(raw_col)

  extras = [c for c in df.columns if c not in {name_col, "Fellow Name"} and c not in shown]
  if extras:
    st.subheader("Additional Fields")
    for c in extras:
      st.write(f"**{c}:** {normalize_value(row.get(c))}")

  # ---------- Weekly Coach Updates ----------
  st.markdown("---")
  st.header("Weekly Coach Updates (Cohort 5)")

  try:
    weekly = load_weekly_updates(WEEKLY_UPDATES_FILE)
  except FileNotFoundError:
    st.error(
      f"Could not find '{WEEKLY_UPDATES_FILE}' next to app.py. "
      "Add it to the repo folder (same level as app.py) and redeploy."
    )
    st.stop()

  if "Fellow" not in weekly.columns:
    st.error("Weekly updates file is missing a 'Fellow' column.")
    st.stop()
  if "Week" not in weekly.columns:
    st.error("Weekly updates file is missing a 'Week' column.")
    st.stop()

  weekly["Fellow"] = weekly["Fellow"].astype(str).str.strip()
  weekly["Week"] = weekly["Week"].astype(str).str.strip()

  weekly_fellow = weekly[weekly["Fellow"] == selected].copy()

  # --- Coach Engagement ---
  engagement_cols = [c for c in weekly.columns if "Coach Engagement" in c]
  if engagement_cols:
    eng_melt = weekly[["Fellow", "Week"] + engagement_cols].copy()
    eng_melt = eng_melt.melt(id_vars=["Fellow", "Week"], var_name="Field", value_name="Text")
    eng_melt["Text"] = eng_melt["Text"].astype(str).str.strip()
    eng_melt = eng_melt[
      eng_melt["Text"].notna()
      & (eng_melt["Text"] != "")
      & (eng_melt["Text"].str.lower() != "nan")
    ]

    st.subheader(f"Coach Engagement Notes (Selected Fellow: {selected})")
    if weekly_fellow.empty:
      st.info("No weekly rows found yet for this fellow.")
    else:
      wf = weekly_fellow[["Week"] + engagement_cols].copy()
      wf["Week"] = wf["Week"].astype(str).str.strip()

      for wk in sorted(wf["Week"].dropna().unique()):
        wk_rows = wf[wf["Week"] == wk].copy()
        with st.expander(f"Week: {wk}", expanded=False):
          any_text = False
          for _, r in wk_rows.iterrows():
            for c in engagement_cols:
              txt = r.get(c)
              txt_norm = "" if pd.isna(txt) else str(txt).strip()
              if txt_norm and txt_norm.lower() != "nan":
                any_text = True
                st.write(f"**{c}:** {txt_norm}")
          if not any_text:
            st.write("(No Coach Engagement text entered for this week yet.)")
  else:
    st.info("No 'Coach Engagement' columns found yet in the weekly updates file.")

  # Downloads
  st.markdown("---")
  st.download_button(
    "Download Selected Fellow Bio Row (CSV)",
    convert_df(df[df["Fellow Name"] == selected]),
    f"{selected}_cohort5_bio.csv",
    "text/csv",
  )
  st.download_button(
    "Download Weekly Updates (CSV)",
    convert_df(weekly),
    "cohort5_weekly_updates.csv",
    "text/csv",
  )

else:
  st.error(
    "This workbook doesn't match Cohort 4 (Attendance_New/Test Scores/Application Status) "
    "or Cohort 5 (Sheet1) schemas."
  )
  st.stop()
