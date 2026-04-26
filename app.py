import pandas as pd
import matplotlib.pyplot as plt
from google.colab import files
from datetime import datetime
import numpy as np

# Étape 1 : Téléverser le fichier CSV
uploaded = files.upload()
file_name = list(uploaded.keys())[0]  # Récupérer le nom du fichier uploadé
df = pd.read_csv(file_name, delimiter=",", header=2)  # Modifier le délimiteur et définir l'en-tête à la ligne 2 (0-indexée)

# Étape 2 : Obtenir la date actuelle et la formater
current_datetime = datetime.now()
formatted_current_date = current_datetime.strftime('%a %b %d %Y')

# Étape 3 : Convertir la colonne 'Expiration Date' en objets datetime pour trouver la date la plus proche
df['Expiration Date_dt'] = pd.to_datetime(df['Expiration Date'], errors='coerce')
current_date_dt = pd.to_datetime(formatted_current_date)
unique_expiration_dates = df['Expiration Date_dt'].dropna().unique()

min_diff = pd.Timedelta.max
closest_expiration_date_dt = None

for exp_date in unique_expiration_dates:
    time_diff = abs(exp_date - current_date_dt)
    if time_diff < min_diff:
        min_diff = time_diff
        closest_expiration_date_dt = exp_date

# Convertir la date d'expiration la plus proche (objet datetime) en format string pour l'affichage
if closest_expiration_date_dt is not None:
    closest_expiration_date = closest_expiration_date_dt.strftime('%a %b %d %Y')
else:
    closest_expiration_date = None

# Étape 4 : Filtrer les options expirant à la date la plus proche trouvée
# Utiliser la colonne datetime pour le filtrage pour plus de robustesse
df_filtered = df[df['Expiration Date_dt'] == closest_expiration_date_dt].copy()

# Supprimer la colonne temporaire 'Expiration Date_dt' du DataFrame original et filtré
df = df.drop(columns=['Expiration Date_dt'])
if 'Expiration Date_dt' in df_filtered.columns:
    df_filtered = df_filtered.drop(columns=['Expiration Date_dt'])

# Étape 5 & 6 : Extraction des données Gamma et Open Interest, conversion et calcul du GEX et ABS
# Assurer que les colonnes sont numériques
df_filtered["Gamma"] = df_filtered["Gamma"].astype(float)
df_filtered["Open Interest"] = df_filtered["Open Interest"].astype(float)
df_filtered["Gamma.1"] = df_filtered["Gamma.1"].astype(float)
df_filtered["Open Interest.1"] = df_filtered["Open Interest.1"].astype(float)

# Calculer le GEX et ABS pour les calls et les puts séparément sur df_filtered
df_filtered["GEX_Calls"] = df_filtered["Gamma"] * df_filtered["Open Interest"] * (df_filtered["Strike"]**2) * 100
df_filtered["GEX_Puts"] = df_filtered["Gamma.1"] * df_filtered["Open Interest.1"] * (df_filtered["Strike"]**2) * 100 * -1

# Calculer le GEX total selon la formule demandée: GEX = (gamma de call * oi de call) - (gamma de put * oi de put)
df_filtered["GEX_Total"] = df_filtered["GEX_Calls"] + df_filtered["GEX_Puts"]

# Calculer l'Absolute Gamma (ABS) selon la formule demandée: ABS = (gamma de call * oi de call) + (gamma de put * oi de put)
df_filtered["ABS_Total"] = (
    abs(df_filtered["GEX_Calls"]) +
    abs(df_filtered["GEX_Puts"])
)

# Préparer le tableau final df_gex en regroupant par Strike et en sommant les GEX_Total et ABS_Total
df_gex = df_filtered[["Strike", "GEX_Total", "ABS_Total"]].dropna().copy()
df_gex = df_gex.groupby("Strike")[["GEX_Total", "ABS_Total"]].sum().reset_index()
df_gex.rename(columns={"GEX_Total": "GEX", "ABS_Total": "ABS"}, inplace=True)

# Éliminer les strikes où GEX est égal à 0
# df_gex = df_gex[df_gex['GEX'] != 0].copy()

# Fonction pour mettre en évidence la ligne avec le plus grand ABS
def highlight_max_abs(s):
    is_max = s == s.max()
    return ['border: 2px solid white' if v else '' for v in is_max]

# Fonction pour colorer les cellules GEX en fonction de leur polarité
def highlight_gex_polarity(s):
    return ['background-color: green' if v > 0 else 'background-color: red' for v in s]

