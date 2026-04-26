import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from datetime import datetime
from pathlib import Path
from scipy.stats import norm as sp_norm

# ============================================================
#  YAHOO FINANCE DATA FETCHING
# ============================================================
try:
    import yfinance as yf
except ImportError:
    st.error("❌ yfinance non installé. Lance : pip install yfinance")
    st.stop()

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
#  YAHOO FINANCE DATA SOURCE
# ============================================================
st.markdown("### 🔗 Source de données — Yahoo Finance")

yf_col1, yf_col2, yf_col3 = st.columns([2, 1, 1])
with yf_col1:
    ticker_input = st.text_input(
        "Ticker Yahoo Finance",
        value=st.session_state.get("ticker", "QQQ"),
        placeholder="Ex: QQQ, SPY, AAPL, TSLA...",
        help="Entrer le symbole Yahoo Finance (ex: QQQ, SPY, NVDA)",
        key="ticker_input"
    ).strip().upper()
    st.session_state["ticker"] = ticker_input

with yf_col2:
    max_expirations = st.number_input(
        "Nb expirations max",
        min_value=1, max_value=20, value=8, step=1,
        help="Nombre maximum d'expirations à charger"
    )

with yf_col3:
    st.markdown("<div style='padding-top:1.8rem;'>", unsafe_allow_html=True)
    load_btn = st.button("🔄 Charger les données", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
#  FONCTION : Récupération & normalisation depuis Yahoo Finance
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def fetch_yfinance_options(ticker: str, max_exp: int):
    """
    Récupère toutes les options disponibles via yfinance et les normalise
    dans un DataFrame compatible avec le reste de l'application.
    Colonnes produites :
      Expiration Date, Strike,
      Last Sale, Bid, Ask, Net, Volume, IV, Delta, Gamma, Open Interest   <- Calls
      Last Sale.1, Net.1, Bid.1, Ask.1, Volume.1, IV.1, Delta.1, Gamma.1, Open Interest.1  <- Puts
    """
    tk = yf.Ticker(ticker)
    expirations = tk.options  # liste de strings 'YYYY-MM-DD'

    if not expirations:
        raise ValueError(f"Aucune expiration disponible pour {ticker}")

    # Limiter le nombre d'expirations
    expirations = expirations[:max_exp]

    rows = []
    for exp_str in expirations:
        try:
            chain = tk.option_chain(exp_str)
        except Exception:
            continue

        calls = chain.calls.copy()
        puts  = chain.puts.copy()

        # Normaliser les colonnes yfinance → noms attendus par l'app
        calls = calls.rename(columns={
            "lastPrice":    "Last Sale",
            "bid":          "Bid",
            "ask":          "Ask",
            "change":       "Net",
            "volume":       "Volume",
            "impliedVolatility": "IV",
            "openInterest": "Open Interest",
            "delta":        "Delta",
            "gamma":        "Gamma",
        })

        puts = puts.rename(columns={
            "lastPrice":    "Last Sale.1",
            "bid":          "Bid.1",
            "ask":          "Ask.1",
            "change":       "Net.1",
            "volume":       "Volume.1",
            "impliedVolatility": "IV.1",
            "openInterest": "Open Interest.1",
            "delta":        "Delta.1",
            "gamma":        "Gamma.1",
        })

        # Colonnes minimales requises
        for col in ["Last Sale", "Bid", "Ask", "Net", "Volume", "IV",
                    "Open Interest", "Delta", "Gamma"]:
            if col not in calls.columns:
                calls[col] = np.nan
        for col in ["Last Sale.1", "Bid.1", "Ask.1", "Net.1", "Volume.1",
                    "IV.1", "Open Interest.1", "Delta.1", "Gamma.1"]:
            if col not in puts.columns:
                puts[col] = np.nan

        # Merge calls + puts sur le Strike
        merged = pd.merge(
            calls[["strike", "Last Sale", "Bid", "Ask", "Net", "Volume",
                   "IV", "Delta", "Gamma", "Open Interest"]],
            puts[["strike", "Last Sale.1", "Bid.1", "Ask.1", "Net.1",
                  "Volume.1", "IV.1", "Delta.1", "Gamma.1", "Open Interest.1"]],
            on="strike",
            how="outer"
        )

        merged.rename(columns={"strike": "Strike"}, inplace=True)
        merged["Expiration Date"] = exp_str
        rows.append(merged)

    if not rows:
        raise ValueError("Aucune donnée d'options récupérée.")

    df_all = pd.concat(rows, ignore_index=True)

    # Nettoyage numériques
    numeric_cols = [
        "Strike", "Last Sale", "Bid", "Ask", "Net", "Volume", "IV",
        "Delta", "Gamma", "Open Interest",
        "Last Sale.1", "Bid.1", "Ask.1", "Net.1", "Volume.1",
        "IV.1", "Delta.1", "Gamma.1", "Open Interest.1"
    ]
    for col in numeric_cols:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

    # yfinance renvoie la IV déjà en décimal (ex: 0.25 = 25%)
    # Delta des puts est négatif dans yfinance → compatible avec l'app

    # Open Interest : remplacer NaN par 0
    df_all["Open Interest"]   = df_all["Open Interest"].fillna(0)
    df_all["Open Interest.1"] = df_all["Open Interest.1"].fillna(0)
    df_all["Volume"]          = df_all["Volume"].fillna(0)
    df_all["Volume.1"]        = df_all["Volume.1"].fillna(0)

    # Gamma des puts : yfinance le donne positif, l'app attend positif aussi
    # (la formule GEX_Puts multiplie par -1 elle-même)

    # Trier
    df_all = df_all.sort_values(["Expiration Date", "Strike"]).reset_index(drop=True)

    return df_all, expirations


def get_spot_price(ticker: str) -> float:
    """Récupère le prix spot actuel du ticker."""
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        info = tk.fast_info
        return float(getattr(info, "last_price", 0) or 0)
    except Exception:
        return 0.0


# ============================================================
#  CHARGEMENT DES DONNÉES
# ============================================================
data_loaded = False
df = None
spot_price = 0.0

# Charger automatiquement si ticker présent en session, ou sur clic bouton
if load_btn or st.session_state.get("data_ready"):

    if not ticker_input:
        st.error("❌ Entrez un ticker valide.")
    else:
        with st.spinner(f"⏳ Chargement des options {ticker_input} depuis Yahoo Finance..."):
            try:
                df, available_expirations = fetch_yfinance_options(ticker_input, max_expirations)
                spot_price = get_spot_price(ticker_input)
                st.session_state["data_ready"] = True
                st.session_state["last_ticker"] = ticker_input
                data_loaded = True

                st.success(
                    f"✅ **{ticker_input}** — {len(available_expirations)} expirations chargées "
                    f"| {len(df):,} lignes strikes | Spot : **{spot_price:.2f}**"
                )

            except Exception as e:
                st.error(f"❌ Erreur Yahoo Finance : {e}")
                st.session_state["data_ready"] = False

elif st.session_state.get("data_ready") and st.session_state.get("last_ticker") == ticker_input:
    # Données déjà en cache
    try:
        df, available_expirations = fetch_yfinance_options(ticker_input, max_expirations)
        spot_price = get_spot_price(ticker_input)
        data_loaded = True
    except Exception:
        st.session_state["data_ready"] = False

if not data_loaded:
    st.info(
        "👆 Entrez un ticker (ex: **QQQ**, **SPY**, **NVDA**) et cliquez sur **Charger les données**.\n\n"
        "Les données sont mises en cache 5 minutes pour éviter les appels répétés."
    )
    st.stop()


# ============================================================
#  PRÉPARATION DU DATAFRAME PRINCIPAL (identique à l'original)
# ============================================================

# Dates
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

# Zero Gamma
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
#  EXPECTED MOVE + TARGET BUY/SELL
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

# Spot price info
spot_display = f"{spot_price:.2f}" if spot_price > 0 else "N/A"
st.markdown(
    f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
    f"border-left:4px solid {BLUE};border-radius:8px;"
    f"padding:0.5rem 1.2rem;margin-bottom:0.8rem;"
    f"font-family:IBM Plex Mono,monospace;font-size:0.82rem;"
    f"color:{BLUE};letter-spacing:0.08em;'>"
    f"📡 {ticker_input} · Spot : <b>{spot_display}</b> "
    f"· Expiration la plus proche : <b>{closest_expiration_date}</b>"
    f"</div>",
    unsafe_allow_html=True
)

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

# -- Courbe GEX --
with chart_col1:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.fill_between(df_top_abs["Strike"], df_top_abs["GEX"], 0,
                    where=df_top_abs["GEX"] >= 0,
                    alpha=0.15, color=GREEN, interpolate=True)
    ax.fill_between(df_top_abs["Strike"], df_top_abs["GEX"], 0,
                    where=df_top_abs["GEX"] < 0,
                    alpha=0.15, color=RED, interpolate=True)
    ax.plot(df_top_abs["Strike"], df_top_abs["GEX"],
            marker='o', markersize=3, linestyle='-',
            color=BLUE, linewidth=1.5, label='GEX')
    ax.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

    if spot_price > 0:
        ax.axvline(x=spot_price, color=GREEN, linestyle='-', linewidth=1.5,
                   alpha=0.6, label=f'Spot ({spot_price:.2f})')

    if isinstance(call_wall, (int, float)):
        ax.axvline(x=call_wall,  color=BLUE,   linestyle='--', linewidth=1.2, label=f'Call Wall ({int(call_wall)})')
    if isinstance(put_wall, (int, float)):
        ax.axvline(x=put_wall,   color=RED,    linestyle='--', linewidth=1.2, label=f'Put Wall ({int(put_wall)})')
    if zero_gamma is not None:
        ax.axvline(x=zero_gamma, color=ORANGE, linestyle='--', linewidth=1.2, label=f'Zero Gamma ({zero_gamma})')

    ax.set_title(f"GAMMA EXPOSURE CURVE - {closest_expiration_date}")
    ax.set_xlabel("Strike Price")
    ax.set_ylabel("GEX")
    ax.legend(fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)

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
    "GEX ANALYSER · Options Flow Intelligence · Data sourced from Yahoo Finance"
    "</div>",
    unsafe_allow_html=True
)


