"""Rekonstruiert die Fließakkumulation je Rasterzelle ``flow_direction_grid.shp``.

Das Original (QGIS, Spalte ``_sum``) ist verloren. ``MCA/water_exploitable_sw.py``
verteilt das Oberflächenwasser jedes Einzugsgebiets b proportional zu ``_sum``:

    sw_c = _sum_c · Σ_{b ∋ c} Basin_b / S_b,    S_b = Σ_{c ∈ b} _sum_c

Mit ``sw_c`` aus ``water_availability_sw.csv`` und den Einzugsgebieten lässt sich
das nach ``_sum`` auflösen. Unbekannt sind nur die 9 Summen S_b; sie folgen aus
den Randzellen, die in mehreren Gebieten liegen (Ausgleichsrechnung), bis auf
einen gemeinsamen Faktor. Diesen liefert die Farbleiste der Originalkarte
``General/06_Diagramme_Karten/EPS/morocco_flow_direction.eps``: vmin = 0,
vmax = 1 091 380 (aus den Tick-Positionen, ±1).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/hydrology/watershead_morocco.shp   aus rebuild_watershead.py
    data/interim/water/water_availability_sw.csv

Ausgaben:
    data/interim/qgis/flow_direction_grid.shp   Spalte ``_sum``, zeilengleich mit dem Raster

Hinweise:
    - Kontrolle: ``MCA/water_exploitable_sw.py`` reproduziert damit
      ``water_availability_sw.csv`` exakt (max. Abweichung 1·10⁻¹⁴). Gegen die
      EPS-Farben liegen die ``sahara``-Zellen etwa 4,5 % daneben, alle anderen
      Gebiete stimmen auf ±1 Farbstufe.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python rebuild_flow_direction_grid.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

VMAX_EPS = 1091380  # Maximum von _sum laut Farbleiste der Originalkarte

gdf_grid = gpd.read_file('../interim/grid/grid_morocco_clear.shp')
gdf_watershead = gpd.read_file('../raw/hydrology/watershead_morocco.shp')
array_sw = pd.read_csv('../interim/water/water_availability_sw.csv')['water_availability_sw[MCM]'].values

# Oberflächenwasser je Einzugsgebiet in MCM, wie in water_exploitable_sw.py
dict_basin = {'sahara': 390, 'loukkos': 3600, 'moulouiya': 1610, 'sebou': 5560, 'bouregreg': 850,
              'oum': 3315, 'tensif': 800, 'south_atlas': 626, 'souss_massa': 1444}
array_basin = gdf_watershead['name'].map(dict_basin).values.astype(float)

# Zelle x Einzugsgebiet: dieselbe intersects-Zuordnung wie list_index()
matrix_member = np.column_stack([gdf_grid.intersects(geom).values for geom in gdf_watershead.geometry]).astype(float)


def flow_sum(log_y):
    """_sum je Zelle für gegebene log(1/S_b)."""
    return array_sw / (matrix_member @ (array_basin * np.exp(log_y)))


def residuals(z):
    log_y = np.concatenate([[0.0], z])                 # S_sahara = 1, Skalierung kommt später
    return np.log(matrix_member.T @ flow_sum(log_y)) + log_y   # S_b · (1/S_b) = 1


result = least_squares(residuals, np.zeros(len(array_basin) - 1), xtol=1e-15, ftol=1e-15, gtol=1e-15)
array_flow = flow_sum(np.concatenate([[0.0], result.x]))
print('max. Residuum der Gebietssummen:', np.abs(residuals(result.x)).max())

gdf_flow = gdf_grid[['geometry']].copy()
gdf_flow['_sum'] = array_flow * VMAX_EPS / array_flow.max()
gdf_flow.to_file('../interim/qgis/flow_direction_grid.shp')
print(gdf_flow['_sum'].describe())
