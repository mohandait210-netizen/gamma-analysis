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
