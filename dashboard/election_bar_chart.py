import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def election_bar_chart(
    df,
    party_col="Partei",
    value_col=None,
    top_n=12,
    title="Wahlergebnis"
):
    """
    df: Pandas DataFrame 
    party_col: Spalte für Parteinamen
    value_col: Spalte mit Stimmen / Prozenten.
               Wenn None: automatische Erkennung
    top_n: Anzahl sichtbarer Parteien
    title: Charttitel, auf app.py immer mit leerem String ersetzen weil bereits eine Box mit TItel vorhanden
    """

    if party_col not in df.columns or df.shape[0] == 0:
        fig = go.Figure()
        fig.update_layout(title=f"Keine Daten für {party_col} verfügbar")
        return fig

    # value_col 
    if value_col is None:
        candidates = ["Stimmen_Prozent", "Stimmen", "Prozent", "Votes", "Anzahl"]
        found = [c for c in candidates if c in df.columns]
        if found:
            value_col = found[0]
        else:
            nums = [c for c in df.columns if c != party_col and pd.api.types.is_numeric_dtype(df[c])]
            value_col = nums[0] if nums else None

    if value_col is None or value_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Keine geeignete Wertespalte gefunden")
        return fig

    # Copy + Cleanup
    d = df[[party_col, value_col]].copy()
    d[party_col] = d[party_col].fillna("keine Angabe")
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce").fillna(0)

    # Prozent-Check (Heuristik)
    is_percent = (
        "prozent" in value_col.lower() or 
        (0 < d[value_col].max() <= 100)
    )

    # Sortieren
    d = d.sort_values(by=value_col, ascending=False).reset_index(drop=True)

    # Top N + "Andere"
    if d.shape[0] > top_n:
        top = d.iloc[:top_n]
        others_sum = d.iloc[top_n:][value_col].sum()
        d_plot = pd.concat([
            top,
            pd.DataFrame([{party_col: "Andere", value_col: others_sum}])
        ], ignore_index=True)
    else:
        d_plot = d


    # Plotly Bar
    fig = px.bar(
        d_plot,
        x=party_col,
        y=value_col,
        text=value_col,
        labels={party_col: "Partei", value_col: ("Prozent" if is_percent else "Stimmen")},
    )

    # Labels formatieren
    if is_percent:
        d_plot["_text"] = d_plot[value_col].map(lambda v: f"{v:.1f} %")
        fig.update_traces(text=d_plot["_text"], textposition="outside")
        fig.update_layout(yaxis=dict(ticksuffix=" %"))
    else:
        d_plot["_text"] = d_plot[value_col].map(lambda v: f"{int(v):,}".replace(",", "."))
        fig.update_traces(text=d_plot["_text"], textposition="outside")
        fig.update_layout(yaxis_tickformat=",")

    fig.update_layout(
        margin=dict(t=40, b=40, l=10, r=10),
        xaxis_tickangle=-30,
        showlegend=False,
    )

    return fig
