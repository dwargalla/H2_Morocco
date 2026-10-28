"""Erzeugt das 10-km-Rohraster über Marokko.

Legt ein Rechteckgitter mit 10 000 m Kantenlänge über die Bounding Box der
Landesgrenze (EPSG:32629, UTM 29N) und behält nur Zellen, die die Grenze
schneiden.

Eingaben:
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp   Landesgrenze

Ausgaben:
    grid_morocco.shp                               Rohraster

Hinweise:
    - Einmaliger Schritt. Alle anderen Skripte verwenden nicht dieses Ergebnis,
      sondern ``grid_morocco_clear.shp`` (manuell bereinigte Fassung, 7219
      Zellen). Diese Bereinigung ist nicht als Code vorhanden.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python grid_morocco.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

gdf_morocco_boundary = gpd.read_file("../../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp")
gdf_morocco_boundary_utm29N = gdf_morocco_boundary.to_crs("EPSG:32629")

# gdf_morocco_boundary.plot()
# gdf_morocco_boundary_utm29N.plot()


def grid_cration(polygon, cell_size):
    """Erzeugt quadratische Zellen der Kantenlänge ``cell_size`` [m] über die Bounding Box von ``polygon``.

    Behält nur Zellen, die ``polygon`` schneiden, und gibt sie als
    GeoDataFrame in EPSG:32629 zurück.
    """
    min_x, min_y, max_x, max_y = polygon.total_bounds
    
    # Gitterpunkte
    x_coords = np.arange(min_x, max_x, cell_size)
    y_coords = np.arange(min_y, max_y, cell_size)
    
    # Erzeuge eine Liste von Polygonen für jede Zelle im rechteckigen Gitter
    grid_polygons = []
    for x in x_coords:
        for y in y_coords:
            cell = Polygon([
                (x, y),
                (x + cell_size, y),
                (x + cell_size, y + cell_size),
                (x, y + cell_size)
            ])

            if polygon.geometry.intersects(cell).any():
                grid_polygons.append(cell)

    return gpd.GeoDataFrame(geometry=grid_polygons, crs="EPSG:32629")

grid_size = 10000
gdf_morocco_gird = grid_cration(polygon=gdf_morocco_boundary_utm29N, cell_size=grid_size)

gdf_morocco_gird.plot()

gdf_morocco_gird.to_file("../../data/interim/grid/grid_morocco.shp", driver='ESRI Shapefile')