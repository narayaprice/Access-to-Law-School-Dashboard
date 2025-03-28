import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

st.set_page_config(layout="wide", page_title="Access to Law School Fellow Data Dashboard")

# Inject custom Yale-inspired CSS
yale_css = """
    <style>
        body {
            font-family: 'Georgia', serif;
            background-color: #f8f9fa;
        }
        .main > div {
            padding: 2rem;
        }
        h1, h2, h3, h4 {
            color: #00356B;
        }
        .stButton>button {
            background-color: #00356B;
            color: white;
            border-radius: 5px;
        }
        .stDownloadButton>button {
            background-color: #0067B1;
            color: white;
        }
    </style>
"""
st.markdown(yale_css, unsafe_allow_html=True)

@st.cache_data
def load_data():
    xls = pd.ExcelFile("YA2LS Cohort 4 Data (2024 Fellows).xlsx")
    attendance = xls.parse("Attendance_New")
    scores = xls.parse("Test Scores")
    return attendance, scores

attendance_df, scores_df = load_data()

# Clean up
attendance_df.columns = attendance_df.columns.str.strip()
scores_df.columns = scores_df.columns.str.strip()

attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']

# Sidebar with logo and branding
st.sidebar.image("https://law.yale.edu/sites/default/files/images/YLS_Logo_Blue.png", use_column_width=True)
st.sidebar.title("Access to Law School Fellow Data Dashboard")

# Sidebar navigation
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

if view == "Cohort Overview":
    st.title("Access to Law School Fellow Data Dashboard")

    st.header("1. Attendance Distributions")
    percent_cols = ["FSG %", "SSG %", "SA %", "Total %"]
    fig, ax = plt.subplots(1, 4, figsize=(20, 5))
    for i, col in enumerate(percent_cols):
        sns.boxplot(y=attendance_df[col], ax=ax[i], color="#00356B")
        ax[i].set_title(col)
    st.pyplot(fig)

    st.header("2. Aggregate Attendance Trends")
    fsg_cols = [col for col in attendance_df.columns if col.startswith("FSG")]
    ssg_cols = [col for col in attendance_df.columns if col.startswith("SSG")]
    sa_cols = [col for col in attendance_df.columns if col.startswith("SA")]

    session_means = pd.DataFrame({
        'FSG': attendance_df[fsg_cols].apply(pd.to_numeric, errors='coerce').mean(),
        'SSG': attendance_df[ssg_cols].apply(pd.to_numeric, errors='coerce').mean(),
        'SA': attendance_df[sa_cols].apply(pd.to_numeric, errors='coerce').mean()
    })
    st.line_chart(session_means)

    st.header("3. Test Score Growth")
    scores_df = scores_df.rename(columns={"Diagnostic ": "Diagnostic"})
    scores_df['Score Change'] = scores_df['Final'] - scores_df['Diagnostic']
    st.write("Average Score Change:", scores_df['Score Change'].mean())
    st.bar_chart(scores_df[['Diagnostic', 'Final']].mean())

    st.header("4. Correlation: Attendance vs. Score Change")
    merged = pd.merge(scores_df, attendance_df, left_on="Name", right_on="Full Name")
    fig, ax = plt.subplots()
    sns.scatterplot(data=merged, x="Total %", y="Score Change", ax=ax, color="#00356B")
    st.pyplot(fig)

    st.header("5. Cohort Summary Table")
    summary = pd.DataFrame({
        "Avg FSG %": [attendance_df["FSG %"].mean()],
        "Avg SSG %": [attendance_df["SSG %"].mean()],
        "Avg SA %": [attendance_df["SA %"].mean()],
        "Avg Total %": [attendance_df["Total %"].mean()],
        "Avg Score Change": [scores_df['Score Change'].mean()],
        "Total Fellows": [len(attendance_df)]
    })
    st.dataframe(summary)

elif view == "Individual Fellow Report":
    st.title("Access to Law School Fellow Data Dashboard")
    fellow = st.selectbox("Select Fellow", attendance_df["Full Name"].unique())
    att_row = attendance_df[attendance_df["Full Name"] == fellow]
    score_row = scores_df[scores_df["Name"] == fellow]

    st.subheader("1. Attendance Timeline")
    fig, ax = plt.subplots(figsize=(12, 4))
    full_att = att_row.filter(like='FSG').T.join(att_row.filter(like='SSG').T).join(att_row.filter(like='SA').T)
    full_att.columns = ['Attendance']
    full_att.plot(kind='bar', ax=ax, color="#00356B")
    st.pyplot(fig)

    st.subheader("2. Score Progression")
    scores = score_row[['Diagnostic', 'PB', 'Final']].T.rename(columns={score_row.index[0]: 'Score'})
    st.line_chart(scores)

    st.subheader("3. Attendance vs. Score Change")
    st.write("Total Attendance %:", att_row['Total %'].values[0])
    st.write("Score Change:", (score_row['Final'].values[0] - score_row['Diagnostic'].values[0]))

    st.subheader("4. Downloadable Report")
    export_df = pd.concat([att_row.reset_index(drop=True), score_row.reset_index(drop=True)], axis=1)
    csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Report", csv, "fellow_report.csv", "text/csv")

