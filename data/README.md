# Daten

Alle Eingangs- und Zwischendaten von MCA und Kostenanalyse liegen in diesem Ordner. Ergebnisse und Abbildungen liegen in `../results/`.

| Ordner | Inhalt | Im Repo? |
|---|---|---|
| `raw/` | Eingabedaten: heruntergeladen, von Hand erstellt oder Altdaten ohne bekannten Rechenweg (`raw/origin_unknown/`). Nur Dateien, die ein aktives Skript liest (Ausnahme: ERA5). Schreiben dürfen hier nur die Download-Skripte `00_era5_download.py` und `01_re_data.py`. | nein, außer kleinen Dateien (siehe Tabelle), `.gitignore` |
| `interim/` | Zwischenergebnisse. **Jede Datei erzeugt ein Skript**; der Ordner lässt sich löschen und mit `main.ipynb` neu erzeugen. | nein |
| `model_parameters/` | Annahmen der Kostenrechnung | ja |

**Alle Dateien je Zelle sind zeilengleich mit dem Raster** `interim/grid/grid_morocco_clear.shp`. Zeile `i` gehört zu Zelle `i`, es gibt keine ID-Spalte. Nicht sortieren und nicht filtern.

---

## raw/

| Datei | Quelle | Spalten | Im Repo |
|---|---|---|---|
| `osm/gis_osm_{landuse_a,roads,railways}_free_1.shp` | OpenStreetMap über Geofabrik, Stand 29.01.2025 (aus `General/04_Recherche/QGIS/morocco-latest-free.shp.zip`); Lizenz ODbL, siehe `osm/README` | `fclass` | nein |
| `globcover/{mar,wsa}_gc_adg/*.shp` | FAO GlobCover Marokko und Westsahara (Download 19.10.2026): https://data.apps.fao.org/catalog/dataset/fad3f475-8973-463f-b56a-e6b6535c1db5, https://data.apps.fao.org/catalog/iso/75aaf5c5-d579-425a-97fb-aa4580536df2 | `GRIDCODE` | nur Legenden-.xls |
| `gmia/gmia_v5_{aei_ha,aai_pct_aei}.asc` | FAO Global Map of Irrigation Areas v5 (Siebert et al. 2013, Universität Bonn / FAO), Download 05.11.2026 von https://www.fao.org/aquastat/en/geospatial-information/global-maps-irrigated-areas/latest-version; 5′, EPSG:4326, Datenstand etwa 2005. Lizenz laut FAO-Katalog CC BY-NC-SA 3.0 IGO (auf der Downloadseite nicht angegeben): nicht kommerziell. | ausgerüstete Fläche [ha], davon tatsächlich bewässert [%], NoData −9 | nein |
| `boundaries/morocco_Morocco_Country_Boundary.shp` | `General/04_Recherche/QGIS/Marokko karte vollständig/Morocco Country Boundary.shp.zip` | – | nein |
| `boundaries/morocco.geojson` | Kernmarokko, `General/04_Recherche/QGIS/Datein/Daten/morocco.geojson` | – | nein |
| `boundaries/Regions.shp` | 12 Verwaltungsregionen mit Bevölkerungsspalten; Original aus dem Masterprojekt (Sciebo `H2 Morocco/Masterprojekt/Python/Cost_analysis/Data/Data/`) | `Nom_Region` | nein |
| `boundaries/conflict_area.shp` | Gebiet östlich des Berms nach Marsili (2024), von Hand digitalisiert; Original aus Sciebo (wie oben) | – | nein |
| `groundwater/{Morocco,WesternSahara}_HG.shp` | BGS Africa Groundwater Atlas; Marokko aus `General/04_Recherche/QGIS/Datein/Daten/Morocco/`, Westsahara https://africagroundwateratlas.org/downloads/WSahara.zip (Download 19.10.2026) | `MorHGComb`, `WSHGComb` | nein |
| `hydrology/watershead_morocco.shp` | 9 Einzugsgebiete aus GADM-1.0-Provinzgruppen (Rezept: Commit `ed25684`, `water_exploitable2.py`); Original aus Sciebo | `name` | nein |
| `hydrology/flow_direction_morocco.tif` | MERIT Hydro, Produkt `dir` (Yamazaki et al. 2019), 83 m, EPSG:32629, aus den Kacheln `dir_n30w030`/`dir_n00w030`; Original aus Sciebo. **D8-Fließrichtungs-Codes** (1, 2, 4, …, 128; 0 Mündung, 247 Ozean, 255 Senke), keine Fließakkumulation (Fehlerprotokoll Nr. 110). 1,5 GB. | Werte 0–255 | nein |
| `hydrology/merit_hydro_upa/{n20w020,n20w015,n25w015,n25w010,n30w010,n30w005,n35w010,n35w005}_upa.tif` | MERIT Hydro v1.0.1, Variable `upa` (Einzugsfläche je Pixel = Fließakkumulation), 3″, EPSG:4326; Yamazaki et al. (2019), https://doi.org/10.1029/2019WR024873. Download nach Registrierung (https://global-hydrodynamics.github.io/MERIT_Hydro/) aus den Paketen `upa_n30w030.tar` und `upa_n00w030.tar`, 05.11.2026. **Lizenz CC BY-NC 4.0: nicht kommerziell, Rohdaten nicht weitergeben** (Fehlerprotokoll Nr. 112). Noch von keinem Skript gelesen; soll `flow_direction_morocco.tif` ersetzen (Nr. 110). | upa [km²], NoData −9999 | nein |
| `climate/{Precipitation,PET}_morocco_2050_corr.shp` | CMIP6, SSP2-4.5, nach Gumus et al. (2024), https://doi.org/10.1016/j.jenvman.2024.122019; Klassen-Polygone, vermutlich aus den Karten des Papers digitalisiert; Original aus Sciebo | `Precipitat`, `PET` | nein |
| `dem/copernicus_dem_glo90/*.tif` | Copernicus DEM GLO-90 (3″), 100 Kacheln, https://copernicus-dem-90m.s3.amazonaws.com/, Copernicus-DEM-Lizenz (frei mit Quellenangabe), Abruf 28.10.2026 | Höhe [m] | nein |
| `renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif` | Global Solar Atlas v2, PV-Jahresertrag Marokko + Westsahara, 30″; aus `General/04_Recherche/QGIS/` (gleich in Sciebo) | PVOUT [kWh/kWp/a] | nein |
| `renewables/gwa/{MAR,ESH}_capacity-factor_IEC3.tif` | Global Wind Atlas v3, Kapazitätsfaktor IEC-Klasse III, 250 m, EPSG:4326; `https://globalwindatlas.info/api/gis/country/{MAR,ESH}/capacity-factor_IEC3`, Abruf 05.11.2026. Klasse III ist eine Annahme (passt zur Referenzturbine Vestas V136-3.45), das Paper nennt keine. | Kapazitätsfaktor [–] | nein |
| `renewables/PV_WIND_50_Punkte.xlsx` | je 50 repräsentative PV- und Wind-Standorte, von Hand gewählt | `Latitude`, `Longitude` | ja |
| `renewables_ninja/pv_wind_electricity.csv` | renewables.ninja API (https://www.renewables.ninja/api/), Jahr 2019, PV MERRA-2 (35°, Süd, 10 % Verluste) und Wind Vestas V136 3450 in 150 m, je 1 kW; geladen mit `Cost_analysis/01_re_data.py`. **Altbestand:** `01` reproduziert ihn nicht (Fehlerprotokoll Nr. 10), die Zuordnung der Profile zu den Orten ist unklar (Nr. 41). | `electricity_{PV,Wind}_i`, 8760 Zeilen | ja |
| `infrastructure/industrial_ports_morocco_{2025,2050}.shp` | von Hand erstellt | – | ja |
| `era5/era5_morocco_2019_{01..12}.nc` | Copernicus CDS, „ERA5 hourly data on single levels“, 2019, geladen mit `Cost_analysis/00_era5_download.py` (braucht `CDS_API_KEY`). Derzeit von keinem Rechenschritt gelesen, bleibt für eine spätere Profilberechnung. | 10 Variablen | nein |
| `origin_unknown/morocco_coast_line.shp` | **Herkunft unbekannt:** QGIS-Ergebnis aus dem Masterprojekt (Sciebo), das Paper nennt keine Quelle. Details in `origin_unknown/README.md`. | – | nein |

## interim/

| Datei | Erzeugt von | Aus |
|---|---|---|
| `grid/grid_morocco.shp` | `MCA/Grid_morocco/grid_morocco.py` | Landesgrenze: 10-km-Quadrate, die sie schneiden |
| `grid/grid_morocco_clear.shp` | `MCA/Grid_morocco/grid_morocco.py` | dieselben Zellen, auf die Landesgrenze zugeschnitten. **Zentrales Raster** (7219 Zellen, EPSG:32629) |
| `layers/flow_direction_grid.shp` | `MCA/ki_generiert/flow_direction_grid.py` | `raw/hydrology/flow_direction_morocco.tif`, Summe je Zelle (Fehlerprotokoll Nr. 110) |
| `layers/PV_yeald_clear_ma_we.shp` | `MCA/ki_generiert/pv_yield_polygons.py` | `raw/renewables/gsa/PVOUT_Morocco_Complete_Yearly.tif`, gerundet und polygonisiert |
| `layers/Wind_pot_morocco_FLH.shp` | `MCA/ki_generiert/wind_flh_grid.py` | `raw/renewables/gwa/`, Kapazitätsfaktor × 8.760 h je Zelle |
| `layers/ToPo_1500.shp` | `MCA/ki_generiert/topography_grid.py` | `raw/dem/copernicus_dem_glo90/`, Höhenspanne je Zelle, `NoGo = 0` ab 1.500 m |
| `landuse/morocco_landuse_2050.shp` | `MCA/forecast_landuse.py` | GlobCover + `Regions` |
| `water/water_availability_{sw,gw}.csv` | `MCA/water_exploitable_{sw,gw}.py` | Einzugsgebiete, Fließrichtung, Grundwasser |
| `water/irrigated_area_gmia.csv` | `MCA/ki_generiert/irrigation_grid.py` | `raw/gmia/`, tatsächlich bewässerte Fläche [ha] je Zelle, flächenanteilig |
| `water/Water_Consumption_{2025,2050}.csv` | `MCA/water_consumption.py` | Stadt (GlobCover), Bewässerung (GMIA), Industrie (OSM) |
| `water/cwb.shp`, `water/water_availability_{sw,gw}_2050.csv` | `MCA/water_forecast.py` | Klimadaten 2050 |
| `mca_criteria/results_*.csv` (14) | MCA-Kriterienskripte | Eingabe für `MCA/mca_maps.py` |
| `re_profiles/flh_re.csv` | `Cost_analysis/ki_generiert/01b_flh_re.py` | `raw/renewables_ninja/pv_wind_electricity.csv` |
| `re_profiles/cell_flh_re.csv` | `Cost_analysis/ki_generiert/01c_cell_flh_re.py` | PV- und Wind-Kriterium der MCA (`mca_criteria/results_{pv_yeald,wind_flh}.csv`) |
| `re_profiles/FLH_electrolyzer_{2025,2050}.csv` | `Cost_analysis/02_FLH_el.py` (Gurobi) | Profile; Auslegung je Szenariojahr |
| `re_profiles/data_re_flh_electrolyzer_{2025,2050}.shp` | `Cost_analysis/03_assignment_re_data.py` | `FLH_electrolyzer_{2025,2050}.csv` + Standorte |

`layers/` enthält aufbereitete räumliche Layer. Bis 05.11.2026 hieß der Ordner `qgis/`, weil die Dateien früher in QGIS entstanden.

---

## Herkunft und Prüfung (Stand 05.11.2026)

**Originale aus Sciebo.** Bis Oktober 2026 fehlten mehrere Eingaben und wurden nachgebaut oder ersetzt (Skripte `data/reconstruction/rebuild_*.py`, letzter Stand Commit `71be5b8`). Am 05.11.2026 fanden sich die Originale im Sciebo-Ordner `H2 Morocco/Masterprojekt/Python/` (`Cost_analysis/Data/Data/`, weitgehend gleich in `MCA/Data/`). Mit ihnen reproduzieren die Skripte die veröffentlichten Kriterien-CSVs (Stand `65f7775`) exakt: Klimadaten 2050 und Küstenlinie (Wasser-Score 2025 und 2050), `conflict_area`, `watershead_morocco` + Fließrichtung (Grund- und Oberflächenwasser), `Regions` (Landnutzung 2050, Stadt, Land, Landwirtschaft, Wasserverbrauch 2050), PV- und Wind-Layer. Die Nachbauten und ihre Skripte sind gelöscht.

**Neu nach den Quellen aus dem Paper abgeleitet (05.11.2026).** Wind-Layer und `cell_flh_re.csv` stammten aus QGIS ohne erhaltenen Rechenweg. Das Paper nennt für Wind den Global Wind Atlas und für die Zuordnung der Referenzpunkte PV-Ertrag und Wind-Volllaststunden je Zelle. Beide werden jetzt so erzeugt:
- **Wind:** Kriterium im Mittel 3.754 statt 4.294 h, Korrelation mit dem alten 0,983, Maximum gleich (7.432 h). MCA-Wind ist min-max-skaliert, die Rangfolge bleibt weitgehend erhalten.
- **`cell_flh_re.csv`:** PV wie bisher; die zweite Spalte war `FLH_el` (unbekannte Umrechnung, Mittel 5.429 h) und ist jetzt die Wind-Volllaststunde (Mittel 3.760 h, gleiche Skala wie die Referenzpunkte). Die Zellen verteilen sich auf alle 50 statt 40 Referenzpunkte.
- **Folge für die Kosten:** mittlerer H₂-Preis 2025 144,66 statt 139,36 €/MWh, 2050 79,46 statt 75,36 €/MWh. Fast der ganze Anstieg kommt aus den Netzkosten: 54 % der Zellen beziehen ihren Strom jetzt aus derselben Produktionszelle (vorher höchstens 1,7 %), siehe Fehlerprotokoll Nr. 48.
- **Netzkosten danach überarbeitet (05.11.2026):** HGÜ nach Danish Energy Agency (2025) mit Verlusten, keine Netzkosten bei Eigenversorgung (Fehlerprotokoll Nr. 45, 48, 63). Mittlerer H₂-Preis damit 140,37 €/MWh (2025) und 73,48 €/MWh (2050).
- **Fehlerbehebungen danach (05.11.2026):** Block 1 (PV/Wind-Leistung je MW Elektrolyseur, F-04; PV-OPEX, F-07) und eigene Auslegung für 2050 (Nr. 8): 110,52 €/MWh (2025) und 52,62 €/MWh (2050). Laufordner `results/runs/2026-11-05_1654_8b475c5-dirty_cost`.

**Früher in QGIS, jetzt per Skript.** Abweichungen gegenüber den QGIS-Dateien aus dem Masterprojekt:

| Datei | Abweichung | Folge |
|---|---|---|
| `grid_morocco_clear.shp` | ≤ 0,00001 m² je Zelle (Rundung); die „manuelle Bereinigung“ war genau der Zuschnitt auf die Landesgrenze | Zelle 2483 berührt die Küstenlinie rechnerisch nicht mehr (Abstand 2·10⁻¹² m): Wasser-Score 2025 und 2050 dort 0 statt 100 |
| `flow_direction_grid.shp` | 7.216 von 7.219 Zellen auf ±1 gleich (Randpixel) | Oberflächenwasser höchstens 0,0002 Mio. m³ anders |
| `PV_yeald_clear_ma_we.shp` | keine (gleiche 478.733 Polygone) | PV-Kriterium identisch |
| `ToPo_1500.shp` | alte Quelle unbekannt, jetzt Copernicus DEM: Höhen im Median 2,8 m anders | Topografie-Maske in 3 Zellen anders (121 statt 124 ausgeschlossen) |
| `water_availability_{sw,gw}_2050.csv` | ersetzen `interim/water_cost/` der Kostenanalyse; Block aus Commit `0ff553c` wiederhergestellt | Oberflächenwasser exakt, Grundwasser höchstens 0,0007 Mio. m³ anders |

Kostenmodell `04` mit diesen Dateien gegen den Lauf vom 05.11.2026, 10:55: H₂-Preis im Mittel unverändert; 2025 in 25 Zellen bis 0,41 €/MWh, 2050 in 705 Zellen bis 0,06 €/MWh anders (nur Wasserkosten).

**Gelöscht, weil ungenutzt** (dienten nur den Nachbauten): GADM 1.0 `MAR_adm{0,2}` (`General/04_Recherche/QGIS/Datein/Daten/MAR_adm/`, Sciebo), `Morocco-Regions.geojson` (https://github.com/Salah-Zkara/Morocco-GeoJson), Global Wind Atlas IEC3 (`https://globalwindatlas.info/api/gis/country/{MAR,ESH}/capacity-factor_IEC3`), `conflict_area_line` und die Klimadaten ohne `_corr` (Sciebo).

**Kontrolle GlobCover:** Der 2025-Teil von `urban_zone.py` liefert dieselben 171 Stadtzellen wie das Original. Es sind also die Originaldaten.
