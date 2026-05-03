import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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
#  INJECT CUSTOM CSS (dark finance theme)
# ============================================================
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ============================================================
#  CONSTANTS
# ============================================================
MULTIPLIER_DEFAULT = 41.36  # Ratio QQQ → NQ Futures (change chaque jour)

# Couleurs pour plotly
COLORS = {
    'bg': '#090c10',
    'card': '#0e1318',
    'border': '#1e2d3d',
    'green': '#00ff9d',
    'red': '#ff3c5a',
    'orange': '#ff9a00',
    'blue': '#00aaff',
    'text': '#e8f0f7',
    'muted': '#5a7a94'
}

# Configuration du template plotly
PLOTLY_TEMPLATE = {
    'layout': {
        'paper_bgcolor': COLORS['bg'],
        'plot_bgcolor': COLORS['card'],
        'font': {'color': COLORS['text'], 'family': 'monospace'},
        'xaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': COLORS['border'],
            'title_font': {'color': COLORS['muted']},
            'tickfont': {'color': COLORS['muted']}
        },
        'yaxis': {
            'gridcolor': COLORS['border'],
            'linecolor': COLORS['border'],
            'title_font': {'color': COLORS['muted']},
            'tickfont': {'color': COLORS['muted']}
        },
        'hoverlabel': {
            'bgcolor': COLORS['card'],
            'font_size': 11,
            'font_family': 'monospace'
        }
    }
}

# ============================================================
#  HEADER
# ============================================================
st.markdown('<div id="gex-principal"></div>', unsafe_allow_html=True)
st.title("Analyse Gamma Exposure (GEX)")

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

# ============================================================
#  RATIO QQQ → NQ (configurable - visible en permanence)
# ============================================================
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


# ============================================================
#  NAVBAR
# ============================================================
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
#  FONCTIONS UTILITAIRES POUR LES GRAPHIQUES PLOTLY
# ============================================================

def create_gex_curve_plotly(df_top_abs, call_wall, put_wall, zero_gamma, title):
    """Crée un graphique interactif de la courbe GEX avec plotly"""
    
    # Préparer les données pour les zones colorées
    df_positive = df_top_abs[df_top_abs['GEX'] >= 0].copy()
    df_negative = df_top_abs[df_top_abs['GEX'] < 0].copy()
    
    fig = go.Figure()
    
    # Ligne principale GEX
    fig.add_trace(go.Scatter(
        x=df_top_abs['Strike'],
        y=df_top_abs['GEX'],
        mode='lines+markers',
        name='GEX',
        line=dict(color=COLORS['blue'], width=1.5),
        marker=dict(size=4, color=COLORS['blue'], symbol='circle'),
        hovertemplate='<b>Strike: %{x:.2f}</b><br>' +
                      'GEX: %{y:,.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Zones colorées (simulées avec des scatter fill)
    if not df_positive.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([df_positive['Strike'], df_positive['Strike'][::-1]]),
            y=pd.concat([df_positive['GEX'], pd.Series([0]*len(df_positive))]),
            fill='toself',
            fillcolor=f'rgba(0, 255, 157, 0.15)',
            line=dict(color='rgba(0,0,0,0)'),
            name='GEX Positif',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    if not df_negative.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([df_negative['Strike'], df_negative['Strike'][::-1]]),
            y=pd.concat([df_negative['GEX'], pd.Series([0]*len(df_negative))]),
            fill='toself',
            fillcolor=f'rgba(255, 60, 90, 0.15)',
            line=dict(color='rgba(0,0,0,0)'),
            name='GEX Négatif',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Ligne horizontale zéro
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS['border'], line_width=1)
    
    # Call Wall
    if isinstance(call_wall, (int, float)):
        fig.add_vline(x=call_wall, line_dash="dash", line_color=COLORS['blue'], line_width=1.2,
                      annotation_text=f"Call Wall ({int(call_wall)})",
                      annotation_position="top",
                      annotation_font_size=10)
    
    # Put Wall
    if isinstance(put_wall, (int, float)):
        fig.add_vline(x=put_wall, line_dash="dash", line_color=COLORS['red'], line_width=1.2,
                      annotation_text=f"Put Wall ({int(put_wall)})",
                      annotation_position="bottom",
                      annotation_font_size=10)
    
    # Zero Gamma
    if zero_gamma is not None:
        fig.add_vline(x=zero_gamma, line_dash="dash", line_color=COLORS['orange'], line_width=1.2,
                      annotation_text=f"Zero Gamma ({zero_gamma})",
                      annotation_position="top",
                      annotation_font_size=10)
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=COLORS['text'])),
        xaxis_title="Strike Price",
        yaxis_title="GEX",
        hovermode='closest',
        **PLOTLY_TEMPLATE['layout']
    )
    
    return fig


