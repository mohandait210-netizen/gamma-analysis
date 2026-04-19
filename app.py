import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from datetime import datetime
from pathlib import Path

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
MULTIPLIER = 41.36   # Ratio de conversion (ex: SPX → CAC40)

# ============================================================
#  HEADER
# ============================================================
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

    max_abs_strike = df_gex.loc[df_gex['ABS'].idxmax(), 'Strike']

    df_gex_positive = df_gex[df_gex['GEX'] > 0]
    call_wall = (df_gex_positive.loc[df_gex_positive['GEX'].idxmax(), 'Strike']
                 if not df_gex_positive.empty else 'N/A')

    df_gex_negative = df_gex[df_gex['GEX'] < 0]
    put_wall = (df_gex_negative.loc[df_gex_negative['GEX'].idxmin(), 'Strike']
                if not df_gex_negative.empty else 'N/A')

    # ============================================================
    #  REGIME + KPI CARDS
    # ============================================================
    is_positive = net_gex > 0
    regime_color  = GREEN if is_positive else RED
    regime_label  = "POSITIVE GAMMA - Market Pinned 🟢" if is_positive else "NEGATIVE GAMMA - Volatile 🔴"
    regime_glow   = "rgba(0,255,157,0.12)" if is_positive else "rgba(255,60,90,0.12)"

    st.markdown(
        f"""<div style='background:{regime_glow};border:1px solid {regime_color};
        border-radius:8px;padding:0.75rem 1.25rem;margin-bottom:1.5rem;
        font-family:IBM Plex Mono,monospace;font-size:0.85rem;
        color:{regime_color};letter-spacing:0.08em;font-weight:600;'>
        ▶ RÉGIME : {regime_label}
        </div>""",
        unsafe_allow_html=True
    )

    # KPI row
    kpi_cols = st.columns(4)
    kpis = [
        ("CALL WALL",   call_wall,                              BLUE),
        ("PUT WALL",    put_wall,                               RED),
        ("ZERO GAMMA",  round(zero_gamma, 1) if zero_gamma else "N/A", ORANGE),
        ("NET GEX",     f"{net_gex:.2e}",                       GREEN if is_positive else RED),
    ]
    for col, (label, value, color) in zip(kpi_cols, kpis):
        col.markdown(
            f"""<div style='background:{CARD_BG};border:1px solid {BORDER};
            border-left:3px solid {color};border-radius:8px;
            padding:1rem 1.2rem;'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;
            color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;
            margin-bottom:0.5rem;'>{label}</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:1.4rem;
            font-weight:600;color:{color};'>{value}</div>
            </div>""",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    #  GRAPHIQUES
    # ============================================================
    top_n = st.slider("Nombre de strikes dominants", 5, 50, 50)
    df_top_abs = df_gex.nlargest(top_n, 'ABS').sort_values("Strike")

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

        if isinstance(call_wall, (int, float)):
            ax.axvline(x=call_wall, color=BLUE,   linestyle='--', linewidth=1.2, label='Call Wall')
        if isinstance(put_wall, (int, float)):
            ax.axvline(x=put_wall,  color=RED,    linestyle='--', linewidth=1.2, label='Put Wall')
        if zero_gamma is not None:
            ax.axvline(x=zero_gamma, color=ORANGE, linestyle='--', linewidth=1.2, label='Zero Gamma')

        ax.set_title(f"GAMMA EXPOSURE CURVE - {closest_expiration_date}")
        ax.set_xlabel("Strike Price")
        ax.set_ylabel("GEX")
        ax.legend()
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
        df_top_comp = df_gex_comp[df_gex_comp['Strike'].isin(df_top_abs['Strike'])]

        fig2, ax2 = plt.subplots(figsize=(8, 4.5))
        bw = 0.4
        ax2.bar(df_top_comp['Strike'] - bw / 2, df_top_comp['GEX_Calls'],
                bw, label='GEX Calls', color=BLUE,  alpha=0.85)
        ax2.bar(df_top_comp['Strike'] + bw / 2, df_top_comp['GEX_Puts'],
                bw, label='GEX Puts',  color=RED,   alpha=0.85)
        ax2.axhline(y=0, color=BORDER, linestyle='--', linewidth=1)
        ax2.set_title(f"CALLS vs PUTS - {closest_expiration_date}")
        ax2.legend()
        fig2.tight_layout()
        st.pyplot(fig2)

    # ============================================================
    #  RÉSUMÉ TABLE
    # ============================================================
    st.markdown("### 📊 Résumé de l'analyse Gamma")
    df_summary = pd.DataFrame({
        'Metric': ['NET GEX', 'Max ABS Strike', 'Call Wall', 'Put Wall', 'Zero Gamma'],
        'Value':  [
            f"{net_gex:.2e}",
            max_abs_strike,
            call_wall,
            put_wall,
            round(zero_gamma, 2) if zero_gamma else 'N/A'
        ]
    })
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # ============================================================
    #  EXPECTED MOVE
    # ============================================================
    st.markdown("### 🎯 Expected Move")
    em_plus  = "0000"
    em_minus = "0000"

    strike_input = st.number_input("Strike de référence :", min_value=0, step=1)

    if strike_input > 0:
        df_strike = df_filtered[df_filtered["Strike"] == strike_input]
        if not df_strike.empty:
            ls_call = df_strike["Last Sale"].iloc[0]   if "Last Sale"   in df_strike.columns else None
            ls_put  = df_strike["Last Sale.1"].iloc[0] if "Last Sale.1" in df_strike.columns else None
            if ls_call is not None and ls_put is not None:
                try:
                    total = float(ls_call) + float(ls_put)
                    em_plus  = strike_input + total
                    em_minus = strike_input - total
                    em_col1, em_col2, em_col3 = st.columns(3)
                    em_col1.metric("Last Sale C+P", f"{total:.2f}")
                    em_col2.metric("EM+", f"{em_plus:.2f}")
                    em_col3.metric("EM−", f"{em_minus:.2f}")
                except Exception:
                    st.warning("❌ Valeurs Last Sale non numériques.")
            else:
                st.warning("Colonnes Last Sale manquantes.")
        else:
            st.warning(f"Aucune donnée pour le strike {strike_input} ({closest_expiration_date}).")

    # ============================================================
    #  TEXTES COPIABLES
    # ============================================================
    top_gex_strikes = (
        df_gex.sort_values("ABS", ascending=False)["Strike"]
        .head(5).tolist()
    )
    while len(top_gex_strikes) < 5:
        top_gex_strikes.append("0000")

    copy_text = (
        f"{call_wall}, {put_wall}, "
        f"{round(zero_gamma, 2) if zero_gamma else 'N/A'}, "
        f"{em_plus}, {em_minus}, "
        f"{top_gex_strikes[0]}, {top_gex_strikes[1]}, "
        f"{top_gex_strikes[2]}, {top_gex_strikes[3]},"
    )

    def safe_int_multiply(val):
        try:
            return int(round(float(val) * MULTIPLIER, 0))
        except Exception:
            return val

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

    st.markdown("### 📋 Export")
    c1, c2 = st.columns(2)
    with c1:
        st.text_area("Valeurs brutes", value=copy_text, height=80)
    with c2:
        st.text_area(f"Valeurs × {MULTIPLIER} (entiers)", value=", ".join(map(str, multiplied)), height=80)

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
