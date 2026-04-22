# plotly_charts.py — Graphiques interactifs Plotly pour GEX ANALYSER
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Couleurs theme dark finance
DARK_BG = "#090c10"
CARD_BG = "#0e1318"
BORDER = "#1e2d3d"
GREEN = "#00ff9d"
RED = "#ff3c5a"
ORANGE = "#ff9a00"
BLUE = "#00aaff"
TEXT = "#e8f0f7"
MUTED = "#5a7a94"

def plot_gex_curve(df_top, call_wall, put_wall, zero_gamma, title):
    """
    Graphique GEX interactif avec hover details
    """
    fig = go.Figure()

    # Remplissage vert/rouge sous la courbe
    fig.add_trace(go.Scatter(
        x=df_top["Strike"],
        y=df_top["GEX"],
        fill='tozeroy',
        fillcolor=f'rgba(0,255,157,0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        hoverinfo='skip',
        name=''
    ))

    # Courbe GEX principale
    fig.add_trace(go.Scatter(
        x=df_top["Strike"],
        y=df_top["GEX"],
        mode='lines+markers',
        name='GEX',
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=4, color=BLUE),
        hovertemplate=
            '<b>Strike: %{x:.0f}</b><br>' +
            'GEX: %{y:.3e}<br>' +
            '<extra></extra>',
        showlegend=True
    ))

    # Ligne zéro
    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, opacity=0.7)

    # Call Wall
    if isinstance(call_wall, (int, float)):
        fig.add_vline(x=call_wall, line_dash="dash", line_color=BLUE, opacity=0.7,
                     annotation_text=f"Call Wall<br>{int(call_wall)}", 
                     annotation_position="top right")

    # Put Wall
    if isinstance(put_wall, (int, float)):
        fig.add_vline(x=put_wall, line_dash="dash", line_color=RED, opacity=0.7,
                     annotation_text=f"Put Wall<br>{int(put_wall)}", 
                     annotation_position="top left")

    # Zero Gamma
    if zero_gamma:
        fig.add_vline(x=zero_gamma, line_dash="dash", line_color=ORANGE, opacity=0.8,
                     annotation_text=f"Zero Gamma<br>{zero_gamma}", 
                     annotation_position="top center")

    # Layout theme dark
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="IBM Plex Mono")),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        hovermode='x unified',
        xaxis=dict(
            title="Strike Price",
            titlefont=dict(color=MUTED, size=11),
            tickfont=dict(color=MUTED),
            gridcolor=BORDER,
            gridwidth=0.5,
            zeroline=False
        ),
        yaxis=dict(
            title="GEX",
            titlefont=dict(color=MUTED, size=11),
            tickfont=dict(color=MUTED),
            gridcolor=BORDER,
            gridwidth=0.5,
            zeroline=False
        ),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=10, color=TEXT, family="IBM Plex Mono")
        ),
        margin=dict(l=60, r=60, t=80, b=60),
        height=500,
        font=dict(family="IBM Plex Mono", color=TEXT, size=11)
    )

    return fig


def plot_iv_skew(df_calls, df_puts, atm_iv, skew_25, title):
    """
    IV Skew interactif avec courbes Calls/Puts
    """
    fig = go.Figure()

    # Courbe IV Calls
    fig.add_trace(go.Scatter(
        x=df_calls["Strike"],
        y=df_calls["IV"]*100,
        mode='lines+markers',
        name='IV Calls',
        line=dict(color=BLUE, width=2),
        marker=dict(size=3),
        hovertemplate='<b>Call Strike: %{x:.0f}</b><br>IV: %{y:.2f}%<extra></extra>'
    ))

    # Courbe IV Puts
    fig.add_trace(go.Scatter(
        x=df_puts["Strike"],
        y=df_puts["IV"]*100,
        mode='lines+markers',
        name='IV Puts',
        line=dict(color=RED, width=2, dash='dash'),
        marker=dict(size=3),
        hovertemplate='<b>Put Strike: %{x:.0f}</b><br>IV: %{y:.2f}%<extra></extra>'
    ))

    # ATM
    fig.add_vline(x=(df_calls["Strike"].min() + df_calls["Strike"].max())/2,
                 line_dash="dash", line_color=GREEN, opacity=0.6)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="IBM Plex Mono")),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        hovermode='x unified',
        xaxis=dict(title="Strike", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), gridcolor=BORDER),
        yaxis=dict(title="IV (%)", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), gridcolor=BORDER),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.3)", bordercolor=BORDER, borderwidth=1),
        margin=dict(l=60, r=60, t=80, b=60),
        height=450,
        font=dict(family="IBM Plex Mono", color=TEXT)
    )

    return fig