# --- Start of modifications to calculate summary metrics earlier for plotting ---
# Calculate ABS_GEX early for consistent peak identification and summary metrics
df_gex['ABS_GEX'] = df_gex['GEX'].abs()

# Calcul du NET_GEX (somme de tous les GEX)
net_gex = df_gex['GEX'].sum()

# Trouver le Strike avec le plus grand ABS
max_abs_strike_row = df_gex.loc[df_gex['ABS'].idxmax()]
max_abs_strike = max_abs_strike_row['Strike']

# Calculer CALL_WALL (strike avec le plus grand GEX positif)
df_gex_positive = df_gex[df_gex['GEX'] > 0]
if not df_gex_positive.empty:
    call_wall = df_gex_positive.loc[df_gex_positive['GEX'].idxmax()]['Strike']
else:
    call_wall = 'N/A' # Aucune valeur GEX positive trouvée

# Calculer PUT_WALL (strike avec le plus petit GEX négatif)
df_gex_negative = df_gex[df_gex['GEX'] < 0]
if not df_gex_negative.empty:
    put_wall = df_gex_negative.loc[df_gex_negative['GEX'].idxmin()]['Strike']
else:
    put_wall = 'N/A' # Aucune valeur GEX négative trouvée
# --- End of modifications ---


# Logique de traçage dynamique
unique_strike_count = df_gex['Strike'].nunique()

if unique_strike_count > 50:
    # Use the already calculated max_abs_strike as peak for centering
    peak_strike = max_abs_strike

    # Find the index of the peak strike
    peak_strike_index = df_gex[df_gex['Strike'] == peak_strike].index[0]

    # Calculate start and end indices to select approximately 50 strikes
    start_index = max(0, peak_strike_index - 25)
    end_index = min(len(df_gex) - 1, peak_strike_index + 25)

    # Select the subset of df_gex for plotting
    df_plot = df_gex.iloc[start_index : end_index + 1].copy()

    # Also, prepare df for GEX Calls/Puts components plotting
    df_gex_components_grouped = df_filtered[['Strike', 'GEX_Calls', 'GEX_Puts']].dropna().copy()
    df_gex_components_grouped = df_gex_components_grouped.groupby('Strike')[['GEX_Calls', 'GEX_Puts']].sum().reset_index()
    df_plot_gex_components = df_gex_components_grouped.iloc[start_index : end_index + 1].copy()

else:
    # If 50 or fewer unique strikes, plot all of them
    df_plot = df_gex.copy()

    # Also, prepare df for GEX Calls/Puts components plotting
    df_gex_components_grouped = df_filtered[['Strike', 'GEX_Calls', 'GEX_Puts']].dropna().copy()
    df_plot_gex_components = df_gex_components_grouped.groupby('Strike')[['GEX_Calls', 'GEX_Puts']].sum().reset_index()


# Étape 8 : Afficher les courbes de GEX et ABS en fonction de Strike sur des graphiques séparés

# Graphique GEX
plt.figure(figsize=(12, 6))
plt.plot(df_plot["Strike"], df_plot["GEX"], marker='o', linestyle='-', color='blue', label='GEX')
plt.xlabel("Strike Price")
plt.ylabel("Gamma Exposure (GEX)")
plt.title(f"Courbe de Gamma Exposure (GEX) par Strike pour la date d'expiration la plus proche ({closest_expiration_date})")
plt.grid(True)

