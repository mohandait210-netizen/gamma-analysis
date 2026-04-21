# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import math
from datetime import datetime
from pathlib import Path
from scipy.stats import norm as sp_norm

# ===========================================================
#  PAGE CONFIG
# ===========================================================
st.set_page_config(
    page_title="GEX Analyser",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
#  COLORS
# ============================================================
DARK_BG     = "#090c10"
CARD_BG     = "#0e1318"
BORDER      = "#1e2d3d"
GREEN       = "#00ff9d"
RED         = "#ff3c5a"
ORANGE      = "#ff9a00"
BLUE        = "#00aaff"
TEXT        = "#e8f0f7"
MUTED       = "#5a7a94"

# ============================================================
#  PLOTLY TEMPLATE
# ============================================================
def get_plotly_layout():
    return dict(
        template="plotly_dark",
        paper_bgcolor=DARK_BG,
        plot_bgcolor=CARD_BG,
        font=dict(family="monospace", color=TEXT, size=11),
        hovermode="x unified",
        margin=dict(l=50, r=30, t=50, b=50),
        xaxis=dict(
            color=MUTED,
            showgrid=True,
            gridwidth=0.5,
            gridcolor=BORDER,
        ),
        yaxis=dict(
            color=MUTED,
            showgrid=True,
            gridwidth=0.5,
            gridcolor=BORDER,
        ),
        legend=dict(
            bgcolor="rgba(14,19,24,0.8)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=9),
        ),
    )

# ============================================================
#  Helper: safe vertical line + annotation
# ============================================================
def format_label(prefix: str, val):
    try:
        if val is None:
            return None
        # convert numpy types
        if isinstance(val, (np.generic,)):
            val = float(val)
        v = float(val)
        if math.isnan(v) or math.isinf(v):
            return None
        return f"{prefix} ({int(round(v))})"
    except Exception:
        return None

def safe_add_vline(fig, x_val, color=ORANGE, width=2, dash="dash", text=None, text_xanchor="right"):
    """
    Add vertical line safely: ignores None/NaN/inf and avoids invalid annotation formatting.
    Uses add_shape + add_annotation (more robust than add_vline with annotation_text on some versions).
    """
    try:
        if x_val is None:
            return
        if isinstance(x_val, (np.generic,)):
            x_val = float(x_val)
        x_f = float(x_val)
        if math.isnan(x_f) or math.isinf(x_f):
            return
    except Exception:
        return

    # Add vertical line spanning paper coords
    fig.add_shape(
        type="line",
        x0=x_f, x1=x_f,
        y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=color, width=width, dash=dash),
        layer="above"
    )
    if text:
        # place annotation just above the top of the plotting area
        fig.add_annotation(
            x=x_f, y=1.02,
            xref="x", yref="paper",
            text=str(text),
            showarrow=False,
            xanchor=text_xanchor,
            yanchor="bottom",
            font=dict(color=color, size=11),
            bgcolor="rgba(0,0,0,0)",
        )

# ============================================================
#  PLOTLY CHART FUNCTIONS (use safe_add_vline for vlines)
# ============================================================

def plot_gex_curve(df_top_abs, call_wall, put_wall, zero_gamma, title):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_top_abs["Strike"],
        y=df_top_abs["GEX"],
        mode='lines+markers',
        line=dict(color=BLUE, width=2),
        marker=dict(size=5),
        name='GEX',
        hovertemplate='<b>Strike: %{x:.0f}</b><br>GEX: %{y:.2e}<extra></extra>'
    ))

    # fills
    pos = df_top_abs[df_top_abs["GEX"] >= 0]
    neg = df_top_abs[df_top_abs["GEX"] < 0]
    if not pos.empty:
        fig.add_trace(go.Scatter(
            x=pos["Strike"], y=pos["GEX"],
            fill='tozeroy', fillcolor='rgba(0,255,157,0.15)',
            line=dict(color='rgba(0,0,0,0)'), hoverinfo='skip', name='GEX Positif'
        ))
    if not neg.empty:
        fig.add_trace(go.Scatter(
            x=neg["Strike"], y=neg["GEX"],
            fill='tozeroy', fillcolor='rgba(255,60,90,0.15)',
            line=dict(color='rgba(0,0,0,0)'), hoverinfo='skip', name='GEX Negatif'
        ))

    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)

    safe_add_vline(fig, call_wall, color=BLUE, width=2, dash="dash",
                   text=format_label("Call Wall", call_wall), text_xanchor="left")
    safe_add_vline(fig, put_wall, color=RED, width=2, dash="dash",
                   text=format_label("Put Wall", put_wall), text_xanchor="right")
    safe_add_vline(fig, zero_gamma, color=ORANGE, width=2, dash="dash",
                   text=f"Zero Γ ({zero_gamma})" if zero_gamma is not None else None, text_xanchor="center")

    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike Price",
        yaxis_title="GEX",
        height=550,
    )
    return fig

def plot_calls_vs_puts(df_comp, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_comp['Strike'],
        y=df_comp['GEX_Calls'],
        name='GEX Calls',
        marker=dict(color=BLUE),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>Calls: %{y:.2e}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=df_comp['Strike'],
        y=df_comp['GEX_Puts'],
        name='GEX Puts',
        marker=dict(color=RED),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>Puts: %{y:.2e}<extra></extra>'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)
    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike",
        yaxis_title="GEX",
        barmode='group',
        height=550,
    )
    return fig

def plot_iv_skew(df_c, df_p, atm, atm_iv, skew_25, title):
    fig = go.Figure()
    df_c_s = df_c.sort_values("Strike") if not df_c.empty else df_c
    df_p_s = df_p.sort_values("Strike") if not df_p.empty else df_p

    if not df_c_s.empty:
        fig.add_trace(go.Scatter(
            x=df_c_s["Strike"],
            y=df_c_s["IV"]*100,
            mode='lines+markers',
            line=dict(color=BLUE, width=2),
            marker=dict(size=5),
            name='IV Calls',
            fill='tozeroy',
            fillcolor='rgba(0,170,255,0.1)',
            hovertemplate='<b>Strike: %{x:.0f}</b><br>IV: %{y:.2f}%<extra></extra>'
        ))
    if not df_p_s.empty:
        fig.add_trace(go.Scatter(
            x=df_p_s["Strike"],
            y=df_p_s["IV"]*100,
            mode='lines+markers',
            line=dict(color=RED, width=2, dash='dash'),
            marker=dict(size=5),
            name='IV Puts',
            fill='tozeroy',
            fillcolor='rgba(255,60,90,0.1)',
            hovertemplate='<b>Strike: %{x:.0f}</b><br>IV: %{y:.2f}%<extra></extra>'
        ))

    safe_add_vline(fig, atm, color=GREEN, width=2, dash="dash",
                   text=format_label("ATM", atm))

    if atm_iv is not None:
        fig.add_annotation(
            x=atm, y=(atm_iv*100 if atm_iv is not None else None),
            text=f"Skew 25d: {skew_25*100:+.2f}%",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor=ORANGE,
            ax=40, ay=-40, font=dict(color=ORANGE, size=11),
            bgcolor="rgba(255,154,0,0.1)", bordercolor=ORANGE, borderwidth=1
        )

    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike Price",
        yaxis_title="Implied Volatility (%)",
        height=550,
    )
    return fig

