# Modellparameter und Umrechnungsfaktoren

| Datei | Inhalt |
|---|---|
| `model_parameters.csv` | Alle Modellparameter (Literaturwerte und Annahmen): Wert in der Quelle, Umrechnung, Wert in EUR 2025, Quelle |
| `mca_weights.csv` | MCA-Gewichte: Hauptkriterien (`group = main`) und Straßenklassen der Erreichbarkeit (`group = roads`), je mit Richtung, Skalierung, Quelle; gelesen über `h2morocco.utils.read_mca_weights()` |
| `conversion_factors.csv` | Inflationsfaktoren auf 2025 und Wechselkurse USD ↔ EUR je Jahr (2000–2025) |
| `raw_ecb_exr_usd_eur_annual.csv` | Rohdaten EZB, unverändert heruntergeladen |
| `raw_eurostat_prc_hicp_aind.json` | Rohdaten Eurostat, unverändert heruntergeladen |
| `dea_energy_transport_datasheet_v8.xlsx` | Danish Energy Agency (2025): Technology Data for Energy Transport, Datenblätter Version 8 (1.7.2025), CC BY 4.0, https://ens.dk/media/7681/download. Quelle der HGÜ-Netzkosten (`dc_*`, `transmission_*`, `substation_loss`). Die älteren Zeilen `hvdc_*` (NEP 2019) liest seit 05.11.2026 kein Skript mehr |

## `model_parameters.csv`

Eine Zeile je Wert und Szenariojahr.

| Spalte | Bedeutung |
|---|---|
| `variable_name` | Name des Werts, Technologie zuerst, ohne Jahr (z. B. `electrolyzer_capex`). Eindeutig ist das Paar `variable_name` + `year` |
| `technology` | Anlage oder Bereich (z. B. `electrolyzer_pem`) |
| `quantity` | Kenngröße (z. B. `capex`, `opex_share`) |
| `description` | Erklärung, was der Wert ist |
| `year` | Szenariojahr im Modell |
| `value_source`, `unit_source` | Wert und Einheit wie in der Quelle |
| `currency`, `currency_year` | Währung und Preisstand der Quelle (leer bei dimensionslosen Werten) |
| `exchange_rate_to_eur`, `inflation_factor_to_2025` | Faktoren aus `conversion_factors.csv` |
| `value_eur2025`, `unit` | Wert im Modell: `value_source` × Wechselkurs × Inflationsfaktor (× Einheitenumrechnung), in EUR 2025 |
| `source`, `url`, `page` | Vollständige Quelle, Link, Seite oder Abbildung |
| `note` | Herleitung, Rechenweg, Auffälligkeiten |

## `mca_weights.csv`

Eine Zeile je Gewicht. Je Gruppe ergeben die Gewichte 1 (Hauptkriterien durch Rundung 1,0001).

| Spalte | Bedeutung |
|---|---|
| `group` | `main` = Hauptkriterium, `roads` = Straßenklasse innerhalb der Erreichbarkeit |
| `criterion` | Name im Code (Spalte in `mca_maps.py` bzw. Spalte von `results_accessibility.csv`) |
| `label_de`, `label_en` | Beschriftung deutsch, englisch (Tortendiagramm) |
| `weight` | Gewicht (Anteil, nicht Prozent) |
| `direction` | `positiv` = hoher Rohwert ist gut, `negativ` = hoher Rohwert ist schlecht |
| `scaling` | wie der Rohwert auf 0–100 gebracht wird |
| `source`, `note` | Herkunft des Gewichts, Abweichungen zum Paper |

## `conversion_factors.csv`

| Spalte | Bedeutung |
|---|---|
| `year` | Preisstand bzw. Jahr des Wechselkurses |
| `hicp_ea_index_2015_100` | Harmonisierter Verbraucherpreisindex (HVPI/HICP), Euroraum, Jahresdurchschnitt, 2015 = 100 |
| `inflation_factor_to_2025` | HICP 2025 / HICP `year`, auf 4 Stellen gerundet. Multipliziert einen EUR-Betrag mit Preisstand `year` auf Preisstand 2025 |
| `usd_per_eur` | EZB-Referenzkurs, Jahresdurchschnitt: 1 EUR = x USD |
| `eur_per_usd` | 1 / `usd_per_eur`, auf 4 Stellen gerundet: 1 USD = x EUR |

**Umrechnung eines Literaturwerts nach EUR 2025:** erst mit dem Wechselkurs des Preisjahres der Quelle in EUR umrechnen, dann mit dem HICP des Euroraums auf 2025 hochrechnen:

    Wert_EUR2025 = Wert_USD(Jahr) × eur_per_usd(Jahr) × inflation_factor_to_2025(Jahr)

Beispiel: 1000 USD₂₀₂₀/kW × 0,8755 × 1,2255 = 1072,9 EUR₂₀₂₅/kW.

## Quellen (abgerufen am 29.10.2026)

- **HICP:** Eurostat, Datensatz `prc_hicp_aind` (HICP – annual data), `unit=INX_A_AVG`, `coicop=CP00` (All-items HICP), `geo=EA` (Euroraum in der jeweiligen Zusammensetzung). Stand des Datensatzes: 06.02.2026.
  https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_aind?format=JSON&unit=INX_A_AVG&coicop=CP00&geo=EA&sinceTimePeriod=2000
- **Wechselkurse:** Europäische Zentralbank, Reihe `EXR.A.USD.EUR.SP00.A` (ECB reference exchange rate, US dollar/Euro, Jahresdurchschnitt).
  https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A?format=csvdata&startPeriod=2000

**Festlegung (29.10.2026): Inflationsbereinigung mit dem HICP des Euroraums (`geo=EA`).** Die Modellwerte sind in Euro, der Euroraum-Index misst den Kaufkraftverlust des Euro. Der EU-27-Index enthält auch Länder mit eigener Währung und ergibt höhere Faktoren. Zum Vergleich, Faktor 2020 → 2025: Euroraum (EA) 1,2255 · EA20 1,2257 · EU-27 1,2562.
