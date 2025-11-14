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
from shiny import reactive
from shiny.express import input, render, ui
from ipyleaflet import Map, GeoJSON
import folium

# === Load population data ===
# Expect columns: "Alter", "Männer", "Frauen", and optionally "Stadtteil"
df_pyr = pd.read_excel("../Input/2022.xlsx")
df_st = gpd.read_file("../Input/stadtteil.geojson")
bv = pd.read_csv("../Input/bevoelkerung.csv")

# Ensure WGS84 for leaflet
if df_st.crs is not None and df_st.crs.to_epsg() != 4326:
    df_st = df_st.to_crs(epsg=4326)


# Coerce types defensively
if "Alter" in df_pyr.columns:
    df_pyr["Alter"] = pd.to_numeric(df_pyr["Alter"], errors="coerce")
for col in ["Männer", "Frauen"]:
    if col in df_pyr.columns:
        df_pyr[col] = pd.to_numeric(df_pyr[col], errors="coerce").fillna(0)

# === UI ===

ui.page_opts(title="Ludwigshafen am Rhein - Dashboard", fillable=True)

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


# ------------------------- Dashboard -----------------------------------

# Ludwigshafen Map
with ui.layout_columns(fill=False):
    with ui.card():
        ui.card_header("Ludwigshafen Stadtteil")
        #output_widget("lu_map")

#  ------------------------- Server / Map logic ---------------------------

        @render_widget
        def lu_map():
        # Center roughly over Ludwigshafen
            m = Map(center=(49.48, 8.44), zoom=12)

            # Add the GeoJSON layer from GeoDataFrame
            geo_layer = GeoJSON(
                data=df_st.__geo_interface__,   # or: json.loads(df_st.to_json())
                name="Stadtteile",
                style={
                    "color": "blue",
                    "weight": 2,
                    "fillOpacity": 0.1,
                },
                hover_style={
                    "color": "red",
                    "weight": 3,
                },
            )

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

with ui.layout_columns(fill=False):

    with ui.card():
        ui.card_header("Bevölkerungsprognose")
        ui.p("Graph here")


# === KPIs ===
with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Wohnberechtigte Bevölkerung"

        @render.text
        def kpi_total():
            d = agg_by_age()
            total = int((d["Männer"].abs() + d["Frauen"]).sum())
            return f"{total:,}".replace(",", ".")

    with ui.value_box(showcase=icon_svg("genderless")):
        "Frauenanteil in %"

        @render.text
        def kpi_female_share():
            d = agg_by_age()
            total = (d["Männer"].abs() + d["Frauen"]).sum()
            female = d["Frauen"].sum()
            pct = 0 if total == 0 else (female / total) * 100
            return f"{pct:.1f} %"

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
