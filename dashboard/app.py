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
from shiny import reactive

# reusable chart functions
from pie_chart import pie_chart_from_column
from election_bar_chart import election_bar_chart
# num data functions
import num_data
# === Load population data ===
df_pyr = pd.read_excel("../Input/2022.xlsx")
df_st = gpd.read_file("../Input/stadtteil.geojson")
bv = pd.read_csv("../Input/bevoelkerung.csv")
wa = pd.read_csv("../Input/wahlen.csv")
df_kos = pd.read_csv("../data/k5000.csv")
# Ensure WGS84 for leaflet
df_st = df_st.set_crs(epsg=25832).to_crs(epsg=4326)

# Coerce types defensively
if "Alter" in df_pyr.columns:
    df_pyr["Alter"] = pd.to_numeric(df_pyr["Alter"], errors="coerce")
for col in ["Männer", "Frauen"]:
    if col in df_pyr.columns:
        df_pyr[col] = pd.to_numeric(df_pyr[col], errors="coerce").fillna(0)
# Create reactive values to store clicked feature info
clicked_district = reactive.Value("")
clicked_einwohner = reactive.Value("")
clicked_flaeche = reactive.Value("")
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

            # Prepare GeoJSON data with enhanced popup content
            geojson_data = df_st_local.__geo_interface__

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


                # Create enhanced popup content as HTML string
                popup_content = f"""
                <div style='padding: 10px; min-width: 250px;'>
                    <h4 style='margin: 0 0 10px 0; color: #2c3e50;'>{name}</h4>
                    <div style='border-top: 1px solid #eee; padding-top: 8px;'>
                        <p style='margin: 5px 0;'><b>ID:</b> {district_id if district_id else 'N/A'}</p>
                        <p style='margin: 5px 0;'><b>Einwohner:</b> {einwohner}</p>
                        <p style='margin: 5px 0;'><b>Fläche:</b> {flaeche} ha</p>
                    </div>
                </div>
                """

                # Add popup to feature properties
                feature['properties']['popup'] = popup_content

                # Also add a simple tooltip property
                feature['properties']['tooltip'] = f"{district_id} {name}" if district_id else name

            # Updated click handler to update reactive values
            def handle_feature_click(event, feature, **kwargs):
                properties = feature.get("properties", {})
                name = properties.get("MIFSTADTT6", "Unbekannter Stadtteil")
                einwohner = properties.get("MIFSTADTT1", "k.A.")
                flaeche = properties.get("MIFSTADTT3", "k.A.")

                # Update reactive values
                clicked_district.set(name)
                clicked_einwohner.set(einwohner)
                clicked_flaeche.set(flaeche)

                # Still print to console for debugging
                print(f"Clicked: {name}; Fläche: {flaeche}; Einwohner: {einwohner}")

            # Hover handler to show polygon name
            def handle_feature_hover(event, feature, **kwargs):
                properties = feature.get("properties", {})
                name = properties.get("MIFSTADTT6", "Unbekannter Stadtteil")
                print(f"Hovering over: {name}")  # This will show in console
                # You could also update a UI element here to show the name

            # Create GeoJSON layer with your desired styling
            geo_layer = IpylGeoJSON(
                data=geojson_data,
                style={
                    "color": "#000",           # Stroke color - black
                    "weight": 1,               # Stroke width
                    "opacity": 0.5,            # Stroke opacity
                    "fillColor": "#c90000",    # Fill color - red
                    "fillOpacity": 0.7,        # Fill opacity
                },
                hover_style={
                    "color": "white",          # Hover stroke color
                    "weight": 3,               # Hover stroke width
                    "fillColor": "#ff4444",    # Hover fill color (lighter red)
                    "fillOpacity": 0.9,        # Hover fill opacity
                },
                # Enable popups
                popup_property=popup_content
            )



            # ================ Walder =====================

            # Fix attempt#1 Wir erstellen die Polygone so, wie leaflet es von uns will

            for feature in geojson_data['features']:
                print(feature['geometry']['coordinates'])
                district_polygon = Polygon(
                    locations=[feature['geometry']['coordinates']],
                    color="#000",
                    fill_color="#c90000"
                )
                m.add(district_polygon)

                message_pop = HTML()

                message_pop.value = feature['properties']['MIFSTADTT6']
                message_pop.placeholder = "Placeholder Test"
                message_pop.description = "DEscription test"

                district_polygon.popup = message_pop

            # ================ Walder =====================

            # Attach the feature click handler
            geo_layer.on_click(handle_feature_click)

            m.add_layer(geo_layer)

            return m

        # Display the selected district information
        @render.text
        def selected_district():
            if clicked_district():
                return f"""Ausgewählter Stadtteil: {clicked_district()};
        Einwohner: {clicked_einwohner()};
        Fläche: {clicked_flaeche()} ha"""
            else:
                return "Klicken Sie auf einen Stadtteil in der Karte, um Informationen anzuzeigen"
            # Right column - Selected district info and pyramid
            with ui.card():
                ui.card_header("Ausgewählter Stadtteil")

                @render.ui
                def selected_district():
                    if clicked_district():
                        return ui.TagList(
                            ui.h4(clicked_district()),
                            ui.p(ui.strong("Einwohner: "), clicked_einwohner()),
                            ui.p(ui.strong("Fläche: "), f"{clicked_flaeche()} ha"),
                            ui.hr()
                        )
                    else:
                        return ui.p("👆 Klicken Sie auf einen Stadtteil in der Karte, um Informationen anzuzeigen", style="color: #666;")


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


