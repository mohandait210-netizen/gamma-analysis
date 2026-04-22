import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from datetime import datetime
from pathlib import Path
from scipy.stats import norm as sp_norm
import plotly.graph_objects as go
import plotly.express as px
from plotly_charts import plot_gex_curve, plot_iv_skew, plot_dex_curve, plot_volume_sentiment, plot_expected_move_term_structure

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
#  MATPLOTLIB DARK THEME
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

mpl.rcParams.update({
    "figure.facecolor":  DARK_BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   MUTED,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold",
    "axes.titlepad":     14,
    "axes.grid":         True,
    "grid.color":        BORDER,
    "grid.linewidth":    0.6,
    "xtick.color":       MUTED,
    "ytick.color":       MUTED,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  BORDER,
    "legend.labelcolor": TEXT,
    "legend.fontsize":   9,
    "text.color":        TEXT,
    "font.family":       "monospace",
})

# ============================================================
#  CONSTANTS
# ============================================================
MULTIPLIER_DEFAULT = 41.36  # Ratio QQQ → NQ Futures (change chaque jour)

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
    # entre le Put Wall et le Call Wall (definition correcte)
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
                break  # on prend le premier croisement entre les deux walls



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

    # Target Buy  = strike call dont le delta est le plus proche de 0.25
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
    regime_color = GREEN if is_positive else RED
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

    # Ligne 2 : EM + Target Buy/Sell
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.markdown(kpi_card("Expected Move ±", f"{em_value}" if em_value != "N/A" else "N/A", GREEN, f"ATM {int(atm_strike) if atm_strike else '—'}"), unsafe_allow_html=True)
    r2c2.markdown(kpi_card("EM+  /  EM−",
        f"{em_plus} / {em_minus}" if em_plus != "N/A" else "N/A",
        GREEN, "Zone de prix attendue"), unsafe_allow_html=True)
    r2c3.markdown(kpi_card("Target Buy",  f"{target_buy}",  "#34d399", "Call delta 25 — IV"), unsafe_allow_html=True)
    r2c4.markdown(kpi_card("Target Sell", f"{target_sell}", "#f87171", "Put delta 25 — IV"),  unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    #  GRAPHIQUES
    # ============================================================
    top_n = st.slider("Nombre de strikes dominants", 5, 50, 50)
    df_top_abs = df_gex_active.nlargest(top_n, 'ABS').sort_values("Strike")

    chart_col1, chart_col2 = st.columns(2)

    # -- Courbe GEX (Plotly interactive) --
    with chart_col1:
        fig_gex = plot_gex_curve(
            df_top_abs,
            call_wall,
            put_wall,
            zero_gamma,
            f"GAMMA EXPOSURE CURVE - {closest_expiration_date}"
        )
        st.plotly_chart(fig_gex, use_container_width=True, config={"displayModeBar": True})

    # -- Calls vs Puts --
    with chart_col2:
        df_gex_comp = (
            df_filtered[['Strike', 'GEX_Calls', 'GEX_Puts']]
            .dropna()
            .groupby('Strike')[['GEX_Calls', 'GEX_Puts']]
            .sum()
            .reset_index()
        )
        df_gex_comp = df_gex_comp[df_gex_comp['Strike'].isin(df_top_abs['Strike'])]

        fig2, ax2 = plt.subplots(figsize=(8, 4.5))
        bw = 0.4
        ax2.bar(df_gex_comp['Strike'] - bw/2, df_gex_comp['GEX_Calls'],
                bw, label='GEX Calls', color=BLUE, alpha=0.85)
        ax2.bar(df_gex_comp['Strike'] + bw/2, df_gex_comp['GEX_Puts'],
                bw, label='GEX Puts',  color=RED,  alpha=0.85)
        ax2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        ax2.set_title(f"CALLS vs PUTS - {closest_expiration_date}")
        ax2.legend(fontsize=8)
        fig2.tight_layout()
        st.pyplot(fig2)

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
#  IV SKEW SECTION
# ============================================================
st.markdown('<div id="iv-skew"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📐 IV Skew — Smile de Volatilite")

if uploaded_file is not None:

    # Expiration selectionnee par slider
    expiry_options = sorted(df['Expiration Date_dt'].dropna().unique())
    expiry_labels  = [d.strftime('%a %b %d %Y') for d in expiry_options]
    selected_label = st.selectbox("Expiration", expiry_labels, index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0)
    selected_dt    = expiry_options[expiry_labels.index(selected_label)]

    df_skew = df[df['Expiration Date_dt'] == selected_dt].copy()
    for col in ["Strike","IV","IV.1","Delta","Delta.1","Open Interest","Open Interest.1"]:
        df_skew[col] = pd.to_numeric(df_skew[col], errors='coerce')

    # Calls et Puts avec IV valide
    df_c = df_skew[df_skew["IV"]   > 0][["Strike","IV","Delta","Open Interest"]].copy()
    df_p = df_skew[df_skew["IV.1"] > 0][["Strike","IV.1","Delta.1","Open Interest.1"]].copy()
    df_p.rename(columns={"IV.1":"IV","Delta.1":"Delta","Open Interest.1":"Open Interest"}, inplace=True)

    if df_c.empty or df_p.empty:
        st.warning("Pas assez de donnees IV pour cette expiration.")
    else:
        # ATM = strike ou delta call est le plus proche de 0.5
        atm = df_c.iloc[(df_c['Delta'] - 0.5).abs().argsort()[:1]]['Strike'].values[0]

        # Skew metrics
        put_25  = df_p.iloc[(df_p['Delta'].abs() - 0.25).abs().argsort()[:1]]
        call_25 = df_c.iloc[(df_c['Delta'] - 0.25).abs().argsort()[:1]]
        atm_iv  = df_c.iloc[(df_c['Delta'] - 0.5).abs().argsort()[:1]]['IV'].values[0]
        skew_25 = put_25['IV'].values[0] - call_25['IV'].values[0]
        skew_pct = skew_25 * 100

        # KPI skew
        sk1, sk2, sk3, sk4 = st.columns(4)
        sk1.metric("ATM IV",          f"{atm_iv*100:.2f}%")
        sk2.metric("IV Put 25-delta", f"{put_25['IV'].values[0]*100:.2f}%", delta=f"strike {int(put_25['Strike'].values[0])}")
        sk3.metric("IV Call 25-delta",f"{call_25['IV'].values[0]*100:.2f}%", delta=f"strike {int(call_25['Strike'].values[0])}")
        sk4.metric("Skew 25d (P-C)",  f"{skew_pct:+.2f}%",
                   delta="Put premium" if skew_25 > 0 else "Call premium",
                   delta_color="inverse" if skew_25 < 0 else "normal")

        # Graphique
        fig3, ax3 = plt.subplots(figsize=(12, 5))

        # Trier par strike
        df_c_s = df_c.sort_values("Strike")
        df_p_s = df_p.sort_values("Strike")

        ax3.plot(df_c_s["Strike"], df_c_s["IV"]*100,
                 color=BLUE, linewidth=1.8, marker='o', markersize=3, label='IV Calls')
        ax3.plot(df_p_s["Strike"], df_p_s["IV"]*100,
                 color=RED,  linewidth=1.8, marker='o', markersize=3, label='IV Puts', linestyle='--')

        # Zones colorees
        ax3.fill_between(df_c_s["Strike"], df_c_s["IV"]*100,
                         alpha=0.08, color=BLUE)
        ax3.fill_between(df_p_s["Strike"], df_p_s["IV"]*100,
                         alpha=0.08, color=RED)

        # Lignes verticales cles
        ax3.axvline(x=atm, color=GREEN, linestyle='--', linewidth=1.5, label=f'ATM ({int(atm)})')
        if isinstance(put_wall,  (int,float)):
            ax3.axvline(x=put_wall,  color=RED,    linestyle=':', linewidth=1, alpha=0.7, label=f'Put Wall ({int(put_wall)})')
        if isinstance(call_wall, (int,float)):
            ax3.axvline(x=call_wall, color=BLUE,   linestyle=':', linewidth=1, alpha=0.7, label=f'Call Wall ({int(call_wall)})')

        # Annotation skew
        ax3.annotate(f'Skew 25d: {skew_pct:+.2f}%',
                     xy=(atm, atm_iv*100),
                     xytext=(atm + 8, atm_iv*100 + 1.5),
                     fontsize=9, color=ORANGE,
                     arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1))

        ax3.set_title(f'IV SKEW - {selected_label}', fontsize=13, fontweight='bold')
        ax3.set_xlabel("Strike Price")
        ax3.set_ylabel("Implied Volatility (%)")
        ax3.legend(fontsize=9)
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}%'))
        fig3.tight_layout()
        st.pyplot(fig3)

        # Interpretation
        interp_color = GREEN if skew_25 > 0.005 else (RED if skew_25 < -0.005 else ORANGE)
        if skew_25 > 0.015:
            msg = "Put premium eleve - le marche paye cher la protection baissiere (fear dominant)"
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


# ============================================================
#  DELTA EXPOSURE (DEX) SECTION
# ============================================================
st.markdown('<div id="dex"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 🧭 Delta Exposure (DEX) — Biais Directionnel")

if uploaded_file is not None:

    # Selecteur expiration
    selected_label_dex = st.selectbox("Expiration (DEX)", expiry_labels,
        index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
        key="dex_expiry")
    selected_dt_dex = expiry_options[expiry_labels.index(selected_label_dex)]

    df_dex_raw = df[df['Expiration Date_dt'] == selected_dt_dex].copy()
    for col in ["Strike","Delta","Delta.1","Open Interest","Open Interest.1"]:
        df_dex_raw[col] = pd.to_numeric(df_dex_raw[col], errors='coerce')

    # Calcul DEX
    # DEX = Delta * OI * Strike * 100
    # Delta call > 0  -> pression acheteuse quand le prix monte
    # Delta put  < 0  -> pression vendeuse quand le prix monte
    df_dex_raw["DEX_Calls"] = df_dex_raw["Delta"]   * df_dex_raw["Open Interest"]   * df_dex_raw["Strike"] * 100
    df_dex_raw["DEX_Puts"]  = df_dex_raw["Delta.1"] * df_dex_raw["Open Interest.1"] * df_dex_raw["Strike"] * 100

    df_dex = df_dex_raw.groupby("Strike")[["DEX_Calls","DEX_Puts"]].sum().reset_index()
    df_dex["DEX_Total"] = df_dex["DEX_Calls"] + df_dex["DEX_Puts"]
    df_dex["ABS_DEX"]   = df_dex["DEX_Total"].abs()
    df_dex_sorted = df_dex.sort_values("Strike")

    # Niveaux cles
    net_dex      = df_dex["DEX_Total"].sum()
    is_bull_dex  = net_dex > 0
    dex_regime   = "HAUSSIER" if is_bull_dex else "BAISSIER"
    dex_color    = GREEN if is_bull_dex else RED

    df_dex_pos = df_dex[df_dex["DEX_Calls"] > 0]
    df_dex_neg = df_dex[df_dex["DEX_Puts"]  < 0]
    delta_call_wall = df_dex_pos.loc[df_dex_pos["DEX_Calls"].idxmax(), "Strike"] if not df_dex_pos.empty else "N/A"
    delta_put_wall  = df_dex_neg.loc[df_dex_neg["DEX_Puts"].idxmin(),  "Strike"] if not df_dex_neg.empty else "N/A"

    # Zero DEX : croisement de la courbe DEX_Total avec y=0 entre les deux walls
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

    # --- KPI cards ---
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
        f"font-weight:600;color:{BLUE};'>{delta_call_wall}</div>"
        f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>Resistance delta</div>"
        f"</div>", unsafe_allow_html=True)
    d3c.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {RED};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>DELTA PUT WALL</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{RED};'>{delta_put_wall}</div>"
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

    # --- Graphiques cote a cote ---
    top_n_dex = st.slider("Nombre de strikes (DEX)", 5, 60, 50, key="dex_slider")
    df_top_dex = df_dex.nlargest(top_n_dex, "ABS_DEX").sort_values("Strike")

    fig_d1, fig_d2 = plt.subplots(1, 2, figsize=(14, 5))

    # -- Courbe DEX Total --
    ax_d1 = fig_d1
    ax_d1 = fig_d2  # on va utiliser subplots correctement
    fig_dex, (axd1, axd2) = plt.subplots(1, 2, figsize=(14, 5))

    # Courbe DEX total
    colors_dex = [GREEN if v >= 0 else RED for v in df_top_dex["DEX_Total"]]
    axd1.fill_between(df_top_dex["Strike"], df_top_dex["DEX_Total"], 0,
                      where=df_top_dex["DEX_Total"] >= 0, alpha=0.2, color=GREEN, interpolate=True)
    axd1.fill_between(df_top_dex["Strike"], df_top_dex["DEX_Total"], 0,
                      where=df_top_dex["DEX_Total"] < 0,  alpha=0.2, color=RED,   interpolate=True)
    axd1.plot(df_top_dex["Strike"], df_top_dex["DEX_Total"],
              color=BLUE, linewidth=1.8, marker='o', markersize=3, label='DEX Total')
    axd1.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

    if isinstance(delta_call_wall, (int,float)):
        axd1.axvline(x=delta_call_wall, color=BLUE,   linestyle='--', linewidth=1.2, label=f'Delta Call Wall ({int(delta_call_wall)})')
    if isinstance(delta_put_wall,  (int,float)):
        axd1.axvline(x=delta_put_wall,  color=RED,    linestyle='--', linewidth=1.2, label=f'Delta Put Wall ({int(delta_put_wall)})')
    if zero_dex:
        axd1.axvline(x=zero_dex, color=ORANGE, linestyle='--', linewidth=1.2, label=f'Zero DEX ({zero_dex})')

    axd1.set_title("DELTA EXPOSURE - Courbe Totale")
    axd1.set_xlabel("Strike Price")
    axd1.set_ylabel("Delta Exposure (DEX)")
    axd1.legend(fontsize=8)

    # Barres Calls vs Puts
    bar_w = 0.4
    df_comp = df_dex[df_dex["Strike"].isin(df_top_dex["Strike"])].sort_values("Strike")
    axd2.bar(df_comp["Strike"] - bar_w/2, df_comp["DEX_Calls"],
             bar_w, label='DEX Calls', color=BLUE,  alpha=0.85)
    axd2.bar(df_comp["Strike"] + bar_w/2, df_comp["DEX_Puts"],
             bar_w, label='DEX Puts',  color=RED,   alpha=0.85)
    axd2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
    axd2.set_title("DEX CALLS vs PUTS")
    axd2.set_xlabel("Strike Price")
    axd2.legend(fontsize=8)

    fig_dex.tight_layout()
    st.pyplot(fig_dex)

    # --- Interpretation ---
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
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {dex_color};border-radius:8px;"
        f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
        f"font-size:0.82rem;color:{TEXT};margin-top:0.5rem;'>"
        f"<b style='color:{dex_color};'>INTERPRETATION :</b> {interp_dex}"
        f"</div>",
        unsafe_allow_html=True
    )

    # --- Résumé DEX ---
    st.markdown("#### 📋 Resume DEX")
    df_dex_summary = pd.DataFrame({
        'Metric': ['NET DEX', 'Regime', 'Delta Call Wall', 'Delta Put Wall', 'Zero DEX'],
        'Value':  [f"{net_dex:.2e}", dex_regime, delta_call_wall, delta_put_wall,
                   zero_dex if zero_dex else 'N/A']
    })
    st.dataframe(df_dex_summary, use_container_width=True, hide_index=True)


