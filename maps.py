import streamlit as st
import plotly.express as px

fig = px.choropleth(
    # df,
    # locations="country_code",  # ISO-3 codes
    # color="value",
    # hover_name="country",
    # projection="natural earth"
)
st.plotly_chart(fig)
