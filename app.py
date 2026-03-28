import json
import streamlit as st
import polars as pl
from maps import WorldMap

st.set_page_config(layout="wide")
st.title("News Bot")

# ISO-2 to ISO-3 mapping for plotly choropleth
ISO2_TO_ISO3 = {
    "us": "USA", "ca": "CAN", "es": "ESP", "co": "COL",
    "mx": "MEX", "in": "IND", "ch": "CHE", "cn": "CHN",
}

ISO2_TO_NAME = {
    "us": "United States of America", "ca": "Canada", "es": "Spain",
    "co": "Colombia", "mx": "Mexico", "in": "India",
    "ch": "Switzerland", "cn": "China",
}

# Load summaries
with open("summaries.json", "r") as f:
    summaries = json.load(f)

# Build dataframe from summaries
rows = []
for country_code, categories in summaries.items():
    total_categories = sum(
        1 for v in categories.values() if v is not None)
    rows.append({
        "country_code_2": country_code,
        "country_code": ISO2_TO_ISO3.get(country_code, country_code.upper()),
        "country": ISO2_TO_NAME.get(country_code, country_code),
        "categories_covered": total_categories,
    })

data = pl.DataFrame(rows)

world_map = WorldMap()
fig = world_map.make_graph(
    df=data,
    locations_col="country_code",
    color_col="categories_covered",
    hover_name_col="country",
    title="News Summaries by Country",
)


@st.dialog("Country News Summaries", width="large")
def show_country_details(country, country_code_2):
    st.markdown(f"## {country}")
    categories = summaries.get(country_code_2, {})
    if not categories:
        st.info("No summaries available for this country.")
        return
    for category, summary in categories.items():
        st.markdown(f"### {category.capitalize()}")
        if summary is None:
            st.warning("No summary for this category.")
        else:
            st.markdown(summary)
        st.divider()


event = st.plotly_chart(fig, width='stretch', on_select="rerun", key="map")

if event and event.selection and event.selection.points:
    point = event.selection.points[0]
    idx = point["point_index"]
    row = data.row(idx, named=True)
    show_country_details(
        country=row["country"],
        country_code_2=row["country_code_2"],
    )
