"""Wandelt den PV-Jahresertrag des Global Solar Atlas in Polygone um.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Gegen den bisherigen Stand geprüft, siehe Hinweise.

Rundet ``PVOUT_Morocco_Complete_Yearly.tif`` kaufmännisch auf ganze kWh/kWp und
fasst benachbarte Pixel mit gleichem Wert (4er-Nachbarschaft) zu einem Polygon
zusammen. Das entspricht dem QGIS-Schritt „Polygonisieren“, mit dem die Datei
im Masterprojekt entstanden ist. ``pv_analysis.py`` mittelt diese Polygone je
Rasterzelle.

Eingaben:
    data/raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif   Global Solar Atlas v2,
                                                PVOUT [kWh/kWp/a], 30″, EPSG:4326

Ausgaben:
    data/interim/qgis/PV_yeald_clear_ma_we.shp  Spalten fid, pv_yeald; EPSG:4326

Hinweise:
    - Nachgerechnet gegen die QGIS-Datei aus dem Masterprojekt (05.11.2026): gleiche
      Anzahl Polygone (478.733), ``pv_analysis.py`` liefert damit dieselben Werte.
    - Der Dateiname mit „yeald“ (statt „yield“) bleibt, weil ``pv_analysis.py`` ihn liest.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python pv_yield_polygons.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

with rasterio.open('../../data/raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif') as src:
    pvout = src.read(1)
    transform = src.transform
    crs = src.crs
    valid = np.isfinite(pvout) & (pvout != src.nodata)

# kaufmännisch runden (,5 aufwärts), wie QGIS; numpy.round rundet ,5 zur geraden Zahl
pv_rounded = np.where(valid, np.floor(pvout + 0.5), 0).astype('int32')

polygons = [(shape(geom), int(value))
            for geom, value in shapes(pv_rounded, mask=valid, transform=transform, connectivity=4)]

gdf_pv = gpd.GeoDataFrame({'fid': np.arange(1, len(polygons) + 1, dtype=float),
                           'pv_yeald': [value for _, value in polygons]},
                          geometry=[geom for geom, _ in polygons], crs=crs)
gdf_pv.to_file('../../data/interim/qgis/PV_yeald_clear_ma_we.shp', driver='ESRI Shapefile')
