import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

st.title("📊 Analyse Gamma Exposure (GEX) — Version corrigée")

uploaded_file = st.file_uploader("Téléverse ton fichier CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, delimiter=",", header=2)

    # ===== SPOT INPUT (CRUCIAL) =====
    spot = st.number_input("Prix actuel du sous-jacent (Spot)", value=0.0)

    # ===== Dates =====
    current_date_dt = pd.to_datetime(datetime.now().date())
    df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
    unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()

    # Expiration la plus proche FUTURE
    future_dates = [d for d in unique_expiration_dates if d >= current_date_dt]
    closest_expiration_date_dt = min(future_dates)
    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')

    # ===== Filtrage =====
    df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()

    # ===== Conversion =====
    for col in ["Gamma","Open Interest","Gamma.1","Open Interest.1"]:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    # ===== VRAI CALCUL GEX =====
    df_filtered["GEX_Calls"] = df_filtered["Gamma"] * df_filtered["Open Interest"] * 100 * spot
    df_filtered["GEX_Puts"]  = df_filtered["Gamma.1"] * df_filtered["Open Interest.1"] * 100 * spot * -1

    df_filtered["GEX_Total"] = df_filtered["GEX_Calls"] + df_filtered["GEX_Puts"]
    df_filtered["ABS_Total"] = abs(df_filtered["GEX_Calls"]) + abs(df_filtered["GEX_Puts"])

    df_gex = df_filtered.groupby("Strike")[["GEX_Total","ABS_Total"]].sum().reset_index()
    df_gex.rename(columns={"GEX_Total":"GEX","ABS_Total":"ABS"}, inplace=True)
    df_gex = df_gex.sort_values("Strike")

    # ===== ZERO GAMMA CORRECT =====
    zero_gamma = None
    if df_gex["GEX"].min() < 0 < df_gex["GEX"].max():
        zero_gamma = np.interp(
            0,
            df_gex["GEX"].values,
            df_gex["Strike"].values
        )

    # ===== WALLS CORRECTES (ABS) =====
    max_abs = df_gex.loc[df_gex['ABS'].idxmax()]
    call_wall = max_abs['Strike'] if max_abs['GEX'] > 0 else 'N/A'
    put_wall  = max_abs['Strike'] if max_abs['GEX'] < 0 else 'N/A'

    # ===== NET GEX & REGIME =====
    net_gex = df_gex["GEX"].sum()
    gamma_regime = "🟢 Positive Gamma (Market pinned)" if net_gex > 0 else "🔴 Negative Gamma (Volatile)"

    st.info(gamma_regime)

    # ===== Graphique GEX =====
    top_n = st.slider("Nombre de strikes dominants (graphique seulement)", 5, 50, 50)
    df_top_abs = df_gex.nlargest(top_n, 'ABS').sort_values("Strike")

    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df_top_abs["Strike"], df_top_abs["GEX"], marker='o')
    ax.axhline(y=0, linestyle="--")

    if isinstance(call_wall, (int, float)):
        ax.axvline(x=call_wall, linestyle='--', label='CALL WALL')
    if isinstance(put_wall, (int, float)):
        ax.axvline(x=put_wall, linestyle='--', label='PUT WALL')
    if zero_gamma is not None:
        ax.axvline(x=zero_gamma, linestyle='--', label='ZERO GAMMA')

    ax.set_title(f"GEX Curve ({closest_expiration_date})")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # ===== Résumé =====
    summary_data = {
        'Metric': ['NET_GEX','CALL_WALL','PUT_WALL','ZERO_GAMMA'],
        'Value': [
            f"{net_gex:.2e}",
            call_wall,
            put_wall,
            round(zero_gamma,2) if zero_gamma else 'N/A'
        ]
    }

    st.write("### 📊 Résumé Gamma")
    st.dataframe(pd.DataFrame(summary_data))
