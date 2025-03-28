import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide", page_title="Access to Law School Cohort 4 Data Dashboard")

@st.cache_data

def load_data():
    xls = pd.ExcelFile("YA2LS Cohort 4 Data (2024 Fellows).xlsx")
    attendance = xls.parse("Attendance_New")
    scores = xls.parse("Test Scores")
    return attendance, scores

attendance_df, scores_df = load_data()

attendance_df.columns = attendance_df.columns.str.strip()
scores_df.columns = scores_df.columns.str.strip()
attendance_df['Full Name'] = attendance_df['First'] + ' ' + attendance_df['Last']
scores_df['Name'] = scores_df['Fellow First'] + ' ' + scores_df['Fellow Last']

st.sidebar.title("Access to Law School Cohort 4")
view = st.sidebar.selectbox("Choose View", ["Cohort Overview", "Individual Fellow Report"])

if view == "Cohort Overview":
    st.title("Cohort Overview")

    st.header("1. Attendance Distributions")
    boxplot_data = attendance_df[['FSG %', 'Spring Small Group %', 'SA %', 'Total Attendance%']].copy()
    boxplot_data = boxplot_data.rename(columns={
        'FSG %': 'FSG (Fall Small Group)',
        'Spring Small Group %': 'SSG (Spring Small Group)',
        'SA %': 'SA (Saturday Academy)',
        'Total Attendance%': 'Total Attendance'
    })
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=boxplot_data, ax=ax, palette='Blues')
    ax.set_ylabel('Attendance Percentage')
    st.pyplot(fig)

    st.header("2. Attendance Heatmap")
    session_cols = [col for col in attendance_df.columns if col.startswith(('FSG', 'SSG', 'SA')) and not col.endswith(('Attended', 'Total', '%'))]
    att_data = attendance_df.set_index('Full Name')[session_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.heatmap(att_data, cmap='Blues', cbar_kws={'label': 'Attendance (1=Present, 0=Absent)'}, ax=ax)
    st.pyplot(fig)

    st.header("3. Average Attendance per Session")
    ordered_sessions = sorted([col for col in session_cols if col.startswith('FSG')]) + \
                       sorted([col for col in session_cols if col.startswith('SSG')]) + \
                       sorted([col for col in session_cols if col.startswith('SA')])
    avg_att = att_data[ordered_sessions].mean().sort_index()
    fig, ax = plt.subplots(figsize=(16, 5))
    avg_att.plot(kind='bar', ax=ax, color='#00356B')
    ax.set_ylabel('Average Attendance')
    st.pyplot(fig)

    st.header("4. Stacked Attendance % by Fellow")
    stacked_df = attendance_df[['Full Name', 'FSG %', 'Spring Small Group %', 'SA %']].rename(columns={
        'FSG %': 'FSG', 'Spring Small Group %': 'SSG', 'SA %': 'SA'
    }).set_index('Full Name')
    fig, ax = plt.subplots(figsize=(16, 6))
    stacked_df.plot(kind='bar', stacked=True, ax=ax, colormap='Blues')
    ax.set_ylabel('Attendance %')
    ax.legend(title='Group')
    ax.set_xticks(range(len(stacked_df.index)))
    ax.set_xticklabels(stacked_df.index, rotation=90)
    st.pyplot(fig)

    st.header("5. Cohort LSAT Score Progression")
    pt_order = ['Diagnostic', 'PT 71', 'PT 73', 'PT 136', 'PT 137', 'PT 138', 'PT 139', 'PT 140', 'PT 141', 'PT 144', 'PT 145', 'PT 146', 'PT 147', 'PT 148', 'PT 149']
    for pt in pt_order:
        if pt in scores_df.columns:
            scores_df[pt] = pd.to_numeric(scores_df[pt], errors='coerce')
    long_scores = scores_df[['Name'] + [pt for pt in pt_order if pt in scores_df.columns]].melt(id_vars='Name', var_name='Test', value_name='Score').dropna()
    avg_scores = long_scores.groupby('Test')['Score'].mean().reindex(pt_order).dropna().reset_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=long_scores, x='Test', y='Score', hue='Name', alpha=0.4, linewidth=1, ax=ax)
    sns.lineplot(data=avg_scores, x='Test', y='Score', color='black', label='Cohort Avg', linewidth=2, ax=ax)
    ax.set_title('Cohort LSAT Score Progression')
    ax.set_ylabel('Score')
    ax.legend(loc='upper left')
    st.pyplot(fig)

    st.header("6. Filtered LSAT Score Progression")
    attendance_pct = attendance_df[['Full Name', 'Total Attendance%']].rename(columns={'Full Name': 'Name'})
    merged = pd.merge(long_scores, attendance_pct, on='Name', how='left')
    filtered = merged[merged['Total Attendance%'] >= 75]
    filtered_avg = filtered.groupby('Test')['Score'].mean().reindex(pt_order).dropna().reset_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=filtered, x='Test', y='Score', hue='Name', alpha=0.4, linewidth=1, ax=ax)
    sns.lineplot(data=filtered_avg, x='Test', y='Score', color='green', label='Filtered Avg (≥75%)', linewidth=2, ax=ax)
    ax.set_title('Filtered LSAT Score Progression')
    ax.set_ylabel('Score')
    ax.legend(loc='upper left')
    st.pyplot(fig)

