import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from faicons import icon_svg
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
from shinywidgets import render_plotly, render_widget
from shiny.express import input, render, ui
from ipyleaflet import Map as IpylMap, GeoJSON as IpylGeoJSON
from ipywidgets import HTML
from ipyleaflet import Map, Marker, Popup, Polygon
#from shiny import reactive, ui
import plotly.graph_objects as go
from plotly.offline import init_notebook_mode, iplot
from plotly.io import to_html
# reusable chart functions
from pie_chart import pie_chart_from_column
from election_bar_chart import election_bar_chart
# num data functions
import num_data
from shiny import reactive, ui as classic_ui  # classic_ui.include_html

# === Load population data ===
df_pyr = pd.read_excel("../Input/2022.xlsx")
df_st = gpd.read_file("../Input/stadtteil.geojson")
bv = pd.read_csv("../Input/bevoelkerung.csv")
wa = pd.read_csv("../Input/wahlen.csv")
df_kos = pd.read_csv("../data/k5000.csv")



MAP_PATHS = {
    "btn_stadt":   r"../Input/Stadtteil.html",
    "btn_lage":    r"../Input/Pkte_Lage.html",
    "btn_kita":   r"../Input/Pkte_Kita.html",
    "btn_schule": r"../Input/Pkte_Schule.html",
    "btn_arzt":   r"../Input/Pkte_Arzt.html",
    "btn_opnv":   r"../Input/Pkte_Oepnv.html",
}



# Ensure WGS84 for leaflet
df_st = df_st.set_crs(epsg=25832).to_crs(epsg=4326)

# Coerce types defensively
if "Alter" in df_pyr.columns:
    df_pyr["Alter"] = pd.to_numeric(df_pyr["Alter"], errors="coerce")
for col in ["Männer", "Frauen"]:
    if col in df_pyr.columns:
        df_pyr[col] = pd.to_numeric(df_pyr[col], errors="coerce").fillna(0)
# Create reactive values to store clicked feature info

# === UI ===
ui.page_opts(title="Statistikdaten 2024 | Ludwigshafen am Rhein", fillable=True)

# ------------------------- Dashboard -----------------------------------

