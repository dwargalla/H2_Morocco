"""Karten des PV- und Windpotenzials je Rasterzelle.

Nur Abbildung, kein Einfluss auf die Ergebnisse.

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/morocco_Morocco_Country_Boundary.shp
    results/results_pv_yeald.csv   aus pv_analysis.py
    results/results_wind_flh.csv   aus wind_analysis.py

Ausgaben:
    Maps/morocco_photovoltaic_potential.png
    Maps/morocco_wind_potential.png

Hinweise:
    - Ausführen aus ``MCA/``: ``python re_potential_map.py``
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd

# Data
gdf_morocco_boundary    = gpd.read_file('Data/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
df_pv = pd.read_csv('results/results_pv_yeald.csv')
gdf_grid = gpd.read_file('Grid_morocco/grid_morocco_clear.shp')
gdf_grid['PV'] = df_pv['pv_yeald']

df_wind = pd.read_csv('results/results_wind_flh.csv')
gdf_grid['Wind'] = df_wind['FLH_wind']

# Map PV
fig, ax = plt.subplots(figsize=(15, 10))
gdf_grid.plot(ax = ax, column='PV', cmap='turbo', legend=True, vmin=1000, legend_kwds={"label": "kWh/kWp", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=cx.providers.CartoDB.Positron)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("Maps/morocco_photovoltaic_potential.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()

# Map Wind
fig, ax = plt.subplots(figsize=(15, 10))
gdf_grid.plot(ax = ax, column='Wind', cmap='turbo', legend=True, legend_kwds={"label": "Hours [h]", "orientation": "vertical"})
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=cx.providers.CartoDB.Positron)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("Maps/morocco_wind_potential.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()