# ============================================================
#  OPEN INTEREST ANALYSIS SECTION
# ============================================================
st.markdown('<div id="open-interest"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📊 Open Interest — Niveaux Cles & Positionnement")

if uploaded_file is not None:

    # Calcul OI global
    df_oi = df.copy()
    for col in ["Strike","Open Interest","Open Interest.1","Volume","Volume.1","Delta","Delta.1"]:
        df_oi[col] = pd.to_numeric(df_oi[col], errors='coerce')

    df_oi["OI_Calls"] = df_oi["Open Interest"].fillna(0)
    df_oi["OI_Puts"]  = df_oi["Open Interest.1"].fillna(0)
    df_oi["OI_Total"] = df_oi["OI_Calls"] + df_oi["OI_Puts"]
    df_oi["Vol_Total"]= df_oi["Volume"].fillna(0) + df_oi["Volume.1"].fillna(0)

    # PCR global
    total_oi_calls = df_oi["OI_Calls"].sum()
    total_oi_puts  = df_oi["OI_Puts"].sum()
    pcr_global     = total_oi_puts / total_oi_calls if total_oi_calls > 0 else 0

    # Par strike (toutes expirations)
    by_strike = df_oi.groupby("Strike")[["OI_Calls","OI_Puts","OI_Total","Vol_Total"]].sum().reset_index()
    by_strike["PCR"] = by_strike["OI_Puts"] / by_strike["OI_Calls"].replace(0, np.nan)

    # Par expiration
    by_exp = df_oi.groupby("Expiration Date_dt")[["OI_Calls","OI_Puts","OI_Total"]].sum().reset_index()
    by_exp["PCR"]   = by_exp["OI_Puts"] / by_exp["OI_Calls"].replace(0, np.nan)
    by_exp["Label"] = by_exp["Expiration Date_dt"].dt.strftime('%b %d')

    # Niveaux cles
    max_oi_strike     = by_strike.loc[by_strike["OI_Total"].idxmax(), "Strike"]
    max_call_strike   = by_strike.loc[by_strike["OI_Calls"].idxmax(), "Strike"]
    max_put_strike    = by_strike.loc[by_strike["OI_Puts"].idxmax(),  "Strike"]
    pcr_color         = RED if pcr_global > 1.2 else (GREEN if pcr_global < 0.8 else ORANGE)
    pcr_label         = "Bearish" if pcr_global > 1.2 else ("Bullish" if pcr_global < 0.8 else "Neutre")

    # --- KPI cards ---
    o1, o2, o3, o4 = st.columns(4)
    for col_ui, label, value, color, sub in [
        (o1, "PCR GLOBAL",       f"{pcr_global:.3f}", pcr_color, pcr_label),
        (o2, "MAX OI STRIKE",    int(max_oi_strike),  ORANGE,    "Niveau le + charge"),
        (o3, "MAX CALL STRIKE",  int(max_call_strike),BLUE,      "Resistance OI"),
        (o4, "MAX PUT STRIKE",   int(max_put_strike), RED,       "Support OI"),
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

    # --- Tabs pour les 3 vues ---
    tab_oi1, tab_oi2, tab_oi3 = st.tabs(["📊 OI par Strike", "📅 OI par Expiration", "🔥 Volume vs OI"])

    with tab_oi1:
        top_n_oi = st.slider("Nombre de strikes", 10, 80, 40, key="oi_slider")
        df_top_oi = by_strike.nlargest(top_n_oi, "OI_Total").sort_values("Strike")

        fig_oi, axoi = plt.subplots(figsize=(13, 5))
        bw = 0.4
        axoi.bar(df_top_oi["Strike"] - bw/2, df_top_oi["OI_Calls"],
                 bw, label="OI Calls", color=BLUE, alpha=0.85)
        axoi.bar(df_top_oi["Strike"] + bw/2, df_top_oi["OI_Puts"],
                 bw, label="OI Puts",  color=RED,  alpha=0.85)

        # Marquer les niveaux cles
        axoi.axvline(x=max_call_strike, color=BLUE,   linestyle='--', linewidth=1.2,
                     label=f"Max Call OI ({int(max_call_strike)})")
        axoi.axvline(x=max_put_strike,  color=RED,    linestyle='--', linewidth=1.2,
                     label=f"Max Put OI ({int(max_put_strike)})")
        axoi.axvline(x=max_oi_strike,   color=ORANGE, linestyle='--', linewidth=1.2,
                     label=f"Max Total OI ({int(max_oi_strike)})")

        axoi.set_title("OPEN INTEREST CALLS vs PUTS PAR STRIKE (toutes expirations)")
        axoi.set_xlabel("Strike")
        axoi.set_ylabel("Open Interest")
        axoi.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
        axoi.legend(fontsize=8)
        fig_oi.tight_layout()
        st.pyplot(fig_oi)

        # PCR par strike (heatmap textuelle)
        st.markdown("**Put/Call Ratio par strike (top 20 OI)**")
        df_pcr = by_strike.nlargest(20,"OI_Total")[["Strike","OI_Calls","OI_Puts","OI_Total","PCR"]].sort_values("Strike")
        df_pcr["Signal"] = df_pcr["PCR"].apply(
            lambda x: "🔴 Bearish" if x > 1.5 else ("🟢 Bullish" if x < 0.7 else "🟡 Neutre")
        )
        st.dataframe(df_pcr.style.format({
            "OI_Calls":"{:,.0f}", "OI_Puts":"{:,.0f}",
            "OI_Total":"{:,.0f}", "PCR":"{:.3f}"
        }), use_container_width=True, hide_index=True)

    with tab_oi2:
        fig_exp, (axe1, axe2) = plt.subplots(1, 2, figsize=(13, 5))

        # OI empile par expiration
        x_exp   = range(len(by_exp))
        axe1.bar(x_exp, by_exp["OI_Calls"], label="OI Calls", color=BLUE,  alpha=0.85)
        axe1.bar(x_exp, by_exp["OI_Puts"],  bottom=by_exp["OI_Calls"],
                 label="OI Puts",  color=RED,   alpha=0.85)
        axe1.set_xticks(list(x_exp))
        axe1.set_xticklabels(by_exp["Label"], rotation=45, ha='right', fontsize=8)
        axe1.set_title("OI TOTAL PAR EXPIRATION")
        axe1.set_ylabel("Open Interest")
        axe1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
        axe1.legend(fontsize=8)

        # PCR par expiration
        pcr_colors = [GREEN if p < 0.8 else (RED if p > 1.2 else ORANGE) for p in by_exp["PCR"]]
        axe2.bar(x_exp, by_exp["PCR"], color=pcr_colors, alpha=0.85)
        axe2.axhline(y=1.0, color=BORDER, linestyle='--', linewidth=1, label='PCR = 1')
        axe2.axhline(y=1.2, color=RED,    linestyle=':',  linewidth=1, alpha=0.5, label='Seuil bearish')
        axe2.axhline(y=0.8, color=GREEN,  linestyle=':',  linewidth=1, alpha=0.5, label='Seuil bullish')
        axe2.set_xticks(list(x_exp))
        axe2.set_xticklabels(by_exp["Label"], rotation=45, ha='right', fontsize=8)
        axe2.set_title("PUT/CALL RATIO PAR EXPIRATION")
        axe2.set_ylabel("PCR")
        axe2.legend(fontsize=8)

        fig_exp.tight_layout()
        st.pyplot(fig_exp)

        # Table recap
        by_exp_display = by_exp.copy()
        by_exp_display["Expiration"] = by_exp_display["Expiration Date_dt"].dt.strftime('%a %d %b %Y')
        by_exp_display["Signal"] = by_exp_display["PCR"].apply(
            lambda x: "🔴 Bearish" if x > 1.2 else ("🟢 Bullish" if x < 0.8 else "🟡 Neutre")
        )
        st.dataframe(
            by_exp_display[["Expiration","OI_Calls","OI_Puts","OI_Total","PCR","Signal"]]
            .style.format({"OI_Calls":"{:,.0f}","OI_Puts":"{:,.0f}",
                           "OI_Total":"{:,.0f}","PCR":"{:.3f}"}),
            use_container_width=True, hide_index=True)

    with tab_oi3:
        # Volume vs OI : detecter les nouveaux positionnements
        df_vol_oi = by_strike[by_strike["Vol_Total"] > 0].copy()
        df_vol_oi["Vol_OI_Ratio"] = df_vol_oi["Vol_Total"] / df_vol_oi["OI_Total"]
        df_top_vol = df_vol_oi.nlargest(40, "Vol_Total").sort_values("Strike")

        fig_vol, (axv1, axv2) = plt.subplots(1, 2, figsize=(13, 5))

        # Volume par strike
        axv1.bar(df_top_vol["Strike"], df_top_vol["Vol_Total"],
                 color=ORANGE, alpha=0.85, label="Volume Total")
        axv1.set_title("VOLUME PAR STRIKE (top 40)")
        axv1.set_xlabel("Strike")
        axv1.set_ylabel("Volume")
        axv1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))

        # Ratio Volume/OI (>1 = nouveau positionnement)
        ratio_colors = [RED if r > 1 else (ORANGE if r > 0.5 else MUTED)
                        for r in df_top_vol["Vol_OI_Ratio"]]
        axv2.bar(df_top_vol["Strike"], df_top_vol["Vol_OI_Ratio"],
                 color=ratio_colors, alpha=0.85)
        axv2.axhline(y=1.0, color=RED,    linestyle='--', linewidth=1.2,
                     label='Vol > OI (nouveau flux)')
        axv2.axhline(y=0.5, color=ORANGE, linestyle=':',  linewidth=1,
                     label='Vol > 50% OI')
        axv2.set_title("RATIO VOLUME / OI PAR STRIKE")
        axv2.set_xlabel("Strike")
        axv2.set_ylabel("Vol / OI")
        axv2.legend(fontsize=8)

        fig_vol.tight_layout()
        st.pyplot(fig_vol)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {ORANGE};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{ORANGE};'>LECTURE :</b> "
            f"Vol/OI > 1 = du volume depasse l'OI existant -> NOUVEAU positionnement (argent frais). "
            f"Vol/OI < 0.3 = activite faible sur l'OI existant -> positions anciennes non touchees."
            f"</div>",
            unsafe_allow_html=True)

    # --- Interpretation globale ---
    st.markdown("<br>", unsafe_allow_html=True)
    if pcr_global > 1.5:
        oi_msg = f"PCR = {pcr_global:.2f} : sentiment tres bearish, les options traders se protegent massivement - contrariant haussier potentiel si le marche tient"
        oi_color = RED
    elif pcr_global > 1.2:
        oi_msg = f"PCR = {pcr_global:.2f} : sentiment bearish modere, prudence dominante sur le marche"
        oi_color = RED
    elif pcr_global < 0.8:
        oi_msg = f"PCR = {pcr_global:.2f} : sentiment bullish, les calls dominent - risque de complaisance"
        oi_color = GREEN
    else:
        oi_msg = f"PCR = {pcr_global:.2f} : sentiment neutre, equilibre entre protection et speculation"
        oi_color = ORANGE

    st.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {oi_color};border-radius:8px;"
        f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
        f"font-size:0.82rem;color:{TEXT};'>"
        f"<b style='color:{oi_color};'>SENTIMENT OI :</b> {oi_msg}"
        f"</div>",
        unsafe_allow_html=True)


