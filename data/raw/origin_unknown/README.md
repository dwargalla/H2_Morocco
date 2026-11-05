# origin_unknown: Altdaten ohne bekannten Rechenweg

Diese Dateien stammen aus dem Masterprojekt (Sciebo `H2 Morocco/Masterprojekt/Python/…/Data/`) und wurden damals in QGIS erzeugt. Weder die Ausgangsdaten noch der genaue Rechenweg sind erhalten. Kein Skript im Repo kann sie neu erzeugen. Sie liegen deshalb unter `raw/` und gelten als Eingabedaten, nicht als Zwischenergebnisse.

Die aktiven Skripte reproduzieren mit diesen Dateien die veröffentlichten Ergebnisse exakt (Prüfung 05.11.2026). Wer sie ersetzt, ändert also die Ergebnisse.

| Datei | Gelesen von | Was bekannt ist | Fehlerprotokoll |
|---|---|---|---|
| `Wind_pot_morocco_FLH.shp` | `MCA/wind_analysis.py` | Ein Polygon je Rasterzelle, Spalte `FLH_wind` (Volllaststunden Wind). Ursprünglicher Ordner `Wind_Energiedichte/wind_yeald/`. Werte bis 7.431 h, physikalisch kaum erreichbar. | Nr. 71 |
| `morocco_coast_line.shp` | `MCA/water_net.py`, `MCA/water_forecast.py`, `Cost_analysis/04_cost_analysis_h2_morocco.py` | Küstenlinie Marokko + Westsahara, 2 Linien, EPSG:4326. Die Spalten `shapeiso`, `shapegroup` deuten auf geoBoundaries als Quelle. Zellen, die sie berühren, gelten als Küstenzellen. | Nr. 69 |
| `cell_flh_re.csv` | `Cost_analysis/04_cost_analysis_h2_morocco.py` | Volllaststunden PV und Wind je Rasterzelle (zeilengleich mit dem Raster). Der Windwert ist eine gesättigte Umrechnung unbekannter Herkunft, keine Atlaswerte. | Nr. 6, 106 |
