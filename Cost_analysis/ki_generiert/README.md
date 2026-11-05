# ki_generiert: von Claude erstellte Skripte der Kostenanalyse

Diese Skripte hat Claude (Claude Code) am 05.11.2026 geschrieben. Sie laufen wie alle anderen aus ihrem eigenen Ordner und sind in `main.ipynb` eingebunden.

| Skript | Erzeugt | Aus | Prüfung |
|---|---|---|---|
| `01b_flh_re.py` | `data/interim/re_profiles/flh_re.csv` | `data/raw/renewables_ninja/pv_wind_electricity.csv` | bitgleich mit dem bisherigen Stand. Der Rechenteil stand vorher in `01_re_data.py`, das jetzt nur noch herunterlädt. |
| `01c_cell_flh_re.py` | `data/interim/re_profiles/cell_flh_re.csv` | PV- und Wind-Kriterium der MCA | ersetzt die QGIS-Datei unbekannter Herkunft, wie im Paper beschrieben. Die zweite Spalte ist jetzt die Wind-Volllaststunde statt `FLH_el`; der mittlere H₂-Preis steigt dadurch um rund 5 €/MWh (siehe `data/README.md`). |

Weitere KI-generierte oder von KI geänderte Dateien listet `README.md` im Hauptordner (Abschnitt „KI-generierte Dateien“).
