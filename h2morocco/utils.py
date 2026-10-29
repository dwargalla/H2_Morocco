"""Gemeinsame Funktionen für alle Skripte: Modellparameter einlesen, Annuitätenfaktor."""
from pathlib import Path

import pandas as pd

# Pfad über diese Datei bestimmt, damit es aus jedem Arbeitsordner funktioniert.
# Deshalb muss das Paket editierbar installiert sein (pip install -e .).
MODEL_PARAMETERS_CSV = Path(__file__).resolve().parents[1] / 'data' / 'model_parameters' / 'model_parameters.csv'


def read_model_parameters():
    """Liest model_parameters.csv und gibt die Modellwerte zurück: (variable_name, year) -> value_eur2025.

    Beispiel:
        model_parameters = read_model_parameters()
        capex_el_2025 = model_parameters['electrolyzer_capex', 2025]
    """
    df = pd.read_csv(MODEL_PARAMETERS_CSV, float_precision='round_trip')
    values = df.set_index(['variable_name', 'year'])['value_eur2025']
    if not values.index.is_unique:
        duplicates = values.index[values.index.duplicated()].tolist()
        raise ValueError(f'model_parameters.csv: doppelte Einträge {duplicates}')
    return values


def annuity_factor(interest_rate, lifetime):
    """Annuitätenfaktor: verteilt eine Investition auf gleich hohe Jahresraten über die Lebensdauer.

    Jahreskosten der Investition [€/a] = annuity_factor(Zins, Lebensdauer) * Investition [€]

    Beispiel:
        annuity_el_2025 = annuity_factor(r, lifetime_el_2025) * p_nom_el * capex_el_2025
    """
    return ((1 + interest_rate) ** lifetime * interest_rate) / ((1 + interest_rate) ** lifetime - 1)
