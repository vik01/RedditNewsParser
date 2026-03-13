import streamlit as st
import polars as pl
from maps import WorldMap

st.set_page_config(layout="wide")
st.title("News Bot")

# Sample data for demonstration — replace with your actual data source
data = pl.DataFrame({
    "country_code": ["USA", "GBR", "DEU", "FRA", "JPN", "BRA", "AUS"],
    "count": [50, 30, 25, 20, 15, 10, 8],
    "country": ["United States", "United Kingdom",
                "Germany", "France", "Japan", "Brazil", "Australia"],
})

world_map = WorldMap()
fig = world_map.make_graph(
    df=data,
    locations_col="country_code",
    color_col="count",
    hover_name_col="country",
    title="News Mentions by Country",
)


@st.dialog("Country Details")
def show_country_details(country, country_code, count):
    st.markdown(f"**Country:** {country}")
    st.markdown(f"**Code:** {country_code}")
    st.markdown(f"**Count:** {count}")


event = st.plotly_chart(fig, width='stretch', on_select="rerun", key="map")

if event and event.selection and event.selection.points:
    point = event.selection.points[0]
    idx = point["point_index"]
    row = data.row(idx)
    show_country_details(
        country=row[2],
        country_code=row[0],
        count=row[1],
    )