def create_calls_vs_puts_plotly(df_gex_comp, title):
    """Crée un graphique à barres interactif Calls vs Puts"""
    
    fig = go.Figure()
    
    # Barres pour les Calls
    fig.add_trace(go.Bar(
        x=df_gex_comp['Strike'],
        y=df_gex_comp['GEX_Calls'],
        name='GEX Calls',
        marker_color=COLORS['blue'],
        opacity=0.85,
        width=0.8,
        hovertemplate='<b>Strike: %{x:.2f}</b><br>' +
                      'GEX Calls: %{y:,.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Barres pour les Puts
    fig.add_trace(go.Bar(
        x=df_gex_comp['Strike'],
        y=df_gex_comp['GEX_Puts'],
        name='GEX Puts',
        marker_color=COLORS['red'],
        opacity=0.85,
        width=0.8,
        hovertemplate='<b>Strike: %{x:.2f}</b><br>' +
                      'GEX Puts: %{y:,.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Ligne horizontale zéro
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS['border'], line_width=1)
    
    # Configuration du layout pour barres groupées
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=COLORS['text'])),
        xaxis_title="Strike Price",
        yaxis_title="GEX",
        barmode='group',
        hovermode='closest',
        **PLOTLY_TEMPLATE['layout']
    )
    
    return fig


def create_dex_curve_plotly(df_top_dex, delta_call_wall, delta_put_wall, zero_dex, title):
    """Crée un graphique interactif de la courbe DEX avec plotly"""
    
    # Préparer les données pour les zones colorées
    df_positive = df_top_dex[df_top_dex['DEX_Total'] >= 0].copy()
    df_negative = df_top_dex[df_top_dex['DEX_Total'] < 0].copy()
    
    fig = go.Figure()
    
    # Ligne principale DEX
    fig.add_trace(go.Scatter(
        x=df_top_dex['Strike'],
        y=df_top_dex['DEX_Total'],
        mode='lines+markers',
        name='DEX Total',
        line=dict(color=COLORS['blue'], width=1.8),
        marker=dict(size=4, color=COLORS['blue'], symbol='circle'),
        hovertemplate='<b>Strike: %{x:.2f}</b><br>' +
                      'DEX Total: %{y:.2e}<br>' +
                      '<extra></extra>'
    ))
    
    # Zones colorées
    if not df_positive.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([df_positive['Strike'], df_positive['Strike'][::-1]]),
            y=pd.concat([df_positive['DEX_Total'], pd.Series([0]*len(df_positive))]),
            fill='toself',
            fillcolor=f'rgba(0, 255, 157, 0.15)',
            line=dict(color='rgba(0,0,0,0)'),
            name='DEX Positif',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    if not df_negative.empty:
        fig.add_trace(go.Scatter(
            x=pd.concat([df_negative['Strike'], df_negative['Strike'][::-1]]),
            y=pd.concat([df_negative['DEX_Total'], pd.Series([0]*len(df_negative))]),
            fill='toself',
            fillcolor=f'rgba(255, 60, 90, 0.15)',
            line=dict(color='rgba(0,0,0,0)'),
            name='DEX Négatif',
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Ligne horizontale zéro
    fig.add_hline(y=0, line_dash="dash", line_color=COLORS['border'], line_width=1)
    
    # Lignes verticales clés
    if isinstance(delta_call_wall, (int, float)):
        fig.add_vline(x=delta_call_wall, line_dash="dash", line_color=COLORS['blue'], line_width=1.2,
                      annotation_text=f"Delta Call Wall ({int(delta_call_wall)})",
                      annotation_position="top",
                      annotation_font_size=10)
    
    if isinstance(delta_put_wall, (int, float)):
        fig.add_vline(x=delta_put_wall, line_dash="dash", line_color=COLORS['red'], line_width=1.2,
                      annotation_text=f"Delta Put Wall ({int(delta_put_wall)})",
                      annotation_position="bottom",
                      annotation_font_size=10)
    
    if zero_dex is not None:
        fig.add_vline(x=zero_dex, line_dash="dash", line_color=COLORS['orange'], line_width=1.2,
                      annotation_text=f"Zero DEX ({zero_dex})",
                      annotation_position="top",
                      annotation_font_size=10)
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=COLORS['text'])),
        xaxis_title="Strike Price",
        yaxis_title="Delta Exposure (DEX)",
        hovermode='closest',
        **PLOTLY_TEMPLATE['layout']
    )
    
    return fig


