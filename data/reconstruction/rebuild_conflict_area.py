"""Rekonstruiert das Konfliktgebiet östlich des Berms ``conflict_area.shp``.

Das Original wurde vermutlich nach Marsili (2024) von Hand digitalisiert und ist
verloren. ``MCA/non_conflict.py`` gibt Zellen, deren Schwerpunkt im Gebiet liegt,
den Wert 0. Die Vereinigung dieser Zellen aus ``results_non_conflict_areas.csv``
ist daher die beste verfügbare Annäherung (besser als Natural Earth „W. Sahara“).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/interim/mca_criteria/results_non_conflict_areas.csv

Ausgaben:
    data/raw/boundaries/conflict_area.shp   ein Polygon, EPSG:32629

Hinweise:
    - Kontrolle: ``non_conflict.py`` trifft 873 von 874 Konfliktzellen; die
      Rangskala der übrigen Zellen weicht im Median um 0,7 Punkte ab.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python rebuild_conflict_area.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import pandas as pd

gdf_grid = gpd.read_file('../interim/grid/grid_morocco_clear.shp')
array_non_conflict = pd.read_csv('../interim/mca_criteria/results_non_conflict_areas.csv').iloc[:, 0].values

gdf_conflict = gpd.GeoDataFrame({'name': ['conflict_area_reconstructed']},
                                geometry=[gdf_grid[array_non_conflict == 0].union_all()], crs=gdf_grid.crs)
gdf_conflict.to_file('../raw/boundaries/conflict_area.shp')
print(f'{(array_non_conflict == 0).sum()} Zellen, {gdf_conflict.area.sum() / 1e6:,.0f} km²')
