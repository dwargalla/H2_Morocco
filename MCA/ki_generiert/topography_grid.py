"""Höhenspanne je Rasterzelle aus dem Copernicus DEM und daraus die Topografie-Maske.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Gegen den bisherigen Stand geprüft, siehe Hinweise.

Für jede Rasterzelle werden die kleinste und größte Höhe aller DEM-Pixel
bestimmt, deren Mittelpunkt in der Zelle liegt. Ist die Spanne größer als
1.500 m, gilt die Zelle als zu steil (``NoGo = 0``), sonst ``NoGo = 1``.
Zellen ohne DEM-Pixel bleiben zulässig. ``no_go_zones.py`` übernimmt die Spalte
``NoGo`` in die No-Go-Maske.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp           Raster (EPSG:32629)
    data/raw/dem/copernicus_dem_glo90/*.tif            Copernicus DEM GLO-90, 3″, EPSG:4326

Ausgaben:
    data/interim/qgis/ToPo_1500.shp                    Spalten FID, _min, _max, Diff, NoGo;
                                                       zeilengleich mit dem Raster

Hinweise:
    - Ersetzt die QGIS-Zonenstatistik aus dem Masterprojekt, deren DEM unbekannt ist.
      Vergleich (05.11.2026): Höhen im Median 2,8 m daneben, Maske in 7.216 von 7.219
      Zellen gleich (121 statt 124 ausgeschlossene Zellen). Das alte DEM deckte 389
      Zellen nicht ab, das Copernicus DEM nur 5.
    - Der Höhenunterschied ist nur ein grobes Maß für Steilheit (Fehlerprotokoll Nr. 29).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python topography_grid.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import glob

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize

MAX_ELEVATION_RANGE_M = 1500   # größere Höhenspanne innerhalb der Zelle → No-Go

gdf_grid = gpd.read_file('../../data/interim/grid/grid_morocco_clear.shp')
n_cells = len(gdf_grid)
elevation_min = np.full(n_cells, np.inf)
elevation_max = np.full(n_cells, -np.inf)

dem_tiles = sorted(glob.glob('../../data/raw/dem/copernicus_dem_glo90/*.tif'))
assert dem_tiles, 'Copernicus-DEM-Kacheln fehlen, siehe data/README.md'

with rasterio.open(dem_tiles[0]) as src:
    gdf_grid_dem_crs = gdf_grid.to_crs(src.crs)

for tile in dem_tiles:
    with rasterio.open(tile) as src:
        bounds = src.bounds
        cells_on_tile = gdf_grid_dem_crs.cx[bounds.left:bounds.right, bounds.bottom:bounds.top]
        if cells_on_tile.empty:
            continue
        elevation = src.read(1)
        # Zellnummer 1..n je Pixel (0 = keine Zelle); Pixel zählt, wenn sein Mittelpunkt in der Zelle liegt
        cell_id = rasterize(((geom, i + 1) for i, geom in zip(cells_on_tile.index, cells_on_tile.geometry)),
                            out_shape=elevation.shape, transform=src.transform, fill=0, dtype='int32')
        inside = cell_id > 0
        if src.nodata is not None:
            inside &= elevation != src.nodata
        np.minimum.at(elevation_min, cell_id[inside] - 1, elevation[inside])
        np.maximum.at(elevation_max, cell_id[inside] - 1, elevation[inside])

elevation_min[np.isinf(elevation_min)] = np.nan
elevation_max[np.isinf(elevation_max)] = np.nan
elevation_range = elevation_max - elevation_min

gdf_topo = gpd.GeoDataFrame({
    'FID':  gdf_grid['FID'],
    '_min': elevation_min,
    '_max': elevation_max,
    'Diff': elevation_range,
    'NoGo': np.where(np.nan_to_num(elevation_range, nan=0) > MAX_ELEVATION_RANGE_M, 0, 1),
}, geometry=gdf_grid.geometry, crs=gdf_grid.crs)
gdf_topo.to_file('../../data/interim/qgis/ToPo_1500.shp', driver='ESRI Shapefile')
