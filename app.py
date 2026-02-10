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
# COLORS
# ============================================================
NAVY = "#00356b"      # Yale Navy
WHITE = "#ffffff"

# ============================================================
# NAVY + WHITE THEME (MAIN + SIDEBAR)
# ============================================================
CSS = f"""
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, [data-testid="stAppViewContainer"] {{
  background-color: {NAVY} !important;
}}

[data-testid="stAppViewContainer"] .main * {{
  color: {WHITE} !important;
  font-family: "Libre Baskerville", Georgia, serif !important;
}}

section[data-testid="stSidebar"] {{
  background-color: {NAVY} !important;
}}

section[data-testid="stSidebar"] * {{
  color: {WHITE} !important;
  font-family: "Source Sans 3", Arial, sans-serif !important;
}}

.sidebar-title {{
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}}

.stButton button,
.stDownloadButton button {{
  background-color: {WHITE} !important;
  color: {NAVY} !important;
  font-weight: 700 !important;
}}
</style>
"""
components.html(CSS, height=0)

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

def normalize_yes_no(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if s in {"yes", "y", "1", "true", "attended"}:
        return "Yes"
    if s in {"no", "n", "0", "false", "missed"}:
        return "No"
    return None

def normalize_value(v):
    if pd.isna(v):
        return "(missing)"
    s = str(v).strip()
    if s == "":
        return "(missing)"
    if s.upper() in {"N/A", "NA", "NOT APPLICABLE"}:
        return "Not Applicable"
    return s

# ============================================================
# PLOTLY STYLING (PLOTLY 6 SAFE)
# ============================================================
def style_plotly(fig):
    fig.update_layout(
        paper_bgcolor=NAVY,
        plot_bgcolor=NAVY,
        font=dict(color=WHITE),
        title=dict(font=dict(color=WHITE)),
        margin=dict(l=70, r=40, t=80, b=70),
        legend=dict(font=dict(color=WHITE)),
    )

    fig.update_xaxes(
        showline=True,
        linecolor=WHITE,
        tickcolor=WHITE,
        tickfont=dict(color=WHITE),
        title=dict(text=fig.layout.xaxis.title.text, font=dict(color=WHITE)),
        showgrid=True,
        gridcolor="rgba(255,255,255,0.2)",
        zeroline=False,
    )

    fig.update_yaxes(
        showline=True,
        linecolor=WHITE,
        tickcolor=WHITE,
        tickfont=dict(color=WHITE),
        title=dict(text=fig.layout.yaxis.title.text, font=dict(color=WHITE)),
        showgrid=True,
        gridcolor="rgba(255,255,255,0.2)",
        zeroline=False,
    )
    return fig

# ============================================================
# FILES
# ============================================================
COHORT_FILES = {
    "Cohort 4 Fellows": "YA2LS Cohort 4 Data (2024 Fellows).xlsx",
    "Cohort 5 Fellows": "Cohort 5 Stats - Updated for Dashboard.xlsx",
}
WEEKLY_UPDATES_FILE = "Cohort 5 - Weekly Fellow Updates - SP26 (Responses).xlsx"

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown(
    '<div class="sidebar-title">Access to Law School Cohort Data Dashboard</div>',
    unsafe_allow_html=True,
)

selected_cohort = st.sidebar.selectbox("Select Cohort", list(COHORT_FILES.keys()))

# ============================================================
# LOAD WORKBOOK
# ============================================================
sheets = load_workbook(COHORT_FILES[selected_cohort])
st.title(selected_cohort)

# ============================================================
# COHORT 5 — BIO + WEEKLY UPDATES
# ============================================================
if "Sheet1" in sheets:
    df = sheets["Sheet1"].copy()

    name_col = next(c for c in df.columns if "name" in c.lower())
    df["Fellow Name"] = df[name_col].astype(str).str.strip()

    selected = st.sidebar.selectbox("Select Fellow", sorted(df["Fellow Name"].unique()))

    st.header("Biographical Snapshot")
    row = df[df["Fellow Name"] == selected].iloc[0]

    for col in df.columns:
        if col not in {name_col, "Fellow Name"}:
            st.write(f"**{col}:** {normalize_value(row[col])}")

    # ========================================================
    # WEEKLY UPDATES
    # ========================================================
    weekly = pd.read_excel(WEEKLY_UPDATES_FILE)
    weekly.columns = weekly.columns.astype(str).str.strip()

    st.header("Weekly Coach Updates")

    # ---------- Saturday Academy ----------
    sa_cols = [c for c in weekly.columns if "Saturday Academy" in c]
    if sa_cols:
        sa = weekly[sa_cols].melt(var_name="Program", value_name="Raw")
        sa["Response"] = sa["Raw"].apply(normalize_yes_no)
        sa = sa.dropna(subset=["Response"])
        counts = sa.groupby(["Program", "Response"]).size().reset_index(name="Count")

        for resp, label in [("Yes", "Attended"), ("No", "Missed")]:
            sub = counts[counts["Response"] == resp]
            fig = px.bar(
                sub,
                x="Program",
                y="Count",
                title=f"Saturday Academy — {label}",
                color_discrete_sequence=[NAVY],
            )
            fig.update_xaxes(title_text="Program")
            fig.update_yaxes(title_text="Count")
            st.plotly_chart(style_plotly(fig), use_container_width=True)

    # ---------- Coach Engagement ----------
    eng_cols = [c for c in weekly.columns if "Coach Engagement" in c]
    if eng_cols:
        eng = weekly.melt(id_vars=["Week"], value_vars=eng_cols, value_name="Text")
        eng = eng[eng["Text"].notna() & (eng["Text"].astype(str).str.strip() != "")]
        week_counts = eng.groupby("Week").size().reset_index(name="Count")

        fig = px.bar(
            week_counts,
            x="Week",
            y="Count",
            title="Coach Engagement Responses per Week",
            color_discrete_sequence=[NAVY],
        )
        fig.update_xaxes(title_text="Week")
        fig.update_yaxes(title_text="Count")
        st.plotly_chart(style_plotly(fig), use_container_width=True)

        for wk in sorted(eng["Week"].unique()):
            with st.expander(f"Week {wk}"):
                for txt in eng[eng["Week"] == wk]["Text"]:
                    st.write(txt)

else:
    st.error("Cohort schema not recognized.")