def plot_dex_curve(df_top_dex, delta_call_wall, delta_put_wall, zero_dex, title):
    fig = go.Figure()
    if not df_top_dex.empty:
        fig.add_trace(go.Scatter(
            x=df_top_dex["Strike"],
            y=df_top_dex["DEX_Total"],
            mode='lines+markers',
            line=dict(color=BLUE, width=2),
            marker=dict(size=5),
            name='DEX Total',
            hovertemplate='<b>Strike: %{x:.0f}</b><br>DEX: %{y:.2e}<extra></extra>'
        ))

        pos = df_top_dex[df_top_dex["DEX_Total"] >= 0]
        neg = df_top_dex[df_top_dex["DEX_Total"] < 0]
        if not pos.empty:
            fig.add_trace(go.Scatter(x=pos["Strike"], y=pos["DEX_Total"], fill='tozeroy',
                                     fillcolor='rgba(0,255,157,0.15)', line=dict(color='rgba(0,0,0,0)'),
                                     hoverinfo="skip", name='DEX Pos'))
        if not neg.empty:
            fig.add_trace(go.Scatter(x=neg["Strike"], y=neg["DEX_Total"], fill='tozeroy',
                                     fillcolor='rgba(255,60,90,0.15)', line=dict(color='rgba(0,0,0,0)'),
                                     hoverinfo="skip", name='DEX Neg'))

    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)

    safe_add_vline(fig, delta_call_wall, color=BLUE, width=2, dash="dash", text=format_label("Call Wall", delta_call_wall))
    safe_add_vline(fig, delta_put_wall, color=RED, width=2, dash="dash", text=format_label("Put Wall", delta_put_wall))
    safe_add_vline(fig, zero_dex, color=ORANGE, width=2, dash="dash", text=f"Zero DEX ({zero_dex})" if zero_dex else None)

    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike Price",
        yaxis_title="Delta Exposure (DEX)",
        height=550,
    )
    return fig

def plot_dex_calls_puts(df_comp, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_comp["Strike"],
        y=df_comp["DEX_Calls"],
        name='DEX Calls',
        marker=dict(color=BLUE),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>Calls: %{y:.2e}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=df_comp["Strike"],
        y=df_comp["DEX_Puts"],
        name='DEX Puts',
        marker=dict(color=RED),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>Puts: %{y:.2e}<extra></extra>'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)
    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike Price",
        yaxis_title="Delta Exposure (DEX)",
        height=550,
    )
    return fig

def plot_oi_chart(df_top_oi, max_call_strike, max_put_strike, max_oi_strike, title):
    fig = go.Figure()
    # Bars: use grouping by offsetting x values slightly (Plotly accepts numeric x)
    strikes = df_top_oi["Strike"].values
    oi_calls = df_top_oi["OI_Calls"].values
    oi_puts  = df_top_oi["OI_Puts"].values
    bw = 0.4

    fig.add_trace(go.Bar(
        x=strikes - bw/2,
        y=oi_calls,
        width=bw,
        name="OI Calls",
        marker=dict(color=BLUE),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>OI Calls: %{y:,.0f}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        x=strikes + bw/2,
        y=oi_puts,
        width=bw,
        name="OI Puts",
        marker=dict(color=RED),
        hovertemplate='<b>Strike: %{x:.0f}</b><br>OI Puts: %{y:,.0f}<extra></extra>'
    ))

    safe_add_vline(fig, max_call_strike, color=BLUE, width=2, dash="dash", text=format_label("Max Call OI", max_call_strike))
    safe_add_vline(fig, max_put_strike, color=RED, width=2, dash="dash", text=format_label("Max Put OI", max_put_strike))
    safe_add_vline(fig, max_oi_strike, color=ORANGE, width=2, dash="dash", text=format_label("Max Total OI", max_oi_strike))

    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike",
        yaxis_title="Open Interest",
        barmode='group',
        height=550,
    )
    return fig

def plot_charm_exposure(df_cv_top, spot_input, title):
    fig = go.Figure()
    colors_ch = [GREEN if v >= 0 else RED for v in df_cv_top["CharmEx"]]
    fig.add_trace(go.Bar(
        x=df_cv_top["Strike"],
        y=df_cv_top["CharmEx"],
        marker=dict(color=colors_ch),
        name='Charm Exposure',
        hovertemplate='<b>Strike: %{x:.0f}</b><br>CharmEx: %{y:.2e}<extra></extra>'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)
    safe_add_vline(fig, spot_input, color=ORANGE, width=2, dash="dash", text=f"Spot ({spot_input})")
    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike",
        yaxis_title="Charm Exposure",
        height=550,
    )
    return fig

def plot_vanna_exposure(df_cv_top, spot_input, title):
    fig = go.Figure()
    colors_va = [GREEN if v >= 0 else RED for v in df_cv_top["VannaEx"]]
    fig.add_trace(go.Bar(
        x=df_cv_top["Strike"],
        y=df_cv_top["VannaEx"],
        marker=dict(color=colors_va),
        name='Vanna Exposure',
        hovertemplate='<b>Strike: %{x:.0f}</b><br>VannaEx: %{y:.2e}<extra></extra>'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=BORDER, line_width=1)
    safe_add_vline(fig, spot_input, color=ORANGE, width=2, dash="dash", text=f"Spot ({spot_input})")
    fig.update_layout(
        **get_plotly_layout(),
        title=title,
        xaxis_title="Strike",
        yaxis_title="Vanna Exposure",
        height=550,
    )
    return fig

def plot_expected_move(df_em, em_method):
    x = list(range(len(df_em)))
    lbl = df_em["label"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=df_em["em_plus_s"],
        mode='lines+markers', line=dict(color=GREEN, width=2), marker=dict(size=8),
        name="EM+", text=lbl, hovertemplate='<b>%{text}</b><br>EM+: %{y:.2f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_em["em_minus_s"],
        mode='lines+markers', line=dict(color=RED, width=2), marker=dict(size=8),
        name="EM-", text=lbl, hovertemplate='<b>%{text}</b><br>EM-: %{y:.2f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_em["atm"],
        mode='lines+markers', line=dict(color=ORANGE, width=2, dash='dash'), marker=dict(size=6),
        name="ATM Strike", text=lbl, hovertemplate='<b>%{text}</b><br>ATM: %{y:.0f}<extra></extra>'
    ))
    # Fill area between em_minus and em_plus (plotly approach: add_trace with fill)
    fig.add_trace(go.Scatter(
        x=x + x[::-1],
        y=list(df_em["em_plus_s"]) + list(df_em["em_minus_s"][::-1]),
        fill='toself',
        fillcolor='rgba(0,170,255,0.08)',
        line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip',
        showlegend=False,
    ))
    fig.update_layout(
        **get_plotly_layout(),
        title=f"EXPECTED MOVE — {em_method}",
        xaxis=dict(
            tickmode='array',
            tickvals=x,
            ticktext=lbl,
        ),
        yaxis_title="Prix QQQ",
        height=550,
    )
    return fig

