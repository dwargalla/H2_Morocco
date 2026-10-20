"""Karten zum Wasser: Grundwasser-Aquifere, Oberflächenwasser, Fließakkumulation, Einzugsgebiete, klimatische Wasserbilanz.

Nur Abbildung, kein Einfluss auf die Ergebnisse.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp
    data/raw/groundwater/Morocco_HG.shp, data/raw/groundwater/WesternSahara_HG.shp
    data/interim/water/water_availability_sw.csv   aus water_exploitable_sw.py
    data/interim/qgis/flow_direction_grid.shp
    data/raw/hydrology/watershead_morocco.shp
    data/interim/water/cwb.shp                     aus water_forecast.py (optional, sonst keine CWB-Karte)

Ausgaben:
    results/figures/mca/morocco_{groundwater,surfacewater,flow_direction,watersheds,cwb}.png

Hinweise:
    - Ausführen aus ``MCA/``: ``python water_maps.py``
"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import os
from dotenv import load_dotenv

# Hintergrundkarte: CARTO-Kacheln brauchen einen API-Key (CARTO_API_KEY in H2_Morocco/.env)
load_dotenv('../.env')
if not os.getenv('CARTO_API_KEY'):
    raise SystemExit('CARTO_API_KEY fehlt: .env.example nach .env kopieren und Key eintragen.')
basemap = cx.providers.CartoDB.Positron(apikey=os.getenv('CARTO_API_KEY'))

gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
# Data
gdf_groundwater_morocco_utm29n = gpd.read_file('../data/raw/groundwater/Morocco_HG.shp').to_crs("EPSG:32629")
gdf_groundwater_western_sahara_utm29n = gpd.read_file('../data/raw/groundwater/WesternSahara_HG.shp').to_crs("EPSG:32629")
gdf_groundwater_morocco_concat = pd.concat([gdf_groundwater_morocco_utm29n, gdf_groundwater_western_sahara_utm29n.rename(columns = 
                                                                                     {'WSGLG': 'MorGLG', 'WSHGComb': 'MorHGComb'})], 
                                           ignore_index=True)
gdf_groundwater = gdf_groundwater_morocco_concat[gdf_groundwater_morocco_concat['MorHGComb'].isin(['CSIF-M/H', 'CSFK-H/VH', 'U-L/H'])]

gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
df_sw = pd.read_csv('../data/interim/water/water_availability_sw.csv')
gdf_grid['Surface Water'] = df_sw['water_availability_sw[MCM]']

gdf_water_direction = gpd.read_file('../data/interim/qgis/flow_direction_grid.shp')

gdf_watershead_morocco = gpd.read_file('../data/raw/hydrology/watershead_morocco.shp')

# Map Ground Water
fig, ax = plt.subplots(figsize=(15, 10))
gdf_groundwater.plot(ax = ax, color='steelblue',alpha = 0.6, label='Groundwater potential')
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
legend_handles = [
    mpatches.Patch(color='steelblue', label='Aquifer productivity \nbetween moderate and very high'),
]
plt.legend(handles=legend_handles, loc='lower right', fontsize=12)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_groundwater.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()

# Map Surface Water
cmap = plt.get_cmap('Blues')
# Nur die untere Hälfte (0 bis 0.5) verwenden
new_cmap = LinearSegmentedColormap.from_list(
    'Blues_half', 
    cmap(np.linspace(0.25, 1, cmap.N))
)
fig, ax = plt.subplots(figsize=(15, 10))
gdf_grid.plot(ax = ax, column='Surface Water', cmap = new_cmap, label='Surface Water potential',legend = True, legend_kwds={"label": "Surface Water Availability [MCM]", "orientation": "vertical"})
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_surfacewater.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()

# Map flow direction
fig, ax = plt.subplots(figsize=(15, 10))
gdf_water_direction.plot(ax = ax, column='_sum', cmap = 'Blues', legend=True, legend_kwds={"label": "Number of cells flowing into one cell", "orientation": "vertical"})
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_flow_direction.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()

# Map Watersheds
fig, ax = plt.subplots(figsize=(15, 10))
gdf_watershead_morocco.plot(ax = ax, column='name',alpha=0.5,edgecolor='black', cmap = 'Paired', legend=True, legend_kwds={'loc': 'lower right'})
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=14)
cbar_ax.yaxis.label.set_size(20)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_watersheds.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()

# Map CWB (nicht im Paper; cwb.shp entsteht erst mit den Klimadaten 2050 in water_forecast.py)
if os.path.exists('../data/interim/water/cwb.shp'):
    gdf_cwb = gpd.read_file('../data/interim/water/cwb.shp')
    fig, ax = plt.subplots(figsize=(15, 10))
    gdf_cwb.plot(ax = ax, column='CWB',alpha=0.9, cmap = 'Blues', legend=True, legend_kwds={"label": "Climate Water Balance [MCM]", "orientation": "vertical"})
    gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
    cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
    plt.axis('off')
    cbar_ax = fig.axes[-1]
    cbar_ax.tick_params(labelsize=14)
    cbar_ax.yaxis.label.set_size(20)
    plt.tight_layout()
    plt.savefig("../results/figures/mca/morocco_cwb.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
    plt.show()
else:
    print('cwb.shp fehlt (Klimadaten 2050), CWB-Karte übersprungen.')