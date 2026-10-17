"""MCA-Kriterium ländliche Fläche: Anteil Wald/Busch/Grasland/Brache je Zelle für 2025 und 2050.

Wählt die GlobCover-Klassen 40–185 und 200–230 und berechnet je Zelle den
Flächenanteil (0–1) für die heutige und die fortgeschriebene Landnutzung.

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/mar_gc_adg/mar_gc_adg.shp   GlobCover Marokko
    Data/wsa_gc_adg/wsa_gc_adg.shp   GlobCover Westsahara
    Data/morocco_landuse_2050.shp    aus forecast_landuse.py

Ausgaben:
    results/results_rural.csv        2025
    results/results_rural_2050.csv   2050

Hinweise:
    - Die Klassenliste enthält auch 230 (No Data), was als positive Fläche zählt
      (Korrekturplan F-20).
    - Ausführen aus ``MCA/``: ``python rural_zone.py``
"""

import pandas as pd
import geopandas as gpd
import numpy as np

from custom import list_index

# Data
    # Grid morocco
gdf_grid = gpd.read_file('Grid_morocco/grid_morocco_clear.shp')
    # Rural zone
    # Source: FAO, via: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5  --> Morocco
    # Source: FAO, via: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2      --> Western Sahara

gdf_landuse_mar         = gpd.read_file('Data/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('Data/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa]))       #Today

    # Same source, but for future landuse (from forecast_landuse.py)
gdf_landuse_concat_2050      = gpd.read_file('Data/morocco_landuse_2050.shp')    #Landuse 2050

gdf_landuse_rural       = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([200, 201, 202, 203, 220, 230, 
                                                                                  40, 41,42,50,60,70,90,91,92,
                                                                                  100,101,110,120,130,131,134,
                                                                                  140,141,150,151,152,160,161,
                                                                                  162,170,180,181,185])]

gdf_landuse_rural_2050       = gdf_landuse_concat_2050[gdf_landuse_concat_2050['GRIDCODE'].isin([200, 201, 202, 203, 220, 230, 
                                                                                  40, 41,42,50,60,70,90,91,92,
                                                                                  100,101,110,120,130,131,134,
                                                                                  140,141,150,151,152,160,161,
                                                                                  162,170,180,181,185])]

list_rural = []
list_rural_2050 = []
for i in range(len(gdf_grid)):
    cell, list_index_intersection = list_index(gdf_landuse_rural, i, gdf_grid)
    cell_2050, list_index_intersection_2050 = list_index(gdf_landuse_rural_2050, i, gdf_grid)

    area = gdf_landuse_rural.loc[list_index_intersection].intersection(cell).area.sum()
    area_2050 = gdf_landuse_rural_2050.loc[list_index_intersection_2050].intersection(cell_2050).area.sum()
    list_rural.append(area/cell.area)
    list_rural_2050.append(area_2050/cell_2050.area)

df_rural = pd.DataFrame(data = list_rural)
df_rural_2050 = pd.DataFrame(data = list_rural_2050)

# # 2025
df_rural.to_csv('results/results_rural.csv', index=False)

# 2050
df_rural_2050.to_csv('results/results_rural_2050.csv', index=False)