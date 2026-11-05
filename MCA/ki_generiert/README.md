# ki_generiert: von Claude erstellte MCA-Skripte

Diese Skripte hat Claude (Claude Code) am 05.11.2026 geschrieben. Sie ersetzen Arbeitsschritte, die im Masterprojekt von Hand in QGIS gemacht wurden; Quellen wie im Paper angegeben, damit `data/interim/` komplett per Skript entsteht. Jedes Skript wurde gegen die alte QGIS-Datei geprüft; die Abweichungen stehen im Kopf des Skripts und in `data/README.md` (Abschnitt „Herkunft und Prüfung“).

Die Skripte laufen wie alle anderen aus ihrem eigenen Ordner (`python flow_direction_grid.py`) und sind in `main.ipynb` eingebunden.

| Skript | Erzeugt | Aus | Abweichung zur QGIS-Datei |
|---|---|---|---|
| `flow_direction_grid.py` | `data/interim/layers/flow_direction_grid.shp` | `data/raw/hydrology/flow_direction_morocco.tif` (MERIT Hydro) | 3 von 7.219 Zellen um mehr als 1 anders; Oberflächenwasser höchstens 0,0002 Mio. m³ |
| `pv_yield_polygons.py` | `data/interim/layers/PV_yeald_clear_ma_we.shp` | `data/raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif` | keine |
| `wind_flh_grid.py` | `data/interim/layers/Wind_pot_morocco_FLH.shp` | `data/raw/renewables/gwa/` (Global Wind Atlas, IEC III) | ersetzt den QGIS-Layer unbekannter Herkunft (Quelle jetzt wie im Paper): Mittel 13 % niedriger, Korrelation 0,983 |
| `topography_grid.py` | `data/interim/layers/ToPo_1500.shp` | `data/raw/dem/copernicus_dem_glo90/` | Topografie-Maske in 3 Zellen anders (altes DEM unbekannt) |

Weitere KI-generierte oder von KI geänderte Dateien listet `README.md` im Hauptordner (Abschnitt „KI-generierte Dateien“).