# ============================================================
#  CONSTANTS
# ============================================================
MULTIPLIER_DEFAULT = 41.36

# ============================================================
#  HEADER / NAVBAR / UI (same as before)
# ============================================================
st.markdown('<div id="gex-principal"></div>', unsafe_allow_html=True)
st.title("📊 GEX Analyser — Interactive Edition")

col_sub1, col_sub2 = st.columns([3, 1])
with col_sub1:
    st.markdown(
        "<span style='font-family:IBM Plex Mono,monospace;font-size:0.8rem;"
        "color:#5a7a94;letter-spacing:0.08em;'>OPTIONS FLOW · GAMMA LEVELS · EXPECTED MOVE</span>",
        unsafe_allow_html=True
    )
with col_sub2:
    st.markdown(
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
        f"color:#2e4a5e;'>{datetime.now().strftime('%Y-%m-%d  %H:%M')}</span>",
        unsafe_allow_html=True
    )
st.markdown("<hr style='margin:0.5rem 0 1.5rem'>", unsafe_allow_html=True)

_r1, _r2, _r3 = st.columns([2, 1, 3])
with _r1:
    MULTIPLIER = st.number_input(
        "⚙️ Ratio QQQ → NQ Futures",
        min_value=1.0,
        max_value=200.0,
        value=float(st.session_state.get("multiplier", MULTIPLIER_DEFAULT)),
        step=0.01,
        format="%.2f",
        help="Change chaque jour : NQ price / QQQ price = ratio",
        key="multiplier_input"
    )
    st.session_state["multiplier"] = MULTIPLIER
with _r2:
    st.markdown(
        f"""<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;
        color:#5a7a94;padding-top:1.9rem;'>
        Défaut : <b style='color:#ff9a00;'>{MULTIPLIER_DEFAULT}</b>
        </div>""", unsafe_allow_html=True)
with _r3:
    st.markdown(
        f"""<div style='font-family:IBM Plex Mono,monospace;font-size:0.72rem;
        color:#2e4a5e;padding-top:1.9rem;'>
        Calcul : NQ price ÷ QQQ price &nbsp;|&nbsp;
        Ex: NQ=21500, QQQ=520 → ratio=41.35
        </div>""", unsafe_allow_html=True)

st.markdown("""
<style>
.gex-navbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #090c10ee;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #1e2d3d;
    padding: 0.5rem 0;
    margin-bottom: 1.5rem;
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    align-items: center;
}
.gex-navbar a {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #5a7a94 !important;
    text-decoration: none !important;
    padding: 0.35rem 0.75rem;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    transition: all 0.15s ease;
    white-space: nowrap;
}
.gex-navbar a:hover {
    color: #e8f0f7 !important;
    border-color: #00aaff;
    background: #0e1318;
}
.gex-navbar a.active {
    color: #00ff9d !important;
    border-color: #00ff9d;
    background: rgba(0,255,157,0.07);
}
</style>

<div class="gex-navbar">
  <a href="#gex-principal">📊 GEX</a>
  <a href="#iv-skew">📐 IV Skew</a>
  <a href="#dex">🧭 DEX</a>
  <a href="#open-interest">📊 OI</a>
  <a href="#multi-expiry">📅 Multi-Expiry</a>
  <a href="#options-chain">🔗 Chain</a>
  <a href="#charm-vanna">⚗️ Charm/Vanna</a>
  <a href="#volume-flow">🔥 Volume</a>
  <a href="#expected-move">📐 Exp.Move</a>
  <a href="#gex-weekly">📅 Weekly</a>
</div>
""", unsafe_allow_html=True)