# ============================================================
#  GEX MULTI-EXPIRY SECTION
# ============================================================
st.markdown('<div id="multi-expiry"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📅 GEX Multi-Expiry — Comparaison des Profils")

if uploaded_file is not None:

    # Calcul GEX pour toutes les expirations
    df_all = df.copy()
    for col in ["Strike","Gamma","Gamma.1","Open Interest","Open Interest.1"]:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

    df_all["GEX_Calls"] = df_all["Gamma"]   * df_all["Open Interest"]   * (df_all["Strike"]**2) * 100
    df_all["GEX_Puts"]  = df_all["Gamma.1"] * df_all["Open Interest.1"] * (df_all["Strike"]**2) * 100 * -1
    df_all["GEX_Total"] = df_all["GEX_Calls"] + df_all["GEX_Puts"]
    df_all["ABS_GEX"]   = df_all["GEX_Calls"].abs() + df_all["GEX_Puts"].abs()

    all_exps    = sorted(df_all['Expiration Date_dt'].dropna().unique())
    exp_labels  = [d.strftime('%a %b %d') for d in all_exps]
    exp_map     = dict(zip(exp_labels, all_exps))

    # NET GEX par expiration
    by_exp_gex = df_all.groupby("Expiration Date_dt")[["GEX_Total","ABS_GEX"]].sum().reset_index()
    by_exp_gex["Label"]   = by_exp_gex["Expiration Date_dt"].dt.strftime('%a %b %d')
    by_exp_gex["Regime"]  = by_exp_gex["GEX_Total"].apply(lambda x: GREEN if x > 0 else RED)
    by_exp_gex["n_strikes"] = df_all.groupby("Expiration Date_dt")["Strike"].nunique().values

    # --- KPI: NET GEX cumule toutes expirations ---
    total_net_gex = by_exp_gex["GEX_Total"].sum()
    dominant_exp  = by_exp_gex.loc[by_exp_gex["ABS_GEX"].idxmax(), "Label"]
    all_positive  = (by_exp_gex["GEX_Total"] > 0).all()

    k1, k2, k3 = st.columns(3)
    for col_k, label, value, color, sub in [
        (k1, "NET GEX CUMULE",    f"{total_net_gex:.2e}", GREEN if total_net_gex > 0 else RED,
             "Toutes expirations"),
        (k2, "EXPIRATION DOMINANTE", dominant_exp,        ORANGE, "Plus grand ABS GEX"),
        (k3, "REGIME GLOBAL",     "ALL POSITIVE" if all_positive else "MIXTE",
             GREEN if all_positive else ORANGE, "Tendance marche"),
    ]:
        col_k.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
            f"font-weight:600;color:{color};'>{value}</div>"
            f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Tabs ---
    tab_mx1, tab_mx2, tab_mx3 = st.tabs([
        "📊 NET GEX par expiration",
        "🔀 Comparaison profils",
        "🌡️ Heatmap strikes x expiry"
    ])

    with tab_mx1:
        fig_mx1, (axm1, axm2) = plt.subplots(1, 2, figsize=(14, 5))

        # Barres NET GEX par expiration
        bar_colors = [GREEN if v > 0 else RED for v in by_exp_gex["GEX_Total"]]
        axm1.bar(range(len(by_exp_gex)), by_exp_gex["GEX_Total"],
                 color=bar_colors, alpha=0.85)
        axm1.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        axm1.set_xticks(range(len(by_exp_gex)))
        axm1.set_xticklabels(by_exp_gex["Label"], rotation=45, ha='right', fontsize=8)
        axm1.set_title("NET GEX PAR EXPIRATION")
        axm1.set_ylabel("Net GEX")
        axm1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))

        # ABS GEX (poids de chaque expiration)
        axm2.bar(range(len(by_exp_gex)), by_exp_gex["ABS_GEX"],
                 color=BLUE, alpha=0.75)
        axm2.set_xticks(range(len(by_exp_gex)))
        axm2.set_xticklabels(by_exp_gex["Label"], rotation=45, ha='right', fontsize=8)
        axm2.set_title("POIDS GEX ABSOLU PAR EXPIRATION")
        axm2.set_ylabel("ABS GEX")
        axm2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))

        fig_mx1.tight_layout()
        st.pyplot(fig_mx1)

        # Table recap
        tbl = by_exp_gex[["Label","GEX_Total","ABS_GEX","n_strikes"]].copy()
        tbl["Regime"] = tbl["GEX_Total"].apply(lambda x: "🟢 Positive" if x > 0 else "🔴 Negative")
        tbl["Poids%"] = (tbl["ABS_GEX"] / tbl["ABS_GEX"].sum() * 100).round(1)
        tbl.rename(columns={"Label":"Expiration","GEX_Total":"Net GEX",
                             "ABS_GEX":"ABS GEX","n_strikes":"Strikes"}, inplace=True)
        st.dataframe(tbl.style.format({
            "Net GEX":"{:.2e}", "ABS GEX":"{:.2e}", "Poids%":"{:.1f}%"
        }), use_container_width=True, hide_index=True)

    with tab_mx2:
        # Selecteur multi-expiration
        selected_exps = st.multiselect(
            "Choisir les expirations a comparer",
            options=exp_labels,
            default=exp_labels[:4]
        )

        if len(selected_exps) < 2:
            st.warning("Selectionnez au moins 2 expirations.")
        else:
            # Palette de couleurs pour les courbes
            palette = [BLUE, GREEN, ORANGE, RED, "#a78bfa", "#34d399", "#fb923c", "#f472b6",
                       "#38bdf8", "#facc15"]

            fig_mx2, ax_mx2 = plt.subplots(figsize=(13, 6))

            for i, label in enumerate(selected_exps):
                dt_sel = exp_map[label]
                df_exp = df_all[df_all["Expiration Date_dt"] == dt_sel]
                df_g   = df_exp.groupby("Strike")[["GEX_Total","ABS_GEX"]].sum().reset_index()
                df_g   = df_g[df_g["ABS_GEX"] > 0].sort_values("Strike")

                color = palette[i % len(palette)]
                ax_mx2.plot(df_g["Strike"], df_g["GEX_Total"],
                            linewidth=1.6, marker='o', markersize=2,
                            label=label, color=color, alpha=0.9)

            ax_mx2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
            ax_mx2.set_title("COMPARAISON PROFILS GEX PAR EXPIRATION")
            ax_mx2.set_xlabel("Strike Price")
            ax_mx2.set_ylabel("GEX")
            ax_mx2.legend(fontsize=9, loc='upper left')
            fig_mx2.tight_layout()
            st.pyplot(fig_mx2)

            # Niveaux cles par expiration selectionnee
            st.markdown("**Niveaux cles par expiration selectionnee**")
            rows = []
            for label in selected_exps:
                dt_sel = exp_map[label]
                df_exp = df_all[df_all["Expiration Date_dt"] == dt_sel]
                df_g   = df_exp.groupby("Strike")[["GEX_Total","ABS_GEX","GEX_Calls","GEX_Puts"]].sum().reset_index()
                df_g   = df_g[df_g["ABS_GEX"] > 0]

                net    = df_g["GEX_Total"].sum()
                df_pos = df_g[df_g["GEX_Total"] > 0]
                df_neg = df_g[df_g["GEX_Total"] < 0]
                cw = df_pos.loc[df_pos["GEX_Total"].idxmax(),"Strike"] if not df_pos.empty else "N/A"
                pw = df_neg.loc[df_neg["GEX_Total"].idxmin(),"Strike"] if not df_neg.empty else "N/A"

                # Zero gamma entre pw et cw
                zg = "N/A"
                if isinstance(cw,(int,float)) and isinstance(pw,(int,float)):
                    lo, hi = min(cw,pw), max(cw,pw)
                    df_bt  = df_g[(df_g["Strike"]>=lo)&(df_g["Strike"]<=hi)&(df_g["ABS_GEX"]>0)].sort_values("Strike").reset_index(drop=True)
                    for ii in range(len(df_bt)-1):
                        g0,g1 = df_bt["GEX_Total"].iloc[ii], df_bt["GEX_Total"].iloc[ii+1]
                        s0,s1 = df_bt["Strike"].iloc[ii],    df_bt["Strike"].iloc[ii+1]
                        if g0*g1 < 0:
                            zg = round(s0+(0-g0)*(s1-s0)/(g1-g0), 1)
                            break

                rows.append({"Expiration":label, "Net GEX":f"{net:.2e}",
                             "Regime":"🟢 POS" if net>0 else "🔴 NEG",
                             "Call Wall":cw, "Put Wall":pw, "Zero Gamma":zg})

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab_mx3:
        st.markdown("**GEX par strike et expiration — intensite relative**")

        # Construire la heatmap : lignes = strikes actifs, colonnes = expirations
        strike_range = st.slider("Zone strikes", int(df_all["Strike"].min()),
                                 int(df_all["Strike"].max()),
                                 (580, 700), step=5, key="heatmap_strikes")

        df_heat = df_all[
            (df_all["Strike"] >= strike_range[0]) &
            (df_all["Strike"] <= strike_range[1])
        ].groupby(["Strike","Expiration Date_dt"])["GEX_Total"].sum().reset_index()

        pivot = df_heat.pivot(index="Strike", columns="Expiration Date_dt", values="GEX_Total").fillna(0)
        pivot.columns = [c.strftime('%b %d') for c in pivot.columns]
        pivot = pivot.sort_index(ascending=False)

        fig_heat, ax_heat = plt.subplots(figsize=(13, max(6, len(pivot)*0.25)))

        import matplotlib.colors as mcolors
        cmap = mcolors.LinearSegmentedColormap.from_list(
            "gex", [RED, DARK_BG, GREEN], N=256)

        vmax = pivot.abs().max().max()
        im = ax_heat.imshow(pivot.values, cmap=cmap, aspect='auto',
                            vmin=-vmax, vmax=vmax)

        ax_heat.set_xticks(range(len(pivot.columns)))
        ax_heat.set_xticklabels(pivot.columns, fontsize=8)
        ax_heat.set_yticks(range(len(pivot.index)))
        ax_heat.set_yticklabels([f"{int(s)}" for s in pivot.index], fontsize=7)
        ax_heat.set_title("HEATMAP GEX — Rouge=Puts dominant / Vert=Calls dominant")

        plt.colorbar(im, ax=ax_heat, fraction=0.02, pad=0.02,
                     label="GEX (negatif=Puts, positif=Calls)")
        fig_heat.tight_layout()
        st.pyplot(fig_heat)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {BLUE};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{BLUE};'>LECTURE :</b> "
            f"Les colonnes vertes = expirations Call-dominantes (marche pince). "
            f"Les zones rouges persistantes sur plusieurs expirations = niveaux de support gamma fort. "
            f"Un strike vert sur toutes les expirations = resistance gamma majeure."
            f"</div>",
            unsafe_allow_html=True)