def plot_dex_curve(df_top_dex, delta_call_wall, delta_put_wall, zero_dex, title):
    """
    Delta Exposure interactif
    """
    fig = go.Figure()

    # Fill vert/rouge
    fig.add_trace(go.Scatter(
        x=df_top_dex["Strike"],
        y=df_top_dex["DEX_Total"],
        fill='tozeroy',
        fillcolor='rgba(0,255,157,0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Courbe DEX
    fig.add_trace(go.Scatter(
        x=df_top_dex["Strike"],
        y=df_top_dex["DEX_Total"],
        mode='lines+markers',
        name='DEX Total',
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=4),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>DEX: %{y:.3e}<extra></extra>'
    ))

    fig.add_hline(y=0, line_dash="dash", line_color=BORDER)

    if isinstance(delta_call_wall, (int, float)):
        fig.add_vline(x=delta_call_wall, line_dash="dash", line_color=BLUE, opacity=0.7)
    if isinstance(delta_put_wall, (int, float)):
        fig.add_vline(x=delta_put_wall, line_dash="dash", line_color=RED, opacity=0.7)
    if zero_dex:
        fig.add_vline(x=zero_dex, line_dash="dash", line_color=ORANGE, opacity=0.8)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="IBM Plex Mono")),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        hovermode='x unified',
        xaxis=dict(title="Strike", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), gridcolor=BORDER),
        yaxis=dict(title="Delta Exposure", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), gridcolor=BORDER),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.3)", bordercolor=BORDER, borderwidth=1),
        margin=dict(l=60, r=60, t=80, b=60),
        height=450,
        font=dict(family="IBM Plex Mono", color=TEXT)
    )

    return fig


def plot_volume_sentiment(by_s_total, title):
    """
    Sentiment volume (% calls vs puts)
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=by_s_total["Strike"],
        y=by_s_total["Bull_Score"]-0.5,
        base=0.5,
        marker=dict(
            color=by_s_total["Bull_Score"].apply(
                lambda x: GREEN if x > 0.6 else (RED if x < 0.4 else ORANGE)
            )
        ),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>% Calls: %{y:.1%}<extra></extra>',
        name='Volume Sentiment',
        showlegend=False
    ))

    fig.add_hline(y=0.5, line_dash="dash", line_color=BORDER)
    fig.add_hrect(y0=0.5, y1=1.0, fillcolor=GREEN, opacity=0.05, layer="below")
    fig.add_hrect(y0=0.0, y1=0.5, fillcolor=RED, opacity=0.05, layer="below")

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="IBM Plex Mono")),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        hovermode='x',
        xaxis=dict(title="Strike", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), gridcolor=BORDER),
        yaxis=dict(title="% Volume Calls", titlefont=dict(color=MUTED), tickfont=dict(color=MUTED), 
                  range=[0, 1], tickformat=".0%", gridcolor=BORDER),
        margin=dict(l=60, r=60, t=80, b=60),
        height=450,
        font=dict(family="IBM Plex Mono", color=TEXT)
    )

    return fig


def plot_expected_move_term_structure(df_em_valid, title):
    """
    Term structure de l'Expected Move
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_em_valid["T_days"],
        y=df_em_valid["em_sel"],
        mode='lines+markers',
        name='EM réel',
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=6, color=ORANGE),
        hovertemplate='<b>%{x} jours</b><br>EM: ±%{y:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="IBM Plex Mono")),
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        hovermode='x unified',
        xaxis=dict(title="Jours avant expiration", titlefont=dict(color=MUTED), 
                  tickfont=dict(color=MUTED), gridcolor=BORDER),
        yaxis=dict(title="Expected Move ($)", titlefont=dict(color=MUTED), 
                  tickfont=dict(color=MUTED), gridcolor=BORDER),
        margin=dict(l=60, r=60, t=80, b=60),
        height=450,
        font=dict(family="IBM Plex Mono", color=TEXT)
    )

    return fig