# ============================================================
#  IV SKEW SECTION
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

    df_c_s = df_c.sort_values("Strike")
    df_p_s = df_p.sort_values("Strike")

    ax3.plot(df_c_s["Strike"], df_c_s["IV"]*100,
             color=BLUE, linewidth=1.8, marker='o', markersize=3, label='IV Calls')
    ax3.plot(df_p_s["Strike"], df_p_s["IV"]*100,
             color=RED,  linewidth=1.8, marker='o', markersize=3, label='IV Puts', linestyle='--')

    ax3.fill_between(df_c_s["Strike"], df_c_s["IV"]*100, alpha=0.08, color=BLUE)
    ax3.fill_between(df_p_s["Strike"], df_p_s["IV"]*100, alpha=0.08, color=RED)

    ax3.axvline(x=atm, color=GREEN, linestyle='--', linewidth=1.5, label=f'ATM ({int(atm)})')
    if isinstance(put_wall,  (int,float)):
        ax3.axvline(x=put_wall,  color=RED,    linestyle=':', linewidth=1, alpha=0.7, label=f'Put Wall ({int(put_wall)})')
    if isinstance(call_wall, (int,float)):
        ax3.axvline(x=call_wall, color=BLUE,   linestyle=':', linewidth=1, alpha=0.7, label=f'Call Wall ({int(call_wall)})')

    ax3.annotate(f'Skew 25d: {skew_pct:+.2f}%',
                 xy=(atm, atm_iv*100),
                 xytext=(atm + (df_c_s["Strike"].max()-df_c_s["Strike"].min())*0.05, atm_iv*100 + 1.5),
                 fontsize=9, color=ORANGE,
                 arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1))

    ax3.set_title(f'IV SKEW - {selected_label}', fontsize=13, fontweight='bold')
    ax3.set_xlabel("Strike Price")
    ax3.set_ylabel("Implied Volatility (%)")
    ax3.legend(fontsize=9)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.1f}%'))
    fig3.tight_layout()
    st.pyplot(fig3)

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
dex_color    = GREEN if is_bull_dex else RED

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

top_n_dex = st.slider("Nombre de strikes (DEX)", 5, 60, 50, key="dex_slider")
df_top_dex = df_dex.nlargest(top_n_dex, "ABS_DEX").sort_values("Strike")

fig_dex, (axd1, axd2) = plt.subplots(1, 2, figsize=(14, 5))

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