# ============================================================
#  OPTIONS CHAIN INTERACTIVE
# ============================================================
st.markdown('<div id="options-chain"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 🔗 Options Chain — Calls | Strike | Puts")

if uploaded_file is not None:

    # Selecteurs
    oc1, oc2, oc3 = st.columns([2, 1, 1])
    with oc1:
        chain_exp_label = st.selectbox("Expiration", expiry_labels,
            index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
            key="chain_expiry")
    with oc2:
        show_atm_only = st.checkbox("Zone ATM uniquement", value=False)
    with oc3:
        atm_range = st.slider("Strikes autour ATM", 5, 50, 20, key="chain_atm_range") if show_atm_only else None

    chain_dt = expiry_options[expiry_labels.index(chain_exp_label)]
    df_chain = df[df['Expiration Date_dt'] == chain_dt].copy()

    for col in ["Strike","Last Sale","Bid","Ask","Net","Volume","IV","Delta","Gamma","Open Interest",
                "Last Sale.1","Net.1","Bid.1","Ask.1","Volume.1","IV.1","Delta.1","Gamma.1","Open Interest.1"]:
        df_chain[col] = pd.to_numeric(df_chain[col], errors='coerce')

    df_chain = df_chain.sort_values("Strike").reset_index(drop=True)

    # ATM strike = delta call le plus proche de 0.5
    df_with_delta = df_chain[df_chain["Delta"].notna() & (df_chain["Delta"] > 0)]
    if not df_with_delta.empty:
        atm_strike = df_with_delta.iloc[(df_with_delta["Delta"] - 0.5).abs().argsort()[:1]]["Strike"].values[0]
    else:
        atm_strike = df_chain["Strike"].median()

    if show_atm_only and atm_range:
        df_chain = df_chain[
            (df_chain["Strike"] >= atm_strike - atm_range) &
            (df_chain["Strike"] <= atm_strike + atm_range)
        ].reset_index(drop=True)

    # Construire le tableau chain
    def fmt_num(val, decimals=2, suffix=""):
        try:
            v = float(val)
            if v == 0 or pd.isna(v): return "-"
            return f"{v:,.{decimals}f}{suffix}"
        except: return "-"

    def fmt_pct(val):
        try:
            v = float(val)
            if v == 0 or pd.isna(v): return "-"
            return f"{v*100:.1f}%"
        except: return "-"

    def fmt_int(val):
        try:
            v = int(float(val))
            if v == 0: return "-"
            return f"{v:,}"
        except: return "-"

    rows = []
    for _, r in df_chain.iterrows():
        strike = r["Strike"]
        is_atm = abs(strike - atm_strike) <= 1

        rows.append({
            # CALLS
            "OI C":     fmt_int(r["Open Interest"]),
            "Vol C":    fmt_int(r["Volume"]),
            "IV C":     fmt_pct(r["IV"]),
            "Delta C":  fmt_num(r["Delta"], 3),
            "Gamma C":  fmt_num(r["Gamma"], 4),
            "Bid C":    fmt_num(r["Bid"]),
            "Ask C":    fmt_num(r["Ask"]),
            "Last C":   fmt_num(r["Last Sale"]),
            # STRIKE
            "⚡ STRIKE": f"{'★ ' if is_atm else ''}{int(strike)}",
            # PUTS
            "Last P":   fmt_num(r["Last Sale.1"]),
            "Bid P":    fmt_num(r["Bid.1"]),
            "Ask P":    fmt_num(r["Ask.1"]),
            "Gamma P":  fmt_num(r["Gamma.1"], 4),
            "Delta P":  fmt_num(r["Delta.1"], 3),
            "IV P":     fmt_pct(r["IV.1"]),
            "Vol P":    fmt_int(r["Volume.1"]),
            "OI P":     fmt_int(r["Open Interest.1"]),
        })

    df_display = pd.DataFrame(rows)

    # CSS pour colorier la colonne strike et les lignes ATM
    def style_chain(df_s):
        styles = pd.DataFrame("", index=df_s.index, columns=df_s.columns)

        for i, row in df_s.iterrows():
            strike_val = row["⚡ STRIKE"].replace("★ ", "")
            try:
                is_atm_row = abs(float(strike_val) - atm_strike) <= 1
            except: is_atm_row = False

            for col in df_s.columns:
                if col == "⚡ STRIKE":
                    if is_atm_row:
                        styles.at[i, col] = f"background-color: {ORANGE}22; color: {ORANGE}; font-weight: bold; text-align: center;"
                    else:
                        styles.at[i, col] = f"background-color: {CARD_BG}; color: {TEXT}; font-weight: bold; text-align: center;"
                elif col.endswith(" C"):
                    styles.at[i, col] = f"color: {BLUE}; text-align: right;"
                elif col.endswith(" P"):
                    styles.at[i, col] = f"color: {RED}; text-align: right;"

        return styles

    # Affichage
    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
        f"color:{MUTED};margin-bottom:0.5rem;'>"
        f"★ = ATM ({int(atm_strike)})&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"<span style='color:{BLUE}'>■ CALLS</span>&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"<span style='color:{RED}'>■ PUTS</span>&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{len(df_chain)} strikes affichés — {chain_exp_label}"
        f"</div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        df_display.style.apply(style_chain, axis=None),
        use_container_width=True,
        hide_index=True,
        height=min(600, len(df_display) * 36 + 40)
    )

    # --- Mini stats ATM ---
    st.markdown("<br>", unsafe_allow_html=True)
    atm_row = df_chain[df_chain["Strike"] == atm_strike]
    if not atm_row.empty:
        r = atm_row.iloc[0]
        spread_call = round(float(r["Ask"]) - float(r["Bid"]), 2) if pd.notna(r["Ask"]) and pd.notna(r["Bid"]) else "N/A"
        spread_put  = round(float(r["Ask.1"]) - float(r["Bid.1"]), 2) if pd.notna(r["Ask.1"]) and pd.notna(r["Bid.1"]) else "N/A"
        em_atm      = round(float(r["Last Sale"]) + float(r["Last Sale.1"]), 2) if pd.notna(r["Last Sale"]) and pd.notna(r["Last Sale.1"]) else "N/A"

        st.markdown(f"**Stats ATM — Strike {int(atm_strike)}**")
        ms1, ms2, ms3, ms4, ms5 = st.columns(5)
        for col_ms, label, value, color in [
            (ms1, "IV ATM Call",    fmt_pct(r["IV"]),          BLUE),
            (ms2, "IV ATM Put",     fmt_pct(r["IV.1"]),        RED),
            (ms3, "Spread Call",    f"{spread_call}",           MUTED),
            (ms4, "Spread Put",     f"{spread_put}",            MUTED),
            (ms5, "Expected Move",  f"±{em_atm}",              ORANGE),
        ]:
            col_ms.markdown(
                f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
                f"border-left:3px solid {color};border-radius:6px;padding:0.75rem 1rem;'>"
                f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;"
                f"color:{MUTED};letter-spacing:0.08em;text-transform:uppercase;"
                f"margin-bottom:0.3rem;'>{label}</div>"
                f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.1rem;"
                f"font-weight:600;color:{color};'>{value}</div>"
                f"</div>", unsafe_allow_html=True)


