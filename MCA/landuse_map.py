"""Karte der Landnutzung: Landwirtschaft, ländliche Flächen, Städte (GlobCover) und Industrie (OSM).

Nur Abbildung, kein Einfluss auf die Ergebnisse.

Eingaben:
    Data/morocco_Morocco_Country_Boundary.shp
    Data/Landuse/mar_gc_adg/mar_gc_adg.shp, Data/Landuse/wsa_gc_adg/wsa_gc_adg.shp
    Data/Landuse/gis_osm_landuse_a_free_1.shp

Ausgaben:
    Maps/morocco_landuse.png

Hinweise:
    - Ausführen aus ``MCA/``: ``python landuse_map.py``
"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import matplotlib.patches as mpatches

gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
# Data
gdf_landuse_mar         = gpd.read_file('../data/raw/globcover/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('../data/raw/globcover/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa]))

gdf_landuse_agri        = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([11, 12, 13, 14, 15, 16, 20, 21, 30, 31, 32])]
gdf_landuse_rural       = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([200, 201, 202, 203, 220, 230, 
                                                                                  40, 41,42,50,60,70,90,91,92,
                                                                                  100,101,110,120,130,131,134,
                                                                                  140,141,150,151,152,160,161,
                                                                                  162,170,180,181,185])]
gdf_landuse_urban       = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([190])]

gdf_landuse_utm29n = gpd.read_file('../data/raw/osm/gis_osm_landuse_a_free_1.shp').to_crs("EPSG:32629")

gdf_industrie_morocco = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['industrial'])]


# Map Landuse

fig, ax = plt.subplots(figsize=(15, 10))
gdf_landuse_agri.plot(ax = ax, color='lightgreen', label='Agricultural land', alpha=0.9)
gdf_landuse_rural.plot(ax = ax, color='sandybrown', label='Rural land', alpha = 0.9)
gdf_landuse_urban.plot(ax = ax, color='b', label='Urban land')
gdf_industrie_morocco.plot(ax = ax, color='red', label='Industrial area', markersize=100)
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=cx.providers.CartoDB.Positron)
plt.axis('off')
legend_handles = [
    mpatches.Patch(color='lightgreen', label='Agricultural land'),
    mpatches.Patch(color='sandybrown', label='Rural land'),
    mpatches.Patch(color='b', label='Urban land'), 
    mpatches.Patch(color='red', label='Industrial area')]
plt.legend(handles=legend_handles, loc='lower right', fontsize=12)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_landuse.png", format="png", bbox_inches='tight', pad_inches=0)
plt.show()