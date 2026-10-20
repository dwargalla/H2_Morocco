# Daten

Alle Eingangs- und Zwischendaten von MCA und Kostenanalyse liegen in diesem Ordner. Ergebnisse und Abbildungen liegen in `../results/`.

| Ordner | Inhalt | Im Repo? |
|---|---|---|
| `raw/` | Extern bezogen oder von Hand erstellt. Schreiben dürfen hier nur die Skripte in `reconstruction/`. | nein (außer kleinen Dateien, s. u.), siehe `.gitignore` |
| `reconstruction/` | Skripte, die verlorene Eingabedateien nachbauen oder ersetzen (siehe unten) | ja |
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
| `boundaries/Regions.shp` | **Ersatz, nicht das Original:** 12 Regionen aus https://github.com/Salah-Zkara/Morocco-GeoJson (`Morocco-Regions.geojson`, Download 19.10.2026), Spalte `nom_region` → `Nom_Region`, Schreibweise an `forecast_landuse.py` angepasst (`Tanger-Tetouan-Al Hoceima`, `Fès-Meknès`). Skript: `reconstruction/rebuild_regions.py`. | `Nom_Region` | ✓ (Ersatz) |
| `boundaries/conflict_area.shp` | **Rekonstruktion, nicht das Original:** Gebiet östlich des Berms nach Marsili (2024), vermutlich von Hand digitalisiert. Nachgebaut als Vereinigung der 874 Zellen, die in `interim/mca_criteria/results_non_conflict_areas.csv` den Wert 0 haben. Natural Earth „W. Sahara“ passt schlechter (988 Zellen). Skript: `reconstruction/rebuild_conflict_area.py`. | – | ✓ (Rekonstruktion) |
| `groundwater/Morocco_HG.shp` | BGS Africa Groundwater Atlas, `General/04_Recherche/QGIS/Datein/Daten/Morocco/` | `MorHGComb` | ✓ |
| `groundwater/WesternSahara_HG.shp` | BGS Africa Groundwater Atlas (Download 19.10.2026): https://africagroundwateratlas.org/downloads/WSahara.zip | `WSHGComb` | ✓ |
| `hydrology/watershead_morocco.shp` | **Exakt rekonstruiert** nach `MCA/water_exploitable2.py` (Commit `ed25684`): 8 Gruppen von GADM-1.0-Provinzen (`MAR_adm2.shp`, `General/04_Recherche/QGIS/Datein/Daten/MAR_adm/`, Spalte `ID_2`) per `dissolve()`, dazu `sahara` = Landesgrenze (`boundaries/morocco_Morocco_Country_Boundary.shp`) minus `MAR_adm0.shp`, inklusive der kleinen Splitter entlang der Grenze. EPSG:32629. Skript: `reconstruction/rebuild_watershead.py`. | `name` | ✓ (Rekonstruktion, exakt) |
| `climate/{Precipitation,PET}_morocco_2050_corr.shp` | CMIP6, SSP2-4.5, nach Gumus et al. (2024), https://doi.org/10.1016/j.jenvman.2024.122019 (Daten bei den Autoren anfragen) | `Precipitat`, `PET` | fehlt |
| `infrastructure/industrial_ports_morocco_{2025,2050}.shp` | von Hand erstellt | – | ✓ (im Repo) |
| `renewables/PV_WIND_50_Punkte.xlsx` | je 50 repräsentative PV- und Wind-Standorte, von Hand gewählt | `Latitude`, `Longitude` | ✓ (im Repo) |
| `boundaries/gadm1/MAR_adm{0,2}.shp` | GADM 1.0 (2009), aus `General/04_Recherche/QGIS/Datein/Daten/MAR_adm/`; Lizenz siehe `MAR_readme.txt`. Quelle für `rebuild_watershead.py` | `ID_2` | ✓ |
| `boundaries/Morocco-Regions.geojson` | https://github.com/Salah-Zkara/Morocco-GeoJson, lädt `rebuild_regions.py` | `nom_region` | ✓ |
| `renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif` | Global Solar Atlas, PV-Jahresertrag Marokko + Westsahara, aus `General/04_Recherche/QGIS/`. Quelle für `rebuild_pv_wind.py` | – | ✓ |
| `renewables/gwa/{MAR,ESH}_capacity-factor_IEC3.tif` | Global Wind Atlas (Download 19.10.2026), lädt `rebuild_pv_wind.py` | – | ✓ |

