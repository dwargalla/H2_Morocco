"""MCA-Kriterium Nicht-Konfliktgebiet (soziopolitische Stabilität).

Wert je Zelle aus dem Abstand ihres Mittelpunkts zur Konfliktzone östlich des Walls
(``conflict_area.shp``, nach Marsili 2024), mit exponentiellem Abfall des Risikos:

    Wert = 100 · (1 − exp(−Abstand / λ)),   λ = 50 km

In der Konfliktzone ist der Wert 0, mit wachsendem Abstand nähert er sich 100
(bei 50 km 63 Punkte, bei 150 km 95 Punkte). Die Zone selbst ist zusätzlich No-Go
(``no_go_zones.py``).

Begründung für λ = 50 km: Die Beschüsse seit 2020 treffen Orte nahe am Wall
(Mahbès etwa 25 km, Smara etwa 31 km von der Zone; UN S/2024/707); die eingesetzten
Raketenwerfer (BM-21 Grad) reichen 20 km, mit neuerer Munition 30–45 km. λ entspricht
damit der größten Waffenreichweite. Sensitivität λ = 25 / 100 km: Fehlerprotokoll Nr. 68.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/boundaries/conflict_area.shp     Konfliktzone östlich des Walls

Ausgaben:
    data/interim/mca_criteria/results_non_conflict_areas.csv   eine Spalte, zeilengleich mit dem Raster

Hinweise:
    - Bis 05.11.2026 war der Indikator das Verhältnis Abstand Konfliktzone ÷ Abstand
      Kernmarokko, nach Rang skaliert: Kernmarokko bekam pauschal 100, auch 2 km neben
      der Zone (Fehlerprotokoll Nr. 68, 38, 72; Korrekturplan F-15, F-16).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python non_conflict.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import numpy as np
import pandas as pd

DECAY_KM = 50       # λ: typische Reichweite des Risikos durch Beschuss [km]

# Data
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
gdf_cells_centroid = gdf_grid.centroid
    # Conflict zone east of the berm (Marsili 2024)
gdf_conflict = gpd.read_file('../data/raw/boundaries/conflict_area.shp').to_crs("EPSG:32629")

# Distance of each cell centre to the conflict zone (0 inside the zone)
distance_km = gdf_cells_centroid.distance(gdf_conflict.geometry[0]) / 1000

# Exponential decay: 0 in the zone, close to 100 far away
non_conflict_score = 100 * (1 - np.exp(-distance_km / DECAY_KM))

pd.DataFrame({'0': non_conflict_score}).to_csv('../data/interim/mca_criteria/results_non_conflict_areas.csv', index=False)

# Map non-conflict score (only shown, not saved)
gdf_grid['non_conflict'] = non_conflict_score
gdf_grid.plot(column='non_conflict', cmap='YlGnBu', legend=True)
