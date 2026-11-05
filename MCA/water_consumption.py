"""Heutiger und künftiger Wasserverbrauch je Zelle (2025, 2050) in Mrd. m³/a.

Verteilt den nationalen Wasserverbrauch (15,9 bzw. 24,223 Mrd. m³/a) nach
Sektoranteilen auf Flächen:
    - Landwirtschaft (87 % / 75 %): nach tatsächlich bewässerter Fläche je Zelle
      (FAO GMIA v5, aus ki_generiert/irrigation_grid.py), in beiden Jahren dieselbe Verteilung
    - Städte (10,4 % / 22,3 %): GlobCover-Klasse 190
    - Industrie (2,6 % / 2,7 %): OSM-Klasse industrial (in beiden Jahren der heutige Stand)
und summiert je Zelle die drei Anteile.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/osm/gis_osm_landuse_a_free_1.shp
    data/raw/globcover/mar_gc_adg/mar_gc_adg.shp, data/raw/globcover/wsa_gc_adg/wsa_gc_adg.shp
    data/interim/landuse/morocco_landuse_2050.shp   aus forecast_landuse.py
    data/interim/water/irrigated_area_gmia.csv      aus ki_generiert/irrigation_grid.py

Ausgaben:
    data/interim/water/Water_Consumption_2025.csv   Indexspalte + ``Water_Consumption[BCM]``
    data/interim/water/Water_Consumption_2050.csv

Hinweise:
    - Agrarwasser nur auf Bewässerungsflächen: Regenfeldbau verbraucht kein Wasser aus
      Flüssen oder Grundwasser (Korrekturplan F-21). Bis 05.11.2026 wurden GlobCover-Klassen
      gewichtet (11–13 voll, 20–21 zu 70 %, 30–32 zu 30 %); die Klasse „bewässert“ (11–13)
      ist in Marokko aber leer, das Wasser landete auf Mosaikflächen (Fehlerprotokoll Nr. 31).
    - 2050: GMIA hat keine Zukunftswerte. Die Bewässerungsflächen bleiben wie 2025; dass
      Städte auf Bewässerungsflächen wachsen, ist vernachlässigt (kleine Fläche).
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

    # Irrigated area per cell [ha] (FAO GMIA v5, from ki_generiert/irrigation_grid.py), used for 2025 and 2050
irrigated_area = pd.read_csv('../data/interim/water/irrigated_area_gmia.csv')['irrigated_area[ha]']
irrigated_share = irrigated_area / irrigated_area.sum()     # share of each cell in the national irrigated area

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

    gdf_landuse_industrial  = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['industrial'])]

    gdf_landuse_urban['Water_Consumption[BCM]']      = (gdf_landuse_urban.area/gdf_landuse_urban.area.sum()) * urban * water_consumption

    gdf_landuse_industrial['Water_Consumption[BCM]'] = (gdf_landuse_industrial.area/gdf_landuse_industrial.area.sum()) * indust * water_consumption

    for i in range(len(gdf_grid_morocco)):
        # Urban
        cell, list_index_intersection_urban = list_index(gdf_landuse_urban, i, gdf_grid_morocco)
        area_urban = gdf_landuse_urban.loc[list_index_intersection_urban].intersection(cell).area.sum()
        water_consumption_urban = (area_urban/gdf_landuse_urban.area.sum()) * urban * water_consumption

        # Agriculture: share of the irrigated area in this cell
        water_consumption_agri = irrigated_share[i] * agri * water_consumption

        # Industrial
        cell, list_index_intersection_industrial = list_index(gdf_landuse_industrial, i, gdf_grid_morocco)
        area_industrial = gdf_landuse_industrial.loc[list_index_intersection_industrial].intersection(cell).area.sum()
        water_consumption_industrial = (area_industrial/gdf_landuse_industrial.area.sum()) * indust * water_consumption

        sum_water_consumption = water_consumption_urban + water_consumption_agri + water_consumption_industrial

        gdf_grid_morocco.at[i, 'Water_Consumption[BCM]'] = sum_water_consumption

    # Save the results to a CSV file
    gdf_grid_morocco['Water_Consumption[BCM]'].to_csv(f'../data/interim/water/Water_Consumption{suffix}.csv')