# Daten

Alle Eingangs- und Zwischendaten von MCA und Kostenanalyse liegen in diesem Ordner. Ergebnisse und Abbildungen liegen in `../results/`.

| Ordner | Inhalt | Im Repo? |
|---|---|---|
| `raw/` | Extern bezogen oder von Hand erstellt. Wird von keinem Skript geschrieben. | nein (außer kleinen Dateien, s. u.), siehe `.gitignore` |
| `interim/` | Abgeleitet, in QGIS oder per Skript. Eingabe für spätere Schritte. | CSVs ja, Geodaten größtenteils nein |

**Alle Dateien je Zelle sind zeilengleich mit dem Raster** `interim/grid/grid_morocco_clear.shp`. Zeile `i` gehört zu Zelle `i`, es gibt keine ID-Spalte. Nicht sortieren und nicht filtern.

---

## raw/

| Datei | Quelle | Spalten | Lokal |
|---|---|---|---|
| `osm/gis_osm_{landuse_a,roads,railways}_free_1.shp` | OpenStreetMap über Geofabrik, Stand 29.01.2025 (aus `General/04_Recherche/QGIS/morocco-latest-free.shp.zip`); Lizenz ODbL, siehe `osm/README` | `fclass` | ✓ |
| `globcover/mar_gc_adg/mar_gc_adg.shp` | FAO GlobCover Marokko: https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5 | `GRIDCODE` | fehlt (Legenden-.xls im Repo) |
| `globcover/wsa_gc_adg/wsa_gc_adg.shp` | FAO GlobCover Westsahara: https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2 | `GRIDCODE` | fehlt (Legenden-.xls im Repo) |
| `boundaries/morocco_Morocco_Country_Boundary.shp` | `General/04_Recherche/QGIS/Marokko karte vollständig/Morocco Country Boundary.shp.zip` | – | ✓ |
| `boundaries/morocco.geojson` | Kernmarokko, `General/04_Recherche/QGIS/Datein/Daten/morocco.geojson` | – | ✓ |
| `boundaries/Regions.shp` | 12 Verwaltungsregionen (Gliederung ab 2015). GADM 4.1 hat noch die 15 alten Regionen und passt nicht. | `Nom_Region` | fehlt |
| `boundaries/conflict_area.shp` | Westsahara östlich des Berms. Annäherung z. B. über Natural Earth „Disputed Areas“: https://www.naturalearthdata.com/downloads/50m-cultural-vectors/ | – | fehlt |
| `groundwater/Morocco_HG.shp` | BGS Africa Groundwater Atlas, `General/04_Recherche/QGIS/Datein/Daten/Morocco/` | `MorHGComb` | ✓ |
| `groundwater/WesternSahara_HG.shp` | BGS Africa Groundwater Atlas: https://www2.bgs.ac.uk/africaGroundwaterAtlas/downloadGIS.html | `WSHGComb` | fehlt |
| `hydrology/watershead_morocco.shp` | 9 Einzugsgebiete. Quelle unbekannt; Annäherung über HydroBASINS: https://www.hydrosheds.org/products/hydrobasins | `name` | fehlt |
| `climate/{Precipitation,PET}_morocco_2050_corr.shp` | CMIP6, SSP2-4.5, nach Gumus et al. (2024), https://doi.org/10.1016/j.jenvman.2024.122019 (Daten bei den Autoren anfragen) | `Precipitat`, `PET` | fehlt |
| `infrastructure/industrial_ports_morocco_{2025,2050}.shp` | von Hand erstellt | – | ✓ (im Repo) |
| `renewables/PV_WIND_50_Punkte.xlsx` | je 50 repräsentative PV- und Wind-Standorte, von Hand gewählt | `Latitude`, `Longitude` | ✓ (im Repo) |

## interim/

| Ordner | Dateien | Erzeugt von |
|---|---|---|
| `grid/` | `grid_morocco.shp` | `MCA/Grid_morocco/grid_morocco.py` |
| | `grid_morocco_clear.shp` | von Hand bereinigte Fassung (7219 Zellen, EPSG:32629). **Zentrales Raster.** |
| `qgis/` | `ToPo_1500.shp` | QGIS, Topografie auf das Raster aggregiert (`NoGo` 0/1). Aus Commit `9927be0` wiederhergestellt, Spalte `NoGos` in `NoGo` umbenannt. |
| | `morocco_coast_line.shp` | **Rekonstruktion, nicht das Original:** Landesgrenze, beschnitten auf die 352 Küstenzellen (Wasser-Score 100), plus zwei Platzhalterlinien für die Zellen 5021 und 5151. Trifft exakt dieselben Zellen wie das Original, taugt aber nur eingeschränkt für Karten. |
| | `cell_flh_re.csv` | QGIS (PV/Wind-Volllaststunden je Zelle), kein Skript |
| | `flow_direction_grid.shp` (fehlt) | QGIS, Fließakkumulation aus MERIT Hydro (`upa`), https://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro |
| | `PV_yeald_clear_ma_we.shp` (fehlt) | QGIS aus Global Solar Atlas `PVOUT.tif` (liegt in `General/04_Recherche/QGIS/Datein/Daten/`), https://globalsolaratlas.info/download/morocco |
| | `Wind_pot_morocco_FLH.shp` (fehlt) | QGIS aus Global Wind Atlas, https://globalwindatlas.info/en/download/gis-files |
| `landuse/` | `morocco_landuse_2050.shp` (fehlt) | `MCA/forecast_landuse.py` |
| `water/` | `water_availability_{sw,gw}.csv` | `MCA/water_exploitable_{sw,gw}.py` |
| | `Water_Consumption_{2025,2050}.csv` | `MCA/water_consumption.py` |
| | `cwb.shp` (fehlt) | `MCA/water_forecast.py` |
| `water_cost/` | `water_availability_{sw,gw}{,_2050}.csv` | eigene, ältere Fassung der Kostenanalyse. **Weicht von `water/` ab.** Die 2050-Dateien lassen sich mit dem aktuellen Code nicht neu erzeugen (Commit `0ff553c`, Korrekturplan F-22). |
| `mca_criteria/` | `results_*.csv` (14 Kriterien-Dateien) | MCA-Kriterienskripte, Eingabe für `MCA/mca_maps.py` |
| `re_profiles/` | `pv_wind_electricity.csv`, `flh_re.csv` | `Cost_analysis/re_data.py` |
| | `FLH_electrolyzer.csv` | `Cost_analysis/FLH_el.py` |
| | `data_re_flh_electrolyzer.shp` | `Cost_analysis/assignment_re_data.py` |

Kontrolle der wiederhergestellten Dateien: `water_net.py`, `no_go_zones.py` und `mca_maps.py` reproduzieren damit die vorhandenen Ergebnis-CSVs wertgleich.