elif view == "Individual Fellow Report":
    fellow = st.selectbox("Select Fellow", attendance_df['Full Name'].unique())
    att_row = attendance_df[attendance_df['Full Name'] == fellow]
    score_row = scores_df[scores_df['Name'] == fellow]

    st.title(f"Individual Fellow Report: {fellow}")

    st.header("1. Attendance Timeline")
    fsg_cols = sorted([col for col in att_row.columns if col.startswith('FSG') and not col.endswith('%')])
    ssg_cols = sorted([col for col in att_row.columns if col.startswith('SSG') and not col.endswith('%')])
    sa_cols = sorted([col for col in att_row.columns if col.startswith('SA') and not col.endswith('%')])
    ordered_session_cols = fsg_cols + ssg_cols + sa_cols

    att_vals = att_row[ordered_session_cols].T.reset_index()
    att_vals.columns = ['Session', 'Attendance']
    att_vals['Group'] = att_vals['Session'].apply(lambda x: 'FSG' if x.startswith('FSG') else ('SSG' if x.startswith('SSG') else 'SA'))
    att_vals['Attendance'] = pd.to_numeric(att_vals['Attendance'], errors='coerce')
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=att_vals, x='Session', y='Attendance', hue='Group', marker='o', ax=ax)
    ax.set_title(f'{fellow} - Attendance Timeline')
    ax.set_ylabel('Present (1) / Absent (0)')
    ax.legend(title='Group')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.header("2. Score Progression")
    available_pts = [pt for pt in pt_order if pt in score_row.columns]
    score_prog = score_row[available_pts].T
    score_prog.columns = ['Score']
    score_prog = score_prog.reset_index().rename(columns={'index': 'Test'})
    score_prog['Score Change'] = score_prog['Score'].diff()
    score_prog['Rolling Avg'] = score_prog['Score'].rolling(window=3, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=score_prog, x='Test', y='Score', marker='o', label='Score', ax=ax)
    sns.lineplot(data=score_prog, x='Test', y='Rolling Avg', linestyle='--', label='3-Test Moving Avg', color='gray', ax=ax)
    for i, row in score_prog.iterrows():
        if pd.notna(row['Score Change']) and abs(row['Score Change']) >= 5:
            ax.text(i, row['Score'] + 1, f"{row['Score Change']:+.0f}", color='green' if row['Score Change'] > 0 else 'red')
    ax.set_title(f'{fellow} - Score Progression with Rolling Average')
    ax.set_ylabel('Score')
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

    st.header("3. Summary")
    st.write("Total Attendance %:", float(att_row['Total Attendance%']))
    if not score_row.empty:
        st.write("Score Change:", float(score_row['Approx PB']) - float(score_row['Diagnostic']))

    st.header("4. Download Report")
    export_df = pd.concat([att_row.reset_index(drop=True), score_row.reset_index(drop=True)], axis=1)
    csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV Report", csv, f"{fellow.replace(' ', '_')}_report.csv", "text/csv")