# ============================================================
#  FILE UPLOAD + MAIN LOGIC (same calculations as before)
#  The plotting calls below use the Plotly functions defined above
# ============================================================
uploaded_file = st.file_uploader("📂 Téléverse ton fichier CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, delimiter=",", header=2)
    except Exception as e:
        st.error(f"❌ Erreur de lecture du CSV : {e}")
        st.stop()

    required_cols = ["Expiration Date", "Strike", "Gamma", "Open Interest", "Gamma.1", "Open Interest.1"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"❌ Colonnes manquantes dans le CSV : {missing}")
        st.stop()

    current_date_dt = pd.to_datetime(datetime.now().date())
    df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
    unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()
    if len(unique_expiration_dates) == 0:
        st.error("❌ Aucune date d'expiration valide trouvée.")
        st.stop()

    closest_expiration_date_dt = min(unique_expiration_dates, key=lambda d: abs(d - current_date_dt))
    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')

    df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()
    for col in ["Gamma", "Open Interest", "Gamma.1", "Open Interest.1", "Strike"]:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_filtered["GEX_Calls"] = df_filtered.get("Gamma", 0) * df_filtered.get("Open Interest", 0) * (df_filtered.get("Strike", 0) ** 2) * 100
    df_filtered["GEX_Puts"]  = df_filtered.get("Gamma.1", 0) * df_filtered.get("Open Interest.1", 0) * (df_filtered.get("Strike", 0) ** 2) * 100 * -1
    df_filtered["GEX_Total"] = df_filtered["GEX_Calls"] + df_filtered["GEX_Puts"]
    df_filtered["ABS_Total"]  = df_filtered["GEX_Calls"].abs() + df_filtered["GEX_Puts"].abs()

    df_gex = df_filtered.groupby("Strike")[["GEX_Total", "ABS_Total"]].sum().reset_index()
    df_gex.rename(columns={"GEX_Total": "GEX", "ABS_Total": "ABS"}, inplace=True)

    net_gex       = df_gex["GEX"].sum()
    df_gex_sorted = df_gex.sort_values("Strike")

    max_abs_strike = df_gex.loc[df_gex['ABS'].idxmax(), 'Strike'] if not df_gex.empty else None

    df_gex_positive = df_gex[df_gex['GEX'] > 0]
    call_wall = (df_gex_positive.loc[df_gex_positive['GEX'].idxmax(), 'Strike'] if not df_gex_positive.empty else None)

    df_gex_negative = df_gex[df_gex['GEX'] < 0]
    put_wall = (df_gex_negative.loc[df_gex_negative['GEX'].idxmin(), 'Strike'] if not df_gex_negative.empty else None)

    zero_gamma = None
    low_bound  = min(filter(lambda x: x is not None, [put_wall, call_wall]), default=None)
    high_bound = max(filter(lambda x: x is not None, [put_wall, call_wall]), default=None)
    if low_bound is not None and high_bound is not None:
        df_between = df_gex_sorted[
            (df_gex_sorted["Strike"] >= low_bound) &
            (df_gex_sorted["Strike"] <= high_bound) &
            (df_gex_sorted["ABS"] > 0)
        ].reset_index(drop=True)
        for i in range(len(df_between) - 1):
            g0 = df_between["GEX"].iloc[i]
            g1 = df_between["GEX"].iloc[i + 1]
            s0 = df_between["Strike"].iloc[i]
            s1 = df_between["Strike"].iloc[i + 1]
            if g0 * g1 < 0:
                zero_gamma = round(s0 + (0 - g0) * (s1 - s0) / (g1 - g0), 2)
                break

    # Expected move calculations (same logic as before)
    em_plus  = "N/A"
    em_minus = "N/A"
    em_value = "N/A"
    target_buy  = "N/A"
    target_sell = "N/A"
    atm_strike  = None

    for col in ["Last Sale", "Last Sale.1", "Bid", "Ask", "Bid.1", "Ask.1", "Delta", "Delta.1", "IV", "IV.1"]:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_atm_candidates = df_filtered[df_filtered["Delta"].notna() & (df_filtered["Delta"] > 0)]
    if not df_atm_candidates.empty:
        atm_idx    = (df_atm_candidates["Delta"] - 0.5).abs().argsort().iloc[0]
        atm_row    = df_atm_candidates.iloc[atm_idx]
        atm_strike = atm_row["Strike"]
        put_row    = df_filtered[df_filtered["Strike"] == atm_strike]

        bid_c = atm_row.get("Bid",   np.nan)
        ask_c = atm_row.get("Ask",   np.nan)
        bid_p = put_row["Bid.1"].values[0]  if len(put_row) > 0 else np.nan
        ask_p = put_row["Ask.1"].values[0]  if len(put_row) > 0 else np.nan

        try:
            mid_c = (float(bid_c)+float(ask_c))/2 if pd.notna(bid_c) and pd.notna(ask_c) else np.nan
            mid_p = (float(bid_p)+float(ask_p))/2 if pd.notna(bid_p) and pd.notna(ask_p) else np.nan
            if pd.notna(mid_c) and pd.notna(mid_p):
                em_value = round(mid_c + mid_p, 2)
                em_plus  = round(atm_strike + em_value, 2)
                em_minus = round(atm_strike - em_value, 2)
        except Exception:
            pass

    df_calls_tb = df_filtered[df_filtered["Delta"].notna() & (df_filtered["Delta"] > 0) & (df_filtered["IV"] > 0)]
    if not df_calls_tb.empty:
        target_buy = int(df_calls_tb.iloc[(df_calls_tb["Delta"] - 0.25).abs().argsort().iloc[0]]["Strike"])

    df_puts_ts = df_filtered[df_filtered["Delta.1"].notna() & (df_filtered["Delta.1"] < 0) & (df_filtered["IV.1"] > 0)]
    if not df_puts_ts.empty:
        target_sell = int(df_puts_ts.iloc[(df_puts_ts["Delta.1"].abs() - 0.25).abs().argsort().iloc[0]]["Strike"])

    # KPI banner (same as before)
    is_positive  = net_gex > 0
    regime_color = GREEN if is_positive else RED
    regime_label = "POSITIVE GAMMA" if is_positive else "NEGATIVE GAMMA"
    regime_icon  = "🟢 Market Pinned" if is_positive else "🔴 Volatile"
    net_gex_m    = round(net_gex / 1e6, 2) if pd.notna(net_gex) else 0
    regime_glow  = "rgba(0,255,157,0.08)" if is_positive else "rgba(255,60,90,0.08)"

    st.markdown(
        f"<div style='background:{regime_glow};border:1px solid {regime_color}33;"
        f"border-left:4px solid {regime_color};border-radius:8px;"
        f"padding:0.6rem 1.2rem;margin-bottom:1rem;"
        f"font-family:IBM Plex Mono,monospace;font-size:0.82rem;"
        f"color:{regime_color};letter-spacing:0.1em;font-weight:700;'>"
        f"▶ {regime_label} &nbsp;·&nbsp; {regime_icon} &nbsp;·&nbsp; "
        f"NET GEX : <span style='font-size:1rem;'>{net_gex_m:,.0f} M</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    def kpi_card(label, value, color, sub=""):
        return (
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;"
            f"padding:0.85rem 1rem;height:100%;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
            f"color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;"
            f"margin-bottom:0.4rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.35rem;"
            f"font-weight:700;color:{color};'>{value}</div>"
            f"<div style='font-size:0.7rem;color:{MUTED};margin-top:0.2rem;'>{sub}</div>"
            f"</div>"
        )

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.markdown(kpi_card("Call Wall",  int(call_wall) if isinstance(call_wall,(int,float)) else "N/A",  BLUE,   "Résistance GEX"), unsafe_allow_html=True)
    r1c2.markdown(kpi_card("Put Wall",   int(put_wall)  if isinstance(put_wall,(int,float))  else "N/A",  RED,    "Support GEX"),    unsafe_allow_html=True)
    r1c3.markdown(kpi_card("Zero Gamma", zero_gamma if zero_gamma else "N/A",                             ORANGE, "Flip regime"),    unsafe_allow_html=True)
    r1c4.markdown(kpi_card("Net GEX",    f"{net_gex_m:,.0f} M",                                          regime_color, regime_label), unsafe_allow_html=True)

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.markdown(kpi_card("Expected Move ±", f"{em_value}" if em_value != "N/A" else "N/A", GREEN, f"ATM {int(atm_strike) if atm_strike else '—'}"), unsafe_allow_html=True)
    r2c2.markdown(kpi_card("EM+  /  EM−",
        f"{em_plus} / {em_minus}" if em_plus != "N/A" else "N/A",
        GREEN, "Zone de prix attendue"), unsafe_allow_html=True)
    r2c3.markdown(kpi_card("Target Buy",  f"{target_buy}",  "#34d399", "Call delta 25 — IV"), unsafe_allow_html=True)
    r2c4.markdown(kpi_card("Target Sell", f"{target_sell}", "#f87171", "Put delta 25 — IV"),  unsafe_allow_html=True)

    # PLOTLY CHARTS
    top_n = st.slider("Nombre de strikes dominants", 5, max(5, min(200, int(df_gex.shape[0]))), 30, key="gex_top_n")
    df_gex_active = df_gex[df_gex["ABS"] > 0].copy()
    df_top_abs = df_gex_active.nlargest(top_n, 'ABS').sort_values("Strike") if not df_gex_active.empty else df_gex_active

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_gex = plot_gex_curve(df_top_abs, call_wall, put_wall, zero_gamma, f"GAMMA EXPOSURE CURVE - {closest_expiration_date}")
        st.plotly_chart(fig_gex, use_container_width=True, config={"displayModeBar": True})

    with chart_col2:
        df_gex_comp = (
            df_filtered[['Strike', 'GEX_Calls', 'GEX_Puts']]
            .dropna()
            .groupby('Strike')[['GEX_Calls', 'GEX_Puts']]
            .sum()
            .reset_index()
        )
        df_gex_comp = df_gex_comp[df_gex_comp['Strike'].isin(df_top_abs['Strike'])] if not df_top_abs.empty else df_gex_comp
        fig_comp = plot_calls_vs_puts(df_gex_comp, f"CALLS vs PUTS - {closest_expiration_date}")
        st.plotly_chart(fig_comp, use_container_width=True)

    # IV SKEW section
    st.markdown('<div id="iv-skew"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📐 IV Skew — Smile de Volatilité")

    expiry_options = sorted(df['Expiration Date_dt'].dropna().unique())
    expiry_labels  = [d.strftime('%a %b %d %Y') for d in expiry_options]
    selected_label = st.selectbox("Expiration", expiry_labels, index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0)
    selected_dt    = expiry_options[expiry_labels.index(selected_label)]

    df_skew = df[df['Expiration Date_dt'] == selected_dt].copy()
    for col in ["Strike","IV","IV.1","Delta","Delta.1","Open Interest","Open Interest.1"]:
        if col in df_skew.columns:
            df_skew[col] = pd.to_numeric(df_skew[col], errors='coerce')

    df_c = df_skew[df_skew["IV"]   > 0][["Strike","IV","Delta","Open Interest"]].copy() if "IV" in df_skew.columns else pd.DataFrame()
    df_p = df_skew[df_skew["IV.1"] > 0][["Strike","IV.1","Delta.1","Open Interest.1"]].copy() if "IV.1" in df_skew.columns else pd.DataFrame()
    if not df_p.empty:
        df_p.rename(columns={"IV.1":"IV","Delta.1":"Delta","Open Interest.1":"Open Interest"}, inplace=True)

    if not df_c.empty and not df_p.empty:
        atm = df_c.iloc[(df_c['Delta'] - 0.5).abs().argsort()[:1]]['Strike'].values[0]
        put_25  = df_p.iloc[(df_p['Delta'].abs() - 0.25).abs().argsort()[:1]]
        call_25 = df_c.iloc[(df_c['Delta'] - 0.25).abs().argsort()[:1]]
        atm_iv  = df_c.iloc[(df_c['Delta'] - 0.5).abs().argsort()[:1]]['IV'].values[0]
        skew_25 = put_25['IV'].values[0] - call_25['IV'].values[0]
        skew_pct = skew_25 * 100

        sk1, sk2, sk3, sk4 = st.columns(4)
        sk1.metric("ATM IV",          f"{atm_iv*100:.2f}%")
        sk2.metric("IV Put 25-delta", f"{put_25['IV'].values[0]*100:.2f}%", delta=f"strike {int(put_25['Strike'].values[0])}")
        sk3.metric("IV Call 25-delta",f"{call_25['IV'].values[0]*100:.2f}%", delta=f"strike {int(call_25['Strike'].values[0])}")
        sk4.metric("Skew 25d (P-C)",  f"{skew_pct:+.2f}%", delta="Put premium" if skew_25 > 0 else "Call premium",
                   delta_color="inverse" if skew_25 < 0 else "normal")

        fig_skew = plot_iv_skew(df_c, df_p, atm, atm_iv, skew_25, f"IV SKEW - {selected_label}")
        st.plotly_chart(fig_skew, use_container_width=True)

        interp_color = GREEN if skew_25 > 0.005 else (RED if skew_25 < -0.005 else ORANGE)
        if skew_25 > 0.015:
            msg = "Put premium elevé - le marche paye cher la protection baissiere (fear dominant)"
        elif skew_25 > 0.005:
            msg = "Skew modere - put premium normal, marche prudent mais pas en panique"
        elif skew_25 < -0.005:
            msg = "Call premium - le marche anticipe une hausse ou couvre des positions courtes"
        else:
            msg = "Skew quasi-nul - marche indecis, calls et puts valorises pareillement"

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {ORANGE};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};margin-top:0.5rem;'>"
            f"<b style='color:{ORANGE};'>INTERPRETATION :</b> {msg}"
            f"</div>",
            unsafe_allow_html=True
        )

    # DEX section (uses plot_dex_curve and plot_dex_calls_puts)
    st.markdown('<div id="dex"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🧭 Delta Exposure (DEX) — Biais Directionnel")

    selected_label_dex = st.selectbox("Expiration (DEX)", expiry_labels,
        index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
        key="dex_expiry")
    selected_dt_dex = expiry_options[expiry_labels.index(selected_label_dex)]

    df_dex_raw = df[df['Expiration Date_dt'] == selected_dt_dex].copy()
    for col in ["Strike","Delta","Delta.1","Open Interest","Open Interest.1"]:
        if col in df_dex_raw.columns:
            df_dex_raw[col] = pd.to_numeric(df_dex_raw[col], errors='coerce')

    df_dex_raw["DEX_Calls"] = df_dex_raw.get("Delta", 0) * df_dex_raw.get("Open Interest", 0) * df_dex_raw.get("Strike", 0) * 100
    df_dex_raw["DEX_Puts"]  = df_dex_raw.get("Delta.1", 0) * df_dex_raw.get("Open Interest.1", 0) * df_dex_raw.get("Strike", 0) * 100

    df_dex = df_dex_raw.groupby("Strike")[["DEX_Calls","DEX_Puts"]].sum().reset_index()
    df_dex["DEX_Total"] = df_dex["DEX_Calls"] + df_dex["DEX_Puts"]
    df_dex["ABS_DEX"]   = df_dex["DEX_Total"].abs()
    df_dex_sorted = df_dex.sort_values("Strike")

    net_dex      = df_dex["DEX_Total"].sum()
    is_bull_dex  = net_dex > 0
    dex_regime   = "HAUSSIER" if is_bull_dex else "BAISSIER"
    dex_color    = GREEN if is_bull_dex else RED

    df_dex_pos = df_dex[df_dex["DEX_Calls"] > 0]
    df_dex_neg = df_dex[df_dex["DEX_Puts"]  < 0]
    delta_call_wall = df_dex_pos.loc[df_dex_pos["DEX_Calls"].idxmax(), "Strike"] if not df_dex_pos.empty else None
    delta_put_wall  = df_dex_neg.loc[df_dex_neg["DEX_Puts"].idxmin(),  "Strike"] if not df_dex_neg.empty else None

    zero_dex = None
    if isinstance(delta_call_wall, (int,float)) and isinstance(delta_put_wall, (int,float)):
        low_dex  = min(delta_call_wall, delta_put_wall)
        high_dex = max(delta_call_wall, delta_put_wall)
        df_dex_between = df_dex_sorted[
            (df_dex_sorted["Strike"] >= low_dex) &
            (df_dex_sorted["Strike"] <= high_dex) &
            (df_dex_sorted["ABS_DEX"] > 0)
        ].reset_index(drop=True)
        for i in range(len(df_dex_between) - 1):
            d0 = df_dex_between["DEX_Total"].iloc[i]
            d1 = df_dex_between["DEX_Total"].iloc[i + 1]
            s0 = df_dex_between["Strike"].iloc[i]
            s1 = df_dex_between["Strike"].iloc[i + 1]
            if d0 * d1 < 0:
                zero_dex = round(s0 + (0 - d0) * (s1 - s0) / (d1 - d0), 2)
                break

    d1c, d2c, d3c, d4c = st.columns(4)
    d1c.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {dex_color};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>NET DEX</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{dex_color};'>{net_dex:.2e}</div>"
        f"<div style='font-size:0.75rem;color:{dex_color};margin-top:0.3rem;'>{dex_regime}</div>"
        f"</div>", unsafe_allow_html=True)
    d2c.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {BLUE};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>DELTA CALL WALL</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{BLUE};'>{delta_call_wall if delta_call_wall is not None else 'N/A'}</div>"
        f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>Resistance delta</div>"
        f"</div>", unsafe_allow_html=True)
    d3c.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {RED};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>DELTA PUT WALL</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{RED};'>{delta_put_wall if delta_put_wall is not None else 'N/A'}</div>"
        f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>Support delta</div>"
        f"</div>", unsafe_allow_html=True)
    d4c.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {ORANGE};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>ZERO DEX</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{ORANGE};'>{zero_dex if zero_dex else 'N/A'}</div>"
        f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>Pivot directionnel</div>"
        f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    top_n_dex = st.slider("Nombre de strikes (DEX)", 5, max(5, min(200, int(df_dex.shape[0]))), 30, key="dex_slider")
    df_top_dex = df_dex.nlargest(top_n_dex, "ABS_DEX").sort_values("Strike") if not df_dex.empty else df_dex

    dex_col1, dex_col2 = st.columns(2)
    with dex_col1:
        fig_dex = plot_dex_curve(df_top_dex, delta_call_wall, delta_put_wall, zero_dex, "DELTA EXPOSURE - Courbe Totale")
        st.plotly_chart(fig_dex, use_container_width=True)
    with dex_col2:
        df_comp = df_dex[df_dex["Strike"].isin(df_top_dex["Strike"])].sort_values("Strike") if not df_top_dex.empty else df_dex
        fig_dex_comp = plot_dex_calls_puts(df_comp, "DEX CALLS vs PUTS")
        st.plotly_chart(fig_dex_comp, use_container_width=True)

    # OPEN INTEREST
    st.markdown('<div id="open-interest"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📊 Open Interest — Niveaux Clés & Positionnement")

    df_oi = df.copy()
    for col in ["Strike","Open Interest","Open Interest.1","Volume","Volume.1","Delta","Delta.1"]:
        if col in df_oi.columns:
            df_oi[col] = pd.to_numeric(df_oi[col], errors='coerce')
    df_oi["OI_Calls"] = df_oi.get("Open Interest", 0).fillna(0)
    df_oi["OI_Puts"]  = df_oi.get("Open Interest.1", 0).fillna(0)
    df_oi["OI_Total"] = df_oi["OI_Calls"] + df_oi["OI_Puts"]

    total_oi_calls = df_oi["OI_Calls"].sum()
    total_oi_puts  = df_oi["OI_Puts"].sum()
    pcr_global     = total_oi_puts / total_oi_calls if total_oi_calls > 0 else 0

    by_strike = df_oi.groupby("Strike")[["OI_Calls","OI_Puts","OI_Total"]].sum().reset_index()
    by_strike["PCR"] = by_strike["OI_Puts"] / by_strike["OI_Calls"].replace(0, np.nan)

    max_oi_strike     = by_strike.loc[by_strike["OI_Total"].idxmax(), "Strike"] if not by_strike.empty else None
    max_call_strike   = by_strike.loc[by_strike["OI_Calls"].idxmax(), "Strike"] if not by_strike.empty else None
    max_put_strike    = by_strike.loc[by_strike["OI_Puts"].idxmax(),  "Strike"] if not by_strike.empty else None
    pcr_color         = RED if pcr_global > 1.2 else (GREEN if pcr_global < 0.8 else ORANGE)
    pcr_label         = "Bearish" if pcr_global > 1.2 else ("Bullish" if pcr_global < 0.8 else "Neutre")

    o1, o2, o3, o4 = st.columns(4)
    for col_ui, label, value, color, sub in [
        (o1, "PCR GLOBAL",       f"{pcr_global:.3f}", pcr_color, pcr_label),
        (o2, "MAX OI STRIKE",    int(max_oi_strike) if isinstance(max_oi_strike,(int,float)) else "N/A",  ORANGE,    "Niveau le + charge"),
        (o3, "MAX CALL STRIKE",  int(max_call_strike) if isinstance(max_call_strike,(int,float)) else "N/A",BLUE,      "Resistance OI"),
        (o4, "MAX PUT STRIKE",   int(max_put_strike) if isinstance(max_put_strike,(int,float)) else "N/A", RED,       "Support OI"),
    ]:
        col_ui.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.4rem;"
            f"font-weight:600;color:{color};'>{value}</div>"
            f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    top_n_oi = st.slider("Nombre de strikes (OI)", 10, max(10, min(200, int(by_strike.shape[0]))), 30, key="oi_slider")
    df_top_oi = by_strike.nlargest(top_n_oi, "OI_Total").sort_values("Strike") if not by_strike.empty else by_strike

    fig_oi = plot_oi_chart(df_top_oi, max_call_strike, max_put_strike, max_oi_strike, 
                           "OPEN INTEREST CALLS vs PUTS PAR STRIKE (toutes expirations)")
    st.plotly_chart(fig_oi, use_container_width=True)

    # CHARM & VANNA (simplified display using Plotly bars)
    st.markdown('<div id="charm-vanna"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### ⚗️ Charm & Vanna — Greeks du 2e Ordre")

    cv_exp_label = st.selectbox("Expiration (Charm/Vanna)", expiry_labels,
        index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
        key="cv_expiry")
    cv_dt = expiry_options[expiry_labels.index(cv_exp_label)]

    cv1, cv2 = st.columns(2)
    with cv1:
        spot_input = st.number_input("Spot price (S)", value=647.0, step=0.5, key="cv_spot")
    with cv2:
        rate_input = st.number_input("Taux sans risque (%)", value=5.0, step=0.1, key="cv_rate") / 100.0

    df_cv = df[df['Expiration Date_dt'] == cv_dt].copy()
    for col in ["Strike","IV","IV.1","Open Interest","Open Interest.1"]:
        if col in df_cv.columns:
            df_cv[col] = pd.to_numeric(df_cv[col], errors='coerce')

    T_cv_days = max((cv_dt - pd.Timestamp(datetime.now().date())).days, 1)
    T_cv      = T_cv_days / 365.0

    def _d1d2(S, K, T, r, sigma):
        d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
        return d1, d1 - sigma*np.sqrt(T)

    def calc_charm_fn(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or K <= 0: return np.nan
        d1, d2 = _d1d2(S, K, T, r, sigma)
        return -sp_norm.pdf(d1) * (2*r*T - d2*sigma*np.sqrt(T)) / (2*T*sigma*np.sqrt(T))

    def calc_vanna_fn(S, K, T, r, sigma):
        if T <= 0 or sigma <= 0 or K <= 0: return np.nan
        d1, d2 = _d1d2(S, K, T, r, sigma)
        return -sp_norm.pdf(d1) * d2 / sigma

    strikes_cv = df_cv["Strike"].values if "Strike" in df_cv.columns else np.array([])
    iv_c_cv    = df_cv["IV"].values if "IV" in df_cv.columns else np.array([])
    iv_p_cv    = df_cv["IV.1"].values if "IV.1" in df_cv.columns else np.array([])
    oi_c_cv    = df_cv["Open Interest"].fillna(0).values if "Open Interest" in df_cv.columns else np.array([])
    oi_p_cv    = df_cv["Open Interest.1"].fillna(0).values if "Open Interest.1" in df_cv.columns else np.array([])

    ch_c, ch_p, va_c, va_p = [], [], [], []
    for i in range(len(strikes_cv)):
        ivc = iv_c_cv[i] if i < len(iv_c_cv) else np.nan
        ivp = iv_p_cv[i] if i < len(iv_p_cv) else np.nan
        oi_c = oi_c_cv[i] if i < len(oi_c_cv) else 0
        oi_p = oi_p_cv[i] if i < len(oi_p_cv) else 0
        K = strikes_cv[i]
        ch_c.append(calc_charm_fn(spot_input, K, T_cv, rate_input, ivc) if pd.notna(ivc) and ivc>0 else np.nan)
        ch_p.append(calc_charm_fn(spot_input, K, T_cv, rate_input, ivp) if pd.notna(ivp) and ivp>0 else np.nan)
        va_c.append(calc_vanna_fn(spot_input, K, T_cv, rate_input, ivc) if pd.notna(ivc) and ivc>0 else np.nan)
        va_p.append(calc_vanna_fn(spot_input, K, T_cv, rate_input, ivp) if pd.notna(ivp) and ivp>0 else np.nan)

    # Build dataframe safe
    if len(strikes_cv) > 0:
        df_cv = df_cv.assign(
            Charm_Call = ch_c,
            Charm_Put  = ch_p,
            Vanna_Call = va_c,
            Vanna_Put  = va_p
        )
        # Exposure multipliers (consistent with earlier logic)
        df_cv["CharmEx_Call"] = df_cv["Charm_Call"].fillna(0) * df_cv.get("Open Interest",0).fillna(0) * df_cv["Strike"] * 100
        df_cv["CharmEx_Put"]  = df_cv["Charm_Put"].fillna(0)  * df_cv.get("Open Interest.1",0).fillna(0) * df_cv["Strike"] * 100 * -1
        df_cv["VannaEx_Call"] = df_cv["Vanna_Call"].fillna(0) * df_cv.get("Open Interest",0).fillna(0) * df_cv["Strike"] * 100
        df_cv["VannaEx_Put"]  = df_cv["Vanna_Put"].fillna(0)  * df_cv.get("Open Interest.1",0).fillna(0) * df_cv["Strike"] * 100 * -1
        df_cv["CharmEx"] = df_cv["CharmEx_Call"].fillna(0) + df_cv["CharmEx_Put"].fillna(0)
        df_cv["VannaEx"] = df_cv["VannaEx_Call"].fillna(0) + df_cv["VannaEx_Put"].fillna(0)
        df_cv_gex = df_cv.groupby("Strike")[["CharmEx","VannaEx"]].sum().reset_index()
    else:
        df_cv_gex = pd.DataFrame(columns=["Strike","CharmEx","VannaEx"])

    net_charm = df_cv_gex["CharmEx"].sum() if not df_cv_gex.empty else 0
    net_vanna = df_cv_gex["VannaEx"].sum() if not df_cv_gex.empty else 0

    kv1, kv2, kv3, kv4 = st.columns(4)
    charm_col  = GREEN if net_charm > 0 else RED
    vanna_col  = GREEN if net_vanna > 0 else RED
    charm_lbl  = "Acheteur" if net_charm > 0 else "Vendeur"
    vanna_lbl  = "VIX crush -> haussier" if net_vanna > 0 else "VIX spike -> baissier"

    for col_kv, label, value, color, sub in [
        (kv1, "CHARM NET",       f"{net_charm:.2e}", charm_col, f"Flux MM: {charm_lbl}"),
        (kv2, "VANNA NET",       f"{net_vanna:.2e}", vanna_col, vanna_lbl),
        (kv3, "T RESTANT",       f"{T_cv_days}j",    ORANGE,    "Avant expiration"),
        (kv4, "SPOT UTILISÉ",    f"{spot_input}",    BLUE,      "Pour les calculs BS"),
    ]:
        col_kv.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
            f"font-weight:600;color:{color};'>{value}</div>"
            f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    top_n_cv = st.slider("Nombre de strikes (Charm/Vanna)", 5, max(5, min(200, int(df_cv_gex.shape[0]))), 30, key="cv_slider")
    if not df_cv_gex.empty:
        df_cv_gex['ABS'] = df_cv_gex["CharmEx"].abs() + df_cv_gex["VannaEx"].abs()
        df_cv_top = df_cv_gex.nlargest(top_n_cv, "ABS").sort_values("Strike")
    else:
        df_cv_top = df_cv_gex

    tab_charm, tab_vanna = st.tabs(["⏱️ Charm Exposure", "🌊 Vanna Exposure"])
    with tab_charm:
        fig_ch = plot_charm_exposure(df_cv_top, spot_input, f"CHARM EXPOSURE - {cv_exp_label}")
        st.plotly_chart(fig_ch, use_container_width=True)
    with tab_vanna:
        fig_va = plot_vanna_exposure(df_cv_top, spot_input, f"VANNA EXPOSURE - {cv_exp_label}")
        st.plotly_chart(fig_va, use_container_width=True)

    # EXPECTED MOVE summary and chart
    st.markdown('<div id="expected-move"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📐 Expected Move — Toutes Expirations")

    em_results = []
    current_dt = pd.Timestamp(datetime.now().date())

    for exp_dt, group in df.groupby("Expiration Date_dt"):
        for col in ["Strike","Last Sale","Last Sale.1","Bid","Ask","Bid.1","Ask.1","IV","IV.1","Delta","Delta.1"]:
            if col in group.columns:
                group[col] = pd.to_numeric(group[col], errors='coerce')

        g_atm = group[group["Delta"].notna() & (group["Delta"] > 0)].copy()
        if g_atm.empty: continue

        atm_row    = g_atm.iloc[(g_atm["Delta"] - 0.5).abs().argsort().iloc[0]]
        atm_strike = atm_row["Strike"]
        iv_atm     = atm_row["IV"]
        T_days     = max((exp_dt - current_dt).days, 1)
        put_row = group[group["Strike"] == atm_strike]

        ls_c  = atm_row.get("Last Sale", np.nan)
        ls_p  = put_row.get("Last Sale.1", np.nan) if not put_row.empty else np.nan
        bid_c = atm_row.get("Bid", np.nan);  ask_c = atm_row.get("Ask", np.nan)
        bid_p = put_row["Bid.1"].values[0]  if len(put_row) > 0 else np.nan
        ask_p = put_row["Ask.1"].values[0]  if len(put_row) > 0 else np.nan

        em_ls  = round(ls_c  + ls_p,  2) if pd.notna(ls_c)  and pd.notna(ls_p)  else np.nan
        mid_c  = (bid_c+ask_c)/2 if pd.notna(bid_c) and pd.notna(ask_c) else np.nan
        mid_p  = (bid_p+ask_p)/2 if pd.notna(bid_p) and pd.notna(ask_p) else np.nan
        em_mid = round(mid_c + mid_p, 2) if pd.notna(mid_c) and pd.notna(mid_p) else np.nan
        em_iv  = round(iv_atm * atm_strike * np.sqrt(T_days/365), 2) if pd.notna(iv_atm) and iv_atm > 0 else np.nan
        em_use = em_mid if pd.notna(em_mid) else em_ls

        em_results.append({
            "exp_dt":    exp_dt,
            "label":     exp_dt.strftime('%a %b %d'),
            "T_days":    T_days,
            "atm":       int(atm_strike),
            "iv_atm":    iv_atm,
            "em_straddle": em_ls,
            "em_mid":    em_mid,
            "em_iv":     em_iv,
            "em_use":    em_use,
            "em_plus":   round(atm_strike + em_use, 2) if pd.notna(em_use) else None,
            "em_minus":  round(atm_strike - em_use, 2) if pd.notna(em_use) else None,
            "em_pct":    round(em_use / atm_strike * 100, 2) if pd.notna(em_use) else None,
        })

    df_em = pd.DataFrame(em_results)
    em_method = st.radio(
        "Méthode de calcul",
        ["Midpoint Bid/Ask (recommandé)", "Last Sale Straddle", "Formule IV Black-Scholes"],
        horizontal=True, key="em_method"
    )
    method_col = {"Midpoint Bid/Ask (recommandé)": "em_mid",
                  "Last Sale Straddle":             "em_straddle",
                  "Formule IV Black-Scholes":        "em_iv"}[em_method]

    if not df_em.empty:
        df_em["em_sel"]    = df_em[method_col]
        df_em["em_plus_s"] = df_em["atm"] + df_em["em_sel"]
        df_em["em_minus_s"]= df_em["atm"] - df_em["em_sel"]
        df_em["em_pct_s"]  = df_em["em_sel"] / df_em["atm"] * 100

        row0 = df_em.iloc[0]
        k1, k2, k3, k4, k5 = st.columns(5)
        for col_k, label, value, color in [
            (k1, "EXPIRY PROCHE",  row0["label"],                  ORANGE),
            (k2, "ATM STRIKE",     f"{row0['atm']}",               BLUE),
            (k3, "EXPECTED MOVE",  f"±{row0['em_sel']:.2f}",       GREEN),
            (k4, "EM+",            f"{row0['em_plus_s']:.2f}",     GREEN),
            (k5, "EM−",            f"{row0['em_minus_s']:.2f}",    RED),
        ]:
            col_k.markdown(
                f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
                f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
                f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
                f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
                f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
                f"font-weight:600;color:{color};'>{value}</div>"
                f"</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        fig_em = plot_expected_move(df_em, em_method)
        st.plotly_chart(fig_em, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;"
        "color:#2e4a5e;text-align:center;padding:0.5rem;'>"
        "GEX ANALYSER · Interactive Edition with Plotly · Hover for details, Drag to pan, Scroll to zoom"
        "</div>",
        unsafe_allow_html=True
    )

else:
    st.info("👆 Téléverse un fichier CSV pour commencer l'analyse")
