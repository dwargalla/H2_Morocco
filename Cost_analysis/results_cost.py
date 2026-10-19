"""Schritt 5 der Kostenanalyse: Kostenkarten, Balkendiagramme und zusammengefasste Ergebnis-CSV.

Eingaben:
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp
    data/interim/grid/grid_morocco_clear.shp
    results/cost/results_cost_{2025,2050}.csv   aus cost_analysis_h2_morocco.py

Ausgaben:
    results/figures/cost/cost_map_{2025,2050}.{pdf,png}                 H2-Kosten je Zelle
    results/figures/cost/bar_cost_components_morocco_seperate.{pdf,png} mittlere Kostenanteile, nebeneinander
    results/figures/cost/bar_cost_components_morocco.{pdf,png}          mittlere Kostenanteile, gestapelt
    results/cost/results_cost_morocco_2025_2050.csv             Gesamtpreis 2025 und 2050 je Zelle

Hinweise:
    - ``plt.show()`` blockiert ohne grafische Oberfläche (``MPLBACKEND=Agg`` setzen).
    - Ausführen aus ``Cost_analysis/``: ``python results_cost.py``
"""

import geopandas as gpd
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import contextily as cx
import os
from dotenv import load_dotenv

# Hintergrundkarte: CARTO-Kacheln brauchen einen API-Key (CARTO_API_KEY in H2_Morocco/.env)
load_dotenv('../.env')
if not os.getenv('CARTO_API_KEY'):
    raise SystemExit('CARTO_API_KEY fehlt: .env.example nach .env kopieren und Key eintragen.')
basemap = cx.providers.CartoDB.Positron(apikey=os.getenv('CARTO_API_KEY'))


gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
gdf_grid_morocco        = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp').to_crs("EPSG:32629")

df_res_2025             = pd.read_csv('../results/cost/results_cost_2025.csv')
df_res_2050             = pd.read_csv('../results/cost/results_cost_2050.csv')

theme_rating = 'jet'
theme_diff   = 'OrRd_r'

# Beispiel-Koordinate
y_limit = 3.15e6

# Filter: alle Objekte, deren Geometrie-Zentrum südlicher liegt
gdf_south = gdf_grid_morocco[gdf_grid_morocco.geometry.centroid.y < y_limit]
gdf_north = gdf_grid_morocco[gdf_grid_morocco.geometry.centroid.y >= y_limit]

# Costs 2025
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=2)
gdf_grid_morocco.plot(ax=ax, cmap=theme_rating, column=df_res_2025['H2_Price_2025 [EUR/MWh_h2]'], legend=True, legend_kwds={"label": r"$\mathrm{[€/MWh_{H_2}]}$", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=10)
cbar_ax.yaxis.label.set_size(20)
plt.savefig("../results/figures/cost/cost_map_2025.pdf", format="pdf", bbox_inches='tight', pad_inches=0)#
plt.savefig("../results/figures/cost/cost_map_2025.png", format="png", dpi = 300, bbox_inches='tight', pad_inches=0)
plt.show()

# Costs 2050
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=2)
gdf_grid_morocco.plot(ax=ax, cmap=theme_rating, column=df_res_2050['H2_Price_2050 [EUR/MWh_h2]'], legend=True, legend_kwds={"label": r"$\mathrm{[€/MWh_{H_2}]}$", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=10)
cbar_ax.yaxis.label.set_size(20)
plt.savefig("../results/figures/cost/cost_map_2050.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/cost/cost_map_2050.png", format="png", dpi = 300, bbox_inches='tight', pad_inches=0)
plt.show()

# Kostenanteile
labels = ['Electrolyzer', 'Electricity Cost', 'Grid Cost', 'Pipeline Cost', 'Water Cost']
costs_2025 = [round(df_res_2025['Electrolyzer_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2025['RE_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2025['Distribution_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2025['Pipeline_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2025['Water_cost [EUR/MWh_h2]'].mean(), 2)]
costs_2050 = [round(df_res_2050['Electrolyzer_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2050['RE_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2050['Distribution_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2050['Pipeline_cost [EUR/MWh_h2]'].mean(), 2), round(df_res_2050['Water_cost [EUR/MWh_h2]'].mean(), 2)]
x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars
fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, costs_2025, width, label='2025', color='skyblue')
rects2 = ax.bar(x + width/2, costs_2050, width, label='2050', color='orange')
# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel(r'Cost $\mathrm{[€/MWh_{H_2}]}$')
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right')
ax.legend()
ax.bar_label(rects1, padding=3)
ax.bar_label(rects2, padding=3)
fig.tight_layout()
plt.savefig("../results/figures/cost/bar_cost_components_morocco_seperate.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/cost/bar_cost_components_morocco_seperate.png", format="png", dpi = 300, bbox_inches='tight', pad_inches=0)
plt.show()

# Gestapeltes Säulendiagramm
x = np.arange(2)  # 2025 und 2050
width = 0.6

fig, ax = plt.subplots(figsize=(8, 6))

bottom = np.zeros(2)
bars = []
colors = plt.cm.tab20.colors  # 20 verschiedene Farben

for i, label in enumerate(labels):
    values = [costs_2025[i], costs_2050[i]]
    bar = ax.bar(x, values, width, bottom=bottom, color=colors[i])
    bars.append(bar)
    bottom += values

ax.set_xticks(x)
ax.set_xticklabels(['2025', '2050'])
ax.set_ylabel(r'Cost $\mathrm{[€/MWh_{H_2}]}$')
ax.legend([b[0] for b in bars], labels, bbox_to_anchor=(1.05, 1), loc='upper left')
fig.tight_layout()
plt.savefig("../results/figures/cost/bar_cost_components_morocco.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/cost/bar_cost_components_morocco.png", format="png", dpi = 300, bbox_inches='tight', pad_inches=0)
plt.show()

# Results export (csv)
df_res = pd.concat([df_res_2025['H2_Price_2025 [EUR/MWh_h2]'], df_res_2050['H2_Price_2050 [EUR/MWh_h2]']], axis=1)
df_res.to_csv('../results/cost/results_cost_morocco_2025_2050.csv', index=False)