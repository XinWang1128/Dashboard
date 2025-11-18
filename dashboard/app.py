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

# reusable chart functions
from pie_chart import pie_chart_from_column
from election_bar_chart import election_bar_chart
# num data functions
import num_data
# === Load population data ===
# Expect columns: "Alter", "Männer", "Frauen", and optionally "Stadtteil"
df_pyr = pd.read_excel("../Input/2022.xlsx")
df_st = gpd.read_file("../Input/stadtteil.geojson")
bv = pd.read_csv("../Input/bevoelkerung.csv")
wa = pd.read_csv("../Input/wahlen.csv")
df_kos = pd.read_csv("../data/k5000.csv")
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
