# Herkunft der lokal ergänzten Geodaten (Stand 2026-10-13)

Die folgenden Dateien sind per `.gitignore` nicht im Repo. Sie wurden aus dem Projektordner `General/` und aus der Git-Historie wiederhergestellt.

| Datei | Herkunft |
|---|---|
| `morocco_Morocco_Country_Boundary.*` (hier und in `Landuse/`) | `General/04_Recherche/QGIS/Marokko karte vollständig/Morocco Country Boundary.shp.zip` |
| `Landuse/gis_osm_{landuse_a,roads,railways}_free_1.*` | `General/04_Recherche/QGIS/morocco-latest-free.shp.zip` (Geofabrik, Stand 29.01.2025) |
| `morocco.geojson` | `General/04_Recherche/QGIS/Datein/Daten/morocco.geojson` |
| `Morocco/Morocco_HG.*` | `General/04_Recherche/QGIS/Datein/Daten/Morocco/` (BGS Africa Groundwater Atlas) |
| `industrial_ports_morocco_{2025,2050}.*` | Kopie aus `Cost_analysis/Data/` |
| `ToPo_1500.*` | Git-Historie, Commit `9927be0` (`MCA/ToPo_1500.*`); Spalte `NoGos` in `NoGo` umbenannt, wie vom Code erwartet |
| `morocco_coast_line.*` (auch `Cost_analysis/Data/Data/`) | **Rekonstruktion, nicht das Original.** Landesgrenze, beschnitten auf die 352 Küstenzellen aus `results/results_water_res_available.csv` (Score 100). Dazu kommen zwei kurze Platzhalterlinien für die Zellen 5021 und 5151, die das Original als Küste führte, die aber die Landesgrenze nicht berühren. Die Linie trifft exakt dieselben Rasterzellen wie das Original. Für Karten taugt sie nur eingeschränkt. |

Kontrolle: `water_net.py`, `no_go_zones.py` und `mca_maps.py` reproduzieren damit die vorhandenen Ergebnis-CSVs wertgleich.

Weiterhin fehlend: GlobCover (`mar_gc_adg`, `wsa_gc_adg`), `Regions.shp`, `conflict_area.shp`, `Morocco/WSahara/WesternSahara_HG.shp`, `watershead_morocco.shp`, `flow_direction_grid.shp`, `PV_yeald_clear_ma_we.shp`, `Wind_pot_morocco_FLH.shp`, `Precipitation_/PET_morocco_2050_corr.shp`.
