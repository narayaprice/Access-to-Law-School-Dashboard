import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt

st.title("YA2LS Fellows Dashboard")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.subheader("Raw Data")
    st.write(data)

    numeric_columns = data.select_dtypes(include='number').columns.tolist()
    categorical_columns = data.select_dtypes(include='object').columns.tolist()

    st.subheader("Altair Visualization")
    x_axis = st.selectbox("Select X-axis", options=numeric_columns)
    y_axis = st.selectbox("Select Y-axis", options=numeric_columns)

    chart = alt.Chart(data).mark_circle(size=60).encode(
        x=x_axis,
        y=y_axis,
        tooltip=[x_axis, y_axis]
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Seaborn Visualization")
    plot_type = st.selectbox("Choose a plot type", ["scatterplot", "boxplot", "violinplot"])

    if plot_type == "scatterplot":
        sns_plot = sns.scatterplot(data=data, x=x_axis, y=y_axis)
    elif plot_type == "boxplot":
        sns_plot = sns.boxplot(data=data, x=x_axis, y=y_axis)
    elif plot_type == "violinplot":
        sns_plot = sns.violinplot(data=data, x=x_axis, y=y_axis)

    st.pyplot(plt.gcf())
    plt.clf()

    st.subheader("Summary Statistics")
    st.write(data.describe())

