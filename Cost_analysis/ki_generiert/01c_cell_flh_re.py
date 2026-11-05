"""Schritt 1c der Kostenanalyse: PV-Ertrag und Wind-Volllaststunden je Rasterzelle.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Ersetzt ``cell_flh_re.csv`` unbekannter Herkunft, siehe Hinweise.

``04_cost_analysis_h2_morocco.py`` ordnet jeder Zelle den Referenzpunkt zu, dessen
(FLH_PV, FLH_Wind) ihren eigenen Werten am nächsten liegt. Wie im Paper
beschrieben („smallest deviation in PV yield and wind full-load hours“) nimmt
dieses Skript dafür dieselben Werte wie die MCA: PV-Ertrag aus dem Global Solar
Atlas und Wind-Volllaststunden aus dem Global Wind Atlas.

Eingaben:
    data/interim/mca_criteria/results_pv_yeald.csv   aus MCA/pv_analysis.py  [kWh/kWp/a]
    data/interim/mca_criteria/results_wind_flh.csv   aus MCA/wind_analysis.py [h/a]
    data/interim/grid/grid_morocco_clear.shp         für den Nachbarschaftsersatz

Ausgaben:
    data/interim/re_profiles/cell_flh_re.csv         Spalten FLH_PV, FLH_Wind; zeilengleich mit dem Raster

Hinweise:
    - Splitterzellen, für die die MCA 0 einträgt (keine Daten, Fehlerprotokoll Nr. 24),
      bekommen hier den Wert der nächstgelegenen Zelle mit Daten. Sonst würden sie dem
      Referenzpunkt mit dem kleinsten Ertrag zugeordnet.
    - Die alte QGIS-Datei (bis 05.11.2026 in ``data/raw/origin_unknown/``, Original in Sciebo) hatte bei PV dieselben
      Werte wie die MCA (99,8 % der Zellen), als zweite Spalte aber ``FLH_el``, eine
      Umrechnung unbekannter Herkunft statt der Wind-Volllaststunden (Nr. 6, 106).
    - Die Referenzpunkte stammen aus renewables.ninja (andere Modelle als die Atlanten);
      der Vergleich mischt also zwei Datenquellen, wie im Paper beschrieben.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python 01c_cell_flh_re.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
import pandas as pd

gdf_grid = gpd.read_file('../../data/interim/grid/grid_morocco_clear.shp')
pv = pd.read_csv('../../data/interim/mca_criteria/results_pv_yeald.csv').iloc[:, 0].to_numpy(dtype=float)
wind = pd.read_csv('../../data/interim/mca_criteria/results_wind_flh.csv').iloc[:, 0].to_numpy(dtype=float)

centroids = np.column_stack([gdf_grid.centroid.x, gdf_grid.centroid.y])


def fill_from_nearest(values):
    """Ersetzt Nullen (keine Daten) durch den Wert der nächstgelegenen Zelle mit Daten."""
    values = values.copy()
    missing = np.where(values == 0)[0]
    have = np.where(values > 0)[0]
    for i in missing:
        distance = np.hypot(*(centroids[have] - centroids[i]).T)
        values[i] = values[have[np.argmin(distance)]]
    return values


df_cell_flh = pd.DataFrame({'FLH_PV': fill_from_nearest(pv), 'FLH_Wind': fill_from_nearest(wind)})
df_cell_flh.to_csv('../../data/interim/re_profiles/cell_flh_re.csv', index=False)
