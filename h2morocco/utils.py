"""Gemeinsame Funktionen für alle Skripte: Modellparameter und MCA-Gewichte einlesen, Annuitätenfaktor."""
from pathlib import Path

import pandas as pd

# Pfad über diese Datei bestimmt, damit es aus jedem Arbeitsordner funktioniert.
# Deshalb muss das Paket editierbar installiert sein (pip install -e .).
MODEL_PARAMETERS_CSV = Path(__file__).resolve().parents[1] / 'data' / 'model_parameters' / 'model_parameters.csv'
MCA_WEIGHTS_CSV = Path(__file__).resolve().parents[1] / 'data' / 'model_parameters' / 'mca_weights.csv'


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


def read_mca_weights(group):
    """Liest die MCA-Gewichte einer Gruppe aus mca_weights.csv: Kriterium -> Gewicht.

    group = 'main'   Hauptkriterien (Summe 1)
    group = 'roads'  Straßenklassen innerhalb der Erreichbarkeit (Summe 1)

    Beispiel:
        weights = read_mca_weights('main')
        weight_water = weights['water_avalibility']
    """
    df = pd.read_csv(MCA_WEIGHTS_CSV)
    df_group = df[df['group'] == group]
    if df_group.empty:
        raise ValueError(f'mca_weights.csv: keine Zeilen für group = {group!r}')
    weights = dict(zip(df_group['criterion'], df_group['weight']))
    total = sum(weights.values())
    if abs(total - 1) > 0.001:
        print(f'Hinweis: Gewichte der Gruppe {group!r} ergeben {total:.4f} statt 1.')
    return weights


def annuity_factor(interest_rate, lifetime):
    """Annuitätenfaktor: verteilt eine Investition auf gleich hohe Jahresraten über die Lebensdauer.

    Jahreskosten der Investition [€/a] = annuity_factor(Zins, Lebensdauer) * Investition [€]

    Beispiel:
        annuity_el_2025 = annuity_factor(r, lifetime_el_2025) * p_nom_el * capex_el_2025
    """
    return ((1 + interest_rate) ** lifetime * interest_rate) / ((1 + interest_rate) ** lifetime - 1)
