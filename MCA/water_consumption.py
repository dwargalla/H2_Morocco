"""Heutiger und künftiger Wasserverbrauch je Zelle (2025, 2050) in Mrd. m³/a.

Verteilt den nationalen Wasserverbrauch (15,9 bzw. 24,223 Mrd. m³/a) nach
Sektoranteilen auf Flächen:
    - Landwirtschaft (87 % / 75 %): GlobCover-Klassen 11–13 voll, 20–21 zu 70 %,
      30–32 zu 30 % gewichtet
    - Städte (10,4 % / 22,3 %): GlobCover-Klasse 190
    - Industrie (2,6 % / 2,7 %): OSM-Klasse industrial (in beiden Jahren der heutige Stand)
und summiert je Zelle die Anteile der darin liegenden Flächen.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/osm/gis_osm_landuse_a_free_1.shp
    data/raw/globcover/mar_gc_adg/mar_gc_adg.shp, data/raw/globcover/wsa_gc_adg/wsa_gc_adg.shp
    data/interim/landuse/morocco_landuse_2050.shp   aus forecast_landuse.py

Ausgaben:
    data/interim/water/Water_Consumption_2025.csv   Indexspalte + ``Water_Consumption[BCM]``
    data/interim/water/Water_Consumption_2050.csv

Hinweise:
    - Regenfeldbau wird nicht vom Agrarwasser ausgenommen (Korrekturplan F-21).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python water_consumption.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import pandas as pd

from custom import list_index

gdf_grid_morocco        = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
    # Industrial landuse
    # Source: OSM, via QGIS
gdf_landuse_utm29n      = gpd.read_file('../data/raw/osm/gis_osm_landuse_a_free_1.shp').to_crs("EPSG:32629")

    # Landuse
    # Source: FAO, via: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5  --> Morocco
    # Source: FAO, via: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2      --> Western Sahara

gdf_landuse_mar         = gpd.read_file('../data/raw/globcover/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('../data/raw/globcover/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa])) #Landuse today

    # Same source, but for future landuse (from forecast_landuse.py)
gdf_landuse_concat_2050      = gpd.read_file('../data/interim/landuse/morocco_landuse_2050.shp')    #Landuse 2050

# List for itteration
list_gdf_landuse = [gdf_landuse_concat, gdf_landuse_concat_2050]

    # Source: Economic concepts to address future water supply–demand imbalances in Iran, Morocco and Saudi Arabia
    # Share of water demand by sector (agriculture, urban, industrial) for Morocco in 2025 and 2050
list_demand_agri = [0.87, 0.75]  #Today, 2050
list_demand_urban = [0.104, 0.223] #Today, 2050
list_demand_indust = [0.026, 0.027] #Today, 2050

list_water_consumption = [15.9, 24.223] #BCM/a Today, 2050

list_suffix = ['_2025', '_2050']



for gdf_landuse, agri, urban, indust, water_consumption, suffix in zip(list_gdf_landuse, list_demand_agri, list_demand_urban, list_demand_indust, list_water_consumption, list_suffix):
    gdf_landuse_urban       = gdf_landuse[gdf_landuse['GRIDCODE'].isin([190])]

    gdf_landuse_agri_100    = gdf_landuse[gdf_landuse['GRIDCODE'].isin([11, 12, 13])]
    gdf_landuse_agri_70     = gdf_landuse[gdf_landuse['GRIDCODE'].isin([20,21])]
    gdf_landuse_agri_30     = gdf_landuse[gdf_landuse['GRIDCODE'].isin([30, 31, 32])]

    gdf_landuse_industrial  = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['industrial'])]

    area_sum_agri = gdf_landuse_agri_100.area.sum() + gdf_landuse_agri_70.area.sum() * 0.7 + gdf_landuse_agri_30.area.sum() *0.3

    gdf_landuse_urban['Water_Consumption[BCM]']      = (gdf_landuse_urban.area/gdf_landuse_urban.area.sum()) * urban * water_consumption

    gdf_landuse_agri_100['Water_Consumption[BCM]']   = (gdf_landuse_agri_100.area/area_sum_agri) * agri * water_consumption
    gdf_landuse_agri_70['Water_Consumption[BCM]']    = (gdf_landuse_agri_70.area/area_sum_agri) * agri * water_consumption * 0.7
    gdf_landuse_agri_30['Water_Consumption[BCM]']    = (gdf_landuse_agri_30.area/area_sum_agri) * agri * water_consumption * 0.3

    gdf_landuse_industrial['Water_Consumption[BCM]'] = (gdf_landuse_industrial.area/gdf_landuse_industrial.area.sum()) * indust * water_consumption

    for i in range(len(gdf_grid_morocco)):
        # Urban
        cell, list_index_intersection_urban = list_index(gdf_landuse_urban, i, gdf_grid_morocco)
        area_urban = gdf_landuse_urban.loc[list_index_intersection_urban].intersection(cell).area.sum()
        water_consumption_urban = (area_urban/gdf_landuse_urban.area.sum()) * urban * water_consumption

        # Agriculture
        cell, list_index_intersection_agri_100 = list_index(gdf_landuse_agri_100, i, gdf_grid_morocco)
        area_agri_100 = gdf_landuse_agri_100.loc[list_index_intersection_agri_100].intersection(cell).area.sum()
        water_consumption_agri_100 = (area_agri_100/area_sum_agri) * agri * water_consumption

        cell, list_index_intersection_agri_70 = list_index(gdf_landuse_agri_70, i, gdf_grid_morocco)
        area_agri_70 = gdf_landuse_agri_70.loc[list_index_intersection_agri_70].intersection(cell).area.sum()
        water_consumption_agri_70 = (area_agri_70/area_sum_agri) * agri * water_consumption * 0.7

        cell, list_index_intersection_agri_30 = list_index(gdf_landuse_agri_30, i, gdf_grid_morocco)
        area_agri_30 = gdf_landuse_agri_30.loc[list_index_intersection_agri_30].intersection(cell).area.sum()
        water_consumption_agri_30 = (area_agri_30/area_sum_agri) * agri * water_consumption * 0.3

        # Industrial
        cell, list_index_intersection_industrial = list_index(gdf_landuse_industrial, i, gdf_grid_morocco)
        area_industrial = gdf_landuse_industrial.loc[list_index_intersection_industrial].intersection(cell).area.sum()
        water_consumption_industrial = (area_industrial/gdf_landuse_industrial.area.sum()) * indust * water_consumption

        sum_water_consumption = water_consumption_urban + water_consumption_agri_100 + water_consumption_agri_70 + water_consumption_agri_30 + water_consumption_industrial

        gdf_grid_morocco.at[i, 'Water_Consumption[BCM]'] = sum_water_consumption

    # Save the results to a CSV file
    gdf_grid_morocco['Water_Consumption[BCM]'].to_csv(f'../data/interim/water/Water_Consumption{suffix}.csv')