# ============================================================
#  CHARM & VANNA SECTION
# ============================================================
st.markdown('<div id="charm-vanna"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### ⚗️ Charm & Vanna — Greeks du 2e Ordre")

# Explication pedagogique
with st.expander("📖 C'est quoi Charm et Vanna ? (cliquer pour lire)", expanded=False):
    st.markdown(f"""
<div style='font-family:IBM Plex Mono,monospace;font-size:0.82rem;
color:{TEXT};line-height:1.8;'>

<b style='color:{ORANGE};'>CHARM (Delta Decay)</b> = dDelta / dTemps<br>
→ A quelle vitesse le delta d'une option change avec le temps.<br>
→ Charm positif : le delta monte avec le temps (call ITM).<br>
→ Charm negatif : le delta baisse avec le temps (call OTM).<br><br>

<b style='color:{BLUE};'>Comment utiliser Charm pour trader ?</b><br>
• En fin de semaine (jeudi/vendredi), le Charm s'accelere.<br>
• Les options proches de l'ATM voient leur delta se desintegrer vite.<br>
• Les MM doivent de-hedger massivement → cree des flux directionnels.<br>
• <b style='color:{GREEN};'>CharmEx negatif</b> = les MM vont vendre des actions pour se de-hedger → pression baissiere.<br>
• <b style='color:{GREEN};'>CharmEx positif</b> = les MM vont acheter → pression haussiere.<br><br>

<b style='color:{ORANGE};'>VANNA (Delta-Vol Sensitivity)</b> = dDelta / dIV = dVega / dSpot<br>
→ Comment le delta change quand la volatilite change.<br>
→ Vanna positif : quand IV monte, delta monte (puts OTM).<br>
→ Vanna negatif : quand IV monte, delta baisse (calls OTM).<br><br>

<b style='color:{BLUE};'>Comment utiliser Vanna pour trader ?</b><br>
• Quand la volatilite baisse (VIX crush), les MM doivent re-hedger.<br>
• <b style='color:{GREEN};'>VannaEx positif + VIX baisse</b> = les MM achevent des actions → rally.<br>
• <b style='color:{GREEN};'>VannaEx negatif + VIX monte</b> = les MM vendent → acceleration baissiere.<br>
• Le "Vanna rally" post-opex est tres connu : VIX baisse apres expiration → flux acheteurs.<br><br>

<b style='color:{RED};'>Combinaison Charm + Vanna :</b><br>
• En approche d'expiration : Charm domine (effet temps).<br>
• En mouvement de vol : Vanna domine (effet IV).<br>
• Les deux ensemble = feuille de route des flux MM pour la semaine.

</div>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    # Parametres
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
        df_cv[col] = pd.to_numeric(df_cv[col], errors='coerce')

    T_cv_days = max((cv_dt - pd.Timestamp(datetime.now().date())).days, 1)
    T_cv      = T_cv_days / 365.0

    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
        f"color:{MUTED};margin:0.5rem 0;'>T = {T_cv_days} jours | "
        f"T_ann = {T_cv:.5f} | Spot = {spot_input}</div>",
        unsafe_allow_html=True)

    # Fonctions Greeks 2e ordre
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

    # Calcul vectorisé
    strikes_cv = df_cv["Strike"].values
    iv_c_cv    = df_cv["IV"].values
    iv_p_cv    = df_cv["IV.1"].values
    oi_c_cv    = df_cv["Open Interest"].fillna(0).values
    oi_p_cv    = df_cv["Open Interest.1"].fillna(0).values

    ch_c, ch_p, va_c, va_p = [], [], [], []
    for i in range(len(strikes_cv)):
        ch_c.append(calc_charm_fn(spot_input, strikes_cv[i], T_cv, rate_input, iv_c_cv[i]) if iv_c_cv[i] > 0 else np.nan)
        ch_p.append(calc_charm_fn(spot_input, strikes_cv[i], T_cv, rate_input, iv_p_cv[i]) if iv_p_cv[i] > 0 else np.nan)
        va_c.append(calc_vanna_fn(spot_input, strikes_cv[i], T_cv, rate_input, iv_c_cv[i]) if iv_c_cv[i] > 0 else np.nan)
        va_p.append(calc_vanna_fn(spot_input, strikes_cv[i], T_cv, rate_input, iv_p_cv[i]) if iv_p_cv[i] > 0 else np.nan)

    df_cv["Charm_Call"] = ch_c
    df_cv["Charm_Put"]  = ch_p
    df_cv["Vanna_Call"] = va_c
    df_cv["Vanna_Put"]  = va_p

    df_cv["CharmEx_Call"] = df_cv["Charm_Call"] * oi_c_cv * strikes_cv * 100
    df_cv["CharmEx_Put"]  = df_cv["Charm_Put"]  * oi_p_cv * strikes_cv * 100 * -1
    df_cv["VannaEx_Call"] = df_cv["Vanna_Call"] * oi_c_cv * strikes_cv * 100
    df_cv["VannaEx_Put"]  = df_cv["Vanna_Put"]  * oi_p_cv * strikes_cv * 100 * -1
    df_cv["CharmEx"]      = df_cv["CharmEx_Call"].fillna(0) + df_cv["CharmEx_Put"].fillna(0)
    df_cv["VannaEx"]      = df_cv["VannaEx_Call"].fillna(0) + df_cv["VannaEx_Put"].fillna(0)

    df_cv_gex = df_cv.groupby("Strike")[["CharmEx","VannaEx"]].sum().reset_index()
    df_cv_gex = df_cv_gex[df_cv_gex[["CharmEx","VannaEx"]].abs().sum(axis=1) > 0]

    net_charm = df_cv_gex["CharmEx"].sum()
    net_vanna = df_cv_gex["VannaEx"].sum()

    # --- KPI cards ---
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

    # --- Graphiques ---
    top_n_cv = st.slider("Nombre de strikes", 5, 60, 40, key="cv_slider")
    df_cv_top = df_cv_gex.assign(
        ABS=df_cv_gex["CharmEx"].abs() + df_cv_gex["VannaEx"].abs()
    ).nlargest(top_n_cv, "ABS").sort_values("Strike")

    tab_charm, tab_vanna, tab_combined = st.tabs(["⏱️ Charm Exposure", "🌊 Vanna Exposure", "🔀 Vue combinée"])

    with tab_charm:
        fig_ch, ax_ch = plt.subplots(figsize=(13, 5))
        colors_ch = [GREEN if v >= 0 else RED for v in df_cv_top["CharmEx"]]
        ax_ch.bar(df_cv_top["Strike"], df_cv_top["CharmEx"],
                  color=colors_ch, alpha=0.85, width=0.6)
        ax_ch.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)
        ax_ch.axvline(x=spot_input, color=ORANGE, linestyle='--', linewidth=1.5,
                      label=f'Spot ({spot_input})')
        ax_ch.set_title(f"CHARM EXPOSURE PAR STRIKE — {cv_exp_label}  (T={T_cv_days}j)")
        ax_ch.set_xlabel("Strike")
        ax_ch.set_ylabel("Charm Exposure")
        ax_ch.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_ch.legend(fontsize=9)
        fig_ch.tight_layout()
        st.pyplot(fig_ch)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {charm_col};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{charm_col};'>CHARM SIGNAL :</b> "
            f"CharmEx NET = {net_charm:.2e} → les MM vont "
            f"{'<b>ACHETER</b> des actions pour maintenir leur hedge' if net_charm > 0 else '<b>VENDRE</b> des actions en se de-hedgeant'}"
            f" au fil du temps. Effet amplifié en fin de semaine (T→0)."
            f"</div>", unsafe_allow_html=True)

    with tab_vanna:
        fig_va, ax_va = plt.subplots(figsize=(13, 5))
        colors_va = [GREEN if v >= 0 else RED for v in df_cv_top["VannaEx"]]
        ax_va.bar(df_cv_top["Strike"], df_cv_top["VannaEx"],
                  color=colors_va, alpha=0.85, width=0.6)
        ax_va.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)
        ax_va.axvline(x=spot_input, color=ORANGE, linestyle='--', linewidth=1.5,
                      label=f'Spot ({spot_input})')
        ax_va.set_title(f"VANNA EXPOSURE PAR STRIKE — {cv_exp_label}")
        ax_va.set_xlabel("Strike")
        ax_va.set_ylabel("Vanna Exposure")
        ax_va.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_va.legend(fontsize=9)
        fig_va.tight_layout()
        st.pyplot(fig_va)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {vanna_col};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{vanna_col};'>VANNA SIGNAL :</b> "
            f"VannaEx NET = {net_vanna:.2e} → si le VIX "
            f"{'<b>BAISSE</b> → flux acheteurs MM (rally). Si VIX monte → flux vendeurs.' if net_vanna > 0 else '<b>MONTE</b> → flux vendeurs MM (sell-off). Si VIX baisse → flux acheteurs.'}"
            f"</div>", unsafe_allow_html=True)

    with tab_combined:
        fig_comb, (ax_c1, ax_c2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

        ax_c1.fill_between(df_cv_top["Strike"], df_cv_top["CharmEx"], 0,
                           where=df_cv_top["CharmEx"] >= 0, color=GREEN, alpha=0.3, interpolate=True)
        ax_c1.fill_between(df_cv_top["Strike"], df_cv_top["CharmEx"], 0,
                           where=df_cv_top["CharmEx"] < 0,  color=RED,   alpha=0.3, interpolate=True)
        ax_c1.plot(df_cv_top["Strike"], df_cv_top["CharmEx"],
                   color=ORANGE, linewidth=1.8, marker='o', markersize=3, label='Charm')
        ax_c1.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        ax_c1.axvline(x=spot_input, color=ORANGE, linestyle=':', linewidth=1, alpha=0.6)
        ax_c1.set_title("CHARM EXPOSURE (effet temps)")
        ax_c1.set_ylabel("Charm Ex")
        ax_c1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_c1.legend(fontsize=9)

        ax_c2.fill_between(df_cv_top["Strike"], df_cv_top["VannaEx"], 0,
                           where=df_cv_top["VannaEx"] >= 0, color=GREEN, alpha=0.3, interpolate=True)
        ax_c2.fill_between(df_cv_top["Strike"], df_cv_top["VannaEx"], 0,
                           where=df_cv_top["VannaEx"] < 0,  color=RED,   alpha=0.3, interpolate=True)
        ax_c2.plot(df_cv_top["Strike"], df_cv_top["VannaEx"],
                   color=BLUE, linewidth=1.8, marker='o', markersize=3, label='Vanna')
        ax_c2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        ax_c2.axvline(x=spot_input, color=ORANGE, linestyle=':', linewidth=1, alpha=0.6,
                      label=f'Spot ({spot_input})')
        ax_c2.set_title("VANNA EXPOSURE (effet volatilite)")
        ax_c2.set_xlabel("Strike")
        ax_c2.set_ylabel("Vanna Ex")
        ax_c2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_c2.legend(fontsize=9)

        fig_comb.tight_layout()
        st.pyplot(fig_comb)

        # Tableau top strikes
        st.markdown("**Top strikes par exposition (Charm + Vanna)**")
        df_cv_table = df_cv_gex.assign(
            ABS_Total=df_cv_gex["CharmEx"].abs()+df_cv_gex["VannaEx"].abs()
        ).nlargest(10,"ABS_Total")[["Strike","CharmEx","VannaEx"]].copy()
        df_cv_table["Charm Signal"] = df_cv_table["CharmEx"].apply(
            lambda x: "🟢 Acheteur" if x > 0 else "🔴 Vendeur")
        df_cv_table["Vanna Signal"] = df_cv_table["VannaEx"].apply(
            lambda x: "🟢 VIX crush -> up" if x > 0 else "🔴 VIX spike -> down")
        st.dataframe(df_cv_table.style.format({
            "CharmEx":"{:.2e}", "VannaEx":"{:.2e}"
        }), use_container_width=True, hide_index=True)


# ============================================================
#  VOLUME FLOW & UNUSUAL ACTIVITY SECTION
# ============================================================
st.markdown('<div id="volume-flow"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 🔥 Volume Flow — Détection Flux Inhabituels")

if uploaded_file is not None:

    df_vol = df.copy()
    for col in ["Strike","Volume","Volume.1","Open Interest","Open Interest.1",
                "Bid","Ask","Bid.1","Ask.1","Last Sale","Last Sale.1","IV","IV.1","Delta","Delta.1"]:
        df_vol[col] = pd.to_numeric(df_vol[col], errors='coerce')

    df_vol["Vol_C"]   = df_vol["Volume"].fillna(0)
    df_vol["Vol_P"]   = df_vol["Volume.1"].fillna(0)
    df_vol["OI_C"]    = df_vol["Open Interest"].fillna(0)
    df_vol["OI_P"]    = df_vol["Open Interest.1"].fillna(0)
    df_vol["Vol_Tot"] = df_vol["Vol_C"] + df_vol["Vol_P"]
    df_vol["Spread_C"]= df_vol["Ask"]   - df_vol["Bid"]
    df_vol["Spread_P"]= df_vol["Ask.1"] - df_vol["Bid.1"]

    # Ratio Vol/OI
    df_vol["VoI_C"] = df_vol["Vol_C"] / df_vol["OI_C"].replace(0, np.nan)
    df_vol["VoI_P"] = df_vol["Vol_P"] / df_vol["OI_P"].replace(0, np.nan)

    # Classification du trade : achat sur Ask = bullish, vente sur Bid = bearish
    # Heuristique : Last Sale >= Ask -> achat agressif | Last Sale <= Bid -> vente agressive
    def classify_flow(last, bid, ask):
        try:
            l,b,a = float(last), float(bid), float(ask)
            mid = (b+a)/2
            if l >= a:   return "🟢 Achat agressif"
            elif l <= b: return "🔴 Vente agressive"
            elif l > mid: return "🟡 Achat passif"
            else:         return "🟠 Vente passive"
        except: return "⚪ Inconnu"

    df_vol["Flow_C"] = [classify_flow(r["Last Sale"],   r["Bid"],   r["Ask"])   for _, r in df_vol.iterrows()]
    df_vol["Flow_P"] = [classify_flow(r["Last Sale.1"], r["Bid.1"], r["Ask.1"]) for _, r in df_vol.iterrows()]

    # Stats globales
    total_vol_c = df_vol["Vol_C"].sum()
    total_vol_p = df_vol["Vol_P"].sum()
    pcr_vol     = total_vol_p / total_vol_c if total_vol_c > 0 else 0

    # Seuil "inhabituel" = p95 du volume non-nul
    p95_c = df_vol[df_vol["Vol_C"]>0]["Vol_C"].quantile(0.95)
    p95_p = df_vol[df_vol["Vol_P"]>0]["Vol_P"].quantile(0.95)
    p95_voi = 2.0  # Vol/OI > 2 = argent frais certain

    # Flux inhabituels
    df_unusual = df_vol[
        (df_vol["Vol_C"] > p95_c) | (df_vol["Vol_P"] > p95_p) |
        (df_vol["VoI_C"] > p95_voi) | (df_vol["VoI_P"] > p95_voi)
    ].copy()

    pcr_col   = GREEN if pcr_vol < 0.8 else (RED if pcr_vol > 1.2 else ORANGE)
    pcr_lbl   = "Bullish" if pcr_vol < 0.8 else ("Bearish" if pcr_vol > 1.2 else "Neutre")

    # --- KPI ---
    fv1, fv2, fv3, fv4 = st.columns(4)
    for col_fv, label, value, color, sub in [
        (fv1, "VOL CALLS TOTAL",  f"{total_vol_c:,.0f}", BLUE,    "Tous strikes/expirations"),
        (fv2, "VOL PUTS TOTAL",   f"{total_vol_p:,.0f}", RED,     "Tous strikes/expirations"),
        (fv3, "PCR VOLUME",       f"{pcr_vol:.3f}",      pcr_col, pcr_lbl),
        (fv4, "FLUX INHABITUELS", f"{len(df_unusual)}",  ORANGE,  f"Vol>p95 ou Vol/OI>2"),
    ]:
        col_fv.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
            f"font-weight:600;color:{color};'>{value}</div>"
            f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>{sub}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_v1, tab_v2, tab_v3, tab_v4 = st.tabs([
        "📊 Volume par Strike",
        "🚨 Flux Inhabituels",
        "💰 Argent Frais (Vol/OI)",
        "🎯 Strikes Dominants"
    ])

    with tab_v1:
        # Selecteur expiration
        vol_exp = st.selectbox("Expiration", ["Toutes"] + expiry_labels, key="vol_exp")
        if vol_exp == "Toutes":
            df_plot = df_vol.groupby("Strike")[["Vol_C","Vol_P","Vol_Tot"]].sum().reset_index()
        else:
            dt_sel  = expiry_options[expiry_labels.index(vol_exp)]
            df_plot = df_vol[df_vol["Expiration Date_dt"]==dt_sel].groupby(
                "Strike")[["Vol_C","Vol_P","Vol_Tot"]].sum().reset_index()

        top_n_vol = st.slider("Strikes affichés", 10, 80, 40, key="vol_slider")
        df_plot_top = df_plot.nlargest(top_n_vol,"Vol_Tot").sort_values("Strike")

        fig_v1, (axv1, axv2) = plt.subplots(1, 2, figsize=(14, 5))

        bw = 0.4
        axv1.bar(df_plot_top["Strike"]-bw/2, df_plot_top["Vol_C"],
                 bw, color=BLUE, alpha=0.85, label="Vol Calls")
        axv1.bar(df_plot_top["Strike"]+bw/2, df_plot_top["Vol_P"],
                 bw, color=RED,  alpha=0.85, label="Vol Puts")
        axv1.set_title("VOLUME CALLS vs PUTS PAR STRIKE")
        axv1.set_xlabel("Strike")
        axv1.set_ylabel("Volume")
        axv1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
        axv1.legend(fontsize=9)

        # PCR volume par strike
        df_plot_top["PCR_vol"] = df_plot_top["Vol_P"] / df_plot_top["Vol_C"].replace(0, np.nan)
        pcr_colors = [GREEN if p < 0.8 else (RED if p > 1.2 else ORANGE)
                      for p in df_plot_top["PCR_vol"].fillna(1)]
        axv2.bar(df_plot_top["Strike"], df_plot_top["PCR_vol"].fillna(0),
                 color=pcr_colors, alpha=0.85)
        axv2.axhline(y=1.0, color=BORDER, linestyle='--', linewidth=1, label='PCR=1')
        axv2.axhline(y=1.2, color=RED,    linestyle=':',  linewidth=1, alpha=0.5)
        axv2.axhline(y=0.8, color=GREEN,  linestyle=':',  linewidth=1, alpha=0.5)
        axv2.set_title("PUT/CALL RATIO VOLUME PAR STRIKE")
        axv2.set_xlabel("Strike")
        axv2.set_ylabel("PCR Volume")
        axv2.legend(fontsize=9)

        fig_v1.tight_layout()
        st.pyplot(fig_v1)

    with tab_v2:
        st.markdown(f"**{len(df_unusual)} lignes avec activité anormale détectée**")

        # Seuil configurable
        min_vol = st.slider("Volume minimum", 100, 10000, 1000, step=100, key="unusual_minvol")
        min_voi = st.slider("Vol/OI minimum", 1.0, 20.0, 2.0, step=0.5, key="unusual_minvoi")

        df_unu = df_vol[
            ((df_vol["Vol_C"] >= min_vol) | (df_vol["Vol_P"] >= min_vol)) &
            ((df_vol["VoI_C"] >= min_voi) | (df_vol["VoI_P"] >= min_voi))
        ].copy()

        if df_unu.empty:
            st.warning("Aucun flux inhabituel avec ces seuils. Réduisez les filtres.")
        else:
            # Calls inhabituels
            df_unu_c = df_unu[df_unu["Vol_C"] >= min_vol].copy()
            df_unu_c = df_unu_c[df_unu_c["VoI_C"] >= min_voi]
            if not df_unu_c.empty:
                st.markdown(f"<b style='color:{BLUE};'>🔵 CALLS inhabituels ({len(df_unu_c)})</b>", unsafe_allow_html=True)
                tbl_c = df_unu_c.nlargest(15,"Vol_C")[
                    ["Expiration Date","Strike","Vol_C","OI_C","VoI_C",
                     "Bid","Ask","Last Sale","IV","Delta","Flow_C"]
                ].copy()
                tbl_c.columns = ["Expiry","Strike","Volume","OI","Vol/OI",
                                  "Bid","Ask","Last","IV","Delta","Signal"]
                tbl_c["IV"] = tbl_c["IV"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "-")
                tbl_c["Vol/OI"] = tbl_c["Vol/OI"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) else "-")
                st.dataframe(tbl_c.style.format({
                    "Volume":"{:,.0f}","OI":"{:,.0f}",
                    "Bid":"{:.2f}","Ask":"{:.2f}","Last":"{:.2f}","Delta":"{:.3f}"
                }), use_container_width=True, hide_index=True)

            # Puts inhabituels
            df_unu_p = df_unu[df_unu["Vol_P"] >= min_vol].copy()
            df_unu_p = df_unu_p[df_unu_p["VoI_P"] >= min_voi]
            if not df_unu_p.empty:
                st.markdown(f"<b style='color:{RED};'>🔴 PUTS inhabituels ({len(df_unu_p)})</b>", unsafe_allow_html=True)
                tbl_p = df_unu_p.nlargest(15,"Vol_P")[
                    ["Expiration Date","Strike","Vol_P","OI_P","VoI_P",
                     "Bid.1","Ask.1","Last Sale.1","IV.1","Delta.1","Flow_P"]
                ].copy()
                tbl_p.columns = ["Expiry","Strike","Volume","OI","Vol/OI",
                                  "Bid","Ask","Last","IV","Delta","Signal"]
                tbl_p["IV"] = tbl_p["IV"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "-")
                tbl_p["Vol/OI"] = tbl_p["Vol/OI"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) else "-")
                st.dataframe(tbl_p.style.format({
                    "Volume":"{:,.0f}","OI":"{:,.0f}",
                    "Bid":"{:.2f}","Ask":"{:.2f}","Last":"{:.2f}","Delta":"{:.3f}"
                }), use_container_width=True, hide_index=True)

    with tab_v3:
        st.markdown("**Vol/OI > 1 = argent frais entrant (position nouvelle, pas du roulement)**")

        fig_voi, (axvoi1, axvoi2) = plt.subplots(1, 2, figsize=(14, 5))

        by_s_all = df_vol.groupby("Strike")[["Vol_C","Vol_P","OI_C","OI_P"]].sum().reset_index()
        by_s_all["VoI_C"] = by_s_all["Vol_C"] / by_s_all["OI_C"].replace(0, np.nan)
        by_s_all["VoI_P"] = by_s_all["Vol_P"] / by_s_all["OI_P"].replace(0, np.nan)
        by_s_top = by_s_all[by_s_all["Vol_C"]+by_s_all["Vol_P"] > 500].sort_values("Strike")

        voi_c_colors = [RED if v > 5 else (ORANGE if v > 2 else BLUE)
                        for v in by_s_top["VoI_C"].fillna(0)]
        voi_p_colors = [RED if v > 5 else (ORANGE if v > 2 else RED)
                        for v in by_s_top["VoI_P"].fillna(0)]

        axvoi1.bar(by_s_top["Strike"], by_s_top["VoI_C"].fillna(0),
                   color=voi_c_colors, alpha=0.85)
        axvoi1.axhline(y=1,  color=ORANGE, linestyle='--', linewidth=1, label='Vol=OI')
        axvoi1.axhline(y=5,  color=RED,    linestyle='--', linewidth=1, label='Vol=5x OI')
        axvoi1.set_title("VOL/OI CALLS — Rouge = flux massif")
        axvoi1.set_xlabel("Strike")
        axvoi1.set_ylabel("Vol/OI")
        axvoi1.legend(fontsize=8)

        axvoi2.bar(by_s_top["Strike"], by_s_top["VoI_P"].fillna(0),
                   color=voi_p_colors, alpha=0.85)
        axvoi2.axhline(y=1,  color=ORANGE, linestyle='--', linewidth=1, label='Vol=OI')
        axvoi2.axhline(y=5,  color=RED,    linestyle='--', linewidth=1, label='Vol=5x OI')
        axvoi2.set_title("VOL/OI PUTS — Rouge = flux massif")
        axvoi2.set_xlabel("Strike")
        axvoi2.set_ylabel("Vol/OI")
        axvoi2.legend(fontsize=8)

        fig_voi.tight_layout()
        st.pyplot(fig_voi)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {ORANGE};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{ORANGE};'>LECTURE Vol/OI :</b> "
            f"🔵 Vol/OI &lt; 1 = roulement de positions existantes. "
            f"🟠 Vol/OI 1-5 = nouveaux entrants significatifs. "
            f"🔴 Vol/OI &gt; 5 = flux massif, probable trade institutionnel ou event-driven."
            f"</div>", unsafe_allow_html=True)

    with tab_v4:
        st.markdown("**Visualisation du sentiment directionnel par strike**")

        by_s_exp = df_vol.groupby(["Strike","Expiration Date_dt"])[
            ["Vol_C","Vol_P","OI_C","OI_P"]].sum().reset_index()
        by_s_exp = by_s_exp[by_s_exp["Vol_C"]+by_s_exp["Vol_P"] > 0]
        by_s_exp["Bull_Score"] = by_s_exp["Vol_C"] / (by_s_exp["Vol_C"]+by_s_exp["Vol_P"])
        by_s_exp["Label"] = by_s_exp["Expiration Date_dt"].dt.strftime('%b %d')

        by_s_total = df_vol.groupby("Strike")[["Vol_C","Vol_P"]].sum().reset_index()
        by_s_total = by_s_total[by_s_total["Vol_C"]+by_s_total["Vol_P"] > 500]
        by_s_total["Bull_Score"] = by_s_total["Vol_C"] / (by_s_total["Vol_C"]+by_s_total["Vol_P"])
        by_s_total = by_s_total.sort_values("Strike")

        fig_sent, ax_sent = plt.subplots(figsize=(13, 5))
        sent_colors = [GREEN if b > 0.6 else (RED if b < 0.4 else ORANGE)
                       for b in by_s_total["Bull_Score"]]
        bars = ax_sent.bar(by_s_total["Strike"], by_s_total["Bull_Score"]-0.5,
                           color=sent_colors, alpha=0.85, bottom=0.5)
        ax_sent.axhline(y=0.5, color=BORDER, linestyle='--', linewidth=1.5)
        ax_sent.axhline(y=0.6, color=GREEN,  linestyle=':',  linewidth=1, alpha=0.6, label='60% Calls')
        ax_sent.axhline(y=0.4, color=RED,    linestyle=':',  linewidth=1, alpha=0.6, label='60% Puts')
        ax_sent.set_title("SENTIMENT VOLUME PAR STRIKE (% Calls vs Puts)")
        ax_sent.set_xlabel("Strike")
        ax_sent.set_ylabel("% Volume Calls")
        ax_sent.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y*100:.0f}%'))
        ax_sent.set_ylim(0, 1)
        ax_sent.legend(fontsize=9)
        ax_sent.fill_between(ax_sent.get_xlim(), 0.5, 1.0, alpha=0.03, color=GREEN)
        ax_sent.fill_between(ax_sent.get_xlim(), 0.0, 0.5, alpha=0.03, color=RED)
        fig_sent.tight_layout()
        st.pyplot(fig_sent)

        # Top 3 signaux les plus forts
        top_bull = by_s_total.nlargest(3,"Bull_Score")[["Strike","Vol_C","Vol_P","Bull_Score"]]
        top_bear = by_s_total.nsmallest(3,"Bull_Score")[["Strike","Vol_C","Vol_P","Bull_Score"]]

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"<b style='color:{GREEN};'>🟢 Strikes les plus Bullish</b>", unsafe_allow_html=True)
            top_bull["Bull_Score"] = top_bull["Bull_Score"].apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(top_bull.style.format({"Vol_C":"{:,.0f}","Vol_P":"{:,.0f}"}),
                         use_container_width=True, hide_index=True)
        with sc2:
            st.markdown(f"<b style='color:{RED};'>🔴 Strikes les plus Bearish</b>", unsafe_allow_html=True)
            top_bear["Bull_Score"] = top_bear["Bull_Score"].apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(top_bear.style.format({"Vol_C":"{:,.0f}","Vol_P":"{:,.0f}"}),
                         use_container_width=True, hide_index=True)


# ============================================================
#  EXPECTED MOVE AUTO — TOUTES EXPIRATIONS
# ============================================================
st.markdown('<div id="expected-move"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📐 Expected Move — Toutes Expirations")

if uploaded_file is not None:

    # Calcul EM pour toutes les expirations
    em_results = []
    current_dt = pd.Timestamp(datetime.now().date())

    for exp_dt, group in df.groupby("Expiration Date_dt"):
        for col in ["Strike","Last Sale","Last Sale.1","Bid","Ask","Bid.1","Ask.1",
                    "IV","IV.1","Delta","Delta.1"]:
            group[col] = pd.to_numeric(group[col], errors='coerce')

        g_atm = group[group["Delta"].notna() & (group["Delta"] > 0)].copy()
        if g_atm.empty: continue

        # ATM = strike dont le delta call est le plus proche de 0.5
        atm_row    = g_atm.iloc[(g_atm["Delta"] - 0.5).abs().argsort().iloc[0]]
        atm_strike = atm_row["Strike"]
        iv_atm     = atm_row["IV"]
        T_days     = max((exp_dt - current_dt).days, 1)

        # Recuperer la ligne put du meme strike
        put_row = group[group["Strike"] == atm_strike]

        ls_c  = atm_row["Last Sale"]
        ls_p  = put_row["Last Sale.1"].values[0]  if len(put_row) > 0 else np.nan
        bid_c = atm_row["Bid"];  ask_c = atm_row["Ask"]
        bid_p = put_row["Bid.1"].values[0]  if len(put_row) > 0 else np.nan
        ask_p = put_row["Ask.1"].values[0]  if len(put_row) > 0 else np.nan

        # EM Straddle (Last Sale)
        em_ls  = round(ls_c  + ls_p,  2) if pd.notna(ls_c)  and pd.notna(ls_p)  else np.nan
        # EM Midpoint Bid/Ask (plus precis)
        mid_c  = (bid_c+ask_c)/2 if pd.notna(bid_c) and pd.notna(ask_c) else np.nan
        mid_p  = (bid_p+ask_p)/2 if pd.notna(bid_p) and pd.notna(ask_p) else np.nan
        em_mid = round(mid_c + mid_p, 2) if pd.notna(mid_c) and pd.notna(mid_p) else np.nan
        # EM formule IV : IV * Spot * sqrt(T/365)
        em_iv  = round(iv_atm * atm_strike * np.sqrt(T_days/365), 2) \
                 if pd.notna(iv_atm) and iv_atm > 0 else np.nan

        em_use = em_mid if pd.notna(em_mid) else em_ls   # preferer midpoint

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

    # --- Methode selecteur ---
    em_method = st.radio(
        "Méthode de calcul",
        ["Midpoint Bid/Ask (recommandé)", "Last Sale Straddle", "Formule IV Black-Scholes"],
        horizontal=True, key="em_method"
    )
    method_col = {"Midpoint Bid/Ask (recommandé)": "em_mid",
                  "Last Sale Straddle":             "em_straddle",
                  "Formule IV Black-Scholes":        "em_iv"}[em_method]

    df_em["em_sel"]    = df_em[method_col]
    df_em["em_plus_s"] = df_em["atm"] + df_em["em_sel"]
    df_em["em_minus_s"]= df_em["atm"] - df_em["em_sel"]
    df_em["em_pct_s"]  = df_em["em_sel"] / df_em["atm"] * 100

    # --- KPI expiration la plus proche ---
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

    tab_em1, tab_em2, tab_em3 = st.tabs([
        "📊 EM par Expiration", "🌡️ Courbe de Volatilité", "📋 Tableau complet"
    ])

    with tab_em1:
        fig_em, (axe1, axe2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

        x   = range(len(df_em))
        lbl = df_em["label"].tolist()

        # Graphique EM± par expiration (zone de prix attendue)
        axe1.fill_between(x,
                          df_em["em_minus_s"].fillna(df_em["atm"]),
                          df_em["em_plus_s"].fillna(df_em["atm"]),
                          alpha=0.2, color=BLUE, label="Zone EM")
        axe1.plot(x, df_em["em_plus_s"],  color=GREEN, linewidth=2,
                  marker='o', markersize=5, label="EM+")
        axe1.plot(x, df_em["em_minus_s"], color=RED,   linewidth=2,
                  marker='o', markersize=5, label="EM-")
        axe1.plot(x, df_em["atm"],        color=ORANGE, linewidth=1.5,
                  linestyle='--', marker='s', markersize=4, label="ATM Strike")

        # Annotations
        for i, row in df_em.iterrows():
            if pd.notna(row["em_sel"]):
                axe1.annotate(f"±{row['em_sel']:.1f}",
                    xy=(i, row["em_plus_s"]),
                    xytext=(0, 6), textcoords='offset points',
                    fontsize=7, color=GREEN, ha='center')

        axe1.set_xticks(list(x))
        axe1.set_xticklabels(lbl, rotation=30, ha='right', fontsize=8)
        axe1.set_title(f"EXPECTED MOVE PAR EXPIRATION — {em_method}")
        axe1.set_ylabel("Prix QQQ")
        axe1.legend(fontsize=8)

        # EM en % par expiration
        bar_colors_em = [GREEN if v < 2 else (ORANGE if v < 4 else RED)
                         for v in df_em["em_pct_s"].fillna(0)]
        axe2.bar(x, df_em["em_pct_s"].fillna(0), color=bar_colors_em, alpha=0.85)
        axe2.set_xticks(list(x))
        axe2.set_xticklabels(lbl, rotation=30, ha='right', fontsize=8)
        axe2.set_title("EXPECTED MOVE EN % DU SPOT")
        axe2.set_ylabel("EM (%)")
        axe2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1f}%'))
        axe2.axhline(y=2, color=ORANGE, linestyle=':', linewidth=1, alpha=0.7, label='2%')
        axe2.axhline(y=4, color=RED,    linestyle=':', linewidth=1, alpha=0.7, label='4%')
        axe2.legend(fontsize=8)

        fig_em.tight_layout()
        st.pyplot(fig_em)

    with tab_em2:
        # Term structure de la IV ATM
        fig_ts, (axts1, axts2) = plt.subplots(1, 2, figsize=(13, 5))

        df_em_valid = df_em[df_em["iv_atm"].notna() & (df_em["iv_atm"] > 0)]

        axts1.plot(df_em_valid["T_days"], df_em_valid["iv_atm"]*100,
                   color=BLUE, linewidth=2, marker='o', markersize=6)
        for _, row in df_em_valid.iterrows():
            axts1.annotate(row["label"],
                xy=(row["T_days"], row["iv_atm"]*100),
                xytext=(3, 4), textcoords='offset points',
                fontsize=7, color=MUTED)
        axts1.set_title("TERM STRUCTURE IV ATM")
        axts1.set_xlabel("Jours avant expiration")
        axts1.set_ylabel("IV ATM (%)")
        axts1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1f}%'))
        axts1.grid(True, alpha=0.3)

        # EM vs T_days : doit etre proportionnel a sqrt(T)
        t_range = np.linspace(1, df_em["T_days"].max()+2, 100)
        iv_ref  = df_em_valid["iv_atm"].mean()
        spot_ref= df_em_valid["atm"].mean()
        em_theory = iv_ref * spot_ref * np.sqrt(t_range/365)

        axts2.scatter(df_em_valid["T_days"], df_em_valid["em_sel"],
                      color=ORANGE, s=80, zorder=5, label="EM réel")
        axts2.plot(t_range, em_theory, color=BLUE, linewidth=1.5,
                   linestyle='--', alpha=0.7, label=f"Théorie sqrt(T) IV={iv_ref*100:.1f}%")
        for _, row in df_em_valid.iterrows():
            if pd.notna(row["em_sel"]):
                axts2.annotate(row["label"],
                    xy=(row["T_days"], row["em_sel"]),
                    xytext=(3,4), textcoords='offset points',
                    fontsize=7, color=MUTED)
        axts2.set_title("EM RÉEL vs THÉORIE sqrt(T)")
        axts2.set_xlabel("Jours avant expiration")
        axts2.set_ylabel("Expected Move ($)")
        axts2.legend(fontsize=8)

        fig_ts.tight_layout()
        st.pyplot(fig_ts)

        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {BLUE};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{BLUE};'>LECTURE TERM STRUCTURE :</b> "
            f"Si la courbe IV est en backwardation (court terme > long terme) → marche stresse, "
            f"event imminent. En contango (court < long) → calme, normalite. "
            f"EM reel au-dessus de la theorie sqrt(T) → marche pricant une surprise."
            f"</div>", unsafe_allow_html=True)

    with tab_em3:
        # Tableau complet toutes methodes
        df_tbl = df_em[["label","T_days","atm","iv_atm",
                         "em_straddle","em_mid","em_iv",
                         "em_plus_s","em_minus_s","em_pct_s"]].copy()
        df_tbl.columns = ["Expiration","Jours","ATM","IV ATM",
                          "EM Last Sale","EM Midpoint","EM Formule IV",
                          "EM+","EM−","EM %"]
        df_tbl["IV ATM"] = df_tbl["IV ATM"].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
        df_tbl["EM %"]   = df_tbl["EM %"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")

        st.dataframe(df_tbl.style.format({
            "EM Last Sale":"{:.2f}", "EM Midpoint":"{:.2f}",
            "EM Formule IV":"{:.2f}", "EM+":"{:.2f}", "EM−":"{:.2f}"
        }), use_container_width=True, hide_index=True)

        # Export texte copiable (format de votre app originale)
        st.markdown("**Export copiable (EM+ / EM− par expiration)**")
        lines_em = []
        for _, row in df_em.iterrows():
            if pd.notna(row["em_sel"]):
                lines_em.append(
                    f"{row['label']} | ATM {row['atm']} | "
                    f"EM ±{row['em_sel']:.2f} | EM+ {row['em_plus_s']:.2f} | EM- {row['em_minus_s']:.2f}"
                )
        st.text_area("Texte copiable", value="\n".join(lines_em), height=200)

        # Multiplier (comme dans app originale)
        st.markdown(f"**Export multiplié × {MULTIPLIER} (entiers)**")
        lines_mult = []
        for _, row in df_em.iterrows():
            if pd.notna(row["em_plus_s"]) and pd.notna(row["em_minus_s"]):
                ep = int(round(row["em_plus_s"]  * MULTIPLIER))
                em = int(round(row["em_minus_s"] * MULTIPLIER))
                lines_mult.append(f"{row['label']} | EM+ {ep} | EM- {em}")
        st.text_area(f"Texte multiplié × {MULTIPLIER}", value="\n".join(lines_mult), height=200)


# ============================================================
#  GEX WEEKLY — Cumul Lundi -> Vendredi
# ============================================================
st.markdown('<div id="gex-weekly"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📅 GEX Weekly — Cumul de la Semaine")

if uploaded_file is not None:

    # Detecter la semaine en cours et les semaines disponibles
    all_exps_dt = sorted(df['Expiration Date_dt'].dropna().unique())

    # Construire la liste des semaines disponibles dans le CSV
    weeks = {}
    for d in all_exps_dt:
        monday = d - pd.Timedelta(days=d.weekday())
        friday = monday + pd.Timedelta(days=4)
        key    = monday.strftime('%d %b')
        label  = f"Sem. {monday.strftime('%d %b')} → {friday.strftime('%d %b %Y')}"
        if key not in weeks:
            weeks[key] = {"label": label, "monday": monday, "friday": friday, "exps": []}
        weeks[key]["exps"].append(d)

    week_labels = [v["label"] for v in weeks.values()]
    week_keys   = list(weeks.keys())

    # Semaine en cours par defaut
    today_ts = pd.Timestamp(datetime.now().date())
    current_monday = today_ts - pd.Timedelta(days=today_ts.weekday())
    current_key    = current_monday.strftime('%d %b')
    default_idx    = week_keys.index(current_key) if current_key in week_keys else 0

    selected_week_label = st.selectbox(
        "Semaine", week_labels, index=default_idx, key="weekly_selector"
    )
    selected_week = weeks[week_keys[week_labels.index(selected_week_label)]]
    week_exps     = selected_week["exps"]
    week_days     = [d.strftime('%a %d %b') for d in week_exps]

    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.78rem;"
        f"color:{MUTED};margin-bottom:1rem;'>"
        f"Expirations incluses : "
        + " · ".join([f"<span style='color:{TEXT};'>{d}</span>" for d in week_days])
        + f"</div>", unsafe_allow_html=True)

    # Calcul GEX pour toutes les expirations de la semaine
    df_week_all = df[df['Expiration Date_dt'].isin(week_exps)].copy()
    for col in ["Strike","Gamma","Gamma.1","Open Interest","Open Interest.1"]:
        df_week_all[col] = pd.to_numeric(df_week_all[col], errors='coerce')

    df_week_all["GEX_Calls"] = df_week_all["Gamma"]   * df_week_all["Open Interest"]   * (df_week_all["Strike"]**2) * 100
    df_week_all["GEX_Puts"]  = df_week_all["Gamma.1"] * df_week_all["Open Interest.1"] * (df_week_all["Strike"]**2) * 100 * -1
    df_week_all["GEX_Total"] = df_week_all["GEX_Calls"] + df_week_all["GEX_Puts"]
    df_week_all["ABS_GEX"]   = df_week_all["GEX_Calls"].abs() + df_week_all["GEX_Puts"].abs()

    # GEX Weekly cumule par strike
    wgex = df_week_all.groupby("Strike")[
        ["GEX_Total","ABS_GEX","GEX_Calls","GEX_Puts"]
    ].sum().reset_index()
    wgex = wgex[wgex["ABS_GEX"] > 0].sort_values("Strike").reset_index(drop=True)

    # GEX par jour (pour la decomposition)
    gex_by_day = {}
    for d in week_exps:
        df_d   = df_week_all[df_week_all["Expiration Date_dt"] == d]
        gex_d  = df_d.groupby("Strike")["GEX_Total"].sum().reset_index()
        gex_d.rename(columns={"GEX_Total": d.strftime('%a')}, inplace=True)
        gex_by_day[d.strftime('%a')] = gex_d

    # Niveaux cles weekly
    net_wgex  = wgex["GEX_Total"].sum()
    is_pos_w  = net_wgex > 0
    wgex_col  = GREEN if is_pos_w else RED

    df_wpos   = wgex[wgex["GEX_Total"] > 0]
    df_wneg   = wgex[wgex["GEX_Total"] < 0]
    wcall_wall= df_wpos.loc[df_wpos["GEX_Total"].idxmax(), "Strike"] if not df_wpos.empty else "N/A"
    wput_wall = df_wneg.loc[df_wneg["GEX_Total"].idxmin(), "Strike"] if not df_wneg.empty else "N/A"

    # Zero Gamma Weekly
    wzero_gamma = None
    if isinstance(wcall_wall,(int,float)) and isinstance(wput_wall,(int,float)):
        lo_w, hi_w = min(wcall_wall, wput_wall), max(wcall_wall, wput_wall)
        df_bt_w = wgex[(wgex["Strike"]>=lo_w)&(wgex["Strike"]<=hi_w)&(wgex["ABS_GEX"]>0)].reset_index(drop=True)
        for i in range(len(df_bt_w)-1):
            g0,g1 = df_bt_w["GEX_Total"].iloc[i], df_bt_w["GEX_Total"].iloc[i+1]
            s0,s1 = df_bt_w["Strike"].iloc[i],    df_bt_w["Strike"].iloc[i+1]
            if g0*g1 < 0:
                wzero_gamma = round(s0 + (0-g0)*(s1-s0)/(g1-g0), 2)
                break

    # Max ABS strike weekly
    wmax_abs = wgex.loc[wgex["ABS_GEX"].idxmax(), "Strike"]

    # --- KPI ---
    w1,w2,w3,w4,w5 = st.columns(5)
    for col_w, label, value, color in [
        (w1, "NET GEX WEEKLY",    f"{net_wgex:.2e}",                         wgex_col),
        (w2, "REGIME",            "🟢 POSITIVE" if is_pos_w else "🔴 NEGATIVE", wgex_col),
        (w3, "CALL WALL W",       f"{int(wcall_wall)}" if isinstance(wcall_wall,(int,float)) else "N/A", BLUE),
        (w4, "PUT WALL W",        f"{int(wput_wall)}"  if isinstance(wput_wall,(int,float))  else "N/A", RED),
        (w5, "ZERO GAMMA W",      f"{wzero_gamma}" if wzero_gamma else "N/A", ORANGE),
    ]:
        col_w.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
            f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
            f"font-weight:600;color:{color};'>{value}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    top_n_w = st.slider("Strikes affichés", 5, 60, 50, key="weekly_slider")
    df_top_w = wgex.nlargest(top_n_w, "ABS_GEX").sort_values("Strike")

    tab_w1, tab_w2, tab_w3 = st.tabs([
        "📈 Courbe GEX Weekly",
        "📊 Décomposition par jour",
        "🧱 Calls vs Puts Weekly"
    ])

    with tab_w1:
        fig_w1, ax_w1 = plt.subplots(figsize=(13, 6))

        # Fill vert/rouge sous la courbe
        ax_w1.fill_between(df_top_w["Strike"], df_top_w["GEX_Total"], 0,
                           where=df_top_w["GEX_Total"] >= 0,
                           alpha=0.18, color=GREEN, interpolate=True)
        ax_w1.fill_between(df_top_w["Strike"], df_top_w["GEX_Total"], 0,
                           where=df_top_w["GEX_Total"] < 0,
                           alpha=0.18, color=RED, interpolate=True)

        ax_w1.plot(df_top_w["Strike"], df_top_w["GEX_Total"],
                   color=BLUE, linewidth=2, marker='o', markersize=3, label="GEX Weekly")
        ax_w1.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

        # Niveaux cles
        if isinstance(wcall_wall,(int,float)):
            ax_w1.axvline(x=wcall_wall, color=BLUE,   linestyle='--', linewidth=1.5,
                          label=f"Call Wall W ({int(wcall_wall)})")
        if isinstance(wput_wall,(int,float)):
            ax_w1.axvline(x=wput_wall,  color=RED,    linestyle='--', linewidth=1.5,
                          label=f"Put Wall W ({int(wput_wall)})")
        if wzero_gamma:
            ax_w1.axvline(x=wzero_gamma, color=ORANGE, linestyle='--', linewidth=1.5,
                          label=f"Zero Gamma W ({wzero_gamma})")

        ax_w1.set_title(
            f"COURBE GEX WEEKLY — {selected_week['monday'].strftime('%d %b')} "
            f"→ {selected_week['friday'].strftime('%d %b %Y')}  "
            f"({len(week_exps)} expirations cumulées)",
            fontsize=12, fontweight='bold')
        ax_w1.set_xlabel("Strike Price")
        ax_w1.set_ylabel("GEX Weekly Cumulé")
        ax_w1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_w1.legend(fontsize=9)
        fig_w1.tight_layout()
        st.pyplot(fig_w1)

        # Resume niveaux
        st.markdown(
            f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
            f"border-left:3px solid {wgex_col};border-radius:8px;"
            f"padding:0.75rem 1.25rem;font-family:IBM Plex Mono,monospace;"
            f"font-size:0.82rem;color:{TEXT};'>"
            f"<b style='color:{wgex_col};'>REGIME WEEKLY :</b> "
            f"NET GEX = {net_wgex:.2e} → "
            f"{'Marche pince, les MM freinent les moves' if is_pos_w else 'Marche volatil, les MM amplifient les moves'}. "
            f"Call Wall {int(wcall_wall) if isinstance(wcall_wall,(int,float)) else 'N/A'} | "
            f"Put Wall {int(wput_wall) if isinstance(wput_wall,(int,float)) else 'N/A'} | "
            f"Zero Gamma {wzero_gamma if wzero_gamma else 'N/A'}"
            f"</div>", unsafe_allow_html=True)

    with tab_w2:
        # Superposition des courbes GEX par jour + weekly
        fig_w2, ax_w2 = plt.subplots(figsize=(13, 6))

        palette_days = [BLUE, GREEN, ORANGE, RED, "#a78bfa"]
        for i, (day_label, gex_d) in enumerate(gex_by_day.items()):
            gex_d_active = gex_d[gex_d[day_label].abs() > 0].sort_values("Strike")
            ax_w2.plot(gex_d_active["Strike"], gex_d_active[day_label],
                       color=palette_days[i % len(palette_days)],
                       linewidth=1.2, alpha=0.7, linestyle='--',
                       marker='o', markersize=2, label=f"GEX {day_label}")

        # Courbe weekly en gras par dessus
        ax_w2.plot(df_top_w["Strike"], df_top_w["GEX_Total"],
                   color=TEXT, linewidth=2.5, label="GEX WEEKLY", zorder=5)
        ax_w2.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

        if isinstance(wcall_wall,(int,float)):
            ax_w2.axvline(x=wcall_wall, color=BLUE, linestyle=':', linewidth=1.2, alpha=0.7)
        if isinstance(wput_wall,(int,float)):
            ax_w2.axvline(x=wput_wall,  color=RED,  linestyle=':', linewidth=1.2, alpha=0.7)

        ax_w2.set_title("DECOMPOSITION GEX PAR JOUR — Contribution de chaque expiration")
        ax_w2.set_xlabel("Strike")
        ax_w2.set_ylabel("GEX")
        ax_w2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_w2.legend(fontsize=9, loc='upper left')
        fig_w2.tight_layout()
        st.pyplot(fig_w2)

        # Poids de chaque jour dans le GEX weekly total
        st.markdown("**Poids de chaque expiration dans le GEX Weekly**")
        poids_rows = []
        for d in week_exps:
            df_d = df_week_all[df_week_all["Expiration Date_dt"]==d]
            gex_d_net = df_d.groupby("Strike")["GEX_Total"].sum().sum()
            gex_d_abs = df_d.groupby("Strike")["ABS_GEX"].sum().sum()
            poids_rows.append({
                "Expiration": d.strftime('%A %d %b'),
                "Net GEX":    f"{gex_d_net:.2e}",
                "ABS GEX":    f"{gex_d_abs:.2e}",
                "Poids %":    f"{gex_d_abs/wgex['ABS_GEX'].sum()*100:.1f}%",
                "Regime":     "🟢 Positive" if gex_d_net > 0 else "🔴 Negative"
            })
        st.dataframe(pd.DataFrame(poids_rows), use_container_width=True, hide_index=True)

    with tab_w3:
        fig_w3, ax_w3 = plt.subplots(figsize=(13, 6))
        bw = 0.4
        df_comp_w = wgex[wgex["Strike"].isin(df_top_w["Strike"])].sort_values("Strike")
        ax_w3.bar(df_comp_w["Strike"]-bw/2, df_comp_w["GEX_Calls"],
                  bw, color=BLUE, alpha=0.85, label="GEX Calls Weekly")
        ax_w3.bar(df_comp_w["Strike"]+bw/2, df_comp_w["GEX_Puts"],
                  bw, color=RED,  alpha=0.85, label="GEX Puts Weekly")
        ax_w3.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        if isinstance(wcall_wall,(int,float)):
            ax_w3.axvline(x=wcall_wall, color=BLUE, linestyle='--', linewidth=1.2,
                          label=f"Call Wall ({int(wcall_wall)})")
        if isinstance(wput_wall,(int,float)):
            ax_w3.axvline(x=wput_wall, color=RED, linestyle='--', linewidth=1.2,
                          label=f"Put Wall ({int(wput_wall)})")
        ax_w3.set_title("GEX CALLS vs PUTS WEEKLY CUMULÉ")
        ax_w3.set_xlabel("Strike")
        ax_w3.set_ylabel("GEX Weekly")
        ax_w3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
        ax_w3.legend(fontsize=9)
        fig_w3.tight_layout()
        st.pyplot(fig_w3)

    # Export texte copiable
    st.markdown("**Export Weekly**")
    wcopy = (
        f"WEEKLY {selected_week['monday'].strftime('%d %b')} - {selected_week['friday'].strftime('%d %b %Y')} | "
        f"Call Wall: {int(wcall_wall) if isinstance(wcall_wall,(int,float)) else 'N/A'} | "
        f"Put Wall: {int(wput_wall) if isinstance(wput_wall,(int,float)) else 'N/A'} | "
        f"Zero Gamma: {wzero_gamma if wzero_gamma else 'N/A'} | "
        f"Max ABS: {int(wmax_abs)}"
    )
    st.text_area("Niveaux Weekly", value=wcopy, height=70)

    # Multiplié
    def safe_mult(v):
        try: return int(round(float(v)*MULTIPLIER))
        except: return "N/A"

    wmult = (
        f"WEEKLY x{MULTIPLIER} | "
        f"CW: {safe_mult(wcall_wall)} | "
        f"PW: {safe_mult(wput_wall)} | "
        f"ZG: {safe_mult(wzero_gamma) if wzero_gamma else 'N/A'} | "
        f"MAX: {safe_mult(wmax_abs)}"
    )
    st.text_area(f"Niveaux Weekly × {MULTIPLIER}", value=wmult, height=70)
