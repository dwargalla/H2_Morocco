"""No-Go-Maske der MCA (1 = zulässig, 0 = ausgeschlossen).

Eine Zelle wird ausgeschlossen, wenn mindestens 50 % ihrer Fläche von
OSM-Flächen der Klassen ``military``, ``nature_reserve`` oder
``recreation_ground`` bedeckt sind, oder wenn sie laut Topografie-Layer
ausgeschlossen ist (``NoGo`` = 0). Beide Masken werden per Minimum kombiniert.

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/Landuse/gis_osm_landuse_a_free_1.shp   (Spalte fclass)
    Data/ToPo_1500.shp                          (Spalte NoGo, 0/1; in QGIS auf das
                                                 Raster aggregiert, muss zeilengleich
                                                 mit dem Raster sein)

Ausgaben:
    results/results_nogo_zones.csv   eine Spalte ``NoGo``, zeilengleich mit dem Raster

Hinweise:
    - In ``mca_maps.py`` wird der gewichtete Score mit dieser Maske multipliziert.
      Die Kostenanalyse verwendet die Maske nicht (Korrekturplan F-25).
    - Ausführen aus ``MCA/``: ``python no_go_zones.py``
"""

import geopandas as gpd
import numpy as np
import pandas as pd

from custom import list_index

# Data
    # Current potential
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')

    # No-Go Zones
    # Source: OSM, via QGIS
gdf_landuse_utm29n = gpd.read_file('../data/raw/osm/gis_osm_landuse_a_free_1.shp').to_crs("EPSG:32629")

    # NO-GO Zones: Military, Nature Reserve, Recreation Ground
gdf_nogo_zones = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['military', 'nature_reserve', 'recreation_ground'])]
gdf_nogo_zones.reset_index(drop=True, inplace=True)
gdf_nogo_zones.index = range(len(gdf_nogo_zones))

    # No-Go Zones: Topography
    # Source: QGIS, via grid-statistics, origin source for topography: Soufiane fragen
gdf_topo_utm29n = gpd.read_file('../data/interim/qgis/ToPo_1500.shp').to_crs("EPSG:32629")   #Already 1 or 0, done in QGIS with grid-statistics

list_nogo = []
for i in range(len(gdf_grid)):
    cell, list_index_intersection = list_index(gdf_nogo_zones, i, gdf_grid)

    if len(list_index_intersection) == 0:
        a = 1
    else:
        intersected_area = gdf_nogo_zones.iloc[list_index_intersection].intersection(cell).area.sum()
        if intersected_area/cell.area >= 0.5:
            a = 0
        else:
            a = 1

    list_nogo.append(a)

array_nogo = np.array(list_nogo)
array_nogo = np.minimum(array_nogo, gdf_topo_utm29n['NoGo'])

df_nogo_zones = pd.DataFrame(data = array_nogo)

df_nogo_zones.to_csv('../data/interim/mca_criteria/results_nogo_zones.csv', index=False)