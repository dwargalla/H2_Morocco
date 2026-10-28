"""MCA-Kriterium Nicht-Konfliktgebiet (soziopolitische Stabilität).

Berechnet für jeden Zellmittelpunkt den Abstand zur Westsahara
(``conflict_area.shp``) und zu Kernmarokko (``morocco.geojson``) und bildet das
Verhältnis Abstand_Konflikt / Abstand_Marokko. Zellen in Kernmarokko erhalten
100, Zellen in der Westsahara 0, alle übrigen werden rangskaliert (0–100).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/boundaries/morocco.geojson       Kernmarokko
    data/raw/boundaries/conflict_area.shp     Westsahara

Ausgaben:
    data/interim/mca_criteria/results_non_conflict_areas.csv   eine Spalte, zeilengleich mit dem Raster
    (zusätzlich eine Kontrollkarte per ``gdf.plot``, wird nicht gespeichert)

Hinweise:
    - Der Indikator ist ein Abstandsverhältnis, keine Distanz (Korrekturplan F-15);
      die Rangskalierung hat einen Off-by-one-Fehler, der einen negativen Wert
      erzeugt (F-16).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python non_conflict.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np

# Data
    # Current potential
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
gdf_cells_centroid = gdf_grid.centroid
    # non_conflict
gdf_morocco = gpd.read_file('../data/raw/boundaries/morocco.geojson').to_crs("EPSG:32629")
    # conflict --> Western Sahara
gdf_conflict = gpd.read_file('../data/raw/boundaries/conflict_area.shp').to_crs("EPSG:32629")

ds_distance_to_morocco = gdf_cells_centroid.distance(gdf_morocco.geometry[0])
ds_distance_to_conflict_area = gdf_cells_centroid.distance(gdf_conflict.geometry[0])
ds_ratio_distance = ds_distance_to_conflict_area/ds_distance_to_morocco
ds_ratio_distance.loc[ds_ratio_distance == 0] = 0
ds_ratio_distance.loc[ds_ratio_distance == np.inf] = 100

# Rang-skale
kriterium = (ds_ratio_distance > 0) & (ds_ratio_distance < 100) | (ds_ratio_distance > 100)

ds_ranks = ds_ratio_distance.loc[kriterium].rank().astype(int)-1
ds_ranks = (ds_ranks - 1) / (len(ds_ranks) - 1) * 100
ds_ratio_distance.loc[kriterium] = ds_ranks
ds_ratio_distance.to_csv('../data/interim/mca_criteria/results_non_conflict_areas.csv', index=False)

# Map non-conflict areas
gdf_grid['non_conflict'] = ds_ratio_distance
gdf_grid.plot(column='non_conflict', cmap='YlGnBu', legend=True)