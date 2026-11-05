# origin_unknown: Altdaten ohne bekannte Quelle

Diese Dateien stammen aus dem Masterprojekt (Sciebo `H2 Morocco/Masterprojekt/Python/…/Data/`) und wurden damals in QGIS erzeugt. Ausgangsdaten und Rechenweg sind nicht erhalten, und das Paper nennt keine Quelle. Kein Skript im Repo kann sie neu erzeugen. Sie liegen deshalb unter `raw/` und gelten als Eingabedaten.

| Datei | Gelesen von | Was bekannt ist | Fehlerprotokoll |
|---|---|---|---|
| `morocco_coast_line.shp` | `MCA/water_net.py`, `MCA/water_forecast.py`, `Cost_analysis/04_cost_analysis_h2_morocco.py` | Küstenlinie Marokko + Westsahara, 2 Linien, EPSG:4326. Die Spalten `shapeiso`, `shapegroup` deuten auf geoBoundaries als Quelle. Zellen, die sie berühren, gelten als Küstenzellen (Entsalzung möglich). | Nr. 69, 111 |

**Früher ebenfalls hier, seit 05.11.2026 nach den Quellen aus dem Paper neu abgeleitet und gelöscht** (Originale weiter in Sciebo):
- `Wind_pot_morocco_FLH.shp` → jetzt `MCA/ki_generiert/wind_flh_grid.py` aus dem Global Wind Atlas
- `cell_flh_re.csv` → jetzt `Cost_analysis/ki_generiert/01c_cell_flh_re.py` aus den MCA-Layern für PV und Wind
