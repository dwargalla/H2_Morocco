"""MCA-Kriterium Landwirtschaft: Anteil Ackerfläche je Zelle für 2025 und 2050.

Wählt die GlobCover-Klassen 11–32 (Acker- und Mosaikflächen) und berechnet je
Zelle den Flächenanteil (0–1), einmal mit der heutigen und einmal mit der
fortgeschriebenen Landnutzung. In ``mca_maps.py`` invertiert skaliert
(hoher Anteil = schlechter Score).

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/Landuse/mar_gc_adg/mar_gc_adg.shp   GlobCover Marokko
    Data/Landuse/wsa_gc_adg/wsa_gc_adg.shp   GlobCover Westsahara
    Data/morocco_landuse_2050.shp            aus forecast_landuse.py

Ausgaben:
    results/results_agriculture.csv          2025
    results/results_agriculture_2050.csv     2050

Hinweise:
    - Liest GlobCover aus ``Data/Landuse/…``, während urban_zone.py und
      rural_zone.py ``Data/…`` verwenden; beide Kopien müssen vorhanden sein.
    - Ausführen aus ``MCA/``: ``python agriculture.py``
"""

import pandas as pd
import geopandas as gpd
import numpy as np

from custom import list_index

# Data
    # Grid morocco
gdf_grid = gpd.read_file('Grid_morocco/grid_morocco_clear.shp')

    # Agriculture
    # Source: FAO, via: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5  --> Morocco
    # Source: FAO, via: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2      --> Western Sahara

gdf_landuse_mar         = gpd.read_file('Data/Landuse/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('Data/Landuse/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa])) #Today

    # Same source, but for future landuse (from forecast_landuse.py)
gdf_landuse_concat_2050      = gpd.read_file('Data/morocco_landuse_2050.shp')    #Landuse 2050

gdf_landuse_agri        = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([11, 12, 13, 14, 15, 16, 20, 21, 30, 31, 32])]
gdf_landuse_agri_2050   = gdf_landuse_concat_2050[gdf_landuse_concat_2050['GRIDCODE'].isin([11, 12, 13, 14, 15, 16, 20, 21, 30, 31, 32])]

list_agriculture = []
list_agriculture_2050 = []
for i in range(len(gdf_grid)):
    cell, list_index_intersection = list_index(gdf_landuse_agri, i, gdf_grid)
    cell_2050, list_index_intersection_2050 = list_index(gdf_landuse_agri_2050, i, gdf_grid)
    area = gdf_landuse_agri.loc[list_index_intersection].intersection(cell).area.sum()
    area_2050 = gdf_landuse_agri_2050.loc[list_index_intersection_2050].intersection(cell_2050).area.sum()

    list_agriculture.append(area/cell.area)
    list_agriculture_2050.append(area_2050/cell_2050.area)

df_agriculture = pd.DataFrame(data = list_agriculture)
df_agriculture_2050 = pd.DataFrame(data = list_agriculture_2050)

# 2025
df_agriculture.to_csv('results/results_agriculture.csv', index=False)

# 2050
df_agriculture_2050.to_csv('results/results_agriculture_2050.csv', index=False)