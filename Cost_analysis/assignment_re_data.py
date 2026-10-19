"""Schritt 3 der Kostenanalyse: Standortkoordinaten an die PyPSA-Ergebnisse anhängen.

Verknüpft die Zeilen von ``FLH_electrolyzer.csv`` positionell mit den
Koordinaten (Zeilen 0–49: PV-Punkte, 50–99: Wind-Punkte) und speichert sie als
Punkt-Shapefile (EPSG:4326).

Eingaben:
    Data/FLH_electrolyzer.csv      aus FLH_el.py
    Data/PV_WIND_50_Punkte.xlsx    Blätter PV_Punkte und Wind_Punkte

Ausgaben:
    Data/data_re_flh_electrolyzer.shp   (Shapefile kürzt Spaltennamen auf 10 Zeichen,
                                         z. B. FLH_electr)

Hinweise:
    - Ausführen aus ``Cost_analysis/``: ``python assignment_re_data.py``
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df_re_data = pd.read_csv('../data/interim/re_profiles/FLH_electrolyzer.csv')

df_coordinates_pv = pd.read_excel('Data/PV_WIND_50_Punkte.xlsx', sheet_name='PV_Punkte')
df_coordinates_wind = pd.read_excel('Data/PV_WIND_50_Punkte.xlsx', sheet_name='Wind_Punkte')

df_coordinates = pd.concat([df_coordinates_pv, df_coordinates_wind], ignore_index=True)

geometry = [Point(xy) for xy in zip(df_coordinates['Longitude'], df_coordinates['Latitude'])]

gdf_re_data = gpd.GeoDataFrame(df_re_data, geometry=geometry, crs="EPSG:4326")
gdf_re_data = gdf_re_data.drop(columns= ['Unnamed: 0'])

gdf_re_data.to_file('../data/interim/re_profiles/data_re_flh_electrolyzer.shp', driver='ESRI Shapefile')