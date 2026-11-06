# Annahmen im Modell

Stand: 06.11.2026. Übersicht über alle Zahlen und Festlegungen, die das Ergebnis beeinflussen.
Ziel: nichts Wichtiges steckt nur im Code. Die Spalte **Ablage** zeigt, wo der Wert steht:

- **CSV**: in einer Parameterdatei dieses Ordners, wird von dort gelesen
- **Code**: fest im Skript eingetragen (Kandidat für eine Parameterdatei)
- **Methode**: keine einzelne Zahl, sondern eine Modellentscheidung

Zeilenangaben gelten für den Stand oben. Bei Änderungen bitte diese Liste mitpflegen.
Offene Fragen zu Quellen und Werten stehen im Fehlerprotokoll (Nummer in der letzten Spalte). Kürzel in Klammern sind die Schlüssel in `bibliography.bib` des Papers.

## 1. Raster und Lesart

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Rastergröße | 10 km × 10 km, 7.219 Zellen, EPSG:32629 | `MCA/Grid_morocco/grid_morocco.py:72` | Festlegung im Projekt | Code | |
| Lesart der Ergebnisse | jede Zelle = Standortpotenzial für **ein** 100-MW-Projekt, keine landesweite Ausbauplanung | gesamtes Kostenmodell | Festlegung im Projekt | Methode | 43 |
| Szenariojahre | 2025 und 2050 | MCA und Kosten | Paper | Methode | |

## 2. MCA: Gewichte

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Gewichte der neun Hauptkriterien | Wasser 34,06 %, Nicht-Konflikt 16,30 %, Industrie 14,46 %, Wind 12,37 %, Erreichbarkeit 8,25 %, PV 6,19 %, Ländlich 4,96 %, Landwirtschaft 1,94 %, Stadt 1,48 % | `mca_weights.csv` (`group = main`) | AHP, Mittel aus drei Perspektiven | CSV | 76 (Paper Tab. 2 weicht in 4 Werten ab) |
| Gewichte der Straßenklassen innerhalb der Erreichbarkeit | Autobahn 0,25 … Weg Klasse 4 0,01; Bahn 0,18 | `mca_weights.csv` (`group = roads`) | Paper Tabelle 2 | CSV | 76 |
| Skalierung der Kriterien | min-max auf 0–100; Landwirtschaft und Stadt invertiert; Wasser und Konflikt kommen schon als 0–100 | `MCA/mca_maps.py:91–116` | Paper | Methode | 67 (Wirkung der Min-Max-Skalierung) |
| 2050 übernimmt aus 2025 | PV, Wind, Erreichbarkeit, Industrie, Konflikt, No-Go; nur Landnutzung und Wasser ändern sich | `MCA/mca_maps.py` | Festlegung im Projekt | Methode | |

## 3. MCA: Kriterien

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Wind-Volllaststunden | Kapazitätsfaktor IEC-Klasse III × 8.760 h | `MCA/ki_generiert/wind_flh_grid.py:43` | Global Wind Atlas; IEC III passt zur Referenzturbine V136 | Code | 71 |
| PV-Ertrag | Global Solar Atlas PVOUT, gerundet, Polygone mit 4er-Nachbarschaft | `MCA/ki_generiert/pv_yield_polygons.py:50` | wie früherer QGIS-Schritt | Code | |
| Landwirtschaftsfläche | GlobCover-Klassen 11–16, 20–21, 30–32 | `MCA/agriculture.py:51–52` | GlobCover-Legende | Code | 40 (Datenstand 2009) |
| Stadtfläche | GlobCover-Klasse 190 | `MCA/urban_zone.py:49–50` | GlobCover-Legende | Code | |
| Ländliche Fläche | GlobCover-Klassen 40–185, 200–203, 220, 230 | `MCA/rural_zone.py:50–60` | GlobCover-Legende | Code | 73 (220 Schnee, 230 „No data“ zählen mit) |
| Industriefläche | OSM `fclass = industrial` | `MCA/industrie.py:34` | OpenStreetMap | Code | |
| Erreichbarkeit | Länge je Straßen- und Bahnklasse in der Zelle (12 OSM-Klassen) | `MCA/accesibility.py:47–49` | OpenStreetMap | Code | |
| Konfliktindikator | 100 · (1 − exp(−Abstand/λ)), **λ = 50 km**, Abstand vom Zellmittelpunkt zur Zone östlich des Walls | `MCA/non_conflict.py:43` | Reichweite BM-21 Grad 20–45 km; Einschlagorte Mahbès/Smara ≈ 25–31 km vom Wall (UN S/2024/707) | Code | 68 |

