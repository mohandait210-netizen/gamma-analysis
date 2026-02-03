import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

st.title("📊 Analyse Gamma Exposure (GEX)")

# -------- CACHE (important pour performance) --------
@st.cache_data
def load_data(file):
    return pd.read_csv(file, delimiter=",", header=2)

uploaded_file = st.file_uploader("Téléverse ton fichier CSV", type=["csv"])

if uploaded_file is not None:

    df = load_data(uploaded_file)

    # -------- Spot price (version institutionnelle) --------
    spot = st.number_input("Spot price", value=500.0)

    # -------- Date actuelle --------
    current_date_dt = pd.to_datetime(datetime.now().date())

    # -------- Conversion dates --------
    df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
    unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()

    closest_expiration_date_dt = min(
        unique_expiration_dates,
        key=lambda d: abs(d - current_date_dt)
    )

    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')

    # -------- Filtrer --------
    df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()

    # -------- Convertir colonnes --------
    for col in ["Gamma","Open Interest","Gamma.1","Open Interest.1","Strike"]:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_filtered.dropna(subset=["Strike"], inplace=True)

    # -------- Calcul GEX (formule PRO basée sur Spot) --------
    df_filtered["GEX_Calls"] = (
        df_filtered["Gamma"] *
        df_filtered["Open Interest"] *
        (spot**2) * 0.01 * 100
    )

    df_filtered["GEX_Puts"] = (
        df_filtered["Gamma.1"] *
        df_filtered["Open Interest.1"] *
        (spot**2) * 0.01 * 100 * -1
    )

    df_filtered["GEX_Total"] = df_filtered["GEX_Calls"] + df_filtered["GEX_Puts"]
    df_filtered["ABS_Total"] = abs(df_filtered["GEX_Calls"]) + abs(df_filtered["GEX_Puts"])

    df_gex = df_filtered.groupby("Strike")[["GEX_Total","ABS_Total"]].sum().reset_index()
    df_gex.rename(columns={"GEX_Total":"GEX","ABS_Total":"ABS"}, inplace=True)

    net_gex = df_gex['GEX'].sum()

    # -------- ZERO GAMMA (corrigé) --------
    zero_gamma = None
    df_zero = df_gex.sort_values("GEX")

    if df_zero["GEX"].min() < 0 < df_zero["GEX"].max():
        zero_gamma = np.interp(
            0,
            df_zero["GEX"],
            df_zero["Strike"]
        )

    # -------- Walls sécurisées --------
    call_wall = None
    put_wall = None

    df_positive = df_gex[df_gex['GEX'] > 0]
    if not df_positive.empty:
        call_wall = df_positive.loc[df_positive['GEX'].idxmax(),'Strike']

    df_negative = df_gex[df_gex['GEX'] < 0]
    if not df_negative.empty:
        put_wall = df_negative.loc[df_negative['GEX'].idxmin(),'Strike']

    max_abs_strike = df_gex.loc[df_gex['ABS'].idxmax(),'Strike']

    # -------- Gamma Flip Distance --------
    flip_distance = None
    if zero_gamma is not None:
        flip_distance = ((zero_gamma - spot) / spot) * 100

    # -------- CUMULATIVE GAMMA --------
    df_gex_sorted = df_gex.sort_values("Strike")
    df_gex_sorted["CumGEX"] = df_gex_sorted["GEX"].cumsum()

    # -------- Choix affichage --------
    show_full = st.checkbox("Afficher tout le Gamma Profile")
    top_n = st.slider("Nombre de strikes dominants", 5, 40, 15)

    if show_full:
        plot_df = df_gex_sorted
    else:
        plot_df = df_gex.nlargest(top_n, 'ABS').sort_values("Strike")

    # -------- Graphique GEX --------
    fig, ax = plt.subplots(figsize=(12,6))

    ax.plot(plot_df["Strike"], plot_df["GEX"], marker='o')
    ax.axhline(y=0, linestyle="--")

    if call_wall is not None:
        ax.axvline(x=call_wall, linestyle='--', label='CALL WALL')

    if put_wall is not None:
        ax.axvline(x=put_wall, linestyle='--', label='PUT WALL')

    if zero_gamma is not None:
        ax.axvline(x=zero_gamma, linestyle='--', label='ZERO GAMMA')

    ax.set_xlabel("Strike Price")
    ax.set_ylabel("Gamma Exposure (GEX)")
    ax.set_title(f"GEX Profile ({closest_expiration_date})")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # -------- Graphique Cumulative Gamma --------
    st.subheader("Cumulative Gamma")

    fig2, ax2 = plt.subplots(figsize=(12,6))
    ax2.plot(df_gex_sorted["Strike"], df_gex_sorted["CumGEX"])
    ax2.axhline(y=0, linestyle="--")

    ax2.set_xlabel("Strike")
    ax2.set_ylabel("Cumulative GEX")
    ax2.grid(True)

    st.pyplot(fig2)

    # -------- Résumé --------
    summary_data = {
        'Metric': [
            'NET_GEX',
            'Max ABS Strike',
            'CALL_WALL',
            'PUT_WALL',
            'ZERO_GAMMA',
            'Gamma Flip Distance (%)'
        ],
        'Value': [
            f"{net_gex:.2e}",
            max_abs_strike,
            call_wall if call_wall else "N/A",
            put_wall if put_wall else "N/A",
            round(zero_gamma,2) if zero_gamma else "N/A",
            round(flip_distance,2) if flip_distance else "N/A"
        ]
    }

    df_summary = pd.DataFrame(summary_data)

    st.write("### 📊 Résumé de l'analyse Gamma")
    st.dataframe(df_summary)
