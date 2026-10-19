"""MCA-Kriterium Stadtfläche: Anteil Siedlungsfläche je Zelle für 2025 und 2050.

Wählt die GlobCover-Klasse 190 (Siedlungsfläche) und berechnet je Zelle den
Flächenanteil (0–1) für die heutige und die fortgeschriebene Landnutzung. In
``mca_maps.py`` invertiert skaliert (hoher Anteil = schlechter Score).

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/mar_gc_adg/mar_gc_adg.shp   GlobCover Marokko
    Data/wsa_gc_adg/wsa_gc_adg.shp   GlobCover Westsahara
    Data/morocco_landuse_2050.shp    aus forecast_landuse.py

Ausgaben:
    results/results_urban.csv        2025
    results/results_urban_2050.csv   2050

Hinweise:
    - Ausführen aus ``MCA/``: ``python urban_zone.py``
"""

import pandas as pd
import geopandas as gpd
import numpy as np

from custom import list_index

# Data
    # Grid morocco
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
    # Urban landuse
    # Source: FAO, via: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5  --> Morocco
    # Source: FAO, via: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2      --> Western Sahara

gdf_landuse_mar         = gpd.read_file('Data/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('Data/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa]))   #Today

    # Same source, but for future landuse (from forecast_landuse.py)
gdf_landuse_concat_2050      = gpd.read_file('../data/interim/landuse/morocco_landuse_2050.shp')    #Landuse 2050

gdf_landuse_urban       = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([190])]
gdf_landuse_urban_2050  = gdf_landuse_concat_2050[gdf_landuse_concat_2050['GRIDCODE'].isin([190])]

list_urban = []
list_urban_2050 = []
for i in range(len(gdf_grid)):
    cell, list_index_intersection = list_index(gdf_landuse_urban, i, gdf_grid)
    area = gdf_landuse_urban.loc[list_index_intersection].intersection(cell).area.sum()

    cell_2050, list_index_intersection_2050 = list_index(gdf_landuse_urban_2050, i, gdf_grid)
    area_2050 = gdf_landuse_urban_2050.loc[list_index_intersection_2050].intersection(cell_2050).area.sum()
    
    
    list_urban.append(area/cell.area)
    list_urban_2050.append(area_2050/cell_2050.area)

df_urban = pd.DataFrame(data = list_urban)
df_urban_2050 = pd.DataFrame(data = list_urban_2050)

# # 2025
df_urban.to_csv('../data/interim/mca_criteria/results_urban.csv', index=False)

# 2050
df_urban_2050.to_csv('../data/interim/mca_criteria/results_urban_2050.csv', index=False)