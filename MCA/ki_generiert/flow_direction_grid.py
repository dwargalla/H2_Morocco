"""Aggregiert das Fließrichtungsraster (MERIT Hydro) auf das 10-km-Raster.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Gegen den bisherigen Stand geprüft, siehe Hinweise.

Für jede Rasterzelle wird die Summe aller Pixelwerte von
``flow_direction_morocco.tif`` gebildet, deren Mittelpunkt in der Zelle liegt.
Das entspricht der QGIS-Zonenstatistik, mit der die Datei im Masterprojekt
entstanden ist. Das Ergebnis ``_sum`` verteilt in ``water_exploitable_sw.py``
das Oberflächenwasser auf die Zellen.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp          Raster (EPSG:32629)
    data/raw/hydrology/flow_direction_morocco.tif     MERIT Hydro ``dir``, 83 m, EPSG:32629

Ausgaben:
    data/interim/layers/flow_direction_grid.shp         Spalten FID, _sum; zeilengleich mit dem Raster

Hinweise:
    - **Methodenfehler (Fehlerprotokoll Nr. 110):** Das Raster enthält D8-Fließrichtungs-
      Codes (1, 2, 4, …, 128), keine Fließakkumulation. ``_sum`` ist deshalb eine Summe
      von Richtungscodes und kein Maß für Abflusswege. Das Skript bildet den
      bisherigen Rechenweg nur nach.
    - Nachgerechnet gegen die QGIS-Datei aus dem Masterprojekt: 7.216 von 7.219 Zellen
      auf ±1 gleich (Randpixel).
    - Speicherbedarf kurzzeitig etwa 3,5 GB (Raster float32, danach uint8 und Zellnummern int16).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python flow_direction_grid.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize

gdf_grid = gpd.read_file('../../data/interim/grid/grid_morocco_clear.shp')

with rasterio.open('../../data/raw/hydrology/flow_direction_morocco.tif') as src:
    raw = src.read(1)                                  # float32, NoData = -999999
    transform = src.transform
    assert src.crs.to_epsg() == gdf_grid.crs.to_epsg() == 32629
    # NoData zählt wie in der QGIS-Zonenstatistik nicht mit; Codes 0–255 passen in uint8
    flow_direction = np.where(raw == src.nodata, 0, raw).astype('uint8')
    del raw

# Zellnummer 1..n je Pixel (0 = außerhalb); Pixel zählt, wenn sein Mittelpunkt in der Zelle liegt
cell_id = rasterize(((geom, i + 1) for i, geom in enumerate(gdf_grid.geometry)),
                    out_shape=flow_direction.shape, transform=transform,
                    fill=0, dtype='int16', all_touched=False)

inside = cell_id > 0
sum_per_cell = np.bincount(cell_id[inside], weights=flow_direction[inside],
                           minlength=len(gdf_grid) + 1)[1:]

gdf_flow = gpd.GeoDataFrame({'FID': gdf_grid['FID'], '_sum': sum_per_cell},
                            geometry=gdf_grid.geometry, crs=gdf_grid.crs)
gdf_flow.to_file('../../data/interim/layers/flow_direction_grid.shp', driver='ESRI Shapefile')
