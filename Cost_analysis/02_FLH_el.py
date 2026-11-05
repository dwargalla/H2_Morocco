"""Schritt 2 der Kostenanalyse: kostenoptimale Auslegung von PV, Wind und Elektrolyseur je Standort.

Baut mit PyPSA ein Modell aus Strom- und Wasserstoffbus: PV und Wind (Profile
aus ``pv_wind_electricity.csv``) speisen über einen Elektrolyseur eine feste
jährliche H2-Abgabe. Die Leistungen werden über annualisierte Kosten minimiert.
Das wird für alle 100 Standorte wiederholt. Alle Annahmen (Wirkungsgrad, Zins,
CAPEX, OPEX, Lebensdauer, H2-Menge) kommen aus model_parameters.csv, Werte des
Szenariojahres ``sizing_year``.

Eingaben:
    data/model_parameters/model_parameters.csv         Annahmen (über h2morocco.utils)
    data/interim/re_profiles/pv_wind_electricity.csv   aus 01_re_data.py

Ausgaben:
    data/interim/re_profiles/FLH_electrolyzer.csv   je Standort: FLH_electrolyzer [h/a],
                                PV und Wind in % der optimierten H2-Abgabeleistung

Hinweise:
    - Solver Gurobi (Lizenz nötig, gurobipy 12); HiGHS (highspy) ist installiert und wäre die freie Alternative.
    - Nur eine Auslegung (sizing_year); 2050 nutzt in 04 dieselbe (Fehlerprotokoll 8).
      PV/Wind werden in % gespeichert, in 04 aber als MW gelesen (F-04).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python 02_FLH_el.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import pandas as pd
import pypsa

from h2morocco.utils import annuity_factor, read_model_parameters


############################################################
# Annahmen aus data/model_parameters/model_parameters.csv
############################################################
# Dieselben Werte wie in 04_cost_analysis_h2_morocco.py. Ausgelegt wird nur einmal,
# mit den Werten des Szenariojahres sizing_year; 04 nutzt das Ergebnis für 2025 und 2050.
sizing_year = 2025
model_parameters = read_model_parameters()

discount_rate             = model_parameters['discount_rate', sizing_year]             # [–]
h2_annual_production      = model_parameters['h2_annual_production', sizing_year]      # [MWh_H2/a]
    # Elektrolyse (PEM)
electrolyzer_efficiency   = model_parameters['electrolyzer_efficiency', sizing_year]   # [–]
electrolyzer_capex        = model_parameters['electrolyzer_capex', sizing_year]        # [€/MW]
electrolyzer_opex_share   = model_parameters['electrolyzer_opex_share', sizing_year]   # [1/a]
electrolyzer_lifetime     = model_parameters['electrolyzer_lifetime', sizing_year]     # [a]
    # PV
pv_capex                  = model_parameters['pv_capex', sizing_year]                  # [€/MWp]
pv_opex_share             = model_parameters['pv_opex_share', sizing_year]             # [1/a]
pv_lifetime               = model_parameters['pv_lifetime', sizing_year]               # [a]
    # Wind
wind_capex                = model_parameters['wind_capex', sizing_year]                # [€/MW]
wind_opex_share           = model_parameters['wind_opex_share', sizing_year]           # [1/a]
wind_lifetime             = model_parameters['wind_lifetime', sizing_year]             # [a]

# Jährliche Kosten je MW Leistung (Annuität + fixe Betriebskosten) = capital_cost in PyPSA
electrolyzer_annual_cost_per_mw = (annuity_factor(discount_rate, electrolyzer_lifetime) + electrolyzer_opex_share) * electrolyzer_capex  # [€/MW/a]
pv_annual_cost_per_mw           = (annuity_factor(discount_rate, pv_lifetime)           + pv_opex_share)           * pv_capex            # [€/MWp/a]
wind_annual_cost_per_mw         = (annuity_factor(discount_rate, wind_lifetime)         + wind_opex_share)         * wind_capex          # [€/MW/a]

df_pv_wind = pd.read_csv('../data/interim/re_profiles/pv_wind_electricity.csv')


#################
# PyPSA Network #
#################
def build_network(pv_profile, wind_profile):
    """Netzwerk für einen Standort: PV und Wind speisen über den Elektrolyseur die feste H2-Jahresmenge.

    Einheiten: Leistung in MW, Energie in MWh, capital_cost in €/MW/a.
    Für jeden Standort wird ein neues Netzwerk gebaut. Früher wurde ein Netzwerk wiederverwendet
    und nur die Profile getauscht; mit HiGHS endeten dabei 33 von 100 Optimierungen ohne Lösung.
    """
    network = pypsa.Network()
    network.set_snapshots(range(len(pv_profile)))

    #Bus
    network.add("Bus", name = "bus_electricity")
    network.add("Bus", name = "bus_hydrogen")
    #Generators
    network.add("Generator", name = "pv", bus = "bus_electricity",
                p_nom_extendable = True, p_max_pu = pv_profile, capital_cost = pv_annual_cost_per_mw)
    network.add("Generator", name = "wind", bus = "bus_electricity",
                p_nom_extendable = True, p_max_pu = wind_profile, capital_cost = wind_annual_cost_per_mw)
    #Link Electrolyzer
    network.add("Link", name = "Electrolyzer", bus0 = "bus_electricity", bus1 = "bus_hydrogen",
                p_nom_extendable = True, efficiency = electrolyzer_efficiency, capital_cost = electrolyzer_annual_cost_per_mw)

    network.add("Generator", name = "negative_gen", bus = "bus_hydrogen",
                p_nom_extendable = True, sign = -1, e_sum_min = h2_annual_production, e_sum_max = h2_annual_production)
    return network


df_flh_electrolyzer = pd.DataFrame(columns=['FLH_electrolyzer'])

# Für jeden der Standorte 0 bis 99 ein eigenes Netzwerk aufbauen und optimieren
for i in range(100):
    network = build_network(df_pv_wind[f'electricity_PV_{i}'].values, df_pv_wind[f'electricity_Wind_{i}'].values)
    status, condition = network.optimize(solver_name = "gurobi")
    if condition != "optimal":
        raise RuntimeError(f"Standort {i}: Optimierung nicht optimal ({status}, {condition})")
    print(f"Standort {i}: optimal")
    flh_el = (network.generators_t.p['negative_gen'].sum())/network.generators.p_nom_opt['negative_gen']
    pv = (network.generators.p_nom_opt['pv']/network.generators.p_nom_opt['negative_gen'])*100
    wind = (network.generators.p_nom_opt['wind']/network.generators.p_nom_opt['negative_gen'])*100


    df_flh_electrolyzer.at[i, 'FLH_electrolyzer'] = flh_el
    df_flh_electrolyzer.at[i, 'PV'] = pv
    df_flh_electrolyzer.at[i, 'Wind'] = wind

df_flh_electrolyzer.to_csv('../data/interim/re_profiles/FLH_electrolyzer.csv')