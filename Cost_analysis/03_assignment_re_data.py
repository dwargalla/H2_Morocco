"""Schritt 3 der Kostenanalyse: Standortkoordinaten an die PyPSA-Ergebnisse anhängen.

Verknüpft die Zeilen von ``FLH_electrolyzer_{2025,2050}.csv`` positionell mit den
Koordinaten (Zeilen 0–49: PV-Punkte, 50–99: Wind-Punkte) und speichert sie als
Punkt-Shapefile (EPSG:4326).

Eingaben:
    data/interim/re_profiles/FLH_electrolyzer_{2025,2050}.csv   aus 02_FLH_el.py
    data/raw/renewables/PV_WIND_50_Punkte.xlsx    Blätter PV_Punkte und Wind_Punkte

Ausgaben:
    data/interim/re_profiles/data_re_flh_electrolyzer_{2025,2050}.shp   (Shapefile kürzt Spaltennamen auf 10 Zeichen,
                                         z. B. FLH_electr)

Hinweise:
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python 03_assignment_re_data.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df_coordinates_pv = pd.read_excel('../data/raw/renewables/PV_WIND_50_Punkte.xlsx', sheet_name='PV_Punkte')
df_coordinates_wind = pd.read_excel('../data/raw/renewables/PV_WIND_50_Punkte.xlsx', sheet_name='Wind_Punkte')
df_coordinates = pd.concat([df_coordinates_pv, df_coordinates_wind], ignore_index=True)
geometry = [Point(xy) for xy in zip(df_coordinates['Longitude'], df_coordinates['Latitude'])]

for year in [2025, 2050]:
    df_re_data = pd.read_csv(f'../data/interim/re_profiles/FLH_electrolyzer_{year}.csv')
    gdf_re_data = gpd.GeoDataFrame(df_re_data, geometry=geometry, crs="EPSG:4326")
    gdf_re_data = gdf_re_data.drop(columns= ['Unnamed: 0'])
    gdf_re_data.to_file(f'../data/interim/re_profiles/data_re_flh_electrolyzer_{year}.shp', driver='ESRI Shapefile')
