"""Erzeugt das 10-km-Raster über Marokko, roh und auf die Landesgrenze zugeschnitten.

Legt ein Rechteckgitter mit 10 000 m Kantenlänge über die Bounding Box der
Landesgrenze (EPSG:32629, UTM 29N) und behält nur Zellen, die die Grenze
schneiden. Danach wird jede Zelle auf die Landesgrenze zugeschnitten; das ist
das zentrale Raster aller weiteren Skripte.

Eingaben:
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp   Landesgrenze

Ausgaben:
    data/interim/grid/grid_morocco.shp             Rohraster (volle 10-km-Quadrate)
    data/interim/grid/grid_morocco_clear.shp       zentrales Raster: Zellen auf die
                                                   Landesgrenze zugeschnitten (7219 Zellen)

Hinweise:
    - Alle anderen Skripte lesen ``grid_morocco_clear.shp``. Früher hieß es, die
      Datei sei von Hand bereinigt; tatsächlich ist sie genau dieser Zuschnitt
      (geprüft 05.11.2026 gegen die alte Datei: Abweichung < 0,00001 m² je Zelle).
    - Zeilenreihenfolge nicht ändern: Alle CSVs je Zelle sind zeilengleich mit
      diesem Raster.
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

gdf_morocco_gird['FID'] = range(len(gdf_morocco_gird))
gdf_morocco_gird = gdf_morocco_gird[['FID', 'geometry']]
gdf_morocco_gird.to_file("../../data/interim/grid/grid_morocco.shp", driver='ESRI Shapefile')

# Zentrales Raster: Zellen auf die Landesgrenze zuschneiden
morocco_shape = gdf_morocco_boundary_utm29N.union_all()
gdf_grid_clear = gdf_morocco_gird.copy()
gdf_grid_clear['geometry'] = gdf_morocco_gird.geometry.intersection(morocco_shape)
gdf_grid_clear.to_file("../../data/interim/grid/grid_morocco_clear.shp", driver='ESRI Shapefile')