with ui.layout_columns(fill=False):

    # === Pyramid ===
    with ui.card(style="height: 700px;", full_screen=True):
        ui.card_header("Alterspyramide")

        @render.ui
        def alterspyramide():
            from plotly.io import to_html
            import plotly.graph_objects as go
            d = agg_by_age().copy()

            # Left side should be negative for Männer to mirror the pyramid
            d_plot = d.copy()
            d_plot["Männer"] = -d_plot["Männer"].abs()

            # Create the plot using Plotly
            fig = go.Figure()

            # Add Men data (left side, negative values)
            fig.add_trace(go.Bar(
                y=d_plot["Alter"],
                x=d_plot["Männer"]/1000,
                orientation='h',
                name='Männer',
                marker=dict(color='light blue'),
                hoverinfo='x+y+name',
                hovertemplate='<b>Männer</b><br>Alter: %{y}<br>Anzahl: %{x}<extra></extra>'
            ))

            # Add Women data (right side, positive values)
            fig.add_trace(go.Bar(
                y=d_plot["Alter"],
                x=d_plot["Frauen"]/1000,
                orientation='h',
                name='Frauen',
                marker=dict(color='pink'),
                hoverinfo='x+y+name',
                hovertemplate='<b>Frauen</b><br>Alter: %{y}<br>Anzahl: %{x}<extra></extra>'
            ))

            # Update layout for pyramid appearance
            fig.update_layout(
                barmode='overlay',
                yaxis=dict(
                    title='Alter in Jahren',
                    range=[0,100]  # Adjust range as needed
                ),
                xaxis=dict(
                    title='Anzahl',
                    # tickvals=[-150, -100, -50, 0, 50, 100, 150],
                   # ticktext=['150', '50', '0', '50', '150'],
                ),
                showlegend=True,
                #title="Bevölkerungspyramide",
                bargap=0.1,
                height=650,  # Set fixed height in pixels
                width=None  # Let width be responsive
            )

            # Convert to HTML and return as UI
            # Convert to HTML and wrap in responsive container
            html_content = to_html(fig, include_plotlyjs=True, config={'responsive': True})
            return ui.HTML(f'<div style="height: 100%; width: 100%;">{html_content}</div>')


            """
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

    # === REPLACED CARD: Combined Stadtteile and Lagekriterium ===
    with ui.card(style="height: 700px;"):
        ui.card_header("Stadtteile und Lagekriterium")

        # --- Buttons ---
        with ui.layout_columns(gap="0.5rem"):
            ui.input_action_button("btn_stadt", "Stadtteile Map")
            ui.input_action_button("btn_lage", "Pkte_Lage Map")
            ui.input_action_button("btn_kita", "Pkte_Kita Map")
            ui.input_action_button("btn_schule", "Pkte_Schule Map")
            ui.input_action_button("btn_arzt", "Pkte_Arzt Map")
            ui.input_action_button("btn_opnv", "Pkte_Oepnv Map")

        # --- Interactive Map ---
        @render_widget

        def lu_map():
            df_st_local = df_st
            map_center = [49.49, 8.4]
            m = IpylMap(center=map_center, zoom=12)

            # Prepare GeoJSON data with enhanced popup content
            geojson_data = df_st_local.__geo_interface__
            # print(geojson_data)
            # Define the district names and IDs from your example
            district_info = {
                "11": "Mitte",
                "12": "Süd",
                "13": "Nord",
                "14": "West",
                "15": "Friesenheim",
                "21": "Oppau",
                "22": "Edigheim",
                "23": "Pfingstweide",
                "31": "Oggersheim",
                "35": "Ruchheim",
                "41": "Maudach",
                "51": "Mundenheim",
                "52": "Rheingönheim",
                "BASF": "BASF"
            }

            # Add popup content to each feature in the GeoJSON data
            for feature in geojson_data['features']:
                properties = feature.get('properties', {})

                # Extract the specific fields
                name = properties.get("MIFSTADTT6", "Unbekannter Stadtteil")
                einwohner = properties.get("MIFSTADTT1", "k.A.")
                flaeche = properties.get("MIFSTADTT3", "k.A.")

                # Find district ID - FIXED: safer approach
                district_id = None
                for id, district_name in district_info.items():
                    # Use the full district name for matching
                    if district_name in name or name in district_name:
                        district_id = id
                        break
                                # If no match found, try partial matching
                if district_id is None:
                    for id, district_name in district_info.items():
                        # Extract main name part (before slash if exists)
                        main_name = district_name.split('/')[0].split()[0] if '/' in district_name else district_name.split()[0]
                        if main_name in name:
                            district_id = id
                            break



        # --- Reactive value for current map ---
        current_map = reactive.Value("btn_stadt")

        @reactive.Effect
        @reactive.event(input.btn_stadt)
        def _():
            current_map.set("btn_stadt")

        @reactive.Effect
        @reactive.event(input.btn_lage)
        def _():
            current_map.set("btn_lage")

        @reactive.Effect
        @reactive.event(input.btn_kita)
        def _():
            current_map.set("btn_kita")

        @reactive.Effect
        @reactive.event(input.btn_schule)
        def _():
            current_map.set("btn_schule")

        @reactive.Effect
        @reactive.event(input.btn_arzt)
        def _():
            current_map.set("btn_arzt")

        @reactive.Effect
        @reactive.event(input.btn_opnv)
        def _():
            current_map.set("btn_opnv")

        # --- Render HTML map ---
        @render.ui
        def map_container():
            key = current_map()
            # Add debug output to see what's happening
            print(f"Loading map with key: {key}")
            print(f"Available keys: {list(MAP_PATHS.keys())}")

            try:
                file_path = MAP_PATHS[key]
                print(f"Looking for file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                return ui.HTML(html_content)
            except KeyError:
                return ui.p(f"Key '{key}' not found in MAP_PATHS. Available keys: {list(MAP_PATHS.keys())}")
            except FileNotFoundError:
                return ui.p(f"File not found: {MAP_PATHS.get(key, 'Unknown key')}")
            except Exception as e:
                return ui.p(f"Error loading map: {str(e)}")


with ui.layout_columns(fill=False):

    with ui.card():
        ui.card_header("Bevölkerungsprognose")
        ui.p("Graph here")

        # === Reactive helpers ===
        @reactive.calc
        def filtered_rows():
            #Filter by selected Stadtteile if the column exists; else return all rows.
            d = df_pyr.copy()
            if "Stadtteil" in d.columns:
                sel = set(input.city_districts())
                d = d[d["Stadtteil"].isin(sel)]
            return d

        @reactive.calc
        def agg_by_age():

            # Aggregate Männer/Frauen by Alter across the selected Stadtteile.
            # If 'Stadtteil' doesn't exist, this just groups the whole table.

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