with ui.layout_columns(fill=False):

    with ui.card():
        ui.card_header("Bevölkerungsprognose")
        ui.p("Graph here")


# === KPIs ===

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Wohnberechtigte Bevölkerung"

        @render.text
        def population():
            return num_data.num_population(bv)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Bevölkerung am Ort der Hauptwohnung"

        @render.text
        def population_main():
            return num_data.num_population_main_household(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Bevölkerung am Ort der Nebenwohnung"

        @render.text
        def population_seconday():
            return num_data.num_population_secondary_household(df_kos)

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Frauenanteil in %"

        @render.text
        def population_female_percentage():
            return num_data.per_population_female(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Männeranteil in %"

        @render.text
        def population_male_percentage():
            return num_data.per_population_male(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittsalter in Jahren"

        @render.text
        def average_age():
            return num_data.num_population_average_age(df_kos)

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Anzahl an Geburten"

        @render.text
        def num_births():
            return num_data.num_population_births(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Anzahl an Sterbefällen"

        @render.text
        def num_deaths():
            return num_data.num_population_deaths(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Saldo Geburten und Sterbefälle"

        @render.text
        def saldo_birth_deaths():
            return num_data.diff_population_births_and_deaths(df_kos)

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Zuzüge"

        @render.text
        def moved_in():
            return num_data.num_population_moved_in(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Fortzüge"

        @render.text
        def moved_out():
            return num_data.num_population_moved_out(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Salo Zu- und Fortzüge"

        @render.text
        def saldo_moved():
            return num_data.diff_population_moved(df_kos)

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Familienstand")
        @render_plotly
        def family_pie():
            fig = pie_chart_from_column(bv, "Familienstand", top_n=8, title="")
            return fig

    with ui.card():  
        ui.card_header("Religionszugehörigkeit")
        @render_plotly
        def religion_pie():
            fig = pie_chart_from_column(df_kos, "Religion", top_n=8, title="")
            return fig

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Bevölkerung nach Migrationshintergrund")
        @render_plotly
        def pop_migra_pie():
            fig = pie_chart_from_column(bv, "Staatsangehörigkeit", top_n=8, title="")
            return fig
        
    with ui.card():  
        ui.card_header("Häufigstes Bezugsland von Personen mit Migrationshintergrund")
        @render_plotly
        def pop_migra_country_pie():
            fig = pie_chart_from_column(bv, "Staatsangehörigkeit", top_n=8, title="")
            return fig

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Privathaushalte")
        @render_plotly
        def pop_private_households():
            fig = pie_chart_from_column(bv, "Staatsangehörigkeit", top_n=8, title="")
            return fig
        
    with ui.card():  
        ui.card_header("Wohnungen")
        ui.p("Boxdiagramm here")

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Sinus-Milieus")
        @render_plotly
        def pop_sinus_milieus():
            fig = pie_chart_from_column(bv, "Staatsangehörigkeit", top_n=8, title="")
            return fig

    with ui.card():  
        ui.card_header("Gemeinderatswahl 2024")
        @render_plotly
        def election_test_bar():
            return election_bar_chart(wa, top_n=8, title="")


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Sozialversicherungspflichtig Beschäftigte"

        @render.text
        def insurance_workforce():
            return num_data.num_population_social_insurance_subject(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Beschäftigungsquote in %"

        @render.text
        def workforce_percentage():
            return num_data.per_population_with_jobs(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Arbeitslose absolut"

        @render.text
        def num_jobless():
            return num_data.num_population_no_jobs(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Arbeitslosenquotient in %"

        @render.text
        def jobless_percentage():
            return num_data.per_population_no_jobs(df_kos)

with ui.layout_column_wrap(fill=False):

    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Durchschnittliche Kaufkraft pro Person in Euro"

        @render.text
        def buying_average():
            return num_data.num_population_buying_average_person(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Kaufkraftindex pro Person"

        @render.text
        def buying_per_person():
            return num_data.num_population_buying_index_person(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittliche Kaufkraft pro Haushalt in Euro"

        @render.text
        def buying_average_households():
            return num_data.num_population_buying_average_household(df_kos)

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Kaufkraftindex pro Haushalt"

        @render.text
        def buying_index_households():
            return num_data.num_population_buying_index_household(df_kos)


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