## 4. MCA: Ausschlussgebiete (No-Go)

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| OSM-Schutzflächen | `military`, `nature_reserve`, `recreation_ground` | `MCA/no_go_zones.py:50` | Paper | Code | |
| Flächenschwelle | Zelle ausgeschlossen ab **≥ 50 %** Flächenanteil (OSM-Flächen und Konfliktzone) | `MCA/no_go_zones.py:66, 80` | Festlegung im Projekt | Code | 37 (Paper: „more than 50 %“) |
| Topografie | Höhenspanne in der Zelle **> 1.500 m** → No-Go | `MCA/ki_generiert/topography_grid.py:44` | Ersatz für Hangneigung | Code | 29 |
| Konfliktzone | Gebiet östlich des Walls ist No-Go | `MCA/no_go_zones.py:76–81` | Festlegung 05.11.2026 | Methode | 68 |
| No-Go nur in der MCA | Kostenanalyse rechnet auch No-Go-Zellen | `Cost_analysis/04_…py` | Festlegung im Projekt | Methode | Korrekturplan F-25 |

## 5. Wasser

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Oberflächenwasser je Einzugsgebiet 2025 [Mio. m³/a] | Sahara 390, Loukkos 3.600, Moulouya 1.610, Sebou 5.560, Bouregreg 850, Oum Er-Rbia 3.315, Tensift 800, Südatlas 626, Souss-Massa 1.444 | `MCA/water_exploitable_sw.py:42–50` | Benzougagh et al. 2024 (`Benzougagh2024Chapter`), Seite/Tabelle fehlt | Code | 115 |
| Verteilung des Oberflächenwassers im Einzugsgebiet | nach summierten Fließrichtungs-Codes je Zelle | `MCA/water_exploitable_sw.py:57–58` | Methode offen, mit Prof abstimmen | Methode | 110, 113 |
| Grundwasser je Einzugsgebiet 2025 [Mio. m³/a] | Sahara 18, Loukkos 110, Moulouya 462, Sebou 1.143, Bouregreg 146, Oum Er-Rbia 457, Tensift 753, Südatlas 208 + 323, Souss-Massa 646 | `MCA/water_exploitable_gw.py:57–65` | Hssaisoune et al. 2020 (`Hssaisoune2020Geosciences`), Seite/Tabelle fehlt | Code | 115 |
| Verteilung des Grundwassers | gleichmäßig je Fläche über den Grundwasserleitern im Einzugsgebiet | `MCA/water_exploitable_gw.py` | BGS Africa Groundwater Atlas | Methode | |
| Wasserverbrauch gesamt [Mrd. m³/a] | 2025: 15,9; 2050: 24,223 | `MCA/water_consumption.py:74` | Hellegers et al. 2013 (`Hellegers2013JHydrol`), Seite/Tabelle fehlt | Code | 115 |
| Sektoranteile Landwirtschaft / Städte / Industrie | 2025: 87 / 10,4 / 2,6 %; 2050: 75 / 22,3 / 2,7 % | `MCA/water_consumption.py:70–72` | Hellegers et al. 2013 (`Hellegers2013JHydrol`), Seite/Tabelle fehlt | Code | 115 |
| Verteilung Agrarwasser | nach tatsächlich bewässerter Fläche (FAO GMIA v5, Stand ca. 2005), 2050 gleich | `MCA/water_consumption.py`, `MCA/ki_generiert/irrigation_grid.py` | Siebert et al. 2013 | Methode | 31 |
| Verteilung Stadt- und Industriewasser | nach Fläche GlobCover 190 bzw. OSM `industrial` | `MCA/water_consumption.py:81–83` | Festlegung im Projekt | Methode | |
| Wasserdargebot 2050 [Mio. m³/a] | gesamt 8.535 = Grundwasser 1.636 + Oberflächenwasser 6.899 | `MCA/water_forecast.py:81, 101, 106` | Hellegers et al. 2013 (`Hellegers2013JHydrol`), Seite/Tabelle fehlt | Code | 77, 115 |
| Verteilung des Rückgangs 2050 | nach klimatischer Wasserbilanz je Zelle | `MCA/water_forecast.py` | Gumus et al. 2024 (`Gumus2024JEnvMan`) | Methode | 36, Korrekturplan F-23 |
| Wasser-Score | 50 % Dargebot + 50 % Überschuss (Dargebot − Verbrauch), je min-max; 2050 mit 2025 als Maßstab | `MCA/water_net.py:54–57`, `MCA/water_forecast.py:128–132` | Festlegung im Projekt | Code | 70 |
| Küstenzellen | Wasser-Score pauschal **100** (Entsalzung möglich) | `MCA/water_net.py:68`, `MCA/water_forecast.py:143` | Planungsannahme | Code | 69 |

