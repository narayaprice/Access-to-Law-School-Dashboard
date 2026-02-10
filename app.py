import re
import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# NAVY + WHITE THEME (force entire app background)
# ============================================================
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root{
    --navy: #00356b;
    --navy2: #286dc0;
    --white: #ffffff;
    --muted: rgba(255,255,255,0.75);
    --grid: rgba(255,255,255,0.12);
  }

  html, body, [data-testid="stApp"]{
    background: var(--navy) !important;
  }

  /* Sidebar */
  [data-testid="stSidebar"]{
    background-color: var(--navy) !important;
    border-right: 1px solid var(--grid) !important;
  }
  [data-testid="stSidebar"] *{
    color: var(--white) !important;
    font-family: "Source Sans 3", Arial, sans-serif !important;
  }

  .sidebar-title{
    color: var(--white) !important;
    font-family: "Source Sans 3", Arial, sans-serif !important;
    font-weight: 700;
    font-size: 20px;
    line-height: 1.2;
    margin: 8px 0 12px 0;
  }

  /* Main container */
  [data-testid="stAppViewContainer"]{
    background: var(--navy) !important;
  }
  [data-testid="stAppViewContainer"] .main{
    background: var(--navy) !important;
  }
  [data-testid="stAppViewContainer"] .main,
  [data-testid="stAppViewContainer"] .main *{
    color: var(--white) !important;
    font-family: "Libre Baskerville", Georgia, serif !important;
  }

  /* Body text / labels use sans */
  [data-testid="stAppViewContainer"] .main label,
  [data-testid="stAppViewContainer"] .main .stMarkdown p,
  [data-testid="stAppViewContainer"] .main .stMarkdown li,
  [data-testid="stAppViewContainer"] .main .stCaption,
  [data-testid="stAppViewContainer"] .main .stText,
  [data-testid="stAppViewContainer"] .main .stAlert{
    font-family: "Source Sans 3", Arial, sans-serif !important;
    color: var(--white) !important;
  }

  /* Metric styling */
  [data-testid="stMetricValue"], [data-testid="stMetricLabel"]{
    color: var(--white) !important;
  }

  /* Expanders */
  [data-testid="stExpander"]{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--grid) !important;
    border-radius: 10px !important;
  }

  /* Inputs */
  .stSelectbox, .stTextInput, .stMultiSelect{
    color: var(--white) !important;
  }

  /* Buttons */
  .stButton>button, .stDownloadButton>button{
    background: var(--white) !important;
    color: var(--navy) !important;
    border: 1px solid var(--white) !important;
    font-family: "Source Sans 3", Arial, sans-serif !important;
    font-weight: 600 !important;
  }
  .stButton>button:hover, .stDownloadButton>button:hover{
    background: rgba(255,255,255,0.85) !important;
    border-color: rgba(255,255,255,0.85) !important;
  }

  /* Horizontal rule */
  hr { border-top: 1px solid var(--grid) !important; }
</style>
"""
components.html(CSS, height=0, scrolling=False)

# ============================================================
# FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}

# Weekly coach form export (Cohort 5)
COHORT5_WEEKLY_FILE = "Cohort 5 - Weekly Fellow Updates - SP26 (Responses).xlsx"

# ============================================================
# HELPERS
# ============================================================
NAVY = "#00356b"
WHITE = "#ffffff"
GRID = "rgba(255,255,255,0.12)"
YALE_BLUES_ON_NAVY = ["#7aa6de", "#b9d3f2", "#286dc0", "#9cc3f5"]  # readable on navy

def style_chart_dark(fig):
    """Make Plotly charts readable on a navy background."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE, family="Source Sans 3, Arial, sans-serif"),
        title=dict(font=dict(color=WHITE, family="Libre Baskerville, Georgia, serif")),
        legend=dict(font=dict(color=WHITE), title_font=dict(color=WHITE)),
        margin=dict(l=40, r=20, t=60, b=40),
        colorway=YALE_BLUES_ON_NAVY,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID, tickfont=dict(color=WHITE), title_font=dict(color=WHITE))
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID, tickfont=dict(color=WHITE), title_font=dict(color=WHITE))
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
    """For display: N/A -> Not Applicable; blanks/NaN -> (missing)."""
    if pd.isna(v):
        return "(missing)"
    s = str(v).strip()
    if s == "":
        return "(missing)"
    if s.upper() in {"N/A", "NA", "N.A.", "NOT APPLICABLE"}:
        return "Not Applicable"
    return s

def count_yes_no(series: pd.Series):
    """Count Yes/No-like responses in a column."""
    s = series.astype(str).str.strip().str.lower()
    yes = s.isin({"yes", "y", "true", "1"}).sum()
    no = s.isin({"no", "n", "false", "0"}).sum()
    return int(yes), int(no)

def week_sort_key(colname: str):
    """
    Sort 'Week of M/D' columns chronologically as best as possible.
    Falls back to original if parsing fails.
    """
    m = re.search(r"week of\s*(\d{1,2})/(\d{1,2})", colname.lower())
    if not m:
        return (999, 999)
    mm = int(m.group(1))
    dd = int(m.group(2))
    return (mm, dd)

