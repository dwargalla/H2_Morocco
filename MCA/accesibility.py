"""MCA-Kriterium Erreichbarkeit: Länge von Straßen und Schienen je Klasse und Zelle.

Fasst OSM-Straßen und -Schienen zusammen, filtert 12 Klassen (motorway …
unclassified, railway) und summiert je Zelle die Länge [m] jeder Klasse
innerhalb der Zelle. Die Gewichtung der Klassen erfolgt erst in
``mca_maps.py`` (``dict_weights_roads``); ``weights_roads`` hier wird nicht
verwendet.

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/Landuse/gis_osm_roads_free_1.shp      (Spalte fclass)
    Data/Landuse/gis_osm_railways_free_1.shp

Ausgaben:
    results/results_accessibility.csv   12 Spalten (eine je Klasse), zeilengleich mit dem Raster

Hinweise:
    - Schleife über alle Zellen ohne räumlichen Index, läuft lange.
    - Ausführen aus ``MCA/``: ``python accesibility.py``
"""

import geopandas as gpd
import pandas as pd

from custom import list_index

# Data
    # Current potential, from previous MCA
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')

    # Accessibility
    # Source: OSM, downloaded via QGIS
gdf_railways_utm29n = gpd.read_file('Data/Landuse/gis_osm_railways_free_1.shp').to_crs("EPSG:32629")
gdf_railways_utm29n['fclass'] = 'railway'
gdf_roads_utm29n = gpd.read_file('Data/Landuse/gis_osm_roads_free_1.shp').to_crs("EPSG:32629")

gdf_roads_railsways = gpd.GeoDataFrame(pd.concat([gdf_roads_utm29n, gdf_railways_utm29n], ignore_index=True), crs=gdf_roads_utm29n.crs)

classes = ['motorway', 'trunk', 'primary', 'secondary', 
           'tertiary', 'track', 'track_grade1', 'track_grade2', 
           'track_grade3', 'track_grade4', 'unclassified', 'railway']
gdf_roads_railsways = gdf_roads_railsways[gdf_roads_railsways['fclass'].isin(classes)]

weights_roads = {'motorway': 0.25,
                  'trunk': 0.18,
                  'primary':0.12, 
                  'secondary':0.09, 
                  'tertiary':0.06, 
                  'track':0.01, 
                  'track_grade1':0.03, 
                  'track_grade2':0.02, 
                  'track_grade3':0.01, 
                  'track_grade4':0.01, 
                  'unclassified':0.04, 
                  'railway':0.18}

df_accessibility = pd.DataFrame(columns = classes)
for i in range(len(gdf_grid)):
    cell, list_index_intersection = list_index(gdf_roads_railsways, i, gdf_grid)
    roads_class = gdf_roads_railsways.loc[list_index_intersection]['fclass']
    road_length = gdf_roads_railsways.loc[list_index_intersection].intersection(cell).length

    df = pd.DataFrame({'class': roads_class, 'length': road_length})

    for y in classes:
        a = df[df['class'] == y]['length'].sum()
        df_accessibility.loc[i, y] = a

df_accessibility.to_csv('../data/interim/mca_criteria/results_accessibility.csv', index=False)