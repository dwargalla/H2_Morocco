"""MCA-Endergebnis: gewichteter Eignungs-Score 2025 und 2050 plus Karten.

Liest alle Kriterien-CSVs aus ``data/interim/mca_criteria/``, skaliert sie auf 0–100
(Landwirtschaft und Stadt invertiert; Wasser und Nicht-Konflikt sind bereits
skaliert), gewichtet sie mit ``dict_weights_category`` und multipliziert die
Summe mit der No-Go-Maske. Für 2050 ändern sich nur Landnutzung und Wasser.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp
    data/interim/mca_criteria/results_*.csv   alle Kriterien (PV, Wind, Erreichbarkeit, Landwirtschaft,
                            Stadt, Industrie, ländlich, Wasser, Nicht-Konflikt, No-Go)

Ausgaben:
    results/mca/results_mca_morocco_2025_2050.csv   Spalten MCA_Morocco_2025, MCA_Morocco_2050
    results/figures/mca/mca_morocco_{2025,2050,diff}.{png,pdf}
    results/figures/mca/pie_chart_weights.{png,pdf}

Hinweise:
    - Die Werte im Tortendiagramm sind fest eingetragen und weichen von
      ``dict_weights_category`` ab.
    - Die Straßengewichte werden rein positionell auf die Spalten von
      results_accessibility.csv angewandt (Reihenfolge muss stimmen).
    - ``plt.show()`` blockiert ohne grafische Oberfläche (``MPLBACKEND=Agg`` setzen).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python mca_maps.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import numpy as np
import matplotlib.colors as mcolors
import os
from dotenv import load_dotenv

# Min-Max_scale-funtion
def min_max_scale(df):
    """Skaliert jede Spalte linear auf 0–1 (Minimum → 0, Maximum → 1)."""
    return (df - df.min())/(df.max()-df.min())

def inverted_min_max_scale(df):
    """Skaliert jede Spalte invertiert auf 0–1 (Maximum → 0, Minimum → 1)."""
    df = -df
    return (df - df.min())/(df.max()-df.min())

# Grid morocco
gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
gdf_mca_morocco_2025 = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp').to_crs("EPSG:32629")
gdf_mca_morocco_2050 = gdf_mca_morocco_2025.copy()

# weights
dict_weights_category = {'avg_pv_yeald': 0.0619, 
                         'avg_windpower': 0.1237, 
                         'accessibility': 0.0825,
                         'agricultural_land_share': 0.0194,
                         'urban_zone_share': 0.0148,
                         'industrial_zone_share': 0.1446,
                         'rural_zone_share': 0.0496,
                         'water_avalibility': 0.3406,
                         'non_conflict_areas': 0.1630}

dict_weights_roads = {'motorway': 0.25,
                  'trunk': 0.18,
                  'primary':0.12, 
                  'secondary':0.09, 
                  'tertiary':0.06, 
                  'track':0.01, 
                  'track_grade1':0.03, 
                  'track_grade2':0.02, 
                  'track_grade3':0.01, 
                  'track_grade4':0.01, 
                  'unclassified':0.04, 
                  'railway':0.18}

# Read results
    # 2025
df_pv_yeald = pd.read_csv('../data/interim/mca_criteria/results_pv_yeald.csv')
df_wind_flh = pd.read_csv('../data/interim/mca_criteria/results_wind_flh.csv')
df_accessibility = pd.read_csv('../data/interim/mca_criteria/results_accessibility.csv')
df_agriculture = pd.read_csv('../data/interim/mca_criteria/results_agriculture.csv')
df_urban = pd.read_csv('../data/interim/mca_criteria/results_urban.csv')
df_industrie = pd.read_csv('../data/interim/mca_criteria/results_industrie.csv')
df_rural = pd.read_csv('../data/interim/mca_criteria/results_rural.csv')
df_water = pd.read_csv('../data/interim/mca_criteria/results_water_res_available.csv')
df_non_conflict_areas = pd.read_csv('../data/interim/mca_criteria/results_non_conflict_areas.csv')

df_nogo_zones = pd.read_csv('../data/interim/mca_criteria/results_nogo_zones.csv')

    # 2050
df_agriculture_2050 = pd.read_csv('../data/interim/mca_criteria/results_agriculture_2050.csv')
df_urban_2050 = pd.read_csv('../data/interim/mca_criteria/results_urban_2050.csv')
df_rural_2050 = pd.read_csv('../data/interim/mca_criteria/results_rural_2050.csv')
df_water_2050 = pd.read_csv('../data/interim/mca_criteria/results_water_res_availabil_2050.csv')

# Scale results.
# Water and non conflict already scored

    # PV Yeald. If high, then high score
df_pv_yeald = min_max_scale(df_pv_yeald)*100

    # Wind flh. If high, then high score
df_wind_flh = min_max_scale(df_wind_flh)*100

    # Accessibility. If high, then high score
df_accessibility -= df_accessibility.min()
df_accessibility = df_accessibility/(df_accessibility.max()-df_accessibility.min())
df_accessibility= df_accessibility*100*dict_weights_roads.values()

ds_accessibility_sum = df_accessibility.sum(axis=1).astype(float)

    # Agriculture, area share of agricultural land. If high, then low score
df_agriculture = inverted_min_max_scale(df_agriculture)*100
df_agriculture_2050 = inverted_min_max_scale(df_agriculture_2050)*100

    # Urban areas, area share of urban land. If high, then low score
df_urban = inverted_min_max_scale(df_urban)*100
df_urban_2050 = inverted_min_max_scale(df_urban_2050)*100

    # Industrie, area share of industrial land. If high, then high score
df_industrie = min_max_scale(df_industrie)*100

    # Rural areas, area share of rural land. If high, then high score
df_rural = min_max_scale(df_rural)*100
df_rural_2050 = min_max_scale(df_rural_2050)*100

# Results 2025
dict_results = {'avg_pv_yeald': df_pv_yeald.values.flatten(), 
                         'avg_windpower': df_wind_flh.values.flatten(), 
                         'accessibility': ds_accessibility_sum.values.flatten(),
                         'agricultural_land_share': df_agriculture.values.flatten(),
                         'urban_zone_share': df_urban.values.flatten(),
                         'industrial_zone_share': df_industrie.values.flatten(),
                         'rural_zone_share': df_rural.values.flatten(),
                         'water_avalibility': df_water.values.flatten(),
                         'non_conflict_areas': df_non_conflict_areas.values.flatten()}
df_results = pd.DataFrame(dict_results)

df_weighted_results = df_results*dict_weights_category
df_mca_morocco = df_weighted_results.sum(axis = 1) * df_nogo_zones['NoGo']
df_mca_morocco.name = 'MCA_Morocco'

gdf_mca_morocco_2025['Hydrogen_potential'] = df_mca_morocco

# Results 2050
dict_results_2050 = {'avg_pv_yeald': df_pv_yeald.values.flatten(), 
                         'avg_windpower': df_wind_flh.values.flatten(), 
                         'accessibility': ds_accessibility_sum.values.flatten(),
                         'agricultural_land_share': df_agriculture_2050.values.flatten(),
                         'urban_zone_share': df_urban_2050.values.flatten(),
                         'industrial_zone_share': df_industrie.values.flatten(),
                         'rural_zone_share': df_rural_2050.values.flatten(),
                         'water_avalibility': df_water_2050.values.flatten(),
                         'non_conflict_areas': df_non_conflict_areas.values.flatten()}
df_results_2050 = pd.DataFrame(dict_results_2050)

df_weighted_results_2050 = df_results_2050*dict_weights_category
df_mca_morocco_2050 = df_weighted_results_2050.sum(axis = 1) * df_nogo_zones['NoGo']
df_mca_morocco_2050.name = 'MCA_Morocco'

gdf_mca_morocco_2050['Hydrogen_potential'] = df_mca_morocco_2050

# Results export (csv)
df_mca = pd.concat([df_mca_morocco, df_mca_morocco_2050], axis=1)
df_mca.columns = ['MCA_Morocco_2025', 'MCA_Morocco_2050']
df_mca.to_csv('../results/mca/results_mca_morocco_2025_2050.csv', index=False)

### MAPS ###

# Hintergrundkarte: CARTO-Kacheln brauchen einen API-Key (CARTO_API_KEY in H2_Morocco/.env)
load_dotenv('../.env')
if not os.getenv('CARTO_API_KEY'):
    raise SystemExit('CARTO_API_KEY fehlt: .env.example nach .env kopieren und Key eintragen.')
basemap = cx.providers.CartoDB.Positron(apikey=os.getenv('CARTO_API_KEY'))

theme_rating = 'jet_r'
theme_diff   = 'OrRd_r'

# Map MCA 2025
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
gdf_mca_morocco_2025.plot(ax=ax, cmap = theme_rating, column= 'Hydrogen_potential', legend=True, legend_kwds={"label": "Relativ hydrogen potential", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_mca_morocco_2025.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/mca_morocco_2025.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/mca/mca_morocco_2025.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.show()

# Map MCA 2050
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
gdf_mca_morocco_2050.plot(ax=ax, cmap = theme_rating, column= 'Hydrogen_potential', legend=True, legend_kwds={"label": "Relativ hydrogen potential", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_mca_morocco_2050.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/mca_morocco_2050.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/mca/mca_morocco_2050.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.show()

    #Difference
gdf_mca_morocco_diff = gpd.GeoDataFrame(geometry=gdf_mca_morocco_2025.geometry, crs = gdf_mca_morocco_2025.crs,
                                               data = gdf_mca_morocco_2050['Hydrogen_potential'] - gdf_mca_morocco_2025['Hydrogen_potential'])

gdf_mca_morocco_diff['alpha'] = np.where(gdf_mca_morocco_diff['Hydrogen_potential'] == 0, 0, 1)

# Map MCA diff
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
gdf_mca_morocco_diff.plot(ax=ax,vmax = 0, cmap = theme_diff, column= 'Hydrogen_potential', legend=True, alpha=gdf_mca_morocco_diff['alpha'],
                          legend_kwds={"label": "Relativ change in hydrogen potential", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_mca_morocco_2025.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/mca_morocco_diff.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/mca/mca_morocco_diff.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.show()

# Pie chart of weights
labels =[
    'Ground Water Availability',
    'Surface Water Availability',
    'Sociopolitical Stability',
    'Industrial Zone Share',
    'Wind Energy Yield',
    'Accessibility',
    'PV Yield',
    'Rural Zone Share',
    'Agricultural Land Share',
    'Urban Zone Share'
]
sizes = [16.99, 16.99, 16.63, 16, 11.13, 8.31, 5.57, 4.96, 1.94, 1.48]
colors = ['deepskyblue', 'lightskyblue', 'lightcoral', 
          'orange', 'limegreen', 'plum', 
          'yellow', 'sandybrown', 
          'green', 'gray']

fig, ax = plt.subplots(figsize=(10, 6))
wedges, texts, autotexts = ax.pie(
    sizes,
    labels=None,  # Keine Labels an den Tortenstücken
    colors=colors,
    startangle=90,
    autopct='%1.2f%%',
    counterclock=False
)
ax.axis('equal')
ax.legend(wedges, labels, title="Criteria", bbox_to_anchor=(1, 0.5), loc="center left", 
          fontsize=14, title_fontsize=16)
plt.subplots_adjust(left=0.05, right=0.75)

# Verschiebe die Prozentzahlen für Agriculture (8) und Urban (9)
for i, autotext in enumerate(autotexts):
    if i == 8:
        autotext.set_position((1.2 * autotext.get_position()[0], 1.2 * autotext.get_position()[1]))
    if i == 9:
        autotext.set_position((1.3 * autotext.get_position()[0], 1.3 * autotext.get_position()[1]))

for autotext in autotexts:
    autotext.set_fontsize(12)  # z.B. 16, nach Wunsch anpassen

plt.tight_layout()
plt.savefig("../results/figures/mca/pie_chart_weights.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/mca/pie_chart_weights.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.show()