"""Wind-Volllaststunden je Rasterzelle aus dem Global Wind Atlas.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Ersetzt den QGIS-Layer unbekannter Herkunft, siehe Hinweise.

Volllaststunden = Kapazitätsfaktor × 8.760 h, gemittelt über alle Pixel, deren
Mittelpunkt in der Zelle liegt. Zellen ohne solchen Pixel (Splitter am Rand)
bekommen das Mittel der Pixel, die sie berühren. Das Ergebnis ist ein Polygon je
Zelle (1 m nach innen gepuffert, damit ``wind_analysis.py`` jede Zelle nur mit
ihrem eigenen Polygon verschneidet).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp                  Raster (EPSG:32629)
    data/raw/renewables/gwa/{MAR,ESH}_capacity-factor_IEC3.tif Global Wind Atlas v3,
                                                  Kapazitätsfaktor IEC-Klasse III, 250 m, EPSG:4326

Ausgaben:
    data/interim/layers/Wind_pot_morocco_FLH.shp     Spalten FID, FLH_wind [h/a]; EPSG:32629

Hinweise:
    - Quelle wie im Paper (Tabelle 3: Global Wind Atlas). Der frühere QGIS-Layer
      (Original in Sciebo) hatte unbekannte Herkunft. Das Wind-Kriterium liegt damit im
      Mittel 13 % niedriger, Korrelation mit dem alten 0,983, Maximum gleich (7.432 h,
      kommt aus dem Atlas selbst; Fehlerprotokoll Nr. 71). Geprüft 05.11.2026.
    - **Annahme Turbinenklasse IEC III:** Das Paper nennt keine Klasse. IEC III passt
      zur Referenzturbine der Kostenanalyse (Vestas V136-3.45, Schwachwindklasse IIIA).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python wind_flh_grid.py``
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

HOURS_PER_YEAR = 8760
GWA_FILES = ['../../data/raw/renewables/gwa/MAR_capacity-factor_IEC3.tif',
             '../../data/raw/renewables/gwa/ESH_capacity-factor_IEC3.tif']

gdf_grid = gpd.read_file('../../data/interim/grid/grid_morocco_clear.shp')
n_cells = len(gdf_grid)


def cell_sums(all_touched):
    """Summe und Anzahl gültiger Kapazitätsfaktoren je Zelle über beide Länderdateien."""
    total = np.zeros(n_cells)
    count = np.zeros(n_cells)
    for path in GWA_FILES:
        with rasterio.open(path) as src:
            capacity_factor = src.read(1)
            grid_in_raster_crs = gdf_grid.to_crs(src.crs)
            cell_id = rasterize(((geom, i + 1) for i, geom in enumerate(grid_in_raster_crs.geometry)),
                                out_shape=capacity_factor.shape, transform=src.transform,
                                fill=0, dtype='int32', all_touched=all_touched)
        valid = (cell_id > 0) & np.isfinite(capacity_factor)
        total += np.bincount(cell_id[valid] - 1, weights=capacity_factor[valid], minlength=n_cells)
        count += np.bincount(cell_id[valid] - 1, minlength=n_cells)
    return total, count


total, count = cell_sums(all_touched=False)          # Pixelmittelpunkt in der Zelle
if (count == 0).any():                               # Splitterzellen: berührende Pixel
    total_touched, count_touched = cell_sums(all_touched=True)
    empty = count == 0
    total[empty], count[empty] = total_touched[empty], count_touched[empty]

with np.errstate(invalid='ignore'):
    flh_wind = total / count * HOURS_PER_YEAR        # NaN, falls gar kein Pixel

gdf_wind = gpd.GeoDataFrame({'FID': gdf_grid['FID'], 'FLH_wind': flh_wind},
                            geometry=gdf_grid.geometry.buffer(-1), crs=gdf_grid.crs)
gdf_wind = gdf_wind[~gdf_wind.geometry.is_empty & gdf_wind['FLH_wind'].notna()]
gdf_wind.to_file('../../data/interim/layers/Wind_pot_morocco_FLH.shp', driver='ESRI Shapefile')
