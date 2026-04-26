import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from datetime import datetime

# ==============================
# Fonction Black-Scholes Gamma
# ==============================
def black_scholes_gamma(S, K, T, r, sigma):
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    return norm.pdf(d1) / (S*sigma*np.sqrt(T))

# ==============================
# Interface Streamlit
# ==============================
st.set_page_config(page_title="GEX Analyser", layout="wide")
st.title("📊 Gamma Exposure (GEX)")

symbol = st.text_input("Ticker :", "SPY")
expiry_index = st.number_input("Index expiration (0 = première)", min_value=0, step=1, value=0)

if symbol:
    ticker = yf.Ticker(symbol)
    expiries = ticker.options
    if len(expiries) > expiry_index:
        expiry = expiries[expiry_index]
        chain = ticker.option_chain(expiry)
        df_calls = chain.calls.copy()
        df_puts = chain.puts.copy()

        # Spot approximatif (prix actuel du sous-jacent)
        spot_price = ticker.history(period="1d")["Close"].iloc[-1]
        r = 0.01  # taux sans risque
        # Temps jusqu’à expiration en années
        T = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.now()).days / 365

        # Calcul Gamma pour calls et puts
        df_calls["Gamma"] = df_calls.apply(
            lambda row: black_scholes_gamma(spot_price, row["strike"], T, r, row["impliedVolatility"])
            if row["impliedVolatility"] > 0 else 0, axis=1
        )
        df_puts["Gamma"] = df_puts.apply(
            lambda row: black_scholes_gamma(spot_price, row["strike"], T, r, row["impliedVolatility"])
            if row["impliedVolatility"] > 0 else 0, axis=1
        )

        # Calcul GEX (Gamma × OI × Strike² × 100)
        df_calls["GEX_Calls"] = df_calls["Gamma"] * df_calls["openInterest"] * (df_calls["strike"]**2) * 100
        df_puts["GEX_Puts"] = df_puts["Gamma"] * df_puts["openInterest"] * (df_puts["strike"]**2) * 100 * -1

        df_gex = pd.DataFrame({
            "Strike": df_calls["strike"],
            "GEX_Calls": df_calls["GEX_Calls"],
            "GEX_Puts": df_puts["GEX_Puts"]
        })
        df_gex["GEX_Total"] = df_gex["GEX_Calls"] + df_gex["GEX_Puts"]

        # Niveaux clés
        call_wall = df_gex.loc[df_gex["GEX_Calls"].idxmax(), "Strike"]
        put_wall = df_gex.loc[df_gex["GEX_Puts"].idxmin(), "Strike"]
        net_gex = df_gex["GEX_Total"].sum()

        # Détection Zero Gamma (croisement autour de 0)
        zero_gamma = None
        df_sorted = df_gex.sort_values("Strike")
        for i in range(len(df_sorted)-1):
            g0, g1 = df_sorted["GEX_Total"].iloc[i], df_sorted["GEX_Total"].iloc[i+1]
            s0, s1 = df_sorted["Strike"].iloc[i], df_sorted["Strike"].iloc[i+1]
            if g0 * g1 < 0:
                zero_gamma = round(s0 + (0-g0)*(s1-s0)/(g1-g0), 2)
                break

        # ==============================
        # Affichage KPI
        # ==============================
        st.subheader("📌 Niveaux clés")
        st.write(f"Call Wall : {call_wall}")
        st.write(f"Put Wall : {put_wall}")
        st.write(f"Zero Gamma : {zero_gamma}")
        st.write(f"Net GEX : {net_gex:.2e}")

        # ==============================
        # Courbe GEX
        # ==============================
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(df_sorted["Strike"], df_sorted["GEX_Total"], color="blue", marker="o", label="GEX Total")
        ax.axhline(0, color="black", linestyle="--")

        ax.axvline(call_wall, color="green", linestyle="--", label="Call Wall")
        ax.axvline(put_wall, color="red", linestyle="--", label="Put Wall")
        if zero_gamma:
            ax.axvline(zero_gamma, color="orange", linestyle="--", label="Zero Gamma")

        ax.set_title(f"GEX Curve - {symbol} ({expiry})")
        ax.set_xlabel("Strike")
        ax.set_ylabel("Gamma Exposure")
        ax.legend()
        st.pyplot(fig)
