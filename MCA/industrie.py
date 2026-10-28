"""MCA-Kriterium Industriefläche: Anteil OSM-Industriefläche an jeder Zelle.

Vereinigt alle OSM-Landnutzungspolygone der Klasse ``industrial`` und berechnet
je Zelle den Flächenanteil (0–1).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/osm/gis_osm_landuse_a_free_1.shp   (Spalte fclass)

Ausgaben:
    data/interim/mca_criteria/results_industrie.csv   eine Spalte, zeilengleich mit dem Raster

Hinweise:
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python industrie.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd

# Data
    # Current potential
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
    # Industrial
    # Source: OSM, via QGIS
gdf_landuse_utm29n = gpd.read_file('../data/raw/osm/gis_osm_landuse_a_free_1.shp').to_crs("EPSG:32629")

gdf_industrie_morocco = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['industrial'])].union_all()

ds_intersection_industrie = (gdf_grid.intersection(gdf_industrie_morocco).area/
                              gdf_grid.area)

ds_intersection_industrie.to_csv('../data/interim/mca_criteria/results_industrie.csv', index=False)