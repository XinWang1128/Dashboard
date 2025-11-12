import seaborn as sns
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df, bv

from shiny import reactive
from shiny.express import input, render, ui

ui.page_opts(title="Ludwigshafen am Rhein - Dashboard", fillable=True)

with ui.sidebar(title="Filter"):

    ui.input_checkbox_group(
        "city_districts",
        "Stadtteile",
        ["Mitte", "Süd", "Nord/Hemshof", "West", "Friesenheim", "Gartenstadt", "Maudach", "Mundenheim", "Oggersheim", "Oppau", "Edigheim", "Pfingstweide", "Rheingönheim", "Ruchheim"],
        selected=["Mitte", "Süd", "Nord/Hemshof", "West", "Friesenheim", "Gartenstadt", "Maudach", "Mundenheim", "Oggersheim", "Oppau", "Edigheim", "Pfingstweide", "Rheingönheim", "Ruchheim"],
    )

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Ludwigshafen auf einen Blick")
        ui.p("Map here")

    with ui.card():  
        ui.card_header("Alterspyramide nach Migrationshintergrund")
        ui.p("Graph here")

with ui.layout_columns(fill=False):  
    with ui.card():  
        ui.card_header("Bevölkerungsprognose")
        ui.p("Graph here")

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Wohnberechtigte Bevölkerung"

        @render.text
        def count():
            return filtered_df().shape[0]

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Bevölkerung am Ort der Hauptwohnung"

        @render.text
        def bill_length():
            return f"{filtered_df()['bill_length_mm'].mean():.1f} mm"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Bevölkerung am Ort der Nebenwohnung"

        @render.text
        def bill_depth():
            return f"{filtered_df()['bill_depth_mm'].mean():.1f} mm"

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
            return "hellau2"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Durchschnittsalter in Jahren"

        @render.text
        def average_age():
            return "hellau3"

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Anzahl an Geburten"

        @render.text
        def num_births():
            return "hellau4"

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Anzahl an Sterbefällen"

        @render.text
        def num_deaths():
            return "hellau5"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Saldo Geburten und Sterbefälle"

        @render.text
        def saldo_birth_deaths():
            return "hellau6"

with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Zuzüge"

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
        ui.p("Tortendiagramm here")

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
 

ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_df():
    filt_df = df[df["species"].isin(input.species())]
    filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
    return filt_df