## 6. Landnutzung 2050

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Wachstum der Stadtflächen je Region bis 2050 | Faktor 1,13 (Casablanca-Settat) bis 2,4 (Dakhla) | `MCA/forecast_landuse.py:53–64` | Bounoua et al. 2024 (`Bounoua2024`) | Code | Korrekturplan F-24 (jährliche Raten als Gesamtfaktor) |
| Genauigkeit der Flächenanpassung | 1 % | `MCA/forecast_landuse.py:69` | Rechentoleranz | Code | |

## 7. Kostenmodell

Alle Kosten-, Wirkungsgrad- und Lebensdauerwerte stehen in **`model_parameters.csv`** (Ablage CSV, mit Quelle und Umrechnung in EUR 2025). Fest im Code oder als Methode bleiben:

| Annahme | Wert | Wo | Quelle / Begründung | Ablage | Nr. |
|---|---|---|---|---|---|
| Wetterjahr der Profile | 2019 (renewables.ninja) | `data/raw/renewables_ninja/` | Altbestand | Methode | 1, 7, 10, 41 |
| Referenzpunkte | 50 von 100 Standorten | `Cost_analysis/ki_generiert/01b_flh_re.py:36` | Altbestand | Code | 2 |
| Auslegung je Standort | PyPSA mit Gurobi, je Szenariojahr getrennt | `Cost_analysis/02_FLH_el.py:48, 104` | Festlegung im Projekt | Methode | 8 |
| Zuordnung Zelle → Referenzpunkt | nächster Punkt nach (Volllaststunden PV, Volllaststunden Wind) | `Cost_analysis/04_…py:281` | Festlegung im Projekt | Methode | |
| Stromquelle | günstigste Zelle inkl. HGÜ-Kosten; bei eigener Zelle keine Netzkosten | `Cost_analysis/04_…py:318–321` | Danish Energy Agency (2025) | Methode | 45, 48, 63 |
| Netz und Pipeline | Anteil an gemeinsamer Infrastruktur (Konglomerat), Luftlinie | `Cost_analysis/04_…py` | Festlegung im Projekt | Methode | 49, 63 |
| Pipeline-Kompression und Transportverluste | nicht berücksichtigt (vereinfachtes System) | – | Festlegung im Projekt | Methode | 49 |
| Wasserbezug | Oberflächenwasser → Grundwasser → Entsalzung (nur Küstenzelle) → Transport aus nächster Zelle mit Wasser | `Cost_analysis/04_…py:339–380` | Festlegung im Projekt | Methode | |
| Hafen | nächster Industriehafen (Liste 2025 und 2050) | `data/raw/infrastructure/` | Festlegung im Projekt | Methode | |