# ============================================================
# SIDEBAR
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

st.title(selected_cohort)

# ============================================================
# SCHEMA DETECTION
# ============================================================
is_cohort4 = ("Attendance_New" in sheets and "Test Scores" in sheets and "Application Status" in sheets)
is_cohort5 = ("Sheet1" in sheets and not is_cohort4)

# ============================================================
# COHORT 4
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

    # LSAT Scores
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
        )
        st.plotly_chart(style_chart_dark(fig_lsat), use_container_width=True)

    # Attendance
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
        )
        fig_att.update_xaxes(title_text="Attendance Type")
        fig_att.update_yaxes(title_text="Attendance Percent out of 100%")
        st.plotly_chart(style_chart_dark(fig_att), use_container_width=True)

    # Application Status (field-by-field)
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
# COHORT 5
# ============================================================
elif is_cohort5:
    df_bio = sheets["Sheet1"].copy()
    df_bio.columns = df_bio.columns.astype(str).str.strip()

    # Name column (support common variants)
    name_col = None
    for c in ["Name", "Full Name", "Unnamed: 0"]:
        if c in df_bio.columns:
            name_col = c
            break
    if name_col is None:
        st.error("Cohort 5 bio file: could not find a name column (expected 'Name' or 'Unnamed: 0').")
        st.stop()

    df_bio["Fellow Name"] = df_bio[name_col].astype(str).str.strip()
    fellows = sorted(df_bio["Fellow Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    # Tabs: Bio + Weekly Updates
    tab_bio, tab_weekly = st.tabs(["Biographical Snapshot", "Weekly Coach Updates"])

    # ---------------- BIO TAB ----------------
    with tab_bio:
        st.header("Individual Fellow Report")
        st.subheader(selected)

        row_df = df_bio[df_bio["Fellow Name"] == selected].copy()
        if row_df.empty:
            st.error("Selected fellow not found in Cohort 5 biographical data.")
            st.stop()
        row = row_df.iloc[0].to_dict()

        # Your requested fields (with typo-tolerance)
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

        extras = [c for c in df_bio.columns if c not in {name_col, "Fellow Name"} and c not in shown]
        if extras:
            st.divider()
            st.subheader("Additional Fields")
            for c in extras:
                st.write(f"**{c}:** {normalize_value(row.get(c))}")

        st.divider()
        st.download_button(
            "Download Fellow Bio Row (CSV)",
            convert_df(df_bio[df_bio["Fellow Name"] == selected]),
            f"{selected}_cohort5_bio.csv",
            "text/csv"
        )
        st.download_button(
            "Download Full Cohort 5 Bio Data (CSV)",
            convert_df(df_bio),
            "cohort5_bio_full.csv",
            "text/csv"
        )

    # ---------------- WEEKLY TAB ----------------
    with tab_weekly:
        st.header("Weekly Coach Updates (Cohort 5)")
        st.caption("Source: Google Form export workbook in the repo folder.")

        try:
            weekly_sheets = load_workbook(COHORT5_WEEKLY_FILE)
        except FileNotFoundError:
            st.error(
                f"Could not find '{COHORT5_WEEKLY_FILE}' next to app.py. "
                "Add it to the repo folder (same level as app.py) and redeploy."
            )
            st.stop()

        # Most Google Form exports use "Form Responses 1"
        if "Form Responses 1" in weekly_sheets:
            df_weekly = weekly_sheets["Form Responses 1"].copy()
        else:
            # fall back to the first sheet
            first_sheet_name = list(weekly_sheets.keys())[0]
            df_weekly = weekly_sheets[first_sheet_name].copy()

        df_weekly.columns = df_weekly.columns.astype(str).str.strip()

        # Try to identify fellow name column in weekly export
        weekly_name_col = None
        for c in ["Name", "Fellow Name", "Student Name", "Fellow", "Full Name"]:
            if c in df_weekly.columns:
                weekly_name_col = c
                break

        if weekly_name_col is None:
            # if we can't detect, still allow aggregate view
            st.info("Could not detect a fellow name column in the weekly export. Showing aggregate charts only.")
            df_filtered = df_weekly
        else:
            df_weekly["Fellow Name"] = df_weekly[weekly_name_col].astype(str).str.strip()
            # filter to selected fellow when possible
            df_filtered = df_weekly[df_weekly["Fellow Name"] == selected].copy()
            if df_filtered.empty:
                st.info("No weekly entries found for this fellow yet. Aggregate charts below reflect all responses.")
                df_filtered = df_weekly

        # Detect Attendance columns
        sa_cols = [c for c in df_weekly.columns if "Saturday Academy" in c]
        ryan_cols = [c for c in df_weekly.columns if "1-on-1 with Ryan" in c or "1-on-1 w/ Ryan" in c or "1 on 1 with Ryan" in c]

        # Detect Coach Engagement columns (they are week-by-week in your sheet)
        ce_cols = [c for c in df_weekly.columns if "Coach Engagement" in c]

        # -------------------- Saturday Academy charts --------------------
        if sa_cols:
            st.subheader("Saturday Academy Attendance (Counts)")

            attended = []
            missed = []

            for c in sa_cols:
                yes, no = count_yes_no(df_weekly[c])
                attended.append({"Program": c.replace(" - Saturday Academy Attendance", "").strip(), "Count": yes})
                missed.append({"Program": c.replace(" - Saturday Academy Attendance", "").strip(), "Count": no})

            df_attended = pd.DataFrame(attended).sort_values("Program")
            df_missed = pd.DataFrame(missed).sort_values("Program")

            c1, c2 = st.columns(2)

            fig_yes = px.bar(df_attended, x="Program", y="Count", title="Attended (Yes)")
            fig_yes.update_xaxes(title_text="Programs Attended")
            fig_yes.update_yaxes(title_text="Count")
            c1.plotly_chart(style_chart_dark(fig_yes), use_container_width=True)

            fig_no = px.bar(df_missed, x="Program", y="Count", title="Missed (No)")
            fig_no.update_xaxes(title_text="Programs Missed")
            fig_no.update_yaxes(title_text="Count")
            c2.plotly_chart(style_chart_dark(fig_no), use_container_width=True)
        else:
            st.info("No 'Saturday Academy Attendance' columns detected yet in the weekly export.")

        st.divider()

        # -------------------- Ryan 1-on-1 charts --------------------
        if ryan_cols:
            st.subheader("1-on-1 with Ryan (Counts)")

            attended = []
            missed = []

            for c in ryan_cols:
                yes, no = count_yes_no(df_weekly[c])
                label = c
                label = re.sub(r"\s*-\s*1[- ]on[- ]1.*$", "", label, flags=re.IGNORECASE).strip()
                attended.append({"Week/Program": label, "Count": yes})
                missed.append({"Week/Program": label, "Count": no})

            df_attended = pd.DataFrame(attended).sort_values("Week/Program")
            df_missed = pd.DataFrame(missed).sort_values("Week/Program")

            c1, c2 = st.columns(2)

            fig_yes = px.bar(df_attended, x="Week/Program", y="Count", title="Attended (Yes)")
            fig_yes.update_xaxes(title_text="Sessions Attended")
            fig_yes.update_yaxes(title_text="Count")
            c1.plotly_chart(style_chart_dark(fig_yes), use_container_width=True)

            fig_no = px.bar(df_missed, x="Week/Program", y="Count", title="Missed (No)")
            fig_no.update_xaxes(title_text="Sessions Missed")
            fig_no.update_yaxes(title_text="Count")
            c2.plotly_chart(style_chart_dark(fig_no), use_container_width=True)
        else:
            st.info("No '1-on-1 with Ryan' columns detected yet in the weekly export.")

        st.divider()

        # -------------------- Coach Engagement --------------------
        if ce_cols:
            st.subheader("Coach Engagement (Weekly)")

            # count how many non-empty responses per week
            week_counts = []
            ce_cols_sorted = sorted(ce_cols, key=week_sort_key)

            for c in ce_cols_sorted:
                s = df_weekly[c].astype(str).str.strip()
                count_non_empty = int((s != "").sum() - (s.str.lower() == "nan").sum())
                week_counts.append({"Week": c.replace(" - Coach Engagement", "").strip(), "Count": count_non_empty})

            df_counts = pd.DataFrame(week_counts)

            fig_ce = px.bar(df_counts, x="Week", y="Count", title="Number of Coach Engagement Responses (Non-Empty)")
            fig_ce.update_xaxes(title_text="Week")
            fig_ce.update_yaxes(title_text="Count")
            st.plotly_chart(style_chart_dark(fig_ce), use_container_width=True)

            st.subheader("What Coaches Wrote (by Week)")

            # Show the actual text, either per selected fellow (if we detected names) or all entries
            for c in ce_cols_sorted:
                week_label = c.replace(" - Coach Engagement", "").strip()
                with st.expander(week_label, expanded=False):
                    s = df_filtered[c] if c in df_filtered.columns else df_weekly[c]
                    s = s.dropna().astype(str).str.strip()
                    s = s[s != ""]
                    if s.empty:
                        st.write("(No responses.)")
                    else:
                        # If we can show coach name along with response, try to detect it
                        if "Coach Name" in df_filtered.columns:
                            show_df = df_filtered[["Coach Name", c]].copy()
                            show_df["Coach Name"] = show_df["Coach Name"].astype(str).str.strip()
                            show_df[c] = show_df[c].astype(str).str.strip()
                            show_df = show_df[(show_df[c] != "") & (show_df[c].str.lower() != "nan")]
                            for _, r in show_df.iterrows():
                                st.write(f"**{r['Coach Name']}:** {r[c]}")
                        else:
                            # Just list responses
                            for txt in s.tolist():
                                st.write(f"- {txt}")
        else:
            st.info("No 'Coach Engagement' columns detected yet in the weekly export.")

        st.divider()
        st.download_button(
            "Download Weekly Export (CSV)",
            convert_df(df_weekly),
            "cohort5_weekly_export.csv",
            "text/csv"
        )

else:
    st.error(
        "This workbook doesn’t match Cohort 4 (Attendance_New/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1) schemas."
    )
    st.stop()
