"""Ersetzt die PV- und Wind-Layer ``PV_yeald_clear_ma_we.shp`` und ``Wind_pot_morocco_FLH.shp``.

Die Originale (QGIS) sind verloren, ihr Rechenweg ist unbekannt. Ersatz: je
Rasterzelle ein Polygon, um 1 m nach innen gepuffert, sodass der
``intersects``-Join in ``MCA/pv_analysis.py`` bzw. ``MCA/wind_analysis.py`` genau
die eigene Zelle trifft. Wert ist das Mittel aller Rasterpixel, die die Zelle
berühren:

- PV: spezifischer Jahresertrag [kWh/kWp] aus dem Global Solar Atlas
  (``PVOUT_Morocco_Complete_Yearly.tif``, Marokko + Westsahara).
- Wind: Volllaststunden = Capacity Factor IEC3 × 8760 h aus dem Global Wind Atlas.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif   aus General/04_Recherche/QGIS/
    data/raw/renewables/gwa/{MAR,ESH}_capacity-factor_IEC3.tif  werden geladen, falls nicht vorhanden

Ausgaben:
    data/interim/qgis/PV_yeald_clear_ma_we.shp   Spalte ``pv_yeald``
    data/interim/qgis/Wind_pot_morocco_FLH.shp   Spalte ``FLH_wind``

Hinweise:
    - Kontrolle gegen die Kriterien-CSVs: PV Korrelation 0,99995 (Median-Abweichung
      0,03 %), Wind Korrelation 0,981 bei im Mittel etwa 15 % niedrigeren Werten.
    - Ausführen aus ``data/reconstruction/``: ``python rebuild_pv_wind.py``
"""

import os

import geopandas as gpd
import numpy as np
import rasterio
import requests
from rasterio.mask import mask
from rasterio.merge import merge

URL_GWA = 'https://globalwindatlas.info/api/gis/country/{country}/capacity-factor_IEC3'

gdf_grid = gpd.read_file('../interim/grid/grid_morocco_clear.shp')


def cell_means(dataset):
    """Mittel aller gültigen Pixel, die eine Rasterzelle berühren (0, wenn keine)."""
    list_mean = []
    for cell in gdf_grid.to_crs(dataset.crs).geometry:
        try:
            values = mask(dataset, [cell], all_touched=True, crop=True, filled=False)[0][0].compressed()
        except ValueError:                                  # Zelle außerhalb des Rasters
            values = np.array([])
        values = values[np.isfinite(values) & (np.abs(values) < 1e30) & (values > 0)]
        list_mean.append(values.mean() if len(values) else 0.0)
    return np.array(list_mean)


def write_layer(values, column, path):
    gdf_layer = gdf_grid[['geometry']].copy()
    gdf_layer[column] = values
    gdf_layer['geometry'] = gdf_layer.buffer(-1)
    gdf_layer[gdf_layer[column] > 0].to_file(path)


# PV
with rasterio.open('../raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif') as dataset:
    write_layer(cell_means(dataset), 'pv_yeald', '../interim/qgis/PV_yeald_clear_ma_we.shp')

# Wind
os.makedirs('../raw/renewables/gwa', exist_ok=True)
list_paths = []
for country in ['MAR', 'ESH']:
    path = f'../raw/renewables/gwa/{country}_capacity-factor_IEC3.tif'
    if not os.path.exists(path):
        response = requests.get(URL_GWA.format(country=country), timeout=600)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
    list_paths.append(path)

list_sources = [rasterio.open(path) for path in list_paths]
array_merged, transform = merge(list_sources, nodata=list_sources[0].nodata)
profile = list_sources[0].profile
profile.update(height=array_merged.shape[1], width=array_merged.shape[2], transform=transform)
with rasterio.MemoryFile() as memfile:
    with memfile.open(**profile) as dataset:
        dataset.write(array_merged)
        write_layer(cell_means(dataset) * 8760, 'FLH_wind', '../interim/qgis/Wind_pot_morocco_FLH.shp')
for source in list_sources:
    source.close()
