import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from faicons import icon_svg
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from shinywidgets import render_plotly, output_widget, render_widget
from ipyleaflet import Map
from shiny import reactive, render, ui
from shiny.express import input, render, ui
from ipyleaflet import Map, GeoJSON
import folium
from folium import GeoJson
from ipyleaflet import Map as IpylMap, GeoJSON as IpylGeoJSON, Popup
from shinywidgets import output_widget, render_widget
from ipywidgets import HTML

# === Load population data ===
df_pyr = pd.read_excel("../Input/2022.xlsx")
df_st = gpd.read_file("../Input/stadtteil.geojson")
bv = pd.read_csv("../Input/bevoelkerung.csv")

# Ensure WGS84 for leaflet
df_st = df_st.set_crs(epsg=25832).to_crs(epsg=4326)

# Coerce types defensively
if "Alter" in df_pyr.columns:
    df_pyr["Alter"] = pd.to_numeric(df_pyr["Alter"], errors="coerce")
for col in ["Männer", "Frauen"]:
    if col in df_pyr.columns:
        df_pyr[col] = pd.to_numeric(df_pyr[col], errors="coerce").fillna(0)

# === UI ===
ui.page_opts(title="Ludwigshafen am Rhein - Dashboard", fillable=True)

# ------------------------- Dashboard -----------------------------------

with ui.layout_columns(fill=False):
    with ui.card():
        ui.card_header("Ludwigshafen Stadtteile")

        @render_widget
        def lu_map():
            df_st_local = df_st
            map_center = [49.48, 8.44]
            m = IpylMap(center=map_center, zoom=11)

            # Prepare GeoJSON data
            geojson_data = df_st_local.__geo_interface__

            # Click handler
            def handle_feature_click(event, feature, **kwargs):
                # If you don't want console output, just delete these two lines
                # print("Event:", event)
                # print("Feature properties:", feature.get("properties", {}))

                properties = feature.get("properties", {})

                name = properties.get("MIFSTADTT6", "Unbekannter Stadtteil")
                einwohner = properties.get("MIFSTADTT1", "k.A.")
                flaeche = properties.get("MIFSTADTT3", "k.A.")
                print(f"Clicked: {name}; Fläche: {flaeche}; Einwohner: {einwohner}")
                # event["coordinates"] is (lon, lat) in GeoJSON
                lon, lat = event["coordinates"]
                coordinates = (lat, lon)  # Leaflet wants (lat, lon)

                html_content = HTML(
                    f"<div style='padding: 10px; min-width: 200px;'>"
                    f"<h4 style='margin: 0 0 10px 0; color: #2c3e50;'>{name}</h4>"
                    f"<div style='border-top: 1px solid #eee; padding-top: 8px;'>"
                    f"<p style='margin: 5px 0;'><b>Einwohner:</b> {einwohner}</p>"
                    f"<p style='margin: 5px 0;'><b>Fläche:</b> {flaeche} ha</p>"
                    f"</div>"
                    f"</div>"
                )

                # Remove previous popups
                for layer in list(m.layers):
                    if isinstance(layer, Popup):
                        m.remove_layer(layer)

                popup = Popup(
                    location=coordinates,
                    child=html_content,
                    close_button=True,
                    auto_close=True,
                )
                m.add_layer(popup)

            # Create GeoJSON layer
            geo_layer = IpylGeoJSON(
                data=geojson_data,
                style={
                    "color": "blue",
                    "weight": 2,
                    "fillColor": "lightblue",
                    "fillOpacity": 0.5,
                },
                hover_style={
                    "fillColor": "orange",
                    "fillOpacity": 0.7,
                    "weight": 3,
                },
            )

            # Attach the feature click handler to the GeoJSON layer
            geo_layer.on_click(handle_feature_click)

            m.add_layer(geo_layer)
            return m

# === Pyramid ===
    with ui.card(full_screen=True):
        ui.card_header("Alterspyramide")

        @render.plot
        def alterspyramide():
            d = agg_by_age().copy()

            # Left side should be negative for Männer to mirror the pyramid
            d_plot = d.copy()
            d_plot["Männer"] = -d_plot["Männer"].abs()

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.barh(d_plot["Alter"], d_plot["Männer"], label="Männer")
            ax.barh(d_plot["Alter"], d_plot["Frauen"], label="Frauen")

            ax.set_xlabel("Bevölkerungszahl")
            ax.set_ylabel("Alter")
            ax.set_title("Bevölkerungspyramide")
            ax.legend()

            # Symmetric x-limits
            max_val = max(d_plot["Frauen"].max(), abs(d_plot["Männer"].min()))
            ax.set_xlim(-max_val, max_val)

            # Show positive tick labels only
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{abs(int(x)):,}".replace(",", "."))
            )

            # Optional: youngest at bottom (classic pyramid look)
            #ax.invert_yaxis()

            fig.tight_layout()
            return fig





















"""
with ui.sidebar(title="Filter"):
    ui.input_checkbox_group(
        "city_districts",
        "Stadtteile",
        [
            "Mitte", "Süd", "Nord/Hemshof", "West", "Friesenheim",
            "Gartenstadt", "Maudach", "Mundenheim", "Oggersheim",
            "Oppau", "Edigheim", "Pfingstweide", "Rheingönheim", "Ruchheim",
        ],
        selected=[
            "Mitte", "Süd", "Nord/Hemshof", "West", "Friesenheim",
            "Gartenstadt", "Maudach", "Mundenheim", "Oggersheim",
            "Oppau", "Edigheim", "Pfingstweide", "Rheingönheim", "Ruchheim",
        ],
    )
"""

with ui.layout_columns(fill=False):

    with ui.card():
        ui.card_header("Bevölkerungsprognose")
        ui.p("Graph here")


# === KPIs ===
with ui.layout_column_wrap(fill=False):

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittsalter in Jahren"

        @render.text
        def kpi_avg_age():
            d = agg_by_age()
            if d.empty or d["Alter"].isna().all():
                return "–"
            weights = (d["Männer"].abs() + d["Frauen"]).values
            ages = d["Alter"].values
            wsum = weights.sum()
            avg = np.nan if wsum == 0 else float((ages * weights).sum() / wsum)
            return f"{avg:.1f}"


# === Styling (optional) ===
# ui.include_css(app_dir / "styles.css")  # Uncomment if you have styles.css

# === Reactive helpers ===
@reactive.calc
def filtered_rows():
    """Filter by selected Stadtteile if the column exists; else return all rows."""
    d = df_pyr.copy()
    if "Stadtteil" in d.columns:
        sel = set(input.city_districts())
        d = d[d["Stadtteil"].isin(sel)]
    return d

@reactive.calc
def agg_by_age():
    """
    Aggregate Männer/Frauen by Alter across the selected Stadtteile.
    If 'Stadtteil' doesn't exist, this just groups the whole table.
    """
    d = filtered_rows()
    required = {"Alter", "Männer", "Frauen"}
    missing = required - set(d.columns)
    if missing:
        # Graceful empty frame if columns are missing
        return pd.DataFrame(columns=["Alter", "Männer", "Frauen"])
    g = (
        d.groupby("Alter", as_index=False)[["Männer", "Frauen"]]
        .sum(numeric_only=True)
        .sort_values("Alter")
    )
    # Clean NaNs
    g[["Männer", "Frauen"]] = g[["Männer", "Frauen"]].fillna(0)
    return g