Kontrolle GlobCover: Der 2025-Teil von `urban_zone.py` liefert damit dieselben 171 Stadtzellen wie `interim/mca_criteria/results_urban.csv` (max. Abweichung 1·10⁻¹³, Rundung). Es sind also die Originaldaten.

## interim/

| Ordner | Dateien | Erzeugt von |
|---|---|---|
| `grid/` | `grid_morocco.shp` | `MCA/Grid_morocco/grid_morocco.py` |
| | `grid_morocco_clear.shp` | von Hand bereinigte Fassung (7219 Zellen, EPSG:32629). **Zentrales Raster.** |
| `qgis/` | `ToPo_1500.shp` | QGIS, Topografie auf das Raster aggregiert (`NoGo` 0/1). Aus Commit `9927be0` wiederhergestellt, Spalte `NoGos` in `NoGo` umbenannt. |
| | `morocco_coast_line.shp` | **Rekonstruktion, nicht das Original:** Landesgrenze, beschnitten auf die 352 Küstenzellen (Wasser-Score 100), plus zwei Platzhalterlinien für die Zellen 5021 und 5151. Trifft exakt dieselben Zellen wie das Original, taugt aber nur eingeschränkt für Karten. |
| | `cell_flh_re.csv` | QGIS (PV/Wind-Volllaststunden je Zelle), kein Skript |
| | `flow_direction_grid.shp` | **Rekonstruktion:** `_sum` je Rasterzelle aus `interim/water/water_availability_sw.csv` zurückgerechnet (Umkehrung von `water_exploitable_sw.py`, 9 Gebietssummen per Ausgleichsrechnung). Den gemeinsamen Faktor liefert die Farbleiste von `General/06_Diagramme_Karten/EPS/morocco_flow_direction.eps` (vmax = 1 091 380). Ursprüngliche Datenquelle unbekannt. Skript: `reconstruction/rebuild_flow_direction_grid.py`. |
| | `PV_yeald_clear_ma_we.shp` | **Ersatz, nicht das Original:** ein Polygon je Rasterzelle (um 1 m nach innen gepuffert) mit dem Mittel aller Pixel aus `General/04_Recherche/QGIS/PVOUT_Morocco_Complete_Yearly.tif` (Global Solar Atlas, Marokko + Westsahara), die die Zelle berühren. Skript: `reconstruction/rebuild_pv_wind.py`. |
| | `Wind_pot_morocco_FLH.shp` | **Ersatz, nicht das Original:** ein Polygon je Rasterzelle (um 1 m nach innen gepuffert) mit `FLH_wind` = Capacity Factor IEC3 × 8760 h, gemittelt über die Pixel. Daten: Global Wind Atlas, `https://globalwindatlas.info/api/gis/country/{MAR,ESH}/capacity-factor_IEC3` (Download 19.10.2026). Das Original lag unter `Wind_Energiedichte/wind_yeald/`, Rechenweg unbekannt. Skript: `reconstruction/rebuild_pv_wind.py`. |
| `landuse/` | `morocco_landuse_2050.shp` | `MCA/forecast_landuse.py` (mit dem Ersatz-`Regions.shp` erzeugt) |
| `water/` | `water_availability_{sw,gw}.csv` | `MCA/water_exploitable_{sw,gw}.py` |
| | `Water_Consumption_{2025,2050}.csv` | `MCA/water_consumption.py` |
| | `cwb.shp` (fehlt) | `MCA/water_forecast.py` |
| `water_cost/` | `water_availability_{sw,gw}{,_2050}.csv` | eigene, ältere Fassung der Kostenanalyse. **Weicht von `water/` ab.** Die 2050-Dateien lassen sich mit dem aktuellen Code nicht neu erzeugen (Commit `0ff553c`, Korrekturplan F-22). |
| `mca_criteria/` | `results_*.csv` (14 Kriterien-Dateien) | MCA-Kriterienskripte, Eingabe für `MCA/mca_maps.py` |
| `re_profiles/` | `pv_wind_electricity.csv`, `flh_re.csv` | `Cost_analysis/re_data.py` |
| | `FLH_electrolyzer.csv` | `Cost_analysis/FLH_el.py` |
| | `data_re_flh_electrolyzer.shp` | `Cost_analysis/assignment_re_data.py` |

