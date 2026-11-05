# Daten

Alle Eingangs- und Zwischendaten von MCA und Kostenanalyse liegen in diesem Ordner. Ergebnisse und Abbildungen liegen in `../results/`.

| Ordner | Inhalt | Im Repo? |
|---|---|---|
| `raw/` | Extern bezogen oder von Hand erstellt. Kein Skript schreibt hierher. | nein (außer kleinen Dateien, s. u.), siehe `.gitignore` |
| `reconstruction/` | nur noch die gesicherten Nachbauten vom Oktober 2026; die Skripte sind gelöscht (siehe unten) | nein |
| `interim/` | Abgeleitet, in QGIS oder per Skript. Eingabe für spätere Schritte. | CSVs ja, Geodaten größtenteils nein |

**Alle Dateien je Zelle sind zeilengleich mit dem Raster** `interim/grid/grid_morocco_clear.shp`. Zeile `i` gehört zu Zelle `i`, es gibt keine ID-Spalte. Nicht sortieren und nicht filtern.

---

## raw/

| Datei | Quelle | Spalten | Lokal |
|---|---|---|---|
| `osm/gis_osm_{landuse_a,roads,railways}_free_1.shp` | OpenStreetMap über Geofabrik, Stand 29.01.2025 (aus `General/04_Recherche/QGIS/morocco-latest-free.shp.zip`); Lizenz ODbL, siehe `osm/README` | `fclass` | ✓ |
| `globcover/mar_gc_adg/mar_gc_adg.shp` | FAO GlobCover Marokko (Download 19.10.2026): https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5 | `GRIDCODE` | ✓ (Legenden-.xls im Repo) |
| `globcover/wsa_gc_adg/wsa_gc_adg.shp` | FAO GlobCover Westsahara (Download 19.10.2026): https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2 | `GRIDCODE` | ✓ (Legenden-.xls im Repo) |
| `boundaries/morocco_Morocco_Country_Boundary.shp` | `General/04_Recherche/QGIS/Marokko karte vollständig/Morocco Country Boundary.shp.zip` | – | ✓ |
| `boundaries/morocco.geojson` | Kernmarokko, `General/04_Recherche/QGIS/Datein/Daten/morocco.geojson` | – | ✓ |
| `boundaries/Regions.shp` | **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026). 12 Regionen mit Bevölkerungsspalten (`Population`, `Nb_Menages`, …). Bis dahin genutzter Ersatz aus https://github.com/Salah-Zkara/Morocco-GeoJson (früher `rebuild_regions.py`, siehe unten) liegt in `reconstruction/ersetzt_2026-11-05/`. | `Nom_Region` | ✓ (Original) |
| `boundaries/conflict_area.shp` | **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026). Gebiet östlich des Berms nach Marsili (2024), EPSG:4326. Die Rekonstruktion aus dem früheren `rebuild_conflict_area.py` liegt in `reconstruction/ersetzt_2026-11-05/`. | – | ✓ (Original) |
| `groundwater/Morocco_HG.shp` | BGS Africa Groundwater Atlas, `General/04_Recherche/QGIS/Datein/Daten/Morocco/` | `MorHGComb` | ✓ |
| `groundwater/WesternSahara_HG.shp` | BGS Africa Groundwater Atlas (Download 19.10.2026): https://africagroundwateratlas.org/downloads/WSahara.zip | `WSHGComb` | ✓ |
| `hydrology/watershead_morocco.shp` | **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026). 9 Einzugsgebiete, EPSG:32629. Entstanden aus GADM-1.0-Provinzgruppen, siehe das frühere `rebuild_watershead.py` (unten); der Nachbau weicht nur um 2·10⁻⁹ der Fläche ab und liegt in `reconstruction/ersetzt_2026-11-05/`. | `name` | ✓ (Original) |
| `hydrology/flow_direction_morocco.tif` (+ `.aux.xml`) | **Original** (Sciebo `…/Cost_analysis/Data/Data/`, übernommen 05.11.2026). 1,5 GB, 83 m, EPSG:32629. MERIT Hydro, Produkt `dir` (D8-Fließrichtung: 1, 2, 4, …, 128; 0 Mündung, 247 Ozean, 255 Senke), aus den Kacheln `dir_n30w030`/`dir_n00w030` (Sciebo `QGIS/Daten/`). Vom Code nicht gelesen; Quelle von `interim/qgis/flow_direction_grid.shp`, Zonensumme nachgerechnet (7.216/7.219 Zellen auf ±1 gleich). | Werte 0–255 | ✓ (Original) |
| `climate/{Precipitation,PET}_morocco_2050_corr.shp` | CMIP6, SSP2-4.5, nach Gumus et al. (2024), https://doi.org/10.1016/j.jenvman.2024.122019. **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026). Klassen-Polygone (20 bzw. 17), vermutlich aus den Karten des Papers digitalisiert. | `Precipitat`, `PET` | ✓ (Original) |
| `infrastructure/industrial_ports_morocco_{2025,2050}.shp` | von Hand erstellt | – | ✓ (im Repo) |
| `renewables/PV_WIND_50_Punkte.xlsx` | je 50 repräsentative PV- und Wind-Standorte, von Hand gewählt | `Latitude`, `Longitude` | ✓ (im Repo) |
| `renewables_ninja/pv_wind_electricity.csv` | renewables.ninja API (https://www.renewables.ninja/api/), Jahr 2019, PV MERRA-2 (35°, Süd, 10 % Verluste) und Wind Vestas V136 3450 in 150 m, je 1 kW. Geladen mit `Cost_analysis/01_re_data.py` (Token in `.env`). **Altbestand aus dem Masterprojekt:** `01` reproduziert ihn nicht (Fehlerprotokoll Nr. 10), und die Zuordnung der Profile zu den Orten ist unklar (Nr. 41). Bis 05.11.2026 in `interim/re_profiles/`. | `electricity_{PV,Wind}_0…49`, 8760 Zeilen | ✓ (im Repo) |
| `origin_unknown/` | **Herkunft unbekannt:** `Wind_pot_morocco_FLH.shp`, `morocco_coast_line.shp`, `cell_flh_re.csv`. Originale aus dem Masterprojekt (Sciebo), damals in QGIS erzeugt; Ausgangsdaten und Rechenweg fehlen, kein Skript kann sie erzeugen. Bis 05.11.2026 lagen sie in `interim/qgis/`. Details und Fehlerprotokoll-Verweise in `origin_unknown/README.md`. | `FLH_wind`; –; `FLH_PV`, `FLH_Wind` | ✓ (Original, `cell_flh_re.csv` im Repo) |
| `era5/era5_morocco_2019_{01..12}.nc` | Copernicus CDS, „ERA5 hourly data on single levels“, Jahr 2019, geladen mit `Cost_analysis/00_era5_download.py` (braucht `CDS_API_KEY`). Derzeit von keinem Rechenschritt gelesen, bleibt für eine spätere Profilberechnung. | 10 Variablen (Strahlung, Temperatur, Wind 10/100 m, Rauigkeit) | ✓ |

Gelöscht am 05.11.2026, weil kein Skript sie mehr liest (sie dienten nur den Nachbauten): GADM 1.0 `MAR_adm{0,2}` (in `General/04_Recherche/QGIS/Datein/Daten/MAR_adm/` und Sciebo), `Morocco-Regions.geojson` (https://github.com/Salah-Zkara/Morocco-GeoJson), `PVOUT_Morocco_Complete_Yearly.tif` (`General/04_Recherche/QGIS/`), Global Wind Atlas IEC3 (`https://globalwindatlas.info/api/gis/country/{MAR,ESH}/capacity-factor_IEC3`), `conflict_area_line` und die Klimadaten ohne `_corr` (Sciebo `…/Cost_analysis/Data/Data/`).

Kontrolle GlobCover: Der 2025-Teil von `urban_zone.py` liefert damit dieselben 171 Stadtzellen wie `interim/mca_criteria/results_urban.csv` (max. Abweichung 1·10⁻¹³, Rundung). Es sind also die Originaldaten.

## interim/

| Ordner | Dateien | Erzeugt von |
|---|---|---|
| `grid/` | `grid_morocco.shp` | `MCA/Grid_morocco/grid_morocco.py` |
| | `grid_morocco_clear.shp` | von Hand bereinigte Fassung (7219 Zellen, EPSG:32629). **Zentrales Raster.** |
| `qgis/` | `ToPo_1500.shp` | QGIS, Topografie auf das Raster aggregiert (`NoGo` 0/1). **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026); gleich der Fassung aus Commit `9927be0`, zusätzlich Spalte `Diff` (vom Code nicht gelesen). |
| | `flow_direction_grid.shp` | **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026): `_sum` je Rasterzelle = QGIS-Zonensumme von `raw/hydrology/flow_direction_morocco.tif`. **Achtung:** Das sind summierte D8-Fließrichtungs-Codes, keine Fließakkumulation (Fehlerprotokoll Nr. 110). Die Rückrechnung aus dem früheren `rebuild_flow_direction_grid.py` liegt in `reconstruction/ersetzt_2026-11-05/`; sie passt nur zum rekonstruierten `watershead_morocco`. |
| | `PV_yeald_clear_ma_we.shp` | **Original** (Sciebo `…/Data/Data/Morocco_GISdata_LTAy_YearlyMonthlyTotals_GlobalSolarAtlas-v2_GEOTIFF/`, übernommen 05.11.2026): Global Solar Atlas v2, PV-Jahresertrag. Der Ersatz aus dem früheren `rebuild_pv_wind.py` liegt in `reconstruction/ersetzt_2026-11-05/`. |
| `landuse/` | `morocco_landuse_2050.shp` | `MCA/forecast_landuse.py`. **Original** aus Sciebo (übernommen 05.11.2026); `forecast_landuse.py` erzeugt mit dem Original-`Regions.shp` dieselbe Geometrie und dieselben Werte. |
| `water/` | `water_availability_{sw,gw}.csv` | `MCA/water_exploitable_{sw,gw}.py` |
| | `Water_Consumption_{2025,2050}.csv` | `MCA/water_consumption.py` |
| | `cwb.shp` | `MCA/water_forecast.py`. **Original** (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`, übernommen 05.11.2026); identisch mit dem, was `water_forecast.py` aus den Klimadaten erzeugt. |
| `water_cost/` | `water_availability_{sw,gw}{,_2050}.csv` | eigene, ältere Fassung der Kostenanalyse. **Weicht von `water/` ab.** Die 2050-Dateien lassen sich mit dem aktuellen Code nicht neu erzeugen (Commit `0ff553c`, Korrekturplan F-22). |
| `mca_criteria/` | `results_*.csv` (14 Kriterien-Dateien) | MCA-Kriterienskripte, Eingabe für `MCA/mca_maps.py` |
| `re_profiles/` | `flh_re.csv` | `Cost_analysis/01b_flh_re.py` (aus `raw/renewables_ninja/pv_wind_electricity.csv`) |
| | `FLH_electrolyzer.csv` | `Cost_analysis/FLH_el.py` |
| | `data_re_flh_electrolyzer.shp` | `Cost_analysis/assignment_re_data.py` |

## reconstruction/

Hier lagen bis 05.11.2026 die Skripte `rebuild_watershead.py`, `rebuild_flow_direction_grid.py`, `rebuild_regions.py`, `rebuild_conflict_area.py` und `rebuild_pv_wind.py`. Sie bauten verlorene Eingabedateien nach oder ersetzten sie durch frei verfügbare Daten. Seit die Originale aus Sciebo vorliegen (siehe unten), sind sie überflüssig und **gelöscht**. Letzter Stand in der Git-Historie: Commit `71be5b8` (`git show 71be5b8:data/reconstruction/rebuild_regions.py`).

Die damit erzeugten Nachbauten liegen in `reconstruction/ersetzt_2026-11-05/` (gleiche Unterordner wie in `data/`, gitignored).

### Frühere Kontrolle der Nachbauten (19.10.2026, nur noch historisch)

| Datei | Prüfung | Ergebnis |
|---|---|---|
| `watershead_morocco` | `water_exploitable_gw.py` (mit `WesternSahara_HG`) gegen `water_availability_gw.csv`; außerdem das alte `MCA/water_exploitable.shp` aus Commit `1c71831` nachgerechnet | max. Abweichung 4·10⁻⁸, also exakt |
| `flow_direction_grid` | `water_exploitable_sw.py` gegen `water_availability_sw.csv` | max. Abweichung 1·10⁻¹⁴, also exakt. Gegen die EPS-Karte: 95 % der Zellen treffen den Farbwert auf ±1 Stufe, nur die `sahara`-Zellen liegen um etwa 4,5 % daneben (Zuordnung der Randzellen zu den Grenzsplittern war damals leicht anders) |
| `Regions` | `forecast_landuse.py` + Stadtanteil 2050 gegen `results_urban_2050.csv` | dieselben 194 Stadtzellen, Summe −0,06 %, größte Abweichung je Zelle 2,3 Prozentpunkte (geoBoundaries: +0,5 % bzw. 9,4 Punkte; HDX hat nur 10 Regionen) |
| `conflict_area` | `non_conflict.py` gegen `results_non_conflict_areas.csv` | 1 von 874 Konfliktzellen abweichend; Rangskala der Zwischenzellen im Median 0,7 Punkte daneben (95 %: ≤ 6,5) |
| `PV_yeald_clear_ma_we` | `pv_analysis.py` gegen `results_pv_yeald.csv` | Korrelation 0,99995, Median-Abweichung 0,03 %, max. 8,9 kWh/kWp |
| `Wind_pot_morocco_FLH` | `wind_analysis.py` gegen `results_wind_flh.csv` | Korrelation 0,981 (Rang 0,986); Werte im Mittel etwa 15 % niedriger. Für die MCA unkritisch, weil `mca_maps.py` min-max-skaliert |

### Originale aus Sciebo (05.11.2026)

Die verlorenen Originale lagen im Sciebo-Ordner `H2 Morocco/Masterprojekt/Python/` (`Cost_analysis/Data/Data/`, weitgehend gleich in `MCA/Data/`). Sie wurden übernommen, die Nachbauten nach `reconstruction/ersetzt_2026-11-05/` verschoben (gleiche Unterordner). Geprüft wurde, indem die Original-Skripte in einer Kopie des Repos mit den Sciebo-Dateien liefen und ihre Ausgaben mit den getrackten Ergebnis-CSVs verglichen wurden (alle 7219 Zellen):

| Datei(en) | Prüfung | Ergebnis |
|---|---|---|
| `climate/{Precipitation,PET}_morocco_2050_corr` + `morocco_coast_line` | `water_forecast.py` gegen `results_water_res_availabil_2050.csv` | exakt (max. 2·10⁻¹³). Mit der rekonstruierten Küstenlinie wich 1 Zelle um 12,6 Punkte ab |
| `cwb` | gegen die von `water_forecast.py` neu erzeugte `cwb.shp` | gleiche 52 Polygone und Werte |
| `morocco_coast_line` | `water_net.py` gegen `results_water_res_available.csv` | exakt |
| `conflict_area` | `non_conflict.py` gegen `results_non_conflict_areas.csv` | exakt, dieselben 874 Nullzellen |
| `flow_direction_grid` + `watershead_morocco` | `water_exploitable_sw.py` gegen `water_availability_sw.csv` | exakt. Das Original-`flow_direction_grid` mit dem rekonstruierten `watershead_morocco` dagegen nicht (max. 0,16 MCM) |
| `watershead_morocco` | `water_exploitable_gw.py` gegen `water_availability_gw.csv` | exakt (2·10⁻¹³) |
| `Regions` | `forecast_landuse.py`, dann `urban_zone.py`, `rural_zone.py`, `agriculture.py` gegen die sechs CSVs 2025/2050 | alle exakt (≤ 7·10⁻¹³); Landnutzung 2050 gleich dem Sciebo-Original |
| `PV_yeald_clear_ma_we` | `pv_analysis.py` gegen `results_pv_yeald.csv` | exakt |
| `Wind_pot_morocco_FLH` | `wind_analysis.py` gegen `results_wind_flh.csv` | exakt |
| `ToPo_1500` | Geometrie und Spalten gegen die Fassung aus Commit `9927be0` | gleich (plus Spalte `Diff`) |