# Ajuster les ticks de l'axe X pour une meilleure lisibilité
if len(df_plot) > 20:
    tick_interval = max(1, len(df_plot) // 10)
    plt.xticks(df_plot["Strike"].iloc[::tick_interval], rotation=45)
else:
    plt.xticks(df_plot["Strike"], rotation=45)

plt.axhline(y=0, color="blue", linestyle="--", linewidth=2) # L'axe de 0 en bleu et plus épais

# --- Start of modifications to add vertical lines to GEX plot ---
min_plot_strike = df_plot['Strike'].min()
max_plot_strike = df_plot['Strike'].max()

if isinstance(max_abs_strike, (int, float)) and min_plot_strike <= max_abs_strike <= max_plot_strike:
    plt.axvline(x=max_abs_strike, color='purple', linestyle='--', linewidth=2, label='Strike (Max ABS)')
if isinstance(call_wall, (int, float)) and min_plot_strike <= call_wall <= max_plot_strike:
    plt.axvline(x=call_wall, color='green', linestyle='--', linewidth=2, label='CALL_WALL')
if isinstance(put_wall, (int, float)) and min_plot_strike <= put_wall <= max_plot_strike:
    plt.axvline(x=put_wall, color='red', linestyle='--', linewidth=2, label='PUT_WALL')
# --- End of modifications ---

plt.legend()
plt.tight_layout()

# Save and download the GEX plot
gex_filename = f"gex_plot_{closest_expiration_date.replace(' ', '_')}.png"
plt.savefig(gex_filename)
# files.download(gex_filename) # Removed this line

plt.show()

# Graphique ABS
plt.figure(figsize=(12, 6))
plt.bar(df_plot["Strike"], df_plot["ABS"], color='red', label='ABS') # Changed to bar plot
plt.xlabel("Strike Price")
plt.ylabel("Absolute Gamma (ABS)")
plt.title(f"Graphique à barres d'Absolute Gamma (ABS) par Strike pour la date d'expiration la plus proche ({closest_expiration_date})")
plt.grid(True)

# Ajuster les ticks de l'axe X pour une meilleure lisibilité
if len(df_plot) > 20:
    tick_interval = max(1, len(df_plot) // 10)
    plt.xticks(df_plot["Strike"].iloc[::tick_interval], rotation=45)
else:
    plt.xticks(df_plot["Strike"], rotation=45)

# plt.axhline(y=0, color="red", linestyle="--", linewidth=2) # Line at y=0 is less relevant for bar plot of absolute values
plt.legend()
plt.tight_layout()

# Save and download the ABS plot
abs_filename = f"abs_plot_{closest_expiration_date.replace(' ', '_')}.png"
plt.savefig(abs_filename)
# files.download(abs_filename) # Removed this line

plt.show()

# --- Start of new GEX Calls and GEX Puts grouped bar chart ---
plt.figure(figsize=(14, 7))
bar_width = 0.35
index = df_plot_gex_components['Strike']

bar1 = plt.bar(index - bar_width/2, df_plot_gex_components['GEX_Calls'], bar_width, label='GEX Calls', color='skyblue')
bar2 = plt.bar(index + bar_width/2, df_plot_gex_components['GEX_Puts'], bar_width, label='GEX Puts', color='lightcoral')

plt.xlabel("Strike Price")
plt.ylabel("Gamma Exposure (GEX)")
plt.title(f"GEX Calls et GEX Puts par Strike pour la date d'expiration la plus proche ({closest_expiration_date})")
plt.grid(True, axis='y')

# Ajuster les ticks de l'axe X pour une meilleure lisibilité
if len(df_plot_gex_components) > 20:
    tick_interval = max(1, len(df_plot_gex_components) // 10)
    plt.xticks(index.iloc[::tick_interval], rotation=45)
else:
    plt.xticks(index, rotation=45)

plt.axhline(y=0, color='gray', linestyle='--', linewidth=1)
plt.legend()
plt.tight_layout()

# Save and download the GEX Calls/Puts plot
gex_components_filename = f"gex_calls_puts_plot_{closest_expiration_date.replace(' ', '_')}.png"
plt.savefig(gex_components_filename)
# files.download(gex_components_filename)

plt.show()
# --- End of new GEX Calls and GEX Puts grouped bar chart ---

# --- Summary table display (already updated in previous turn) ---
# Créer un DataFrame pour afficher les résultats
summary_data = {'Metric': ['Strike (Max ABS)', 'NET_GEX', 'CALL_WALL', 'PUT_WALL'],
                'Value': [max_abs_strike, net_gex, call_wall, put_wall]}
df_summary = pd.DataFrame(summary_data)

# Formater le DataFrame pour l'affichage
df_summary_formatted = df_summary.copy()
for idx, row in df_summary_formatted.iterrows():
    if row['Metric'] == 'NET_GEX':
        if isinstance(row['Value'], (int, float, np.number)): # Use np.number for numpy floats
            df_summary_formatted.loc[idx, 'Value'] = f'{row["Value"]:.2e}'
        else:
            df_summary_formatted.loc[idx, 'Value'] = str(row['Value'])
    elif isinstance(row['Value'], (int, float, np.number)):
        df_summary_formatted.loc[idx, 'Value'] = f'{row["Value"]:.2f}'
    else:
        df_summary_formatted.loc[idx, 'Value'] = str(row['Value'])

print(f"📊 Résumé de l'analyse Gamma pour la date d'expiration la plus proche ({closest_expiration_date}) :")
display(df_summary_formatted.style.hide(axis='index'))