bar_w = 0.4
df_comp = df_dex[df_dex["Strike"].isin(df_top_dex["Strike"])].sort_values("Strike")
axd2.bar(df_comp["Strike"] - bar_w/2, df_comp["DEX_Calls"], bar_w, label='DEX Calls', color=BLUE,  alpha=0.85)
axd2.bar(df_comp["Strike"] + bar_w/2, df_comp["DEX_Puts"],  bar_w, label='DEX Puts',  color=RED,   alpha=0.85)
axd2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
axd2.set_title("DEX CALLS vs PUTS")
axd2.set_xlabel("Strike Price")
axd2.legend(fontsize=8)

fig_dex.tight_layout()
st.pyplot(fig_dex)

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

df_oi = df.copy()
for col in ["Strike","Open Interest","Open Interest.1","Volume","Volume.1","Delta","Delta.1"]:
    df_oi[col] = pd.to_numeric(df_oi[col], errors='coerce')

df_oi["OI_Calls"] = df_oi["Open Interest"].fillna(0)
df_oi["OI_Puts"]  = df_oi["Open Interest.1"].fillna(0)
df_oi["OI_Total"] = df_oi["OI_Calls"] + df_oi["OI_Puts"]
df_oi["Vol_Total"]= df_oi["Volume"].fillna(0) + df_oi["Volume.1"].fillna(0)

total_oi_calls = df_oi["OI_Calls"].sum()
total_oi_puts  = df_oi["OI_Puts"].sum()
pcr_global     = total_oi_puts / total_oi_calls if total_oi_calls > 0 else 0

by_strike = df_oi.groupby("Strike")[["OI_Calls","OI_Puts","OI_Total","Vol_Total"]].sum().reset_index()
by_strike["PCR"] = by_strike["OI_Puts"] / by_strike["OI_Calls"].replace(0, np.nan)

by_exp = df_oi.groupby("Expiration Date_dt")[["OI_Calls","OI_Puts","OI_Total"]].sum().reset_index()
by_exp["PCR"]   = by_exp["OI_Puts"] / by_exp["OI_Calls"].replace(0, np.nan)
by_exp["Label"] = by_exp["Expiration Date_dt"].dt.strftime('%b %d')

max_oi_strike     = by_strike.loc[by_strike["OI_Total"].idxmax(), "Strike"]
max_call_strike   = by_strike.loc[by_strike["OI_Calls"].idxmax(), "Strike"]
max_put_strike    = by_strike.loc[by_strike["OI_Puts"].idxmax(),  "Strike"]
pcr_color         = RED if pcr_global > 1.2 else (GREEN if pcr_global < 0.8 else ORANGE)
pcr_label         = "Bearish" if pcr_global > 1.2 else ("Bullish" if pcr_global < 0.8 else "Neutre")

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

tab_oi1, tab_oi2, tab_oi3 = st.tabs(["📊 OI par Strike", "📅 OI par Expiration", "🔥 Volume vs OI"])

with tab_oi1:
    top_n_oi = st.slider("Nombre de strikes", 10, 80, 40, key="oi_slider")
    df_top_oi = by_strike.nlargest(top_n_oi, "OI_Total").sort_values("Strike")

    fig_oi, axoi = plt.subplots(figsize=(13, 5))
    bw = 0.4
    axoi.bar(df_top_oi["Strike"] - bw/2, df_top_oi["OI_Calls"], bw, label="OI Calls", color=BLUE, alpha=0.85)
    axoi.bar(df_top_oi["Strike"] + bw/2, df_top_oi["OI_Puts"],  bw, label="OI Puts",  color=RED,  alpha=0.85)
    axoi.axvline(x=max_call_strike, color=BLUE,   linestyle='--', linewidth=1.2, label=f"Max Call OI ({int(max_call_strike)})")
    axoi.axvline(x=max_put_strike,  color=RED,    linestyle='--', linewidth=1.2, label=f"Max Put OI ({int(max_put_strike)})")
    axoi.axvline(x=max_oi_strike,   color=ORANGE, linestyle='--', linewidth=1.2, label=f"Max Total OI ({int(max_oi_strike)})")
    axoi.set_title("OPEN INTEREST CALLS vs PUTS PAR STRIKE (toutes expirations)")
    axoi.set_xlabel("Strike")
    axoi.set_ylabel("Open Interest")
    axoi.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
    axoi.legend(fontsize=8)
    fig_oi.tight_layout()
    st.pyplot(fig_oi)

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

    x_exp = range(len(by_exp))
    axe1.bar(x_exp, by_exp["OI_Calls"], label="OI Calls", color=BLUE, alpha=0.85)
    axe1.bar(x_exp, by_exp["OI_Puts"], bottom=by_exp["OI_Calls"], label="OI Puts", color=RED, alpha=0.85)
    axe1.set_xticks(list(x_exp))
    axe1.set_xticklabels(by_exp["Label"], rotation=45, ha='right', fontsize=8)
    axe1.set_title("OI TOTAL PAR EXPIRATION")
    axe1.set_ylabel("Open Interest")
    axe1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
    axe1.legend(fontsize=8)

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
    df_vol_oi = by_strike[by_strike["Vol_Total"] > 0].copy()
    df_vol_oi["Vol_OI_Ratio"] = df_vol_oi["Vol_Total"] / df_vol_oi["OI_Total"]
    df_top_vol = df_vol_oi.nlargest(40, "Vol_Total").sort_values("Strike")

    fig_vol, (axv1, axv2) = plt.subplots(1, 2, figsize=(13, 5))

    axv1.bar(df_top_vol["Strike"], df_top_vol["Vol_Total"], color=ORANGE, alpha=0.85, label="Volume Total")
    axv1.set_title("VOLUME PAR STRIKE (top 40)")
    axv1.set_xlabel("Strike")
    axv1.set_ylabel("Volume")
    axv1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))

    ratio_colors = [RED if r > 1 else (ORANGE if r > 0.5 else MUTED) for r in df_top_vol["Vol_OI_Ratio"]]
    axv2.bar(df_top_vol["Strike"], df_top_vol["Vol_OI_Ratio"], color=ratio_colors, alpha=0.85)
    axv2.axhline(y=1.0, color=RED,    linestyle='--', linewidth=1.2, label='Vol > OI (nouveau flux)')
    axv2.axhline(y=0.5, color=ORANGE, linestyle=':',  linewidth=1,   label='Vol > 50% OI')
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

st.markdown("<br>", unsafe_allow_html=True)
if pcr_global > 1.5:
    oi_msg = f"PCR = {pcr_global:.2f} : sentiment tres bearish, les options traders se protegent massivement"
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

