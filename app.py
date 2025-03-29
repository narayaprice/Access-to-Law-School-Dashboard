import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# ======================================================
# Data Loading and Preparation
# ======================================================
data_file = "YA2LS Cohort 4 Data (2024 Fellows).xlsx"
df_dict = pd.read_excel(data_file, sheet_name=["Attendance_New", "Test Scores"])
df_attendance = df_dict["Attendance_New"]
df_scores = df_dict["Test Scores"]

# ----- Define Attendance Column Names (all binary: 0 = not present, 1 = present) -----
fall_col   = "Fall Small Group Attendance %"
spring_col = "Spring Small Group Attendance %"
small_group_total_col = "Total Small Group Attendance $"
sa_col     = "SA %"
total_attendance_col = "Total Attendance %"

required_cols = [fall_col, spring_col, small_group_total_col, sa_col, total_attendance_col]
for col in required_cols:
    if col not in df_attendance.columns:
        raise Exception(f"Required column '{col}' not found in Attendance_New sheet.")

# Check if the Attendance_New sheet has a "Fellow" column.
has_attendance_fellow = "Fellow" in df_attendance.columns

# ----- Process Test Scores Data -----
# Test Scores sheet must include a "Fellow" column and the following test columns.
score_columns = ["Diagnostic", "PT 71", "PT 73", "PT136", "PT 137", "PT 138", 
                 "PT 139", "PT 140", "PT 141", "PT 144", "PT 145", "PT 146", 
                 "PT 147", "PT 148", "PT 149"]

if "Fellow" not in df_scores.columns:
    raise Exception("Required column 'Fellow' not found in Test Scores sheet.")

# Melt the test scores into long format for plotting trends.
scores_long = df_scores.melt(
    id_vars="Fellow",
    value_vars=score_columns,
    var_name="Test",
    value_name="Score"
)
scores_long["Test"] = pd.Categorical(scores_long["Test"], categories=score_columns, ordered=True)

# Compute LSAT score improvement for each fellow.
df_scores["Score_Improvement"] = df_scores["PT 149"] - df_scores["Diagnostic"]

# If Attendance_New doesn’t have "Fellow", assign it from Test Scores by row order.
if not has_attendance_fellow:
    df_attendance["Fellow"] = df_scores["Fellow"]

attendance_by_fellow = df_attendance.copy()

# Merge attendance with test scores for the comparison scatter plot.
comparison_df = pd.merge(
    df_scores[["Fellow", "Score_Improvement"]],
    attendance_by_fellow[["Fellow", total_attendance_col]],
    on="Fellow",
    how="left"
)

# ======================================================
# Create Cohort Overview Charts
# ======================================================
# Because the attendance columns are binary, we create bar charts showing the counts for 0’s vs. 1’s.
def create_binary_bar_chart(df, column, title):
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, "Count"]
    fig = px.bar(counts, x=column, y="Count", title=title, text=column)
    return fig

fig_fall = create_binary_bar_chart(df_attendance, fall_col, "Fall Small Group Attendance % Distribution")
fig_spring = create_binary_bar_chart(df_attendance, spring_col, "Spring Small Group Attendance % Distribution")
fig_small_group_total = create_binary_bar_chart(df_attendance, small_group_total_col, "Total Small Group Attendance Distribution")
fig_sa = create_binary_bar_chart(df_attendance, sa_col, "SA % Distribution")
fig_total_attendance = create_binary_bar_chart(df_attendance, total_attendance_col, "Total Attendance % Distribution")

# Scatter plot: Total Attendance % vs. LSAT Score Improvement
fig_comparison = px.scatter(
    comparison_df,
    x=total_attendance_col,
    y="Score_Improvement",
    hover_data=["Fellow"],
    title="LSAT Score Improvement vs. Total Attendance %"
)

# Average LSAT scores over test events (across the cohort)
avg_scores = scores_long.groupby("Test", as_index=False).mean()
fig_scores = px.line(
    avg_scores,
    x="Test",
    y="Score",
    title="Average LSAT Scores Over Test Events",
    markers=True
)

# Helper function to apply Yale-inspired styling.
def style_chart(fig):
    fig.update_layout(
        title_font=dict(family="Georgia, serif", color="#0a2240"),
        font=dict(family="Georgia, serif", color="#0a2240")
    )
    return fig

fig_fall = style_chart(fig_fall)
fig_spring = style_chart(fig_spring)
fig_small_group_total = style_chart(fig_small_group_total)
fig_sa = style_chart(fig_sa)
fig_total_attendance = style_chart(fig_total_attendance)
fig_comparison = style_chart(fig_comparison)
fig_scores = style_chart(fig_scores)

# ======================================================
# Dash App Layout and Callbacks
# ======================================================
app = dash.Dash(__name__)

app.layout = html.Div([
    # Sidebar with Yale image and dashboard title.
    html.Div([
        html.Img(
            src="https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv",
            style={"width": "100%", "height": "auto", "marginBottom": "20px"}
        ),
        html.H2(
            "Access to Law School Cohort 4 Data Dashboard",
            style={"textAlign": "center", "color": "#0a2240", "fontFamily": "Georgia, serif"}
        )
    ], style={
        "width": "20%", "display": "inline-block", "verticalAlign": "top", "padding": "10px", "backgroundColor": "#f5f5f5"
    }),
    # Main content with Tabs.
    html.Div([
        dcc.Tabs(id="tabs", value="tab-cohort", children=[
            dcc.Tab(label="Cohort Overview", value="tab-cohort", style={"fontFamily": "Georgia, serif", "color": "#0a2240"}),
            dcc.Tab(label="Individual Fellow Reports", value="tab-individual", style={"fontFamily": "Georgia, serif", "color": "#0a2240"})
        ]),
        html.Div(id="tabs-content", style={"padding": "20px"})
    ], style={"width": "75%", "display": "inline-block", "paddingLeft": "20px", "verticalAlign": "top"})
])

@app.callback(Output("tabs-content", "children"), Input("tabs", "value"))
def render_content(tab):
    if tab == "tab-cohort":
        return html.Div([
            html.H2("Cohort Overview", style={"textAlign": "center", "color": "#0a2240", "fontFamily": "Georgia, serif"}),
            dcc.Graph(id="fall-chart", figure=fig_fall),
            dcc.Graph(id="spring-chart", figure=fig_spring),
            dcc.Graph(id="small-group-total-chart", figure=fig_small_group_total),
            dcc.Graph(id="sa-chart", figure=fig_sa),
            dcc.Graph(id="total-attendance-chart", figure=fig_total_attendance),
            dcc.Graph(id="comparison-chart", figure=fig_comparison),
            dcc.Graph(id="scores-chart", figure=fig_scores)
        ], style={"margin": "20px"})
    elif tab == "tab-individual":
        fellows = sorted(df_scores["Fellow"].unique())
        return html.Div([
            html.H2("Individual Fellow Reports", style={"textAlign": "center", "color": "#0a2240", "fontFamily": "Georgia, serif"}),
            html.Div([
                html.Label("Select Fellow:", style={"fontWeight": "bold", "fontFamily": "Georgia, serif", "color": "#0a2240"}),
                dcc.Dropdown(
                    id="fellow-dropdown",
                    options=[{"label": f, "value": f} for f in fellows],
                    value=fellows[0] if fellows else None,
                    clearable=False
                )
            ], style={"width": "50%", "margin": "auto", "paddingBottom": "20px"}),

