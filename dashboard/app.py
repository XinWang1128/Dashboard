import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from faicons import icon_svg
import plotly.express as px
import plotly.graph_objects as go
from shiny import reactive
from shiny.express import input, render, ui
# ⬇️ add these imports for the map
from shinywidgets import render_plotly, output_widget, render_widget
from ipyleaflet import Map


# === Load population data ===
# Expect columns: "Alter", "Männer", "Frauen", and optionally "Stadtteil"
df_pyr = pd.read_excel("../Input/2022.xlsx")
bv = pd.read_csv("../Input/bevoelkerung.csv")

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
        # output_widget("lu_map")

#  ------------------------- Server / Map logic ---------------------------

        @render_widget
        def lu_map():
            # Approx center of Ludwigshafen am Rhein
            center = (49.4774, 8.4452)
            # Simple ipyleaflet map; you can add layers/markers later
            m = Map(center=center, zoom=12)
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

### ^^^ Wang ^^^ ###
### vvv Walder vvv ###

with ui.layout_column_wrap(fill=False):
    
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Wohnberechtigte Bevölkerung"

        @render.text
        def kpi_total():
            d = agg_by_age()
            total = int((d["Männer"].abs() + d["Frauen"]).sum())
            return f"{total:,}".replace(",", ".")
        
    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Bevölkerung am Ort der Hauptwohnung"

        @render.text
        def bill_length():
            return "test"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Bevölkerung am Ort der Nebenwohnung"

        @render.text
        def bill_depth():
            return "test"

with ui.layout_column_wrap(fill=False):

    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Frauenanteil in %"

        @render.text
        def population_female_percentage():
            total = bv.shape[0]
            if total == 0:
                return "Keine Daten"
            women = bv[bv["Geschlecht"] == "w"].shape[0]
            return f"{(women / total * 100):.1f} %"

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Männeranteil in %"

        @render.text
        def population_male_percentage():
            total = bv.shape[0]
            if total == 0:
                return "Keine Daten"
            women = bv[bv["Geschlecht"] == "m"].shape[0]
            return f"{(women / total * 100):.1f} %"
 

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittsalter in Jahren"

        @render.text
        def age_average():
            return f"{bv['Alter'].mean():.1f} Jahre"


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


        @render.text
        def moved_in():
            return "hellau7"

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Fortzüge"

        @render.text
        def moved_out():
            return "hellau8"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Salo Zu- und Fortzüge"

        @render.text
        def saldo_moved():
            return "hellau9"

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Familienstand")
        ui.p("Tortendiagramm here")

    with ui.card():  
        ui.card_header("Religionszugehörigkeit")
        @render_plotly
        def religion_pie_plot():
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            # this function needs to be replaced with the common religion codes we use
            # defensive checks
            if "Religion" not in bv.columns or bv.shape[0] == 0:
                fig = go.Figure()
                fig.update_layout(title="Keine Religion-Daten verfügbar")
                return fig

            counts = bv["Religion"].fillna("keine Angabe").value_counts()

            # limit to Top N, smaller religions will be summed up in "Andere"
            top_n = 8
            if len(counts) > top_n:
                top = counts.nlargest(top_n)
                others = counts.drop(top.index).sum()
                counts = top.append(pd.Series({"Andere": others}))

            # creating pie with potly
            fig = px.pie(
                names=counts.index,
                values=counts.values,
                title="",
            )
            fig.update_traces(textinfo="percent+label", textposition="inside")
            fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), legend_title_text=None)

            return fig


with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Bevölkerung nach Migrationshintergrund")
        ui.p("Tortendiagramm here")

    with ui.card():  
        ui.card_header("Häufigstes Bezugsland von Personen mit Migrationshintergrund")
        ui.p("Tortendiagramm here")

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Privathaushalte")
        ui.p("Tortendiagramm here")

    with ui.card():  
        ui.card_header("Wohnungen")
        ui.p("Boxdiagramm here")

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Sinus-Milieus")
        ui.p("Tortendiagramm here")

    with ui.card():  
        ui.card_header("Gemeinderatswahl 2024")
        ui.p("Balkendiagramm here")

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Sozialversicherungspflichtig Beschäftigte"

        @render.text
        def insurance_workforce():
            return "hellau7"

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Beschäftigungsquote in %"

        @render.text
        def workforce_percentage():
            return "hellau8"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Arbeitslose absolut"

        @render.text
        def num_jobless():
            return "hellau9"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Arbeitslosenquotient in %"

        @render.text
        def jobless_percentage():
            return "hellau9"

with ui.layout_column_wrap(fill=False):

    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Durchschnittliche Kaufkraft pro Person in Euro"

        @render.text
        def buying_average():
            return "hellau7"

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Kaufkraftindex pro Person"

        @render.text
        def buying_per_person():
            return "hellau8"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittliche Kaufkraft pro Haushalt in Euro"

        @render.text
        def buying_average_households():
            return "hellau9"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Kaufkraftindex pro Haushalt"

        @render.text
        def buying_index_households():
            return "hellau9"
 


ui.include_css("styles.css")

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