by_exp_gex = df_all.groupby("Expiration Date_dt")[["GEX_Total","ABS_GEX"]].sum().reset_index()
by_exp_gex["Label"]   = by_exp_gex["Expiration Date_dt"].dt.strftime('%a %b %d')
by_exp_gex["Regime"]  = by_exp_gex["GEX_Total"].apply(lambda x: GREEN if x > 0 else RED)
by_exp_gex["n_strikes"] = df_all.groupby("Expiration Date_dt")["Strike"].nunique().values

total_net_gex = by_exp_gex["GEX_Total"].sum()
dominant_exp  = by_exp_gex.loc[by_exp_gex["ABS_GEX"].idxmax(), "Label"]
all_positive  = (by_exp_gex["GEX_Total"] > 0).all()

k1, k2, k3 = st.columns(3)
for col_k, label, value, color, sub in [
    (k1, "NET GEX CUMULE",    f"{total_net_gex:.2e}", GREEN if total_net_gex > 0 else RED, "Toutes expirations"),
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

tab_mx1, tab_mx2, tab_mx3 = st.tabs([
    "📊 NET GEX par expiration",
    "🔀 Comparaison profils",
    "🌡️ Heatmap strikes x expiry"
])

with tab_mx1:
    fig_mx1, (axm1, axm2) = plt.subplots(1, 2, figsize=(14, 5))

    bar_colors = [GREEN if v > 0 else RED for v in by_exp_gex["GEX_Total"]]
    axm1.bar(range(len(by_exp_gex)), by_exp_gex["GEX_Total"], color=bar_colors, alpha=0.85)
    axm1.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
    axm1.set_xticks(range(len(by_exp_gex)))
    axm1.set_xticklabels(by_exp_gex["Label"], rotation=45, ha='right', fontsize=8)
    axm1.set_title("NET GEX PAR EXPIRATION")
    axm1.set_ylabel("Net GEX")
    axm1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))

    axm2.bar(range(len(by_exp_gex)), by_exp_gex["ABS_GEX"], color=BLUE, alpha=0.75)
    axm2.set_xticks(range(len(by_exp_gex)))
    axm2.set_xticklabels(by_exp_gex["Label"], rotation=45, ha='right', fontsize=8)
    axm2.set_title("POIDS GEX ABSOLU PAR EXPIRATION")
    axm2.set_ylabel("ABS GEX")
    axm2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))

    fig_mx1.tight_layout()
    st.pyplot(fig_mx1)

    tbl = by_exp_gex[["Label","GEX_Total","ABS_GEX","n_strikes"]].copy()
    tbl["Regime"] = tbl["GEX_Total"].apply(lambda x: "🟢 Positive" if x > 0 else "🔴 Negative")
    tbl["Poids%"] = (tbl["ABS_GEX"] / tbl["ABS_GEX"].sum() * 100).round(1)
    tbl.rename(columns={"Label":"Expiration","GEX_Total":"Net GEX",
                         "ABS_GEX":"ABS GEX","n_strikes":"Strikes"}, inplace=True)
    st.dataframe(tbl.style.format({
        "Net GEX":"{:.2e}", "ABS GEX":"{:.2e}", "Poids%":"{:.1f}%"
    }), use_container_width=True, hide_index=True)

with tab_mx2:
    selected_exps = st.multiselect(
        "Choisir les expirations a comparer",
        options=exp_labels,
        default=exp_labels[:min(4, len(exp_labels))]
    )

    if len(selected_exps) < 2:
        st.warning("Selectionnez au moins 2 expirations.")
    else:
        palette = [BLUE, GREEN, ORANGE, RED, "#a78bfa", "#34d399", "#fb923c", "#f472b6", "#38bdf8", "#facc15"]

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

    s_min = int(df_all["Strike"].min())
    s_max = int(df_all["Strike"].max())
    s_mid = int((s_min + s_max) / 2)
    default_lo = max(s_min, s_mid - 50)
    default_hi = min(s_max, s_mid + 50)

    strike_range = st.slider("Zone strikes", s_min, s_max, (default_lo, default_hi), step=5, key="heatmap_strikes")

    df_heat = df_all[
        (df_all["Strike"] >= strike_range[0]) &
        (df_all["Strike"] <= strike_range[1])
    ].groupby(["Strike","Expiration Date_dt"])["GEX_Total"].sum().reset_index()

    pivot = df_heat.pivot(index="Strike", columns="Expiration Date_dt", values="GEX_Total").fillna(0)
    pivot.columns = [c.strftime('%b %d') for c in pivot.columns]
    pivot = pivot.sort_index(ascending=False)

    fig_heat, ax_heat = plt.subplots(figsize=(13, max(6, len(pivot)*0.25)))

    import matplotlib.colors as mcolors
    cmap = mcolors.LinearSegmentedColormap.from_list("gex", [RED, DARK_BG, GREEN], N=256)

    vmax = pivot.abs().max().max()
    im = ax_heat.imshow(pivot.values, cmap=cmap, aspect='auto', vmin=-vmax, vmax=vmax)

    ax_heat.set_xticks(range(len(pivot.columns)))
    ax_heat.set_xticklabels(pivot.columns, fontsize=8)
    ax_heat.set_yticks(range(len(pivot.index)))
    ax_heat.set_yticklabels([f"{int(s)}" for s in pivot.index], fontsize=7)
    ax_heat.set_title("HEATMAP GEX — Rouge=Puts dominant / Vert=Calls dominant")

    plt.colorbar(im, ax=ax_heat, fraction=0.02, pad=0.02, label="GEX (negatif=Puts, positif=Calls)")
    fig_heat.tight_layout()
    st.pyplot(fig_heat)


