"""Schreibt die Landnutzung (GlobCover) auf 2050 fort, indem Stadtflächen wachsen.

Für jede Verwaltungsregion werden die heutigen Stadtflächen (GlobCover-Klasse
190) um ihren Schwerpunkt skaliert, bis ihre Fläche dem regionalen Zielwert
``Fläche_heute × dict_urbanisation_rates[Region]`` entspricht (Toleranz 1 %),
und auf die Region zugeschnitten. Die übrigen Landnutzungsflächen werden um die
neuen Stadtflächen verkleinert.

Eingaben:
    Data/Landuse/mar_gc_adg/mar_gc_adg.shp   GlobCover Marokko (Spalte GRIDCODE)
    Data/Landuse/wsa_gc_adg/wsa_gc_adg.shp   GlobCover Westsahara
    Data/Landuse/Regions.shp                 Regionen (Spalte Nom_Region)
    Data/Landuse/morocco_Morocco_Country_Boundary.shp   (eingelesen, aber nicht verwendet)

Ausgaben:
    Data/morocco_landuse_2050.shp            Landnutzung 2050, genutzt von
                                             agriculture.py, urban_zone.py,
                                             rural_zone.py, water_consumption.py

Hinweise:
    - Die Faktoren 1,13–2,4 stammen laut Quelle aus jährlichen Raten, werden hier
      aber als Gesamtfaktor bis 2050 verwendet (Korrekturplan F-24).
    - Ausführen aus ``MCA/``: ``python forecast_landuse.py``
"""

import geopandas as gpd
import pandas as pd
import numpy as np

# Data
    # Source: FAO, via: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5  --> Morocco
    # Source: FAO, via: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2      --> Western Sahara
gdf_landuse_mar         = gpd.read_file('Data/Landuse/mar_gc_adg/mar_gc_adg.shp').to_crs("EPSG:32629") 
gdf_landuse_wsa         = gpd.read_file('Data/Landuse/wsa_gc_adg/wsa_gc_adg.shp').to_crs("EPSG:32629")
gdf_landuse_concat      = gpd.GeoDataFrame(pd.concat([gdf_landuse_mar, gdf_landuse_wsa]))

gdf_landuse_urban       = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'].isin([190])]

gdf_morocco_boundary    = gpd.read_file('Data/Landuse/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")

gdf_morocco_regions     = gpd.read_file('Data/Landuse/Regions.shp').to_crs("EPSG:32629")

# Urbanisation
# Urbanisationrates:
dict_urbanisation_rates = {'Béni Mellal-Khénifra': 1.79,
                           'Drâa-Tafilalet': 1.84,
                           'Eddakhla-Oued Eddahab': 2.4, 
                           'Fès-Meknès': 1.93,
                           'Grand Casablanca-Settat': 1.13,
                           'Guelmim-Oued Noun': 1.39,
                           'Laayoune-Sakia El Hamra': 1.55,
                           'Marrakech-Safi': 1.23,
                           'Oriental': 1.36,
                           'Rabat-Salé-Kénitra': 1.39,
                           'Souss-Massa': 1.27,
                           'Tanger-Tetouan-Al Hoceima': 1.44}
# Source: "Urban Sustainability Development in Morocco, a Review", via: https://www.mdpi.com/2413-8851/8/2/28

gdf_new_urban_areas = gpd.GeoDataFrame(columns=gdf_landuse_urban.columns, crs=gdf_landuse_urban.crs)

delta = 0.01    #1% difference between benchmark and real urbanisation
for region in gdf_morocco_regions['Nom_Region']:
    urbanisation = dict_urbanisation_rates[region]
    gdf_landuse_urban_region = gpd.clip(gdf_landuse_urban, gdf_morocco_regions[gdf_morocco_regions['Nom_Region'] == region])
    if gdf_landuse_urban_region.area.sum() == 0:
        continue
    goal = gdf_landuse_urban_region.area.sum() * urbanisation
    s = np.sqrt(urbanisation)  # Linear scaling

    # Scale of urbanareas
    gdf_urban = gdf_landuse_urban_region.copy()
    gdf_urban.geometry = gdf_urban.geometry.scale(
        xfact=s, 
        yfact=s, 
        origin='centroid')
    
    curent_urban_area = gpd.clip(gdf_urban, gdf_morocco_regions[gdf_morocco_regions['Nom_Region'] == region]) # Boundary of region

    while (goal - curent_urban_area.area.sum())/goal > delta:
        diff = (goal - curent_urban_area.area.sum())/goal
        s = np.sqrt(1 + diff)
        curent_urban_area.geometry = curent_urban_area.geometry.scale(xfact=s, yfact=s, origin='centroid')
        curent_urban_area = gpd.clip(curent_urban_area, gdf_morocco_regions[gdf_morocco_regions['Nom_Region'] == region])
        if (goal - curent_urban_area.area.sum())/goal < delta:
            break

    gdf_new_urban_areas = pd.concat([gdf_new_urban_areas, curent_urban_area])

gdf_new = gdf_landuse_concat[gdf_landuse_concat['GRIDCODE'] != 190].overlay(gdf_new_urban_areas, how = 'difference')

gdf_new_landuse = pd.concat([gdf_new, gdf_new_urban_areas])

gdf_new_landuse = gpd.GeoDataFrame(gdf_new_landuse, crs=gdf_landuse_concat.crs, geometry='geometry')

gdf_new_landuse['GRIDCODE'] = gdf_new_landuse['GRIDCODE'].astype(int)

gdf_new_landuse.to_file('Data/morocco_landuse_2050.shp', driver='ESRI Shapefile')