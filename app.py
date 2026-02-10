import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Access to Law School Dashboard", layout="wide")

# ============================================================
# NAVY + WHITE THEME (components.html prevents CSS from printing as text)
# ============================================================
CSS = """
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  :root{
    --navy: #00356b;        /* Yale blue */
    --navy-2: #00264d;      /* deeper */
    --accent: #286dc0;      /* lighter Yale blue */
    --white: #ffffff;
  }

  /* Entire app background */
  [data-testid="stAppViewContainer"]{
    background: var(--navy) !important;
  }

  /* Main area text defaults */
  [data-testid="stAppViewContainer"] .main,
  [data-testid="stAppViewContainer"] .main *{
    color: var(--white) !important;
    font-family: "Libre Baskerville", Georgia, serif !important;
  }

  /* Make smaller UI text Source Sans */
  [data-testid="stAppViewContainer"] .main label,
  [data-testid="stAppViewContainer"] .main .stMarkdown p,
  [data-testid="stAppViewContainer"] .main .stMarkdown li{
    font-family: "Source Sans 3", Arial, sans-serif !important;
  }

  /* Sidebar background */
  [data-testid="stSidebar"]{
    background-color: var(--navy-2) !important;
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

  /* Buttons */
  .stButton>button, .stDownloadButton>button{
    background: var(--accent) !important;
    color: var(--white) !important;
    border: 1px solid var(--accent) !important;
  }
  .stButton>button:hover, .stDownloadButton>button:hover{
    background: var(--white) !important;
    color: var(--navy) !important;
    border-color: var(--white) !important;
  }
</style>
"""
components.html(CSS, height=0, scrolling=False)

YALE_BLUES = ["#286dc0", "#7aa6de", "#00356b"]

def style_chart(fig):
    # Transparent charts on navy background
    grid = "rgba(255,255,255,0.18)"
    fig.update_layout(
        font=dict(family="Source Sans 3, Arial, sans-serif", color="white"),
        title=dict(font=dict(family="Libre Baskerville, Georgia, serif", color="white")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="white"), title_font=dict(color="white")),
        hoverlabel=dict(font=dict(color="white")),
        margin=dict(l=40, r=20, t=60, b=40),
        colorway=YALE_BLUES
    )
    fig.update_xaxes(gridcolor=grid, linecolor=grid, zerolinecolor=grid)
    fig.update_yaxes(gridcolor=grid, linecolor=grid, zerolinecolor=grid)
    return fig

def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

@st.cache_data
def load_workbook(path: str) -> dict:
    sheets = pd.read_excel(path, sheet_name=None)
    # normalize column names (trim) for every sheet
    for k, df in sheets.items():
        df.columns = df.columns.astype(str).str.strip()
        sheets[k] = df
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

def _norm_yes_no(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if s in {"yes", "y", "true", "1"}:
        return "Yes"
    if s in {"no", "n", "false", "0"}:
        return "No"
    return None

def _safe_strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

# ============================================================
# FILES IN REPO
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}