## reconstruction/

Baut verlorene Eingabedateien nach (Rekonstruktion) oder ersetzt sie durch frei verfügbare Daten (Ersatz). Ausführen aus `data/reconstruction/`, in dieser Reihenfolge:

```bash
python rebuild_watershead.py           # -> raw/hydrology/watershead_morocco.shp
python rebuild_flow_direction_grid.py  # -> interim/qgis/flow_direction_grid.shp (braucht watershead_morocco)
python rebuild_regions.py              # -> raw/boundaries/Regions.shp
python rebuild_conflict_area.py        # -> raw/boundaries/conflict_area.shp
python rebuild_pv_wind.py              # -> interim/qgis/PV_yeald_clear_ma_we.shp, Wind_pot_morocco_FLH.shp
```

`rebuild_flow_direction_grid.py` und `rebuild_conflict_area.py` rechnen aus den getrackten Ergebnis-CSVs zurück. Sie ersetzen also keine Originaldaten, sondern machen die Pipeline wieder lauffähig und die Karten zeichenbar.

Kontrolle der wiederhergestellten Dateien: `water_net.py`, `no_go_zones.py` und `mca_maps.py` reproduzieren damit die vorhandenen Ergebnis-CSVs wertgleich.

### Kontrolle der Rekonstruktionen (19.10.2026)

| Datei | Prüfung | Ergebnis |
|---|---|---|
| `watershead_morocco` | `water_exploitable_gw.py` (mit `WesternSahara_HG`) gegen `water_availability_gw.csv`; außerdem das alte `MCA/water_exploitable.shp` aus Commit `1c71831` nachgerechnet | max. Abweichung 4·10⁻⁸, also exakt |
| `flow_direction_grid` | `water_exploitable_sw.py` gegen `water_availability_sw.csv` | max. Abweichung 1·10⁻¹⁴, also exakt. Gegen die EPS-Karte: 95 % der Zellen treffen den Farbwert auf ±1 Stufe, nur die `sahara`-Zellen liegen um etwa 4,5 % daneben (Zuordnung der Randzellen zu den Grenzsplittern war damals leicht anders) |
| `Regions` | `forecast_landuse.py` + Stadtanteil 2050 gegen `results_urban_2050.csv` | dieselben 194 Stadtzellen, Summe −0,06 %, größte Abweichung je Zelle 2,3 Prozentpunkte (geoBoundaries: +0,5 % bzw. 9,4 Punkte; HDX hat nur 10 Regionen) |
| `conflict_area` | `non_conflict.py` gegen `results_non_conflict_areas.csv` | 1 von 874 Konfliktzellen abweichend; Rangskala der Zwischenzellen im Median 0,7 Punkte daneben (95 %: ≤ 6,5) |
| `PV_yeald_clear_ma_we` | `pv_analysis.py` gegen `results_pv_yeald.csv` | Korrelation 0,99995, Median-Abweichung 0,03 %, max. 8,9 kWh/kWp |
| `Wind_pot_morocco_FLH` | `wind_analysis.py` gegen `results_wind_flh.csv` | Korrelation 0,981 (Rang 0,986); Werte im Mittel etwa 15 % niedriger. Für die MCA unkritisch, weil `mca_maps.py` min-max-skaliert |

Nicht beschaffbar: `climate/{Precipitation,PET}_morocco_2050_corr.shp` (Gumus et al. 2024, Daten nur auf Anfrage; die Endung `_corr` deutet auf abdigitalisierte Karten hin) und damit `interim/water/cwb.shp`.
