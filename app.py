import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
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


# ============================================================
#  IV SKEW SECTION
# ============================================================
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