# ============================================================
#  OPTIONS CHAIN INTERACTIVE
# ============================================================
st.markdown('<div id="options-chain"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 🔗 Options Chain — Calls | Strike | Puts")

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
    if col in df_chain.columns:
        df_chain[col] = pd.to_numeric(df_chain[col], errors='coerce')

df_chain = df_chain.sort_values("Strike").reset_index(drop=True)

df_with_delta = df_chain[df_chain["Delta"].notna() & (df_chain["Delta"] > 0)]
if not df_with_delta.empty:
    atm_strike_chain = df_with_delta.iloc[(df_with_delta["Delta"] - 0.5).abs().argsort()[:1]]["Strike"].values[0]
else:
    atm_strike_chain = df_chain["Strike"].median()

if show_atm_only and atm_range:
    df_chain = df_chain[
        (df_chain["Strike"] >= atm_strike_chain - atm_range) &
        (df_chain["Strike"] <= atm_strike_chain + atm_range)
    ].reset_index(drop=True)

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

rows_chain = []
for _, r in df_chain.iterrows():
    strike = r["Strike"]
    is_atm = abs(strike - atm_strike_chain) <= 1
    rows_chain.append({
        "OI C":     fmt_int(r.get("Open Interest")),
        "Vol C":    fmt_int(r.get("Volume")),
        "IV C":     fmt_pct(r.get("IV")),
        "Delta C":  fmt_num(r.get("Delta"), 3),
        "Gamma C":  fmt_num(r.get("Gamma"), 4),
        "Bid C":    fmt_num(r.get("Bid")),
        "Ask C":    fmt_num(r.get("Ask")),
        "Last C":   fmt_num(r.get("Last Sale")),
        "⚡ STRIKE": f"{'★ ' if is_atm else ''}{int(strike)}",
        "Last P":   fmt_num(r.get("Last Sale.1")),
        "Bid P":    fmt_num(r.get("Bid.1")),
        "Ask P":    fmt_num(r.get("Ask.1")),
        "Gamma P":  fmt_num(r.get("Gamma.1"), 4),
        "Delta P":  fmt_num(r.get("Delta.1"), 3),
        "IV P":     fmt_pct(r.get("IV.1")),
        "Vol P":    fmt_int(r.get("Volume.1")),
        "OI P":     fmt_int(r.get("Open Interest.1")),
    })

df_display = pd.DataFrame(rows_chain)

def style_chain(df_s):
    styles = pd.DataFrame("", index=df_s.index, columns=df_s.columns)
    for i, row in df_s.iterrows():
        strike_val = row["⚡ STRIKE"].replace("★ ", "")
        try:
            is_atm_row = abs(float(strike_val) - atm_strike_chain) <= 1
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

st.markdown(
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;"
    f"color:{MUTED};margin-bottom:0.5rem;'>"
    f"★ = ATM ({int(atm_strike_chain)})&nbsp;&nbsp;|&nbsp;&nbsp;"
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


# ============================================================
#  CHARM & VANNA SECTION
# ============================================================
st.markdown('<div id="charm-vanna"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### ⚗️ Charm & Vanna — Greeks du 2e Ordre")

with st.expander("📖 C'est quoi Charm et Vanna ? (cliquer pour lire)", expanded=False):
    st.markdown(f"""
<div style='font-family:IBM Plex Mono,monospace;font-size:0.82rem;
color:{TEXT};line-height:1.8;'>

<b style='color:{ORANGE};'>CHARM (Delta Decay)</b> = dDelta / dTemps<br>
→ A quelle vitesse le delta d'une option change avec le temps.<br><br>

<b style='color:{ORANGE};'>VANNA (Delta-Vol Sensitivity)</b> = dDelta / dIV = dVega / dSpot<br>
→ Comment le delta change quand la volatilite change.<br><br>

<b style='color:{RED};'>Combinaison Charm + Vanna :</b><br>
• En approche d'expiration : Charm domine (effet temps).<br>
• En mouvement de vol : Vanna domine (effet IV).<br>

</div>
""", unsafe_allow_html=True)

cv_exp_label = st.selectbox("Expiration (Charm/Vanna)", expiry_labels,
    index=expiry_labels.index(closest_expiration_date) if closest_expiration_date in expiry_labels else 0,
    key="cv_expiry")
cv_dt = expiry_options[expiry_labels.index(cv_exp_label)]

cv1, cv2 = st.columns(2)
with cv1:
    spot_input = st.number_input("Spot price (S)", value=float(spot_price) if spot_price > 0 else 100.0, step=0.5, key="cv_spot")
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

kv1, kv2, kv3, kv4 = st.columns(4)
charm_col = GREEN if net_charm > 0 else RED
vanna_col = GREEN if net_vanna > 0 else RED
charm_lbl = "Acheteur" if net_charm > 0 else "Vendeur"
vanna_lbl = "VIX crush -> haussier" if net_vanna > 0 else "VIX spike -> baissier"

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

top_n_cv = st.slider("Nombre de strikes", 5, 60, 40, key="cv_slider")
df_cv_top = df_cv_gex.assign(
    ABS=df_cv_gex["CharmEx"].abs() + df_cv_gex["VannaEx"].abs()
).nlargest(top_n_cv, "ABS").sort_values("Strike")

tab_charm, tab_vanna, tab_combined = st.tabs(["⏱️ Charm Exposure", "🌊 Vanna Exposure", "🔀 Vue combinée"])

with tab_charm:
    fig_ch, ax_ch = plt.subplots(figsize=(13, 5))
    colors_ch = [GREEN if v >= 0 else RED for v in df_cv_top["CharmEx"]]
    ax_ch.bar(df_cv_top["Strike"], df_cv_top["CharmEx"], color=colors_ch, alpha=0.85, width=0.6)
    ax_ch.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)
    ax_ch.axvline(x=spot_input, color=ORANGE, linestyle='--', linewidth=1.5, label=f'Spot ({spot_input})')
    ax_ch.set_title(f"CHARM EXPOSURE PAR STRIKE — {cv_exp_label}  (T={T_cv_days}j)")
    ax_ch.set_xlabel("Strike")
    ax_ch.set_ylabel("Charm Exposure")
    ax_ch.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
    ax_ch.legend(fontsize=9)
    fig_ch.tight_layout()
    st.pyplot(fig_ch)

with tab_vanna:
    fig_va, ax_va = plt.subplots(figsize=(13, 5))
    colors_va = [GREEN if v >= 0 else RED for v in df_cv_top["VannaEx"]]
    ax_va.bar(df_cv_top["Strike"], df_cv_top["VannaEx"], color=colors_va, alpha=0.85, width=0.6)
    ax_va.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)
    ax_va.axvline(x=spot_input, color=ORANGE, linestyle='--', linewidth=1.5, label=f'Spot ({spot_input})')
    ax_va.set_title(f"VANNA EXPOSURE PAR STRIKE — {cv_exp_label}")
    ax_va.set_xlabel("Strike")
    ax_va.set_ylabel("Vanna Exposure")
    ax_va.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
    ax_va.legend(fontsize=9)
    fig_va.tight_layout()
    st.pyplot(fig_va)

with tab_combined:
    fig_comb, (ax_c1, ax_c2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    ax_c1.fill_between(df_cv_top["Strike"], df_cv_top["CharmEx"], 0,
                       where=df_cv_top["CharmEx"] >= 0, color=GREEN, alpha=0.3, interpolate=True)
    ax_c1.fill_between(df_cv_top["Strike"], df_cv_top["CharmEx"], 0,
                       where=df_cv_top["CharmEx"] < 0,  color=RED,   alpha=0.3, interpolate=True)
    ax_c1.plot(df_cv_top["Strike"], df_cv_top["CharmEx"],
               color=ORANGE, linewidth=1.8, marker='o', markersize=3, label='Charm')
    ax_c1.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
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
    ax_c2.axvline(x=spot_input, color=ORANGE, linestyle=':', linewidth=1, alpha=0.6, label=f'Spot ({spot_input})')
    ax_c2.set_title("VANNA EXPOSURE (effet volatilite)")
    ax_c2.set_xlabel("Strike")
    ax_c2.set_ylabel("Vanna Ex")
    ax_c2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
    ax_c2.legend(fontsize=9)

    fig_comb.tight_layout()
    st.pyplot(fig_comb)

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

df_vol = df.copy()
for col in ["Strike","Volume","Volume.1","Open Interest","Open Interest.1",
            "Bid","Ask","Bid.1","Ask.1","Last Sale","Last Sale.1","IV","IV.1","Delta","Delta.1"]:
    if col in df_vol.columns:
        df_vol[col] = pd.to_numeric(df_vol[col], errors='coerce')

df_vol["Vol_C"]    = df_vol.get("Volume", pd.Series(0, index=df_vol.index)).fillna(0)
df_vol["Vol_P"]    = df_vol.get("Volume.1", pd.Series(0, index=df_vol.index)).fillna(0)
df_vol["OI_C"]     = df_vol.get("Open Interest", pd.Series(0, index=df_vol.index)).fillna(0)
df_vol["OI_P"]     = df_vol.get("Open Interest.1", pd.Series(0, index=df_vol.index)).fillna(0)
df_vol["Vol_Tot"]  = df_vol["Vol_C"] + df_vol["Vol_P"]
df_vol["Spread_C"] = df_vol.get("Ask", pd.Series(np.nan, index=df_vol.index)) - df_vol.get("Bid", pd.Series(np.nan, index=df_vol.index))
df_vol["Spread_P"] = df_vol.get("Ask.1", pd.Series(np.nan, index=df_vol.index)) - df_vol.get("Bid.1", pd.Series(np.nan, index=df_vol.index))

df_vol["VoI_C"] = df_vol["Vol_C"] / df_vol["OI_C"].replace(0, np.nan)
df_vol["VoI_P"] = df_vol["Vol_P"] / df_vol["OI_P"].replace(0, np.nan)

def classify_flow(last, bid, ask):
    try:
        l,b,a = float(last), float(bid), float(ask)
        mid = (b+a)/2
        if l >= a:    return "🟢 Achat agressif"
        elif l <= b:  return "🔴 Vente agressive"
        elif l > mid: return "🟡 Achat passif"
        else:         return "🟠 Vente passive"
    except: return "⚪ Inconnu"

df_vol["Flow_C"] = [classify_flow(r.get("Last Sale"), r.get("Bid"), r.get("Ask")) for _, r in df_vol.iterrows()]
df_vol["Flow_P"] = [classify_flow(r.get("Last Sale.1"), r.get("Bid.1"), r.get("Ask.1")) for _, r in df_vol.iterrows()]

total_vol_c = df_vol["Vol_C"].sum()
total_vol_p = df_vol["Vol_P"].sum()
pcr_vol     = total_vol_p / total_vol_c if total_vol_c > 0 else 0

p95_c = df_vol[df_vol["Vol_C"]>0]["Vol_C"].quantile(0.95) if (df_vol["Vol_C"]>0).any() else 0
p95_p = df_vol[df_vol["Vol_P"]>0]["Vol_P"].quantile(0.95) if (df_vol["Vol_P"]>0).any() else 0

vf1, vf2, vf3, vf4 = st.columns(4)
pcr_vol_color = RED if pcr_vol > 1.2 else (GREEN if pcr_vol < 0.8 else ORANGE)
for col_vf, label, value, color, sub in [
    (vf1, "PCR VOLUME",        f"{pcr_vol:.3f}",          pcr_vol_color, "Volume Puts/Calls"),
    (vf2, "VOL CALLS TOTAL",   f"{int(total_vol_c):,}",   BLUE,          "Contrats calls"),
    (vf3, "VOL PUTS TOTAL",    f"{int(total_vol_p):,}",   RED,           "Contrats puts"),
    (vf4, "SEUIL INHABITUEL C",f"{int(p95_c):,}",         ORANGE,        "p95 volume calls"),
]:
    col_vf.markdown(
        f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
        f"border-left:3px solid {color};border-radius:8px;padding:1rem 1.2rem;'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;color:{MUTED};"
        f"letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:600;color:{color};'>{value}</div>"
        f"<div style='font-size:0.75rem;color:{MUTED};margin-top:0.3rem;'>{sub}</div>"
        f"</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab_vf1, tab_vf2 = st.tabs(["📊 Volume par Strike", "🔍 Flux Inhabituels"])

with tab_vf1:
    by_vol_strike = df_vol.groupby("Strike")[["Vol_C","Vol_P","Vol_Tot","OI_C","OI_P"]].sum().reset_index()
    by_vol_strike["VoI"] = by_vol_strike["Vol_Tot"] / (by_vol_strike["OI_C"] + by_vol_strike["OI_P"]).replace(0, np.nan)
    df_top_vol_s = by_vol_strike.nlargest(40, "Vol_Tot").sort_values("Strike")

    fig_vf1, (axvf1, axvf2) = plt.subplots(1, 2, figsize=(13, 5))

    axvf1.bar(df_top_vol_s["Strike"] - 0.2, df_top_vol_s["Vol_C"], 0.4, label="Vol Calls", color=BLUE, alpha=0.85)
    axvf1.bar(df_top_vol_s["Strike"] + 0.2, df_top_vol_s["Vol_P"], 0.4, label="Vol Puts",  color=RED,  alpha=0.85)
    axvf1.set_title("VOLUME CALLS vs PUTS PAR STRIKE (top 40)")
    axvf1.set_xlabel("Strike")
    axvf1.set_ylabel("Volume")
    axvf1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y/1000:.0f}k'))
    axvf1.legend(fontsize=8)

    ratio_c = [RED if r > 1 else (ORANGE if r > 0.5 else MUTED) for r in df_top_vol_s["VoI"]]
    axvf2.bar(df_top_vol_s["Strike"], df_top_vol_s["VoI"], color=ratio_c, alpha=0.85)
    axvf2.axhline(y=1.0, color=RED, linestyle='--', linewidth=1.2, label="Vol > OI")
    axvf2.axhline(y=0.5, color=ORANGE, linestyle=':', linewidth=1, label="Vol > 50% OI")
    axvf2.set_title("RATIO VOLUME / OI PAR STRIKE")
    axvf2.set_xlabel("Strike")
    axvf2.set_ylabel("Vol / OI")
    axvf2.legend(fontsize=8)

    fig_vf1.tight_layout()
    st.pyplot(fig_vf1)

with tab_vf2:
    df_unusual_c = df_vol[(df_vol["Vol_C"] > p95_c) & (df_vol["Vol_C"] > 0)].copy()
    df_unusual_p = df_vol[(df_vol["Vol_P"] > p95_p) & (df_vol["Vol_P"] > 0)].copy()

    st.markdown(f"**Calls inhabituels (Vol > p95 = {int(p95_c):,})**")
    if not df_unusual_c.empty:
        cols_c = ["Strike", "Expiration Date", "Vol_C", "OI_C", "VoI_C", "Flow_C"]
        cols_c = [c for c in cols_c if c in df_unusual_c.columns]
        st.dataframe(df_unusual_c[cols_c].sort_values("Vol_C", ascending=False).head(20)
                     .style.format({"Vol_C":"{:,.0f}", "OI_C":"{:,.0f}", "VoI_C":"{:.2f}"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Aucun flux inhabituel détecté sur les calls.")

    st.markdown(f"**Puts inhabituels (Vol > p95 = {int(p95_p):,})**")
    if not df_unusual_p.empty:
        cols_p = ["Strike", "Expiration Date", "Vol_P", "OI_P", "VoI_P", "Flow_P"]
        cols_p = [c for c in cols_p if c in df_unusual_p.columns]
        st.dataframe(df_unusual_p[cols_p].sort_values("Vol_P", ascending=False).head(20)
                     .style.format({"Vol_P":"{:,.0f}", "OI_P":"{:,.0f}", "VoI_P":"{:.2f}"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Aucun flux inhabituel détecté sur les puts.")


# ============================================================
#  EXPECTED MOVE SECTION
# ============================================================
st.markdown('<div id="expected-move"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📐 Expected Move — Analyse Multi-Expiration")

em_rows = []
for exp_dt in sorted(unique_expiration_dates):
    df_em = df[df['Expiration Date_dt'] == exp_dt].copy()
    for col in ["Strike","Delta","Bid","Ask","Bid.1","Ask.1","IV","IV.1"]:
        if col in df_em.columns:
            df_em[col] = pd.to_numeric(df_em[col], errors='coerce')

    df_atm_em = df_em[df_em["Delta"].notna() & (df_em["Delta"] > 0)]
    if df_atm_em.empty:
        continue

    atm_idx_em = (df_atm_em["Delta"] - 0.5).abs().argsort().iloc[0]
    atm_row_em = df_atm_em.iloc[atm_idx_em]
    atm_s_em   = atm_row_em["Strike"]
    put_row_em = df_em[df_em["Strike"] == atm_s_em]

    bid_c_em = atm_row_em.get("Bid", np.nan)
    ask_c_em = atm_row_em.get("Ask", np.nan)
    bid_p_em = put_row_em["Bid.1"].values[0] if len(put_row_em) > 0 and "Bid.1" in put_row_em.columns else np.nan
    ask_p_em = put_row_em["Ask.1"].values[0] if len(put_row_em) > 0 and "Ask.1" in put_row_em.columns else np.nan

    mid_c_em = (float(bid_c_em)+float(ask_c_em))/2 if pd.notna(bid_c_em) and pd.notna(ask_c_em) else np.nan
    mid_p_em = (float(bid_p_em)+float(ask_p_em))/2 if pd.notna(bid_p_em) and pd.notna(ask_p_em) else np.nan

    if pd.notna(mid_c_em) and pd.notna(mid_p_em):
        em_val = round(mid_c_em + mid_p_em, 2)
        em_pct = round(em_val / atm_s_em * 100, 2) if atm_s_em > 0 else 0
        em_rows.append({
            "Expiration": exp_dt.strftime('%a %d %b %Y'),
            "ATM Strike": int(atm_s_em),
            "EM ±": em_val,
            "EM %": f"{em_pct:.2f}%",
            "EM+": round(atm_s_em + em_val, 2),
            "EM-": round(atm_s_em - em_val, 2),
        })

if em_rows:
    df_em_table = pd.DataFrame(em_rows)
    st.dataframe(df_em_table, use_container_width=True, hide_index=True)

    fig_em, ax_em = plt.subplots(figsize=(13, 5))
    x_em = range(len(df_em_table))
    ax_em.bar(x_em, df_em_table["EM %"].str.replace('%','').astype(float), color=BLUE, alpha=0.75)
    ax_em.set_xticks(list(x_em))
    ax_em.set_xticklabels(df_em_table["Expiration"], rotation=45, ha='right', fontsize=8)
    ax_em.set_title("EXPECTED MOVE (%) PAR EXPIRATION")
    ax_em.set_ylabel("Expected Move (%)")
    ax_em.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1f}%'))
    fig_em.tight_layout()
    st.pyplot(fig_em)
else:
    st.warning("Pas assez de données bid/ask pour calculer l'Expected Move.")


# ============================================================
#  GEX WEEKLY SECTION
# ============================================================
st.markdown('<div id="gex-weekly"></div>', unsafe_allow_html=True)
st.markdown("---")
st.markdown("### 📅 GEX Weekly — Vision Hebdomadaire")

# Construire la liste des semaines disponibles
all_mondays = sorted(set([
    (d - pd.Timedelta(days=d.weekday())).date()
    for d in pd.to_datetime(unique_expiration_dates)
]))

if not all_mondays:
    st.warning("Pas de données hebdomadaires disponibles.")
else:
    week_options = {
        f"Semaine du {m.strftime('%d %b %Y')}": {
            "monday": pd.Timestamp(m),
            "friday": pd.Timestamp(m) + pd.Timedelta(days=4)
        }
        for m in all_mondays
    }

    week_labels = list(week_options.keys())

    # Trouver la semaine courante
    current_monday = (pd.Timestamp(datetime.now().date()) - pd.Timedelta(days=datetime.now().weekday()))
    default_week = 0
    for i, m in enumerate(all_mondays):
        if pd.Timestamp(m) >= current_monday:
            default_week = i
            break

    selected_week_label = st.selectbox("Semaine", week_labels,
                                        index=min(default_week, len(week_labels)-1),
                                        key="weekly_select")
    selected_week = week_options[selected_week_label]

    # Expirations dans la semaine
    week_exps = [
        d for d in pd.to_datetime(unique_expiration_dates)
        if selected_week["monday"] <= d <= selected_week["friday"]
    ]

    if not week_exps:
        st.info("Aucune expiration dans cette semaine.")
    else:
        df_week_all = df_all[df_all["Expiration Date_dt"].isin(week_exps)].copy()

        # GEX par jour (expiration)
        gex_by_day = {}
        for d in week_exps:
            day_label = d.strftime('%a %d')
            df_day = df_week_all[df_week_all["Expiration Date_dt"] == d]
            gex_d = df_day.groupby("Strike")["GEX_Total"].sum().reset_index()
            gex_d.rename(columns={"GEX_Total": day_label}, inplace=True)
            gex_by_day[day_label] = gex_d

        # GEX weekly cumulé
        wgex = df_week_all.groupby("Strike")[["GEX_Total","ABS_GEX","GEX_Calls","GEX_Puts"]].sum().reset_index()
        wgex = wgex[wgex["ABS_GEX"] > 0].sort_values("Strike")

        net_wgex  = wgex["GEX_Total"].sum()
        is_pos_w  = net_wgex > 0
        wgex_col  = GREEN if is_pos_w else RED

        df_wpos   = wgex[wgex["GEX_Total"] > 0]
        df_wneg   = wgex[wgex["GEX_Total"] < 0]
        wcall_wall = df_wpos.loc[df_wpos["GEX_Total"].idxmax(), "Strike"] if not df_wpos.empty else "N/A"
        wput_wall  = df_wneg.loc[df_wneg["GEX_Total"].idxmin(), "Strike"] if not df_wneg.empty else "N/A"

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

        wmax_abs = wgex.loc[wgex["ABS_GEX"].idxmax(), "Strike"]

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

            ax_w1.fill_between(df_top_w["Strike"], df_top_w["GEX_Total"], 0,
                               where=df_top_w["GEX_Total"] >= 0, alpha=0.18, color=GREEN, interpolate=True)
            ax_w1.fill_between(df_top_w["Strike"], df_top_w["GEX_Total"], 0,
                               where=df_top_w["GEX_Total"] < 0, alpha=0.18, color=RED, interpolate=True)

            ax_w1.plot(df_top_w["Strike"], df_top_w["GEX_Total"],
                       color=BLUE, linewidth=2, marker='o', markersize=3, label="GEX Weekly")
            ax_w1.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

            if spot_price > 0:
                ax_w1.axvline(x=spot_price, color=GREEN, linestyle='-', linewidth=1.5, alpha=0.5, label=f'Spot ({spot_price:.2f})')
            if isinstance(wcall_wall,(int,float)):
                ax_w1.axvline(x=wcall_wall, color=BLUE,   linestyle='--', linewidth=1.5, label=f"Call Wall W ({int(wcall_wall)})")
            if isinstance(wput_wall,(int,float)):
                ax_w1.axvline(x=wput_wall,  color=RED,    linestyle='--', linewidth=1.5, label=f"Put Wall W ({int(wput_wall)})")
            if wzero_gamma:
                ax_w1.axvline(x=wzero_gamma, color=ORANGE, linestyle='--', linewidth=1.5, label=f"Zero Gamma W ({wzero_gamma})")

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
            fig_w2, ax_w2 = plt.subplots(figsize=(13, 6))

            palette_days = [BLUE, GREEN, ORANGE, RED, "#a78bfa"]
            for i, (day_label, gex_d) in enumerate(gex_by_day.items()):
                gex_d_active = gex_d[gex_d[day_label].abs() > 0].sort_values("Strike")
                ax_w2.plot(gex_d_active["Strike"], gex_d_active[day_label],
                           color=palette_days[i % len(palette_days)],
                           linewidth=1.2, alpha=0.7, linestyle='--',
                           marker='o', markersize=2, label=f"GEX {day_label}")

            ax_w2.plot(df_top_w["Strike"], df_top_w["GEX_Total"],
                       color=TEXT, linewidth=2.5, label="GEX WEEKLY", zorder=5)
            ax_w2.axhline(y=0, color=BORDER, linestyle="--", linewidth=1)

            ax_w2.set_title("DECOMPOSITION GEX PAR JOUR — Contribution de chaque expiration")
            ax_w2.set_xlabel("Strike")
            ax_w2.set_ylabel("GEX")
            ax_w2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y,_: f'{y:.1e}'))
            ax_w2.legend(fontsize=9, loc='upper left')
            fig_w2.tight_layout()
            st.pyplot(fig_w2)

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
            ax_w3.bar(df_comp_w["Strike"]-bw/2, df_comp_w["GEX_Calls"], bw, color=BLUE, alpha=0.85, label="GEX Calls Weekly")
            ax_w3.bar(df_comp_w["Strike"]+bw/2, df_comp_w["GEX_Puts"],  bw, color=RED,  alpha=0.85, label="GEX Puts Weekly")
            ax_w3.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
            if isinstance(wcall_wall,(int,float)):
                ax_w3.axvline(x=wcall_wall, color=BLUE, linestyle='--', linewidth=1.2, label=f"Call Wall ({int(wcall_wall)})")
            if isinstance(wput_wall,(int,float)):
                ax_w3.axvline(x=wput_wall,  color=RED,  linestyle='--', linewidth=1.2, label=f"Put Wall ({int(wput_wall)})")
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


# ============================================================
#  FINAL FOOTER
# ============================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;"
    f"color:#2e4a5e;text-align:center;padding:0.5rem;'>"
    f"GEX ANALYSER · Options Flow Intelligence · "
    f"Data sourced from Yahoo Finance via yfinance · {ticker_input} · "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    f"</div>",
    unsafe_allow_html=True
)
