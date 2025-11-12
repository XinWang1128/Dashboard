import seaborn as sns
from faicons import icon_svg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Import data from shared.py
from shared import app_dir, df

from shiny import reactive
from shiny.express import input, render, ui


# ---- NEW: load population data for the pyramid (separate name to avoid clashing) ----
df_pyr = pd.read_excel("C:/Users/24634/Desktop/Dashboard/Dashboard/Input/2022.xlsx")


ui.page_opts(title="Penguins dashboard", fillable=True)


with ui.sidebar(title="Filter controls"):
    ui.input_slider("mass", "Mass", 2000, 6000, 6000)
    ui.input_checkbox_group(
        "species",
        "Species",
        ["Adelie", "Gentoo", "Chinstrap"],
        selected=["Adelie", "Gentoo", "Chinstrap"],
    )


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Number of penguins"

        @render.text
        def count():
            return filtered_df().shape[0]

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Average bill length"

        @render.text
        def bill_length():
            return f"{filtered_df()['bill_length_mm'].mean():.1f} mm"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Average bill depth"

        @render.text
        def bill_depth():
            return f"{filtered_df()['bill_depth_mm'].mean():.1f} mm"


with ui.layout_columns():

    with ui.card(full_screen=True):
        ui.card_header("Penguin data")

        @render.data_frame
        def summary_statistics():
            cols = [
                "species",
                "island",
                "bill_length_mm",
                "bill_depth_mm",
                "body_mass_g",
            ]
            return render.DataGrid(filtered_df()[cols], filters=True)

    with ui.card(full_screen=True):
        ui.card_header("Alterspyramide")

        @render.plot
        def alterspyramide():
            d = df_pyr.copy()
            # negative for left side (men)
            d["Männer"] = -d["Männer"]

            fig, ax = plt.subplots(figsize=(10, 8))
            ax.barh(d["Alter"], d["Männer"], label="Männer", color="steelblue")
            ax.barh(d["Alter"], d["Frauen"], label="Frauen", color="lightcoral")

            ax.set_xlabel("Bevölkerungszahl")
            ax.set_ylabel("Alter")
            ax.set_title("Bevölkerungspyramide")
            ax.legend()

            # symmetric x-limits
            max_val = max(d["Frauen"].max(), abs(d["Männer"].min()))
            ax.set_xlim(-max_val, max_val)

            # show positive tick labels only
            ax.xaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{abs(int(x)):,}")
            )

            # optional: classic pyramid look (youngest at bottom)
            # ax.invert_yaxis()

            plt.tight_layout()
            return fig




ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_df():
    filt_df = df[df["species"].isin(input.species())]
    filt_df = filt_df.loc[filt_df["body_mass_g"] < input.mass()]
    return filt_df