# Weekly coach form responses (Cohort 5)
COHORT5_WEEKLY_FILE = "Cohort 5 - Weekly Fellow Updates - SP26 (Responses).xlsx"
COHORT5_WEEKLY_SHEET = "Form Responses 1"

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
# COHORT 4 — INDIVIDUAL ONLY (charts OK)
# ============================================================
if is_cohort4:
    df_attendance = sheets["Attendance_New"].copy()
    df_scores = sheets["Test Scores"].copy()
    df_app = sheets["Application Status"].copy()

    df_attendance = _safe_strip_cols(df_attendance)
    df_scores = _safe_strip_cols(df_scores)
    df_app = _safe_strip_cols(df_app)

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
            scores_long, x="Test", y="Score",
            title=f"LSAT Scores for {selected}",
            markers=True
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
        )
        fig_att.update_xaxes(title_text="Attendance Type")
        fig_att.update_yaxes(title_text="Attendance Percent out of 100%")
        st.plotly_chart(style_chart(fig_att), use_container_width=True)

    # -------------------- Application Status (field-by-field) --------------------
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
# COHORT 5 — INDIVIDUAL ONLY (+ WEEKLY COACH UPDATES)
# N/A -> Not Applicable
# ============================================================
elif is_cohort5:
    df = sheets["Sheet1"].copy()
    df = _safe_strip_cols(df)

    # Name column (support variants)
    name_col = None
    for c in ["Name", "Full Name", "Unnamed: 0"]:
        if c in df.columns:
            name_col = c
            break
    if name_col is None:
        st.error("Cohort 5 Stats file: could not find a name column (expected 'Name' or 'Unnamed: 0').")
        st.stop()

    df["Fellow Name"] = df[name_col].astype(str).str.strip()
    fellows = sorted(df["Fellow Name"].dropna().unique())
    selected = st.sidebar.selectbox("Select Fellow", fellows)

    st.header("Individual Fellow Report")
    st.subheader(selected)

    row_df = df[df["Fellow Name"] == selected].copy()
    if row_df.empty:
        st.error("Selected fellow not found in Cohort 5 stats data.")
        st.stop()
    row = row_df.iloc[0].to_dict()

    tab_bio, tab_weekly = st.tabs(["Biographical Snapshot", "Weekly Coach Updates"])

    # -------------------- BIO TAB --------------------
    with tab_bio:
        # NOTE: sheet has typo "Undergraduate Instituion" in some versions
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

        extras = [c for c in df.columns if c not in {name_col, "Fellow Name"} and c not in shown]
        if extras:
            st.subheader("Additional Fields")
            for c in extras:
                st.write(f"**{c}:** {normalize_value(row.get(c))}")

        st.download_button(
            "Download Fellow Row (CSV)",
            convert_df(df[df["Fellow Name"] == selected]),
            f"{selected}_cohort5_stats.csv",
            "text/csv"
        )
        st.download_button(
            "Download Full Cohort 5 Stats (CSV)",
            convert_df(df),
            "cohort5_stats_full.csv",
            "text/csv"
        )

    # -------------------- WEEKLY TAB --------------------
    with tab_weekly:
        st.subheader("Weekly Coach Updates (from form responses)")

        # Load weekly responses
        try:
            weekly_sheets = load_workbook(COHORT5_WEEKLY_FILE)
        except FileNotFoundError:
            st.error(
                f"Could not find '{COHORT5_WEEKLY_FILE}' next to app.py. "
                "Add it to the repo folder (same level as app.py) and redeploy."
            )
            st.stop()

        if COHORT5_WEEKLY_SHEET not in weekly_sheets:
            st.error(
                f"Weekly file found, but sheet '{COHORT5_WEEKLY_SHEET}' is missing. "
                f"Available sheets: {list(weekly_sheets.keys())}"
            )
            st.stop()

        wdf = _safe_strip_cols(weekly_sheets[COHORT5_WEEKLY_SHEET])

        # Identify key columns (based on your uploaded sheet)
        fellow_col = None
        for c in ["Fellow name (first and last)", "Fellow Name", "Student", "Fellow"]:
            if c in wdf.columns:
                fellow_col = c
                break
        if fellow_col is None:
            st.error("Weekly file: could not find the fellow name column.")
            st.stop()

        coach_col = None
        for c in ["Coach name (first and last)", "Coach Name", "Coach"]:
            if c in wdf.columns:
                coach_col = c
                break

        # Filter to selected fellow (case-insensitive, trimmed)
        wdf["_fellow_norm"] = wdf[fellow_col].astype(str).str.strip().str.lower()
        sel_norm = str(selected).strip().lower()
        wsel = wdf[wdf["_fellow_norm"] == sel_norm].copy()

        if wsel.empty:
            st.info("No weekly coach submissions found yet for this fellow.")
        else:
            # ---------------- Attendance: Saturday Academies ----------------
            att_cols = [c for c in wsel.columns if "Saturday Academy" in c]
            # Keep stable order
            att_cols = sorted(att_cols, key=lambda s: s)

            if att_cols:
                att_long = []
                for c in att_cols:
                    session = str(c).strip().replace("  ", " ")
                    series = wsel[c].apply(_norm_yes_no)
                    yes = int((series == "Yes").sum())
                    no = int((series == "No").sum())
                    if yes > 0:
                        att_long.append({"Session": session, "Response": "Yes", "Count": yes})
                    if no > 0:
                        att_long.append({"Session": session, "Response": "No", "Count": no})

                att_long = pd.DataFrame(att_long)

                st.subheader("Saturday Academy Attendance (Counts)")

                # Separate charts exactly as requested: attended vs missed
                attended = att_long[att_long["Response"] == "Yes"].copy()
                missed = att_long[att_long["Response"] == "No"].copy()

                if attended.empty:
                    st.info("No 'Yes' (attended) Saturday Academy responses recorded yet.")
                else:
                    fig_yes = px.bar(
                        attended,
                        x="Session",
                        y="Count",
                        title="Programs Attended (Yes)",
                    )
                    fig_yes.update_xaxes(title_text="Program Attended")
                    fig_yes.update_yaxes(title_text="Count")
                    st.plotly_chart(style_chart(fig_yes), use_container_width=True)

                if missed.empty:
                    st.info("No 'No' (missed) Saturday Academy responses recorded yet.")
                else:
                    fig_no = px.bar(
                        missed,
                        x="Session",
                        y="Count",
                        title="Programs Missed (No)",
                    )
                    fig_no.update_xaxes(title_text="Program Missed")
                    fig_no.update_yaxes(title_text="Count")
                    st.plotly_chart(style_chart(fig_no), use_container_width=True)

            else:
                st.info("No Saturday Academy columns found yet in the weekly form export.")

            # ---------------- Attendance: 1-on-1 with Ryan ----------------
            ryan_cols = [c for c in wsel.columns if "1-on-1 with Ryan" in c]
            ryan_cols = sorted(ryan_cols, key=lambda s: s)

            if ryan_cols:
                r_long = []
                for c in ryan_cols:
                    label = str(c).strip().replace("  ", " ")
                    series = wsel[c].apply(_norm_yes_no)
                    yes = int((series == "Yes").sum())
                    no = int((series == "No").sum())
                    if yes > 0:
                        r_long.append({"Session": label, "Response": "Yes", "Count": yes})
                    if no > 0:
                        r_long.append({"Session": label, "Response": "No", "Count": no})

                r_long = pd.DataFrame(r_long)

                st.subheader("1-on-1 with Ryan (Counts)")

                attended = r_long[r_long["Response"] == "Yes"].copy()
                missed = r_long[r_long["Response"] == "No"].copy()

                if not attended.empty:
                    fig_yes = px.bar(attended, x="Session", y="Count", title="Sessions Attended (Yes)")
                    fig_yes.update_xaxes(title_text="Session Attended")
                    fig_yes.update_yaxes(title_text="Count")
                    st.plotly_chart(style_chart(fig_yes), use_container_width=True)
                else:
                    st.info("No 'Yes' (attended) 1-on-1 with Ryan responses recorded yet.")

                if not missed.empty:
                    fig_no = px.bar(missed, x="Session", y="Count", title="Sessions Missed (No)")
                    fig_no.update_xaxes(title_text="Session Missed")
                    fig_no.update_yaxes(title_text="Count")
                    st.plotly_chart(style_chart(fig_no), use_container_width=True)
                else:
                    st.info("No 'No' (missed) 1-on-1 with Ryan responses recorded yet.")

            else:
                st.info("No 1-on-1 with Ryan columns found yet in the weekly form export.")

            # ---------------- Coach Engagement (free text) ----------------
            engage_cols = [c for c in wsel.columns if "Coach Engagement" in c]
            engage_cols = sorted(engage_cols, key=lambda s: s)

            if engage_cols:
                notes = []
                for _, r in wsel.iterrows():
                    coach = str(r.get(coach_col)).strip() if coach_col else "Coach"
                    for c in engage_cols:
                        txt = r.get(c)
                        if pd.isna(txt) or str(txt).strip() == "":
                            continue
                        week_label = str(c).strip()
                        notes.append(
                            {
                                "Week": week_label,
                                "Coach": coach,
                                "Note": str(txt).strip(),
                            }
                        )

                notes_df = pd.DataFrame(notes)

                st.subheader("Coach Engagement (Weekly)")

                if notes_df.empty:
                    st.info("No Coach Engagement text has been submitted yet for this fellow.")
                else:
                    # Chart: number of engagement notes per week
                    counts = (
                        notes_df.groupby("Week")["Note"]
                        .count()
                        .reset_index(name="Count")
                        .sort_values("Week")
                    )
                    fig_counts = px.bar(
                        counts,
                        x="Week",
                        y="Count",
                        title="Number of Coach Engagement Entries per Week",
                    )
                    fig_counts.update_xaxes(title_text="Week")
                    fig_counts.update_yaxes(title_text="Count")
                    st.plotly_chart(style_chart(fig_counts), use_container_width=True)

                    # Expanders: actual text (most useful for Forman / staff)
                    for week in counts["Week"].tolist():
                        wk = notes_df[notes_df["Week"] == week].copy()
                        with st.expander(week, expanded=False):
                            for _, rr in wk.iterrows():
                                st.write(f"**{rr['Coach']}:** {rr['Note']}")

                    st.download_button(
                        "Download This Fellow’s Weekly Notes (CSV)",
                        convert_df(notes_df),
                        f"{selected}_weekly_coach_engagement.csv",
                        "text/csv"
                    )
            else:
                st.info("No Coach Engagement columns found yet in the weekly form export.")

            # Download raw weekly rows for this fellow (good for audits/debugging)
            st.download_button(
                "Download Raw Weekly Responses for This Fellow (CSV)",
                convert_df(wsel.drop(columns=["_fellow_norm"], errors="ignore")),
                f"{selected}_weekly_raw.csv",
                "text/csv"
            )

else:
    st.error(
        "This workbook doesn’t match Cohort 4 (Attendance_New/Test Scores/Application Status) "
        "or Cohort 5 (Sheet1) schemas."
    )
    st.stop()