# ============================================================
#  FILE UPLOAD
# ============================================================
uploaded_file = st.file_uploader("📂  Téléverse ton fichier CSV", type=["csv"])

if uploaded_file is not None:

    # --- Lecture robuste ---
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

    # --- Dates ---
    current_date_dt = pd.to_datetime(datetime.now().date())
    df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
    unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()

    if len(unique_expiration_dates) == 0:
        st.error("❌ Aucune date d'expiration valide trouvée.")
        st.stop()

    closest_expiration_date_dt = min(unique_expiration_dates, key=lambda d: abs(d - current_date_dt))
    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')

    # --- Filtrage & calculs GEX ---
    df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()

    for col in ["Gamma", "Open Interest", "Gamma.1", "Open Interest.1", "Strike"]:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_filtered["GEX_Calls"] = (
        df_filtered["Gamma"] * df_filtered["Open Interest"] * (df_filtered["Strike"] ** 2) * 100
    )
    df_filtered["GEX_Puts"] = (
        df_filtered["Gamma.1"] * df_filtered["Open Interest.1"] * (df_filtered["Strike"] ** 2) * 100 * -1
    )
    df_filtered["GEX_Total"] = df_filtered["GEX_Calls"] + df_filtered["GEX_Puts"]
    df_filtered["ABS_Total"]  = abs(df_filtered["GEX_Calls"]) + abs(df_filtered["GEX_Puts"])

    df_gex = df_filtered.groupby("Strike")[["GEX_Total", "ABS_Total"]].sum().reset_index()
    df_gex.rename(columns={"GEX_Total": "GEX", "ABS_Total": "ABS"}, inplace=True)

    # --- Niveaux clés ---
    net_gex       = df_gex["GEX"].sum()
    df_gex_sorted = df_gex.sort_values("Strike")

    max_abs_strike = df_gex.loc[df_gex['ABS'].idxmax(), 'Strike']

    df_gex_positive = df_gex[df_gex['GEX'] > 0]
    call_wall = (df_gex_positive.loc[df_gex_positive['GEX'].idxmax(), 'Strike']
                 if not df_gex_positive.empty else 'N/A')

    df_gex_negative = df_gex[df_gex['GEX'] < 0]
    put_wall = (df_gex_negative.loc[df_gex_negative['GEX'].idxmin(), 'Strike']
                if not df_gex_negative.empty else 'N/A')

    # Zero Gamma : premier croisement de la courbe GEX avec y=0
    zero_gamma = None
    low_bound  = min(put_wall, call_wall) if isinstance(put_wall, (int,float)) and isinstance(call_wall, (int,float)) else None
    high_bound = max(put_wall, call_wall) if isinstance(put_wall, (int,float)) and isinstance(call_wall, (int,float)) else None

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

    # ============================================================
    #  FILTRAGE STRIKES ACTIFS
    # ============================================================
    df_gex_active = df_gex[df_gex["ABS"] > 0].copy()

    # ============================================================
    #  EXPECTED MOVE + TARGET BUY/SELL (calculs auto)
    # ============================================================
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

        mid_c = (float(bid_c)+float(ask_c))/2 if pd.notna(bid_c) and pd.notna(ask_c) else np.nan
        mid_p = (float(bid_p)+float(ask_p))/2 if pd.notna(bid_p) and pd.notna(ask_p) else np.nan

        if pd.notna(mid_c) and pd.notna(mid_p):
            em_value = round(mid_c + mid_p, 2)
            em_plus  = round(atm_strike + em_value, 2)
            em_minus = round(atm_strike - em_value, 2)

    # Target Buy = strike call dont le delta est le plus proche de 0.25
    df_calls_tb = df_filtered[df_filtered["Delta"].notna() & (df_filtered["Delta"] > 0) & (df_filtered["IV"] > 0)]
    if not df_calls_tb.empty:
        target_buy = int(df_calls_tb.iloc[(df_calls_tb["Delta"] - 0.25).abs().argsort().iloc[0]]["Strike"])

    # Target Sell = strike put dont le delta est le plus proche de -0.25
    df_puts_ts = df_filtered[df_filtered["Delta.1"].notna() & (df_filtered["Delta.1"] < 0) & (df_filtered["IV.1"] > 0)]
    if not df_puts_ts.empty:
        target_sell = int(df_puts_ts.iloc[(df_puts_ts["Delta.1"].abs() - 0.25).abs().argsort().iloc[0]]["Strike"])

    # ============================================================
    #  RÉSUMÉ PRINCIPAL — 8 métriques clés
    # ============================================================
    is_positive  = net_gex > 0
    regime_color = COLORS['green'] if is_positive else COLORS['red']
    regime_label = "POSITIVE GAMMA" if is_positive else "NEGATIVE GAMMA"
    regime_icon  = "🟢 Market Pinned" if is_positive else "🔴 Volatile"
    net_gex_m    = round(net_gex / 1e6, 2)
    regime_glow  = "rgba(0,255,157,0.08)" if is_positive else "rgba(255,60,90,0.08)"

    # Banniere regime
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

    # Ligne 1 : 4 niveaux GEX
    def kpi_card(label, value, color, sub=""):
        return (
            f"<div style='background:{COLORS['card']};border:1px solid {COLORS['border']};"
            f"border-left:3px solid {color};border-radius:8px;"
            f"padding:0.85rem 1rem;height:100%;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
            f"color:{COLORS['muted']};letter-spacing:0.1em;text-transform:uppercase;"
            f"margin-bottom:0.4rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.35rem;"
            f"font-weight:700;color:{color};'>{value}</div>"
            f"<div style='font-size:0.7rem;color:{COLORS['muted']};margin-top:0.2rem;'>{sub}</div>"
            f"</div>"
        )

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.markdown(kpi_card("Call Wall",  int(call_wall) if isinstance(call_wall,(int,float)) else "N/A",  COLORS['blue'],   "Résistance GEX"), unsafe_allow_html=True)
    r1c2.markdown(kpi_card("Put Wall",   int(put_wall)  if isinstance(put_wall,(int,float))  else "N/A",  COLORS['red'],    "Support GEX"),    unsafe_allow_html=True)
    r1c3.markdown(kpi_card("Zero Gamma", zero_gamma if zero_gamma else "N/A",                             COLORS['orange'], "Flip regime"),    unsafe_allow_html=True)
    r1c4.markdown(kpi_card("Net GEX",    f"{net_gex_m:,.0f} M",                                          regime_color, regime_label), unsafe_allow_html=True)

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # Ligne 2 : EM + Target Buy/Sell
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.markdown(kpi_card("Expected Move ±", f"{em_value}" if em_value != "N/A" else "N/A", COLORS['green'], f"ATM {int(atm_strike) if atm_strike else '—'}"), unsafe_allow_html=True)
    r2c2.markdown(kpi_card("EM+  /  EM−",
        f"{em_plus} / {em_minus}" if em_plus != "N/A" else "N/A",
        COLORS['green'], "Zone de prix attendue"), unsafe_allow_html=True)
    r2c3.markdown(kpi_card("Target Buy",  f"{target_buy}",  "#34d399", "Call delta 25 — IV"), unsafe_allow_html=True)
    r2c4.markdown(kpi_card("Target Sell", f"{target_sell}", "#f87171", "Put delta 25 — IV"),  unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    #  GRAPHIQUES INTERACTIFS AVEC PLOTLY
    # ============================================================
    top_n = st.slider("Nombre de strikes dominants", 5, 50, 50)
    df_top_abs = df_gex_active.nlargest(top_n, 'ABS').sort_values("Strike")

    chart_col1, chart_col2 = st.columns(2)

    # -- Courbe GEX interactive --
    with chart_col1:
        fig1 = create_gex_curve_plotly(
            df_top_abs, 
            call_wall, 
            put_wall, 
            zero_gamma, 
            f"GAMMA EXPOSURE CURVE - {closest_expiration_date}"
        )
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': True})

    # -- Calls vs Puts interactif --
    with chart_col2:
        df_gex_comp = (
            df_filtered[['Strike', 'GEX_Calls', 'GEX_Puts']]
            .dropna()
            .groupby('Strike')[['GEX_Calls', 'GEX_Puts']]
            .sum()
            .reset_index()
        )
        df_gex_comp = df_gex_comp[df_gex_comp['Strike'].isin(df_top_abs['Strike'])]
        
        fig2 = create_calls_vs_puts_plotly(
            df_gex_comp,
            f"CALLS vs PUTS - {closest_expiration_date}"
        )
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': True})

    # ============================================================
    #  RESUME + EXPECTED MOVE AUTO
    # ============================================================
    res_col1, res_col2 = st.columns([1, 1])

    with res_col1:
        st.markdown("**📊 Niveaux clés**")
        df_summary = pd.DataFrame({
            'Niveau':  ['Call Wall', 'Put Wall', 'Zero Gamma', 'Max ABS Strike', 'NET GEX'],
            'Valeur':  [
                int(call_wall)  if isinstance(call_wall,  (int,float)) else 'N/A',
                int(put_wall)   if isinstance(put_wall,   (int,float)) else 'N/A',
                zero_gamma      if zero_gamma else 'N/A',
                int(max_abs_strike),
                f"{net_gex:.2e}",
            ]
        })
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

    with res_col2:
        st.markdown("**🎯 Expected Move (ATM auto)**")
        em_kpi1, em_kpi2, em_kpi3 = st.columns(3)
        em_kpi1.metric("EM ±",  f"{em_value}" if em_value != '0000' else 'N/A')
        em_kpi2.metric("EM+",   f"{em_plus}"  if em_plus  != '0000' else 'N/A', delta="haussier")
        em_kpi3.metric("EM-",   f"{em_minus}" if em_minus != '0000' else 'N/A', delta="baissier", delta_color="inverse")

    # ============================================================
    #  EXPORT COPIABLE
    # ============================================================
    top_gex_strikes = (
        df_gex_active.sort_values("ABS", ascending=False)["Strike"]
        .head(4).tolist()
    )
    while len(top_gex_strikes) < 4:
        top_gex_strikes.append("0000")

    def safe_int_multiply(val):
        try:    return int(round(float(val) * MULTIPLIER, 0))
        except: return val

    copy_text = (
        f"{int(call_wall) if isinstance(call_wall,(int,float)) else 'N/A'}, "
        f"{int(put_wall)  if isinstance(put_wall,(int,float))  else 'N/A'}, "
        f"{zero_gamma if zero_gamma else 'N/A'}, "
        f"{em_plus}, {em_minus}, "
        f"{int(top_gex_strikes[0])}, {int(top_gex_strikes[1])}, "
        f"{int(top_gex_strikes[2])}, {int(top_gex_strikes[3])}"
    )

    multiplied = [
        safe_int_multiply(call_wall),
        safe_int_multiply(put_wall),
        safe_int_multiply(zero_gamma if zero_gamma else 0),
        safe_int_multiply(em_plus),
        safe_int_multiply(em_minus),
        safe_int_multiply(top_gex_strikes[0]),
        safe_int_multiply(top_gex_strikes[1]),
        safe_int_multiply(top_gex_strikes[2]),
        safe_int_multiply(top_gex_strikes[3]),
    ]

    st.markdown("**📋 Export**")
    exp_c1, exp_c2 = st.columns(2)
    with exp_c1:
        st.text_area("Valeurs brutes", value=copy_text, height=70)
    with exp_c2:
        st.text_area(f"× {MULTIPLIER} (entiers)", value=", ".join(map(str, multiplied)), height=70)

    # ============================================================
    #  FOOTER
    # ============================================================
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;"
        "color:#2e4a5e;text-align:center;padding:0.5rem;'>"
        "GEX ANALYSER · Options Flow Intelligence · Data sourced from user CSV"
        "</div>",
        unsafe_allow_html=True
    )

    # ============================================================
    #  IV SKEW SECTION (optionnellement interactive)
    # ============================================================
    st.markdown('<div id="iv-skew"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📐 IV Skew — Smile de Volatilite")

    # Expiration selectionnee par slider
    expiry_options = sorted(df['Expiration Date_dt'].dropna().unique())
    expiry_labels  = [d.strftime('%a %b %d %Y') for d in expiry_options]
    selected_label = st.selectbox("Expiration", expiry_labels, index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0)
    selected_dt    = expiry_options[expiry_labels.index(selected_label)]

    df_skew = df[df['Expiration Date_dt'] == selected_dt].copy()
    for col in ["Strike","IV","IV.1","Delta","Delta.1","Open Interest","Open Interest.1"]:
        df_skew[col] = pd.to_numeric(df_skew[col], errors='coerce')

    df_c = df_skew[df_skew["IV"]   > 0][["Strike","IV","Delta","Open Interest"]].copy()
    df_p = df_skew[df_skew["IV.1"] > 0][["Strike","IV.1","Delta.1","Open Interest.1"]].copy()
    df_p.rename(columns={"IV.1":"IV","Delta.1":"Delta","Open Interest.1":"Open Interest"}, inplace=True)

    if not (df_c.empty or df_p.empty):
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
        sk4.metric("Skew 25d (P-C)",  f"{skew_pct:+.2f}%",
                   delta="Put premium" if skew_25 > 0 else "Call premium",
                   delta_color="inverse" if skew_25 < 0 else "normal")

        # Graphique IV Skew interactif
        from plotly.subplots import make_subplots
        
        fig_iv = go.Figure()
        
        df_c_s = df_c.sort_values("Strike")
        df_p_s = df_p.sort_values("Strike")
        
        fig_iv.add_trace(go.Scatter(
            x=df_c_s["Strike"], y=df_c_s["IV"]*100,
            mode='lines+markers',
            name='IV Calls',
            line=dict(color=COLORS['blue'], width=1.8),
            marker=dict(size=4, symbol='circle'),
            hovertemplate='<b>Strike: %{x:.2f}</b><br>IV Calls: %{y:.2f}%<extra></extra>'
        ))
        
        fig_iv.add_trace(go.Scatter(
            x=df_p_s["Strike"], y=df_p_s["IV"]*100,
            mode='lines+markers',
            name='IV Puts',
            line=dict(color=COLORS['red'], width=1.8, dash='dash'),
            marker=dict(size=4, symbol='circle'),
            hovertemplate='<b>Strike: %{x:.2f}</b><br>IV Puts: %{y:.2f}%<extra></extra>'
        ))
        
        # Zones colorées
        fig_iv.add_trace(go.Scatter(
            x=df_c_s["Strike"], y=df_c_s["IV"]*100,
            fill='tozeroy', fillcolor='rgba(0, 170, 255, 0.08)',
            line=dict(color='rgba(0,0,0,0)'), name='Zone Calls', showlegend=False
        ))
        
        fig_iv.add_trace(go.Scatter(
            x=df_p_s["Strike"], y=df_p_s["IV"]*100,
            fill='tozeroy', fillcolor='rgba(255, 60, 90, 0.08)',
            line=dict(color='rgba(0,0,0,0)'), name='Zone Puts', showlegend=False
        ))
        
        fig_iv.add_vline(x=atm, line_dash="dash", line_color=COLORS['green'], line_width=1.5,
                         annotation_text=f'ATM ({int(atm)})', annotation_position="top")
        
        if isinstance(put_wall, (int,float)):
            fig_iv.add_vline(x=put_wall, line_dash="dot", line_color=COLORS['red'], line_width=1,
                             annotation_text=f'Put Wall ({int(put_wall)})', annotation_position="bottom",
                             annotation_font_size=9)
        
        if isinstance(call_wall, (int,float)):
            fig_iv.add_vline(x=call_wall, line_dash="dot", line_color=COLORS['blue'], line_width=1,
                             annotation_text=f'Call Wall ({int(call_wall)})', annotation_position="top",
                             annotation_font_size=9)
        
        fig_iv.add_annotation(
            x=atm, y=atm_iv*100 + 1.5,
            text=f'Skew 25d: {skew_pct:+.2f}%',
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=COLORS['orange'],
            font=dict(size=9, color=COLORS['orange'])
        )
        
        fig_iv.update_layout(
            title=f'IV SKEW - {selected_label}',
            xaxis_title="Strike Price",
            yaxis_title="Implied Volatility (%)",
            hovermode='closest',
            **PLOTLY_TEMPLATE['layout']
        )
        
        st.plotly_chart(fig_iv, use_container_width=True, config={'displayModeBar': True})
        
        interp_color = COLORS['green'] if skew_25 > 0.005 else (COLORS['red'] if skew_25 < -0.005 else COLORS['orange'])
        if skew_25 > 0.015:
            msg = "Put premium eleve - le marche paye cher la protection baissiere (fear dominant)"
        elif skew_25 > 0.005:
            msg = "Skew modere - put premium normal, marche prudent mais pas en panique"
        elif skew_25 < -0.005:
            msg = "Call premium - le marche anticipe une hausse ou couvre des positions courtes"
        else:
            msg = "Skew quasi-nul - marche indecis, calls et puts valorises pareillement"

        st.markdown(
            f"<div style='background:{COLORS['card']};border:1px solid {COLORS['border']};"
            f"border-left:3px solid {COLORS['orange']};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{COLORS['text']};margin-top:0.5rem;'>"
            f"<b style='color:{COLORS['orange']};'>INTERPRETATION :</b> {msg}"
            f"</div>",
            unsafe_allow_html=True
        )

    # ============================================================
    #  DELTA EXPOSURE (DEX) SECTION avec graphiques interactifs
    # ============================================================
    st.markdown('<div id="dex"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🧭 Delta Exposure (DEX) — Biais Directionnel")

    selected_label_dex = st.selectbox("Expiration (DEX)", expiry_labels,
        index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
        key="dex_expiry")
    selected_dt_dex = expiry_options[expiry_labels.index(selected_label_dex)]

    df_dex_raw = df[df['Expiration Date_dt'] == selected_dt_dex].copy()
    for col in ["Strike","Delta","Delta.1","Open Interest","Open Interest.1"]:
        df_dex_raw[col] = pd.to_numeric(df_dex_raw[col], errors='coerce')

    df_dex_raw["DEX_Calls"] = df_dex_raw["Delta"]   * df_dex_raw["Open Interest"]   * df_dex_raw["Strike"] * 100
    df_dex_raw["DEX_Puts"]  = df_dex_raw["Delta.1"] * df_dex_raw["Open Interest.1"] * df_dex_raw["Strike"] * 100

    df_dex = df_dex_raw.groupby("Strike")[["DEX_Calls","DEX_Puts"]].sum().reset_index()
    df_dex["DEX_Total"] = df_dex["DEX_Calls"] + df_dex["DEX_Puts"]
    df_dex["ABS_DEX"]   = df_dex["DEX_Total"].abs()
    df_dex_sorted = df_dex.sort_values("Strike")

    net_dex      = df_dex["DEX_Total"].sum()
    is_bull_dex  = net_dex > 0
    dex_regime   = "HAUSSIER" if is_bull_dex else "BAISSIER"
    dex_color    = COLORS['green'] if is_bull_dex else COLORS['red']

    df_dex_pos = df_dex[df_dex["DEX_Calls"] > 0]
    df_dex_neg = df_dex[df_dex["DEX_Puts"]  < 0]
    delta_call_wall = df_dex_pos.loc[df_dex_pos["DEX_Calls"].idxmax(), "Strike"] if not df_dex_pos.empty else "N/A"
    delta_put_wall  = df_dex_neg.loc[df_dex_neg["DEX_Puts"].idxmin(),  "Strike"] if not df_dex_neg.empty else "N/A"

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

    # KPI cards
    d1c, d2c, d3c, d4c = st.columns(4)
    d1c.markdown(kpi_card("NET DEX", f"{net_dex:.2e}", dex_color, dex_regime), unsafe_allow_html=True)
    d2c.markdown(kpi_card("DELTA CALL WALL", delta_call_wall, COLORS['blue'], "Resistance delta"), unsafe_allow_html=True)
    d3c.markdown(kpi_card("DELTA PUT WALL", delta_put_wall, COLORS['red'], "Support delta"), unsafe_allow_html=True)
    d4c.markdown(kpi_card("ZERO DEX", zero_dex if zero_dex else 'N/A', COLORS['orange'], "Pivot directionnel"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Graphiques DEX interactifs
    top_n_dex = st.slider("Nombre de strikes (DEX)", 5, 60, 50, key="dex_slider")
    df_top_dex = df_dex.nlargest(top_n_dex, "ABS_DEX").sort_values("Strike")

    # Subplot: courbe DEX à gauche, barres à droite
    fig_dex = make_subplots(rows=1, cols=2, 
                            subplot_titles=("DELTA EXPOSURE - Courbe Totale", "DEX CALLS vs PUTS"),
                            horizontal_spacing=0.12)

    # Courbe DEX
    df_dex_pos_curve = df_top_dex[df_top_dex['DEX_Total'] >= 0]
    df_dex_neg_curve = df_top_dex[df_top_dex['DEX_Total'] < 0]

    if not df_dex_pos_curve.empty:
        fig_dex.add_trace(go.Scatter(
            x=df_dex_pos_curve["Strike"], y=df_dex_pos_curve["DEX_Total"],
            mode='lines+markers', name='DEX Total',
            line=dict(color=COLORS['blue'], width=1.8),
            marker=dict(size=4, color=COLORS['blue']),
            fill='tozeroy', fillcolor='rgba(0, 255, 157, 0.15)',
            hovertemplate='<b>Strike: %{x:.2f}</b><br>DEX: %{y:.2e}<extra></extra>'
        ), row=1, col=1)

    if not df_dex_neg_curve.empty:
        fig_dex.add_trace(go.Scatter(
            x=df_dex_neg_curve["Strike"], y=df_dex_neg_curve["DEX_Total"],
            mode='lines+markers', name='DEX Total',
            line=dict(color=COLORS['blue'], width=1.8),
            marker=dict(size=4, color=COLORS['blue']),
            fill='tozeroy', fillcolor='rgba(255, 60, 90, 0.15)',
            showlegend=False,
            hovertemplate='<b>Strike: %{x:.2f}</b><br>DEX: %{y:.2e}<extra></extra>'
        ), row=1, col=1)

    fig_dex.add_hline(y=0, line_dash="dash", line_color=COLORS['border'], row=1, col=1)

    if isinstance(delta_call_wall, (int,float)):
        fig_dex.add_vline(x=delta_call_wall, line_dash="dash", line_color=COLORS['blue'], 
                          annotation_text=f"DCW ({int(delta_call_wall)})", annotation_position="top",
                          row=1, col=1)
    if isinstance(delta_put_wall, (int,float)):
        fig_dex.add_vline(x=delta_put_wall, line_dash="dash", line_color=COLORS['red'],
                          annotation_text=f"DPW ({int(delta_put_wall)})", annotation_position="bottom",
                          row=1, col=1)

    # Barres Calls vs Puts
    df_comp = df_dex[df_dex["Strike"].isin(df_top_dex["Strike"])].sort_values("Strike")
    
    fig_dex.add_trace(go.Bar(
        x=df_comp["Strike"], y=df_comp["DEX_Calls"],
        name='DEX Calls', marker_color=COLORS['blue'], opacity=0.85,
        hovertemplate='<b>Strike: %{x:.2f}</b><br>DEX Calls: %{y:.2e}<extra></extra>'
    ), row=1, col=2)
    
    fig_dex.add_trace(go.Bar(
        x=df_comp["Strike"], y=df_comp["DEX_Puts"],
        name='DEX Puts', marker_color=COLORS['red'], opacity=0.85,
        hovertemplate='<b>Strike: %{x:.2f}</b><br>DEX Puts: %{y:.2e}<extra></extra>'
    ), row=1, col=2)

    fig_dex.add_hline(y=0, line_dash="dash", line_color=COLORS['border'], row=1, col=2)

    fig_dex.update_layout(
        title="Delta Exposure Analysis",
        hovermode='closest',
        barmode='group',
        showlegend=True,
        **PLOTLY_TEMPLATE['layout']
    )

    fig_dex.update_xaxes(title_text="Strike Price", row=1, col=1)
    fig_dex.update_yaxes(title_text="Delta Exposure (DEX)", row=1, col=1)
    fig_dex.update_xaxes(title_text="Strike Price", row=1, col=2)
    fig_dex.update_yaxes(title_text="DEX", row=1, col=2)

    st.plotly_chart(fig_dex, use_container_width=True, config={'displayModeBar': True})

    # Interpretation
    if net_dex > 0:
        if net_dex > 5e9:
            interp_dex = "DEX tres positif : les market makers sont massivement long delta -> hedging acheteur au-dessus du spot, frein naturel a la baisse"
        else:
            interp_dex = "DEX positif : biais directionnel haussier modere, les MM renforcent les hausses"
    else:
        if net_dex < -5e9:
            interp_dex = "DEX tres negatif : les market makers sont massivement short delta -> hedging vendeur sous le spot, acceleration possible a la baisse"
        else:
            interp_dex = "DEX negatif : biais directionnel baissier, les MM amplifient les baisses"

    st.markdown(
        f"<div style='background:{COLORS['card']};border:1px solid {COLORS['border']};"
        f"border-left:3px solid {dex_color};border-radius:8px;"
        f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
        f"font-size:0.82rem;color:{COLORS['text']};margin-top:0.5rem;'>"
        f"<b style='color:{dex_color};'>INTERPRETATION :</b> {interp_dex}"
        f"</div>",
        unsafe_allow_html=True
    )

    # Resume DEX
    st.markdown("#### 📋 Resume DEX")
    df_dex_summary = pd.DataFrame({
        'Metric': ['NET DEX', 'Regime', 'Delta Call Wall', 'Delta Put Wall', 'Zero DEX'],
        'Value':  [f"{net_dex:.2e}", dex_regime, delta_call_wall, delta_put_wall,
                   zero_dex if zero_dex else 'N/A']
    })
    st.dataframe(df_dex_summary, use_container_width=True, hide_index=True)

# Note: Les autres sections (Open Interest, Multi-Expiry, Options Chain, 
# Charm/Vanna, Volume Flow, Expected Move, GEX Weekly) peuvent être 
# converties de la même manière en utilisant plotly pour l'interactivité.
# Pour des raisons de longueur, je ne les ai pas toutes incluses ici,
# mais le principe est le même : remplacer plt par plotly.
