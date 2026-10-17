# H2 Morocco – Standortanalyse für grünen Wasserstoff

Räumliche Analyse, **wo in Marokko grüner Wasserstoff (H2) für 2025 und 2050 am sinnvollsten und am günstigsten produziert werden kann**. Entstanden als Masterprojekt (TH Köln).

Marokko (inklusive Westsahara) wird dafür in ein Raster aus **7219 Zellen à 10 × 10 km** zerlegt. Für jede Zelle werden zwei voneinander unabhängige Kennzahlen berechnet:

| Analyse | Ordner | Ergebnis je Zelle | Frage |
|---|---|---|---|
| **Multikriterienanalyse (MCA)** | `MCA/` | Eignungs-Score 0–100 | Wie *geeignet* ist der Standort (Ressourcen, Wasser, Infrastruktur, Flächenkonkurrenz, Stabilität)? |
| **Kostenanalyse** | `Cost_analysis/` | Wasserstoffkosten in €/MWh_H2 | Was *kostet* Wasserstoff, der an diesem Ort benötigt wird, inklusive Strom, Elektrolyse, Netz, Pipeline und Wasser? |

Beide Analysen werden jeweils für **2025** und **2050** gerechnet.

---

## Inhalt

- [Projektstruktur](#projektstruktur)
- [Setup](#setup)
- [Grundprinzip: das Raster](#grundprinzip-das-raster)
- [Teil 1: Multikriterienanalyse (MCA)](#teil-1-multikriterienanalyse-mca)
- [Teil 2: Kostenanalyse](#teil-2-kostenanalyse)
- [Ergebnisse reproduzieren](#ergebnisse-reproduzieren)
- [Eingangsdaten](#eingangsdaten)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)

---

## Projektstruktur

```
H2_Morocco/
├── MCA/
│   ├── Grid_morocco/         Rastererzeugung + grid_morocco_clear.shp (zentrales Raster)
│   ├── Data/                 Eingangsdaten (GIS größtenteils nicht im Repo) + Wasser-CSVs
│   ├── results/              ein CSV je Kriterium + Endergebnis results_mca_morocco_2025_2050.csv
│   ├── Maps/                 erzeugte Karten (nicht im Repo)
│   ├── custom.py             Hilfsfunktion list_index() für Zell-Verschneidungen
│   ├── *.py                  Kriterien-, Wasser- und Kartenskripte (siehe unten)
│   └── old/                  veraltete Skripte
├── Cost_analysis/
│   ├── Data/                 Eingaben + Ergebnisse der Kostenanalyse
│   ├── Maps/                 erzeugte Karten und Diagramme
│   ├── *.py                  Pipeline der Kostenanalyse (siehe unten)
│   └── 01_old/               veraltete Skripte
└── requirements.txt
```

---

## Setup

Benötigt wird Python ≥ 3.10.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

- `FLH_el.py` braucht zusätzlich eine **Gurobi-Lizenz** (für Hochschulen kostenlos).
- `re_data.py` braucht einen **API-Token von [renewables.ninja](https://www.renewables.ninja/api/)**. Er wird aus `.env` gelesen: `cp .env.example .env` und `RENEWABLES_NINJA_TOKEN` eintragen. `.env` ist per `.gitignore` vom Repo ausgeschlossen.

**Wichtig:** Alle Skripte verwenden relative Pfade und müssen **aus ihrem eigenen Ordner** gestartet werden:

```bash
cd MCA && python mca_maps.py
cd Cost_analysis && python cost_analysis_h2_morocco.py
```

---

## Grundprinzip: das Raster

`MCA/Grid_morocco/grid_morocco_clear.shp` (Kopie in `Cost_analysis/Data/`) ist das Rückgrat des Projekts:

- 7219 quadratische Zellen à 10 km, Koordinatensystem **EPSG:32629 (UTM 29N)**, alle Längen in m, alle Flächen in m².
- `grid_morocco.py` erzeugt das Rohraster; `grid_morocco_clear.shp` ist eine manuell bereinigte Fassung.

**Alle Zwischenergebnisse sind über die Zeilennummer mit dem Raster verknüpft.** Zeile `i` in jeder CSV in `results/` oder `Data/` gehört zu Zelle `i` im Raster. Es gibt keine ID-Spalte. Wer eine Zwischen-CSV sortiert oder filtert, verschiebt alle Werte, ohne dass ein Fehler auftritt.

Die meisten Kriterien-Skripte gehen alle Zellen in einer Schleife durch und verschneiden sie mit den Geodaten (`custom.list_index`). Deshalb laufen sie teils lange.

---

## Teil 1: Multikriterienanalyse (MCA)

### Idee

Jede Zelle bekommt für neun Kriterien einen Wert, der auf 0–100 skaliert wird. Daraus wird eine gewichtete Summe gebildet. Zum Schluss wird sie mit einer No-Go-Maske (0/1) multipliziert, sodass Ausschlussgebiete den Score 0 erhalten.

```
Score(Zelle) = NoGo(Zelle) × Σ  Gewicht_k × Kriterium_k(Zelle)
```

### Kriterien und Gewichte

Die Gewichte stehen in `MCA/mca_maps.py` als `dict_weights_category`.

| Kriterium | Gewicht | Skript | Was berechnet wird | Richtung |
|---|---|---|---|---|
| Wasserverfügbarkeit | 34,06 % | `water_net.py` / `water_forecast.py` | siehe [Wasser](#wasser) | hoch = gut |
| Nicht-Konfliktgebiet | 16,30 % | `non_conflict.py` | Verhältnis der Abstände zur Westsahara und zu Kernmarokko, rangskaliert | hoch = gut |
| Industrieflächenanteil | 14,46 % | `industrie.py` | Anteil OSM-Industriefläche an der Zelle | hoch = gut |
| Windertrag | 12,37 % | `wind_analysis.py` | mittlere Wind-Volllaststunden (Global Wind Atlas) | hoch = gut |
| Erreichbarkeit | 8,25 % | `accesibility.py` | Länge von Straßen/Schienen je Klasse, gewichtet (Autobahn 0,25 … Feldweg 0,01) | hoch = gut |
| PV-Ertrag | 6,19 % | `pv_analysis.py` | mittlerer PV-Ertrag (Global Solar Atlas) | hoch = gut |
| Ländlicher Flächenanteil | 4,96 % | `rural_zone.py` | Anteil Wald/Busch/Grasland/Brache (GlobCover) | hoch = gut |
| Landwirtschaftsanteil | 1,94 % | `agriculture.py` | Anteil Ackerfläche (GlobCover) | hoch = **schlecht** |
| Stadtflächenanteil | 1,48 % | `urban_zone.py` | Anteil Siedlungsfläche (GlobCover-Klasse 190) | hoch = **schlecht** |

**No-Go-Maske** (`no_go_zones.py`): Eine Zelle wird ausgeschlossen (0), wenn mindestens 50 % ihrer Fläche Militär-, Naturschutz- oder Erholungsgebiet sind (OSM) oder wenn sie aufgrund der Topografie ausgeschlossen ist (`ToPo_1500.shp`).

### Was sich zwischen 2025 und 2050 ändert

Nur **Landnutzung** und **Wasser**. PV, Wind, Erreichbarkeit, Industrie, Konfliktgebiet und No-Go-Zonen bleiben gleich.

- **Landnutzung 2050** (`forecast_landuse.py`): Die heutigen Stadtflächen werden je Region um regionale Urbanisierungsraten vergrößert (Faktor 1,13–2,4, Quelle MDPI 2024). Ergebnis: `Data/morocco_landuse_2050.shp`, das von `agriculture.py`, `urban_zone.py`, `rural_zone.py` und `water_consumption.py` genutzt wird.
- **Wasser 2050** (`water_forecast.py`): siehe unten.

### Wasser

Wasser ist das am stärksten gewichtete Kriterium und hat eine eigene Teilkette:

| Skript | Ergebnis | Inhalt |
|---|---|---|
| `water_exploitable_sw.py` | `Data/water_availability_sw.csv` | Oberflächenwasser [Mio. m³/a] je Zelle: Das Dargebot jedes der 9 Einzugsgebiete wird nach Fließakkumulation auf die Zellen verteilt. |
| `water_exploitable_gw.py` | `Data/water_availability_gw.csv` | Grundwasser [Mio. m³/a] je Zelle: Das Dargebot je Einzugsgebiet wird flächenanteilig auf die ergiebigen Aquifere (BGS-Atlas) verteilt. |
| `water_consumption.py` | `Data/Water_Consumption_{2025,2050}.csv` | heutiger und künftiger Wasserverbrauch [Mrd. m³/a] je Zelle, verteilt nach Stadt-, Landwirtschafts- und Industrieflächen und den Sektoranteilen |
| `water_net.py` | `results/results_water_res_available.csv` | Score 2025 |
| `water_forecast.py` | `results/results_water_res_availabil_2050.csv` (+ `Data/cwb.shp`) | Score 2050: Der Rückgang des Wasserdargebots wird über die klimatische Wasserbilanz (Niederschlag − Verdunstung 2050) auf die Zellen verteilt. |

**Wasser-Score:**
- 50 % entfallen auf die Wasserverfügbarkeit, 50 % auf den Überschuss nach Abzug des Verbrauchs (beide min-max-skaliert).
- **Küstenzellen bekommen pauschal 100**, weil dort Meerwasserentsalzung möglich ist.

### Skripte, die nur Karten erzeugen

`infra_map.py`, `landuse_map.py`, `nogo_maps.py`, `re_potential_map.py` und `water_maps.py` erzeugen nur Abbildungen in `Maps/` und haben keinen Einfluss auf die Ergebnisse.

### Endergebnis

`mca_maps.py` skaliert und gewichtet die Kriterien und schreibt:
- `results/results_mca_morocco_2025_2050.csv`
- Karten `Maps/mca_morocco_{2025,2050,diff}`
- Tortendiagramm der Gewichte

---

## Teil 2: Kostenanalyse

### Idee

Für jede Zelle wird gefragt: *Wenn hier Wasserstoff gebraucht wird, von welcher Zelle aus wird er am günstigsten erzeugt und was kostet er dann?*

Betrachtet wird ein **100-MW-Elektrolyseur** (PEM), der von PV und Wind gespeist wird. Die H2-Kosten setzen sich aus fünf Bestandteilen zusammen:

| Kostenbestandteil | Berechnung |
|---|---|
| **Elektrolyseur** | Annuität + O&M; Wirkungsgrad 60 % (2025) bzw. 80 % (2050) |
| **Erneuerbarer Strom** | Annuitäten der PV- und Windanlagen, die je Standort optimal ausgelegt sind (siehe `FLH_el.py`) |
| **Stromnetz** | HGÜ-Leitung von der Produktions- zur Bedarfszelle (€/km) + zwei Konverter |
| **H2-Pipeline** | von der Bedarfszelle zum nächstgelegenen Industriehafen |
| **Wasser** | 13 kg Wasser je kg H2, bezogen in der Reihenfolge Oberflächenwasser (0,19 €/m³) → Grundwasser (0,05 €/m³) → Entsalzung (1 €/m³, nur an der Küste) → Transport aus der nächsten Zelle mit Wasser (0,0007 €/m³/km) |

Die Kosten werden auf die erzeugte Wasserstoffmenge umgelegt:

```
H2-Kosten [€/MWh_H2] = Σ Jahreskosten [€/a] / (Volllaststunden_Elektrolyseur × 100 MW × Wirkungsgrad)
```

Alle Kostenannahmen (CAPEX, OPEX, Lebensdauer, Zinssatz 8 %) stehen mit Quellenangabe (IRENA, Wuppertal Institut, NEP) im Kopf von `cost_analysis_h2_morocco.py`.

### Pipeline

| Schritt | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 1 | `re_data.py` | `Data/PV_WIND_50_Punkte.xlsx` (je 50 PV- und Wind-Standorte) | stündliche PV/Wind-Profile 2019 von renewables.ninja → `Data/pv_wind_electricity.csv`, `Data/flh_re.csv` |
| 2 | `FLH_el.py` | `Data/pv_wind_electricity.csv` | PyPSA-Optimierung je Standort: kostenoptimaler Mix aus PV, Wind und Elektrolyseur → `Data/FLH_electrolyzer.csv` (Volllaststunden Elektrolyseur, PV- und Windleistung) |
| 3 | `assignment_re_data.py` | `FLH_electrolyzer.csv` + Koordinaten | `Data/data_re_flh_electrolyzer.shp` |
| 4 | `cost_analysis_h2_morocco.py` | Raster, Häfen, Standortdaten, Wasserverfügbarkeit | `Data/results_cost_{2025,2050}.csv` mit allen Kostenbestandteilen je Zelle |
| 5 | `results_cost.py` | Ergebnisse aus Schritt 4 | Kostenkarten und Balkendiagramme in `Maps/`, `Data/results_cost_morocco_2025_2050.csv` |

**Wie Schritt 4 funktioniert:**
1. Jeder Zelle wird der repräsentative Standort zugeordnet, dessen PV- und Wind-Volllaststunden ihren eigenen am ähnlichsten sind (`Data/cell_flh_re.csv`).
2. Für jede Bedarfszelle wird über alle Zellen die günstigste Produktionszelle gesucht, inklusive Netzkosten über die Entfernung.
3. Pipeline- und Wasserkosten werden addiert.

Weil dabei eine Entfernungsmatrix aller Zellen untereinander (7219 × 7219) entsteht, ist das Skript rechen- und speicherintensiv.

---

## Ergebnisse reproduzieren

### Variante A: aus den vorhandenen Zwischenergebnissen (schnell)

Die Zwischenergebnisse liegen im Repo. Es fehlen nur zwei Geodateien:

- `morocco_Morocco_Country_Boundary.shp` → in `MCA/Data/` und `MCA/Data/Landuse/`
- `morocco_coast_line.shp` → in `MCA/Data/` und `Cost_analysis/Data/Data/`

```bash
cd MCA && python mca_maps.py

cd ../Cost_analysis
python assignment_re_data.py
python cost_analysis_h2_morocco.py
python results_cost.py
```

### Variante B: vollständig neu rechnen

Dafür werden alle [Eingangsdaten](#eingangsdaten) benötigt. Innerhalb eines Schritts ist die Reihenfolge beliebig.

**MCA** (in `MCA/`):

1. `forecast_landuse.py`
2. `pv_analysis.py`, `wind_analysis.py`, `accesibility.py`, `industrie.py`, `no_go_zones.py`, `non_conflict.py`, `agriculture.py`, `urban_zone.py`, `rural_zone.py`
3. `water_exploitable_gw.py`, `water_exploitable_sw.py`, `water_consumption.py`
4. `water_net.py`, `water_forecast.py`
5. `mca_maps.py`

**Kosten** (in `Cost_analysis/`):

1. `re_data.py` (API-Limit: max. 50 Anfragen pro Stunde; die Schleife ist für schrittweisen Abruf gedacht)
2. `FLH_el.py`
3. `assignment_re_data.py`
4. `cost_analysis_h2_morocco.py`
5. `results_cost.py`

Die MCA-Wasserdaten werden **nicht** automatisch an die Kostenanalyse übergeben. `Cost_analysis/Data/` enthält eigene Kopien.

---

## Eingangsdaten

Geodaten (`*.shp`, `*.tif`, `*.geojson`, …) und Karten sind per `.gitignore` vom Repo ausgeschlossen. Im Repo liegen nur das Raster, die Häfen, die CSVs und die Standortdaten der Kostenanalyse. Alle folgenden Pfade beziehen sich auf `MCA/`.

| Datei | Quelle | Benötigte Spalten |
|---|---|---|
| `Data/Landuse/gis_osm_landuse_a_free_1.shp` | OpenStreetMap (Geofabrik) | `fclass` |
| `Data/Landuse/gis_osm_roads_free_1.shp`, `…_railways_free_1.shp` | OpenStreetMap (Geofabrik) | `fclass` |
| `Data/Landuse/{mar,wsa}_gc_adg/*.shp` **und** `Data/{mar,wsa}_gc_adg/*.shp` | FAO GlobCover (Marokko / Westsahara) | `GRIDCODE` |
| `Data/Landuse/Regions.shp` | Verwaltungsregionen | `Nom_Region` |
| `Data/morocco_Morocco_Country_Boundary.shp` (auch in `Data/Landuse/`) | Landesgrenze | – |
| `Data/morocco_coast_line.shp` | Küstenlinie | – |
| `Data/morocco.geojson`, `Data/conflict_area.shp` | Kernmarokko bzw. Westsahara | – |
| `Data/Morocco/Morocco_HG.shp`, `Data/Morocco/WSahara/WesternSahara_HG.shp` | BGS African Groundwater Atlas | `MorHGComb` / `WSHGComb` |
| `Data/watershead_morocco.shp` | Einzugsgebiete (9 Becken) | `name` |
| `Data/flow_direction_grid.shp` | Fließakkumulation, in QGIS auf das Raster aggregiert | `_sum`, **zeilengleich mit dem Raster** |
| `Data/ToPo_1500.shp` | Topografie, in QGIS auf das Raster aggregiert | `NoGo` (0/1), **zeilengleich mit dem Raster** |
| `Data/Morocco_GISdata_…_GEOTIFF/PV_yeald_clear_ma_we.shp` | Global Solar Atlas | `pv_yeald` |
| `Data/Wind_Energiedichte/wind_yeald/Wind_pot_morocco_FLH.shp` | Global Wind Atlas | `FLH_wind` |
| `Data/Precipitation_morocco_2050_corr.shp`, `Data/PET_morocco_2050_corr.shp` | Klimaprojektion 2050 | `Precipitat`, `PET` |

Weitere Literaturquellen (Wasserdargebot, Sektoranteile, Kosten) sind direkt in den Skripten kommentiert.

---

## Bekannte Einschränkungen

1. **2050-Wasserdaten der Kostenanalyse:** `Cost_analysis/Data/water_availability_{sw,gw}_2050.csv` lassen sich mit dem aktuellen Code nicht neu erzeugen. Die Berechnung wurde in Commit `0ff553c` aus `water_exploitable_{sw,gw}.py` entfernt und benötigte `MCA/Data/cwp_cell.csv`.
2. **`Cost_analysis/Data/cell_flh_re.csv`** stammt nicht aus einem Skript im Repo (vermutlich QGIS).
3. **Abweichende Wasserdaten:** Die Wasser-CSVs in `Cost_analysis/Data/` sind älter als die in `MCA/Data/` und weichen von ihnen ab.
4. **Nur 50 von 100 Standorten:** `re_data.py` berechnet `flh_re.csv` nur für die ersten 50 von 100 Standorten, die Kostenanalyse ordnet Zellen deshalb nur diesen zu.
5. **PV-Kosten vermutlich überschätzt:** In `cost_analysis_h2_morocco.py` werden die jährlichen PV-Kosten als `Annuität + CAPEX × Leistung` statt `Annuität + OPEX × Leistung` berechnet.
6. **Gewichte im Tortendiagramm:** Das Diagramm in `mca_maps.py` nutzt fest eingetragene Werte, die von `dict_weights_category` abweichen.
7. **Blockierende Fenster:** Kartenskripte rufen `plt.show()` auf und blockieren ohne grafische Oberfläche.
