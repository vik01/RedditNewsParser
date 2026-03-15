import plotly.graph_objects as go


class WorldMap:
    def __init__(self):
        self.projection = "natural earth"

    def make_graph(self, df,
                   locations_col,
                   color_col,
                   hover_name_col=None,
                   title="World Map"):
        fig = go.Figure(
            go.Choropleth(
                locations=df[locations_col],
                z=df[color_col],
                text=df[hover_name_col] if hover_name_col else None,
                colorscale="Viridis",
            )
        )
        fig.update_layout(
            title_text=title,
            geo=dict(
                projection_type=self.projection,
                showframe=False,
                showcoastlines=True,
                coastlinecolor="rgba(0,0,0,0.3)",
                landcolor="#d4e8d0",
                oceancolor="#a8d5e2",
                showocean=True,
                showland=True,
                showlakes=True,
                lakecolor="#a8d5e2",
                showcountries=True,
                countrycolor="rgba(0,0,0,0.2)",
            ),
            height=700,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        return fig
