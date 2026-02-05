import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

st.title("📊 Analyse Gamma Exposure (GEX)")

# Étape 1 : Upload du fichier CSV
uploaded_file = st.file_uploader("Téléverse ton fichier CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, delimiter=",", header=2)

    # Étape 2 : Date actuelle
    current_date_dt = pd.to_datetime(datetime.now().date())

    # Étape 3 : Conversion des dates
    df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
    unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()
    closest_expiration_date_dt = min(unique_expiration_dates, key=lambda d: abs(d - current_date_dt))
    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')

    # Étape 4 : Filtrer
    df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()

    # Étape 5 : Calculs Gamma
    for col in ["Gamma","Open Interest","Gamma.1","Open Interest.1"]:
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    df_filtered["GEX_Calls"] = df_filtered["Gamma"]*df_filtered["Open Interest"]*(df_filtered["Strike"]**2)*100
    df_filtered["GEX_Puts"] = df_filtered["Gamma.1"]*df_filtered["Open Interest.1"]*(df_filtered["Strike"]**2)*100*-1
    df_filtered["GEX_Total"] = df_filtered["GEX_Calls"]+df_filtered["GEX_Puts"]
    df_filtered["ABS_Total"] = abs(df_filtered["GEX_Calls"])+abs(df_filtered["GEX_Puts"])

    df_gex = df_filtered.groupby("Strike")[["GEX_Total","ABS_Total"]].sum().reset_index()
    df_gex.rename(columns={"GEX_Total":"GEX","ABS_Total":"ABS"}, inplace=True)

    # Calculs supplémentaires
    net_gex = df_gex['GEX'].sum()
    df_gex_sorted = df_gex.sort_values("Strike")
    zero_gamma = None
    if df_gex_sorted["GEX"].min() < 0 < df_gex_sorted["GEX"].max():
        zero_gamma = np.interp(0, df_gex_sorted["GEX"], df_gex_sorted["Strike"])

    max_abs_strike_row = df_gex.loc[df_gex['ABS'].idxmax()]
    max_abs_strike = max_abs_strike_row['Strike']

    df_gex_positive = df_gex[df_gex['GEX'] > 0]
    call_wall = df_gex_positive.loc[df_gex_positive['GEX'].idxmax()]['Strike'] if not df_gex_positive.empty else 'N/A'

    df_gex_negative = df_gex[df_gex['GEX'] < 0]
    put_wall = df_gex_negative.loc[df_gex_negative['GEX'].idxmin()]['Strike'] if not df_gex_negative.empty else 'N/A'

    # --- Graphique GEX en courbe ---
    top_n = st.slider("Nombre de strikes dominants", 5, 50, 50)
    df_top_abs = df_gex.nlargest(top_n, 'ABS')

    # ✅ CORRECTION UNIQUE : trier par Strike pour une courbe correcte
    df_top_abs = df_top_abs.sort_values("Strike")

    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df_top_abs["Strike"], df_top_abs["GEX"], marker='o', linestyle='-', color='blue', label='GEX')
    ax.axhline(y=0, color="blue", linestyle="--", linewidth=2)

    # Lignes verticales
    if isinstance(call_wall, (int, float)):
        ax.axvline(x=call_wall, color='green', linestyle='--', linewidth=2, label='CALL_WALL')
    if isinstance(put_wall, (int, float)):
        ax.axvline(x=put_wall, color='red', linestyle='--', linewidth=2, label='PUT_WALL')
    if zero_gamma is not None and isinstance(zero_gamma, (int, float)):
        ax.axvline(x=zero_gamma, color='orange', linestyle='--', linewidth=2, label='ZERO GAMMA')

    ax.set_xlabel("Strike Price")
    ax.set_ylabel("Gamma Exposure (GEX)")
    ax.set_title(f"Courbe de Gamma Exposure (GEX) ({closest_expiration_date})")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # --- Graphique Calls vs Puts ---
    df_gex_components_grouped = df_filtered[['Strike','GEX_Calls','GEX_Puts']].dropna().copy()
    df_gex_components_grouped = df_gex_components_grouped.groupby('Strike')[['GEX_Calls','GEX_Puts']].sum().reset_index()
    df_top_components = df_gex_components_grouped[df_gex_components_grouped['Strike'].isin(df_top_abs['Strike'])]

    fig2, ax2 = plt.subplots(figsize=(14,7))
    bar_width = 0.4
    index = df_top_components['Strike']
    ax2.bar(index - bar_width/2, df_top_components['GEX_Calls'], bar_width, label='GEX Calls', color='skyblue')
    ax2.bar(index + bar_width/2, df_top_components['GEX_Puts'], bar_width, label='GEX Puts', color='lightcoral')
    ax2.axhline(y=0, color='gray', linestyle='--')
    ax2.set_title(f"GEX Calls vs Puts ({closest_expiration_date})")
    ax2.legend()
    ax.grid(True)
    st.pyplot(fig2)

    # --- Résumé ---
    summary_data = {
        'Metric': ['NET_GEX','Max ABS Strike','CALL_WALL','PUT_WALL','ZERO GAMMA'],
        'Value': [f"{net_gex:.2e}", max_abs_strike, call_wall, put_wall, round(zero_gamma,2) if zero_gamma else 'N/A']
    }
    df_summary = pd.DataFrame(summary_data)
    st.write("### 📊 Résumé de l'analyse Gamma")
    st.dataframe(df_summary)
    
    # --- Saisie utilisateur pour un strike et somme Last Sale ---
    strike_input = st.number_input("Entrez un strike :", min_value=0, step=1)
    if strike_input > 0:
        df_strike = df_filtered[df_filtered["Strike"] == strike_input]
        if not df_strike.empty:
            last_sale_call = df_strike["Last Sale"].iloc[0] if "Last Sale" in df_strike.columns else None
            last_sale_put = df_strike["Last Sale.1"].iloc[0] if "Last Sale.1" in df_strike.columns else None
            if last_sale_call is not None and last_sale_put is not None:
                total_last_sale = last_sale_call + last_sale_put
                st.success(f"👉 Somme Last Sale Call + Put pour le strike {strike_input} = {total_last_sale}")

                # ✅ Ajout : calcul EM+ et EM-
                em_plus = strike_input + total_last_sale
                em_minus = strike_input - total_last_sale

                st.info(f"📌 EM+ = {em_plus}")
                st.info(f"📌 EM- = {em_minus}")
            else:
                st.warning("Colonnes Last Sale manquantes dans le fichier CSV.")
        else:
            st.warning(f"Aucune donnée trouvée pour le strike {strike_input} à la date {closest_expiration_date}.")
            
            # --- Texte copiable ---
    top_gex_strikes = (
        df_gex
        .sort_values("ABS", ascending=False)
        ["Strike"]
        .head(4)
        .tolist()
    )

    while len(top_gex_strikes) < 4:
        top_gex_strikes.append("0000")

    copy_text = f"{call_wall}, {put_wall}, {round(zero_gamma,2) if zero_gamma else 'N/A'}, {em_plus}, {em_minus}, " \
                f"{top_gex_strikes[0]}, {top_gex_strikes[1]}, {top_gex_strikes[2]},"

    st.text_area(
        "Texte copiable",
        value=copy_text,
        height=120
    )
