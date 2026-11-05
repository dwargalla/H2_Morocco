"""Schritt 1b der Kostenanalyse: Volllaststunden der Referenzpunkte aus den Profilen.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``. Gegen den bisherigen Stand geprüft, siehe Hinweise.

Summiert die stündlichen Profile einer 1-kW-Anlage über das Jahr. Das Ergebnis
sind die Volllaststunden je Standort, für PV und Wind getrennt. Braucht keinen
API-Zugang und lässt sich deshalb jederzeit neu rechnen, anders als der
Download in ``01_re_data.py``.

Eingaben:
    data/raw/renewables_ninja/pv_wind_electricity.csv   stündliche Profile, Spalten
                                                        electricity_{PV,Wind}_i

Ausgaben:
    data/interim/re_profiles/flh_re.csv                 FLH_PV, FLH_Wind für die Standorte 0–49

Hinweise:
    - Nur die ersten 50 Standorte, wie bisher in ``01_re_data.py``; die CSV enthält
      zwar 100 Profilpaare, das Kostenmodell ordnet Zellen aber nur diesen 50 zu
      (siehe README, Abschnitt Kostenanalyse).
    - Geprüft (05.11.2026): erzeugt ``flh_re.csv`` bitgleich mit dem bisherigen Stand.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python 01b_flh_re.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import pandas as pd

N_POINTS = 50   # Anzahl der Standorte, die das Kostenmodell nutzt

df_electricity = pd.read_csv('../../data/raw/renewables_ninja/pv_wind_electricity.csv', index_col=0)
ds_annual_sum = df_electricity.sum()   # kWh je kW installierter Leistung = Volllaststunden

df_flh = pd.DataFrame({
    'FLH_PV':   [ds_annual_sum[f'electricity_PV_{i}'] for i in range(N_POINTS)],
    'FLH_Wind': [ds_annual_sum[f'electricity_Wind_{i}'] for i in range(N_POINTS)],
})
df_flh.to_csv('../../data/interim/re_profiles/flh_re.csv', index=False)
