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

# --- Process Attendance Data ---
attendance_agg = df_attendance.copy()
attendance_agg['Date'] = pd.to_datetime(attendance_agg['Date'])
attendance_agg = attendance_agg.sort_values('Date')
attendance_long = attendance_agg.melt(id_vars='Date', value_vars=['FSG', 'SSG', 'SA'],
                                      var_name='Session', value_name='Attendance')

# --- Process Test Scores Data ---
score_columns = ["Diagnostic", "PT 71", "PT 73", "PT136", "PT 137", "PT 138", 
                 "PT 139", "PT 140", "PT 141", "PT 144", "PT 145", "PT 146", 
                 "PT 147", "PT 148", "PT 149"]
scores_long = df_scores.melt(id_vars='Fellow', value_vars=score_columns,
                             var_name='Test', value_name='Score')
scores_long['Test'] = pd.Categorical(scores_long['Test'], categories=score_columns, ordered=True)

# --- Compute Comparison Metrics: Attendance vs. Score Improvement ---
if 'Fellow' in df_attendance.columns:
    attendance_by_fellow = df_attendance.groupby('Fellow')[['FSG', 'SSG', 'SA']].sum().reset_index()
    attendance_by_fellow['Total_Attendance'] = attendance_by_fellow[['FSG', 'SSG', 'SA']].sum(axis=1)
else:
    attendance_by_fellow = pd.DataFrame({
        "Fellow": df_scores['Fellow'],
        "Total_Attendance": [0] * len(df_scores)
    })

df_scores['Score_Improvement'] = df_scores["PT 149"] - df_scores["Diagnostic"]
comparison_df = pd.merge(df_scores[['Fellow', 'Score_Improvement']], 
                         attendance_by_fellow[['Fellow', 'Total_Attendance']],
                         on='Fellow', how='left')

# ======================================================
# Dash App Setup and Global Styling
# ======================================================
app = dash.Dash(__name__)

# Helper function to update chart layouts with Yale styling.
def style_chart(fig):
    fig.update_layout(
        title_font=dict(family="Georgia, serif", color="#0a2240"),
        font=dict(family="Georgia, serif", color="#0a2240")
    )
    return fig

# ======================================================
# App Layout: Sidebar and Main Content
# ======================================================
app.layout = html.Div([
    # Sidebar
    html.Div([
        html.Img(
            src="https://law.yale.edu/sites/default/files/styles/content_full_width/public/images/news/accessday1-3381.jpg?itok=6vWWOiBv",
            style={'width': '100%', 'height': 'auto', 'marginBottom': '20px'}
        ),
        html.H2(
            "Access to Law School Cohort 4 Data Dashboard",
            style={'textAlign': 'center', 'color': '#0a2240', 'fontFamily': 'Georgia, serif'}
        )
    ], style={
        'width': '20%', 
        'display': 'inline-block', 
        'verticalAlign': 'top', 
        'padding': '10px', 
        'backgroundColor': '#f5f5f5'
    }),
    
    # Main Content: Tabs and Dashboard Views
    html.Div([
        dcc.Tabs(id='tabs', value='tab-cohort', children=[
            dcc.Tab(label='Cohort Overview', value='tab-cohort',
                    style={'fontFamily': 'Georgia, serif', 'color': '#0a2240'}),
            dcc.Tab(label='Individual Fellow Reports', value='tab-individual',
                    style={'fontFamily': 'Georgia, serif', 'color': '#0a2240'})
        ]),
        html.Div(id='tabs-content', style={'padding': '20px'})
    ], style={
        'width': '75%', 
        'display': 'inline-block', 
        'paddingLeft': '20px', 
        'verticalAlign': 'top'
    })
])

# ======================================================
# Callback: Render Tab Content
# ======================================================
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-cohort':
        # Attendance over time chart
        fig_attendance = px.line(attendance_long, x='Date', y='Attendance', color='Session',
                                 title="Attendance Over Time", markers=True)
        fig_attendance = style_chart(fig_attendance)
        
        # Average LSAT scores chart (across test events)
        avg_scores = scores_long.groupby('Test', as_index=False).mean()
        fig_scores = px.line(avg_scores, x='Test', y='Score',
                             title="Average LSAT Scores Over Test Events", markers=True)
        fig_scores = style_chart(fig_scores)
        
        # Scatter plot: Total Attendance vs. Score Improvement
        fig_comparison = px.scatter(comparison_df, x='Total_Attendance', y='Score_Improvement',
                                    hover_data=['Fellow'],
                                    title="Score Improvement vs. Total Attendance")
        fig_comparison = style_chart(fig_comparison)
        
        return html.Div([
            html.H2("Cohort Overview", style={'textAlign': 'center', 'color': '#0a2240', 'fontFamily': 'Georgia, serif'}),
            dcc.Graph(id='attendance-chart', figure=fig_attendance),
            dcc.Graph(id='scores-chart', figure=fig_scores),
            dcc.Graph(id='comparison-chart', figure=fig_comparison)
        ], style={'margin': '20px'})
    
    elif tab == 'tab-individual':
        fellows = sorted(df_scores['Fellow'].unique())
        return html.Div([
            html.H2("Individual Fellow Reports", style={'textAlign': 'center', 'color': '#0a2240', 'fontFamily': 'Georgia, serif'}),
            html.Div([
                html.Label("Select Fellow:", style={'fontWeight': 'bold', 'fontFamily': 'Georgia, serif', 'color': '#0a2240'}),
                dcc.Dropdown(
                    id='fellow-dropdown',
                    options=[{'label': fellow, 'value': fellow} for fellow in fellows],
                    value=fellows[0] if fellows else None,
                    clearable=False
                )
            ], style={'width': '50%', 'margin': 'auto', 'paddingBottom': '20px'}),
            dcc.Graph(id='individual-attendance-chart'),
            dcc.Graph(id='individual-scores-chart')
        ], style={'margin': '20px'})

# ======================================================
# Callback: Update Individual Fellow Charts
# ======================================================
@app.callback(
    [Output('individual-attendance-chart', 'figure'),
     Output('individual-scores-chart', 'figure')],
    Input('fellow-dropdown', 'value')
)
def update_individual_charts(selected_fellow):
    if 'Fellow' in df_attendance.columns:
        df_att_fellow = df_attendance[df_attendance['Fellow'] == selected_fellow].copy()
        df_att_fellow['Date'] = pd.to_datetime(df_att_fellow['Date'])
        df_att_fellow = df_att_fellow.sort_values('Date')
        att_long = df_att_fellow.melt(id_vars='Date', value_vars=['FSG', 'SSG', 'SA'],
                                      var_name='Session', value_name='Attendance')
        fig_att = px.line(att_long, x='Date', y='Attendance', color='Session',
                          title=f"Attendance Over Time for {selected_fellow}", markers=True)
        fig_att = style_chart(fig_att)
    else:
        fig_att = px.line(title="Attendance data not available for individuals.")
        fig_att = style_chart(fig_att)
    
    df_scores_fellow = scores_long[scores_long['Fellow'] == selected_fellow]
    fig_scores = px.line(df_scores_fellow, x='Test', y='Score',
                         title=f"LSAT Scores Trend for {selected_fellow}", markers=True)
    fig_scores = style_chart(fig_scores)
    
    return fig_att, fig_scores

# ======================================================
# Run the App
# ======================================================
if __name__ == '__main__':
    app.run_server(debug=True)


