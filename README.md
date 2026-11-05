# H2 Morocco – Standortanalyse für grünen Wasserstoff

Räumliche Analyse, **wo in Marokko grüner Wasserstoff (H2) für 2025 und 2050 am sinnvollsten und am günstigsten produziert werden kann**. Entstanden als Masterprojekt (TH Köln).

Marokko (inklusive Westsahara) wird dafür in ein Raster aus **7219 Zellen à 10 × 10 km** zerlegt. Für jede Zelle werden zwei voneinander unabhängige Kennzahlen berechnet:

| Analyse | Ordner | Ergebnis je Zelle | Frage |
|---|---|---|---|
| **Multikriterienanalyse (MCA)** | `MCA/` | Eignungs-Score 0–100 | Wie *geeignet* ist der Standort (Ressourcen, Wasser, Infrastruktur, Flächenkonkurrenz, Stabilität)? |
| **Kostenanalyse** | `Cost_analysis/` | Wasserstoffkosten in €/MWh_H2 | Was *kostet* Wasserstoff aus einem 100-MW-Elektrolyseur an diesem Ort, inklusive Strom, Netz, Pipeline zum Hafen und Wasser? |

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
- [KI-generierte Dateien](#ki-generierte-dateien)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)

---

## Projektstruktur

```
H2_Morocco/
├── main.ipynb                Gesamtlauf aller Skripte (Schalter je Schritt), danach Vergleich MCA ↔ Kosten
├── compare_mca_cost.py       Übersichtsfolie: MCA-Score gegen H2-Kosten
├── h2morocco/                gemeinsamer Code: Parameter einlesen, Annuität, Laufordner (runs.py)
├── data/
│   ├── README.md             Herkunft und Links aller Dateien
│   ├── raw/                  Eingabedaten: Downloads, Handarbeit, origin_unknown/ (nicht im Repo, außer kleinen Dateien)
│   ├── interim/              Zwischenstufen, alle per Skript erzeugt (löschbar): Raster, Layer, Wasser, MCA-Kriterien, Profile
│   └── model_parameters/     alle Kostenannahmen mit Quelle (model_parameters.csv)
├── results/
│   ├── runs/                 je Kostenlauf ein Ordner <Datum>_<Uhrzeit>_<Commit>_cost mit Ergebnissen, Parametern, Karten
│   ├── mca/                  results_mca_morocco_2025_2050.csv
│   ├── cost/                 veröffentlichte Kostenergebnisse (Stand Paper, werden nicht überschrieben)
│   └── figures/{mca,cost}/   Karten und Diagramme
├── MCA/                      nur Code
│   ├── Grid_morocco/         Rastererzeugung (grid_morocco.py)
│   ├── custom.py             Hilfsfunktion list_index() für Zell-Verschneidungen
│   ├── *.py                  Kriterien-, Wasser- und Kartenskripte (siehe unten)
│   ├── ki_generiert/         von Claude geschriebene Skripte (ersetzen QGIS-Schritte)
│   └── old/                  veraltete Skripte
├── Cost_analysis/            nur Code
│   ├── 00_…05_*.py           Pipeline der Kostenanalyse (siehe unten)
│   ├── ki_generiert/         von Claude geschriebene Skripte (01b_flh_re.py, 01c_cell_flh_re.py)
│   └── 01_old/               veraltete Skripte
├── Fehlerprotokoll.md        bekannte Fehler und ihr Status (lokal, nicht im Repo)
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

- `02_FLH_el.py` braucht zusätzlich eine **Gurobi-Lizenz** (für Hochschulen kostenlos).
- `01_re_data.py` braucht einen **API-Token von [renewables.ninja](https://www.renewables.ninja/api/)**. Er wird aus `.env` gelesen: `cp .env.example .env` und `RENEWABLES_NINJA_TOKEN` eintragen. `.env` ist per `.gitignore` vom Repo ausgeschlossen.
- Die Kartenskripte (`*_map(s).py`, `05_results_cost.py`) brauchen einen **CARTO-API-Key** für die Hintergrundkarte ([anfordern](https://carto.com/basemaps/apikey/)), ebenfalls in `.env` als `CARTO_API_KEY`. Ohne Key liefert CARTO die Kacheln mit dem Wasserzeichen „API KEY REQUIRED“ aus.

**Direkt in VS Code starten:** Öffne das gewünschte Skript und klicke oben rechts auf **Python-Datei ausführen**. Wähle über **Python: Interpreter auswählen** die Python-Umgebung `H2_Morocco/.venv` aus (wenn `H2_Morocco` selbst geöffnet ist: `.venv`).

Die aktiven Skripte in `Cost_analysis/`, `MCA/`, `MCA/Grid_morocco/` und den Ordnern `ki_generiert/` setzen beim direkten Start ihr Arbeitsverzeichnis automatisch auf ihren eigenen Ordner. Dadurch werden `../data/...` und `../results/...` unabhängig vom Arbeitsordner des Terminals korrekt aufgelöst. Auch ein Start aus dem Projektordner funktioniert:

```bash
python MCA/mca_maps.py
python Cost_analysis/04_cost_analysis_h2_morocco.py
```

Benötigte Eingangsdaten, Pakete, API-Zugangsdaten und Solver-Lizenzen müssen weiterhin vorhanden sein. Die archivierten Skripte in `MCA/old/` und `Cost_analysis/01_old/` enthalten teilweise alte absolute Windows-Pfade und sind von dieser Anpassung ausgenommen.

---

## Grundprinzip: das Raster

`data/interim/grid/grid_morocco_clear.shp` ist das Rückgrat des Projekts:

- 7219 quadratische Zellen à 10 km, Koordinatensystem **EPSG:32629 (UTM 29N)**, alle Längen in m, alle Flächen in m².
- `grid_morocco.py` erzeugt das Rohraster und `grid_morocco_clear.shp`, dieselben Zellen auf die Landesgrenze zugeschnitten.

**Alle Zwischenergebnisse sind über die Zeilennummer mit dem Raster verknüpft.** Zeile `i` in jeder CSV in `data/interim/` oder `results/` gehört zu Zelle `i` im Raster. Es gibt keine ID-Spalte. Wer eine Zwischen-CSV sortiert oder filtert, verschiebt alle Werte, ohne dass ein Fehler auftritt.

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

- **Landnutzung 2050** (`forecast_landuse.py`): Die heutigen Stadtflächen werden je Region um regionale Urbanisierungsraten vergrößert (Faktor 1,13–2,4, Quelle MDPI 2024). Ergebnis: `data/interim/landuse/morocco_landuse_2050.shp`, das von `agriculture.py`, `urban_zone.py`, `rural_zone.py` und `water_consumption.py` genutzt wird.
- **Wasser 2050** (`water_forecast.py`): siehe unten.

### Wasser

Wasser ist das am stärksten gewichtete Kriterium und hat eine eigene Teilkette:

| Skript | Ergebnis | Inhalt |
|---|---|---|
| `water_exploitable_sw.py` | `data/interim/water/water_availability_sw.csv` | Oberflächenwasser [Mio. m³/a] je Zelle: Das Dargebot jedes der 9 Einzugsgebiete wird nach `flow_direction_grid` auf die Zellen verteilt. Das sind summierte Fließrichtungs-Codes, keine Fließakkumulation (Fehlerprotokoll Nr. 110, Methode offen). |
| `water_exploitable_gw.py` | `data/interim/water/water_availability_gw.csv` | Grundwasser [Mio. m³/a] je Zelle: Das Dargebot je Einzugsgebiet wird flächenanteilig auf die ergiebigen Aquifere (BGS-Atlas) verteilt. |
| `water_consumption.py` | `data/interim/water/Water_Consumption_{2025,2050}.csv` | heutiger und künftiger Wasserverbrauch [Mrd. m³/a] je Zelle, verteilt nach Stadt-, Landwirtschafts- und Industrieflächen und den Sektoranteilen |
| `water_net.py` | `data/interim/mca_criteria/results_water_res_available.csv` | Score 2025 |
| `water_forecast.py` | `data/interim/mca_criteria/results_water_res_availabil_2050.csv` (+ `data/interim/water/cwb.shp`, `water_availability_{sw,gw}_2050.csv` für die Kostenanalyse) | Score 2050: Der Rückgang des Wasserdargebots wird über die klimatische Wasserbilanz (Niederschlag − Verdunstung 2050) auf die Zellen verteilt. |

**Wasser-Score:**
- 50 % entfallen auf die Wasserverfügbarkeit, 50 % auf den Überschuss nach Abzug des Verbrauchs (beide min-max-skaliert).
- **Küstenzellen bekommen pauschal 100**, weil dort Meerwasserentsalzung möglich ist.

### Skripte, die nur Karten erzeugen

`infra_map.py`, `landuse_map.py`, `nogo_maps.py`, `re_potential_map.py` und `water_maps.py` erzeugen nur Abbildungen in `results/figures/mca/` und haben keinen Einfluss auf die Ergebnisse.

### Endergebnis

`mca_maps.py` skaliert und gewichtet die Kriterien und schreibt:
- `results/mca/results_mca_morocco_2025_2050.csv`
- Karten `results/figures/mca/mca_morocco_{2025,2050,diff}`
- Tortendiagramm der Gewichte

---

## Teil 2: Kostenanalyse

### Idee

Für jede Zelle wird gefragt: *Wenn hier ein Elektrolyseur gebaut wird, was kostet der Wasserstoff, bis er am nächsten Industriehafen ist?* Der Strom kann vor Ort erzeugt oder per HGÜ aus einer Zelle mit besserem Wind- und Solarangebot bezogen werden; das Modell nimmt die günstigere Variante.

Betrachtet wird ein **100-MW-Elektrolyseur** (PEM), der von PV und Wind gespeist wird. Die H2-Kosten setzen sich aus fünf Bestandteilen zusammen:

| Kostenbestandteil | Berechnung |
|---|---|
| **Elektrolyseur** | Annuität + O&M; Wirkungsgrad 60 % (2025) bzw. 76 % (2050) |
| **Erneuerbarer Strom** | Annuitäten + Betriebskosten der PV- und Windanlagen, die je Standort und Szenariojahr optimal ausgelegt sind (siehe `02_FLH_el.py`) |
| **Stromnetz** | HGÜ-Freileitung von der Zelle mit der Stromerzeugung zur Zelle des Elektrolyseurs (€/km) + zwei Konverterstationen, mit Übertragungsverlusten; Werte der Danish Energy Agency (2025) für große Trassen, verstanden als Anteil an gemeinsamer Infrastruktur. Bei Eigenversorgung keine Netzkosten |
| **H2-Pipeline** | von der Zelle des Elektrolyseurs zum nächstgelegenen Industriehafen |
| **Wasser** | 13 kg Wasser je kg H2, bezogen in der Reihenfolge Oberflächenwasser (0,25 €/m³) → Grundwasser (0,07 €/m³) → Entsalzung (1,30 €/m³, nur an der Küste) → Transport aus der nächsten Zelle mit Wasser (0,0007 €/m³/km); Preise in EUR 2025 |

Die Kosten werden auf die erzeugte Wasserstoffmenge umgelegt:

```
H2-Kosten [€/MWh_H2] = Σ Jahreskosten [€/a] / (Volllaststunden_Elektrolyseur × 100 MW × Wirkungsgrad)
```

Alle Kostenannahmen (CAPEX, OPEX, Lebensdauer, Zinssatz 8 %) stehen mit Quellenangabe in `data/model_parameters/model_parameters.csv`.

**Lesart:** Das Ergebnis je Zelle ist das Standortpotenzial für ein einzelnes 100-MW-Projekt, keine landesweite Ausbauplanung. Viele Zellen können dieselbe Produktionszelle wählen.

### Pipeline

| Schritt | Skript | Eingabe | Ausgabe |
|---|---|---|---|
| 0 | `00_era5_download.py` | – | stündliche ERA5-Wetterdaten → `data/raw/era5/` (CDS-Key; derzeit von keinem Schritt genutzt) |
| 1 | `01_re_data.py` | `data/raw/renewables/PV_WIND_50_Punkte.xlsx` (je 50 PV- und Wind-Standorte) | Download der stündlichen PV/Wind-Profile 2019 von renewables.ninja → `data/raw/renewables_ninja/pv_wind_electricity.csv` (API-Token; reproduziert den vorhandenen Bestand nicht, Fehlerprotokoll Nr. 10) |
| 1b | `ki_generiert/01b_flh_re.py` | Profile | Volllaststunden je Standort (Jahressumme der Profile) → `data/interim/re_profiles/flh_re.csv` |
| 1c | `ki_generiert/01c_cell_flh_re.py` | PV- und Wind-Kriterium der MCA | PV-Ertrag und Wind-Volllaststunden je Zelle → `data/interim/re_profiles/cell_flh_re.csv` |
| 2 | `02_FLH_el.py` | Profile | PyPSA-Optimierung je Standort und Szenariojahr: kostenoptimaler Mix aus PV, Wind und Elektrolyseur → `data/interim/re_profiles/FLH_electrolyzer_{2025,2050}.csv` (Volllaststunden Elektrolyseur, PV und Wind in MW je MW Elektrolyseur) |
| 3 | `03_assignment_re_data.py` | `FLH_electrolyzer_{2025,2050}.csv` + Koordinaten | `data/interim/re_profiles/data_re_flh_electrolyzer_{2025,2050}.shp` |
| 4 | `04_cost_analysis_h2_morocco.py` | Raster, Häfen, Referenzpunkte, Wasserverfügbarkeit | neuer Laufordner `results/runs/<Datum>_<Uhrzeit>_<Commit>_cost/` mit `results_cost_{2025,2050}.csv` (alle Kostenbestandteile je Zelle), Parametern und Codestand |
| 5 | `05_results_cost.py` | letzter Laufordner | Kostenkarten und Balkendiagramme in `<Laufordner>/figures/`, `results_cost_morocco_2025_2050.csv` |

**Wie Schritt 4 funktioniert:**
1. Jeder Zelle wird der repräsentative Standort zugeordnet, dessen PV- und Wind-Volllaststunden ihren eigenen am ähnlichsten sind (`data/interim/re_profiles/cell_flh_re.csv` gegen `flh_re.csv`).
2. Für jede Zelle (Standort des Elektrolyseurs) wird über alle Zellen die günstigste Stromquelle gesucht, inklusive Netzkosten über die Entfernung; Eigenversorgung kostet kein Netz.
3. Pipeline- und Wasserkosten werden addiert.

Weil dabei eine Entfernungsmatrix aller Zellen untereinander (7219 × 7219) entsteht, ist das Skript rechen- und speicherintensiv.

---

## Ergebnisse reproduzieren

**Gesamtlauf:** `main.ipynb` führt alle Schritte in der richtigen Reihenfolge aus (Schalter je Schritt in `STEPS`) und vergleicht danach MCA und Kosten. Aus leerem `data/interim/` dauert das etwa 17 Minuten (Referenzlauf 05.11.2026: 33 Schritte fehlerfrei), am längsten `02_FLH_el.py` mit Gurobi. Voraussetzungen: alle Eingangsdaten in `data/raw/` (siehe `data/README.md`), Gurobi-Lizenz, `CARTO_API_KEY` für die Karten.

```bash
jupyter nbconvert --to notebook --execute main.ipynb --output-dir /tmp --ExecutePreprocessor.timeout=-1
```

`main.ipynb` wird ohne Ausgaben committet; beim Ausführen die Ausgabe wie oben in einen anderen Ordner schreiben. Die Ausgabe aller Schritte steht in `results/runs/main_last.log`.

**Einzelne Skripte:** Jedes Skript läuft auch allein, solange seine Eingaben in `data/interim/` liegen. Die Reihenfolge steht in `STEPS` in `main.ipynb`.

Die Kostenanalyse liest dieselben Wasserdaten wie die MCA aus `data/interim/water/`. Für 2050 erzeugt `water_forecast.py` eigene Dateien, getrennt nach Grund- und Oberflächenwasser; sie weichen vom Wasser 2050 der MCA ab (Fehlerprotokoll Nr. 36, 77).

---

## Eingangsdaten

Alle Eingangs- und Zwischendaten mit Quelle, Download-Link, benötigten Spalten und Status (lokal vorhanden oder fehlt) stehen in **[`data/README.md`](data/README.md)**. Rohdaten unter `data/raw/` sind per `.gitignore` vom Repo ausgeschlossen. Getrackt sind nur kleine Dateien (Häfen, Legenden, PV/Wind-Standorte).

Alle Kostenannahmen stehen mit Quelle in `data/model_parameters/model_parameters.csv`. Weitere Literaturquellen der MCA (Wasserdargebot, Sektoranteile) sind direkt in den Skripten kommentiert.

---

## KI-generierte Dateien

Neue Skripte, die Claude (Claude Code) geschrieben hat, liegen in eigenen Unterordnern `ki_generiert/` und tragen im Kopf den Vermerk **KI-generiert**:

| Ordner | Skripte | Übersicht |
|---|---|---|
| `MCA/ki_generiert/` | `flow_direction_grid.py`, `pv_yield_polygons.py`, `wind_flh_grid.py`, `topography_grid.py` (ersetzen frühere QGIS-Schritte) | `MCA/ki_generiert/README.md` |
| `Cost_analysis/ki_generiert/` | `01b_flh_re.py` (Volllaststunden der Referenzpunkte), `01c_cell_flh_re.py` (PV/Wind je Zelle) | `Cost_analysis/ki_generiert/README.md` |

**Vorhandene Skripte, die Claude am 05.11.2026 inhaltlich geändert hat** (Diff in Git):
- `MCA/Grid_morocco/grid_morocco.py`: schreibt zusätzlich `grid_morocco_clear.shp` (Zuschnitt auf die Landesgrenze)
- `MCA/water_forecast.py`: schreibt zusätzlich Wasser 2050 für die Kostenanalyse (Block aus Commit `0ff553c`)
- `Cost_analysis/01_re_data.py`: nur noch Download nach `data/raw/renewables_ninja/`, Rechenteil nach `01b_flh_re.py`
- `Cost_analysis/02_FLH_el.py`: Auslegung je Szenariojahr; Volllaststunden und PV/Wind bezogen auf den Elektrolyseur (MW je MW)
- `Cost_analysis/03_assignment_re_data.py`: je Szenariojahr eine Datei
- `Cost_analysis/04_cost_analysis_h2_morocco.py`: Wasser aus `data/interim/water/`, `cell_flh_re.csv` aus `data/interim/re_profiles/`, HGÜ-Netzkosten nach DEA 2025 mit Verlusten und ohne Netz bei Eigenversorgung, PV/Wind-Leistung in MW (F-04), PV-OPEX (F-07), Auslegung je Jahr
- `MCA/wind_analysis.py`: liest den Wind-Layer aus `data/interim/layers/` (Global Wind Atlas)
- Pfade und Kommentare in `water_net.py`, `water_exploitable_{sw,gw}.py`, `no_go_zones.py`, `nogo_maps.py`, `02_FLH_el.py`

**Ältere KI-generierte Dateien** (laut Git-Commits mit „Co-Authored-By: Claude“; nicht verschoben, weil sie importiert werden bzw. im Hauptordner liegen müssen): `main.ipynb`, `compare_mca_cost.py`, `h2morocco/__init__.py`, `h2morocco/overview.py`, `h2morocco/runs.py`. Commits ohne diesen Vermerk können ebenfalls KI-Anteile enthalten.

---

## Bekannte Einschränkungen

Vollständig und mit Status in `Fehlerprotokoll.md`. Die wichtigsten:

1. **Oberflächenwasser:** wird nach summierten Fließrichtungs-Codes verteilt statt nach Fließakkumulation (Fehlerprotokoll Nr. 110, 113). Die Methode wird noch abgestimmt; MERIT Hydro `upa` liegt bereit.
2. **Herkunft unbekannt:** Die Küstenlinie stammt aus QGIS ohne erhaltene Quelle, siehe `data/raw/origin_unknown/README.md`.
3. **Nur 50 von 100 Standorten:** `ki_generiert/01b_flh_re.py` berechnet `flh_re.csv` nur für die ersten 50 Standorte, die Kostenanalyse ordnet Zellen deshalb nur diesen zu (Nr. 2; zurückgestellt, bis die Profile ggf. aus ERA5 neu entstehen).
4. **Profile und Orte passen nicht sicher zusammen:** Einige renewables.ninja-Profile sind an verschiedenen Orten identisch (Nr. 41).
5. **Gewichte im Tortendiagramm:** Das Diagramm in `mca_maps.py` nutzt fest eingetragene Werte, die von `dict_weights_category` abweichen.
6. **Blockierende Fenster:** Kartenskripte rufen `plt.show()` auf und blockieren ohne grafische Oberfläche; `main.ipynb` setzt deshalb `MPLBACKEND=Agg`.
