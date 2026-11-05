"""Schritt 2 der Kostenanalyse: kostenoptimale Auslegung von PV, Wind und Elektrolyseur je Standort.

Baut mit PyPSA ein Modell aus Strom- und Wasserstoffbus: PV und Wind (Profile
aus ``pv_wind_electricity.csv``) speisen über einen Elektrolyseur eine feste
jährliche H2-Abgabe. Die Leistungen werden über annualisierte Kosten minimiert.
Das wird für alle 100 Standorte wiederholt. Alle Annahmen (Wirkungsgrad, Zins,
CAPEX, OPEX, Lebensdauer, H2-Menge) kommen aus model_parameters.csv, Werte des
jeweiligen Szenariojahres; ausgelegt wird für 2025 und 2050 getrennt.

Eingaben:
    data/model_parameters/model_parameters.csv         Annahmen (über h2morocco.utils)
    data/raw/renewables_ninja/pv_wind_electricity.csv  aus 01_re_data.py (Download)

Ausgaben:
    data/interim/re_profiles/FLH_electrolyzer_{2025,2050}.csv   je Standort: FLH_electrolyzer [h/a],
                                PV_ratio und Wind_ratio [MW je MW Elektrolyseur]

Hinweise:
    - Solver Gurobi (Lizenz nötig, gurobipy 12); HiGHS (highspy) ist installiert und wäre die freie Alternative.
    - Je Szenariojahr eine eigene Auslegung (seit 05.11.2026; vorher nutzte 2050 die
      Auslegung von 2025, Fehlerprotokoll Nr. 8). Laufzeit daher etwa 8 Minuten.
    - Volllaststunden und Leistungsverhältnisse beziehen sich auf die optimierte
      Elektrolyseurleistung, nicht auf die frei wählbare H2-Abgabe ``negative_gen``
      (Fehlerprotokoll Nr. 17). Bis 05.11.2026 standen PV und Wind in % der H2-Abgabe
      und wurden in 04 als MW gelesen (F-04, Nr. 11).
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
# Dieselben Werte wie in 04_cost_analysis_h2_morocco.py. Ausgelegt wird je Szenariojahr
# mit dessen Kosten und Wirkungsgrad; 04 bewertet jedes Jahr mit der eigenen Auslegung.
YEARS = [2025, 2050]
model_parameters = read_model_parameters()


def sizing_parameters(year):
    """Wirkungsgrad, H2-Jahresmenge und Jahreskosten je MW (Annuität + fixe Betriebskosten) für ein Jahr."""
    m = lambda name: model_parameters[name, year]
    def annual_cost_per_mw(tech):
        return (annuity_factor(m('discount_rate'), m(f'{tech}_lifetime')) + m(f'{tech}_opex_share')) * m(f'{tech}_capex')
    return {
        'electrolyzer_efficiency': m('electrolyzer_efficiency'),                 # [–]
        'h2_annual_production':    m('h2_annual_production'),                    # [MWh_H2/a]
        'electrolyzer':            annual_cost_per_mw('electrolyzer'),           # [€/MW/a]
        'pv':                      annual_cost_per_mw('pv'),                     # [€/MWp/a]
        'wind':                    annual_cost_per_mw('wind'),                   # [€/MW/a]
    }


df_pv_wind = pd.read_csv('../data/raw/renewables_ninja/pv_wind_electricity.csv')


#################
# PyPSA Network #
#################
def build_network(pv_profile, wind_profile, par):
    """Netzwerk für einen Standort: PV und Wind speisen über den Elektrolyseur die feste H2-Jahresmenge.

    Einheiten: Leistung in MW, Energie in MWh, capital_cost in €/MW/a. ``par`` aus sizing_parameters().
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
                p_nom_extendable = True, p_max_pu = pv_profile, capital_cost = par['pv'])
    network.add("Generator", name = "wind", bus = "bus_electricity",
                p_nom_extendable = True, p_max_pu = wind_profile, capital_cost = par['wind'])
    #Link Electrolyzer
    network.add("Link", name = "Electrolyzer", bus0 = "bus_electricity", bus1 = "bus_hydrogen",
                p_nom_extendable = True, efficiency = par['electrolyzer_efficiency'], capital_cost = par['electrolyzer'])

    network.add("Generator", name = "negative_gen", bus = "bus_hydrogen",
                p_nom_extendable = True, sign = -1,
                e_sum_min = par['h2_annual_production'], e_sum_max = par['h2_annual_production'])
    return network


# Je Szenariojahr für jeden der Standorte 0 bis 99 ein eigenes Netzwerk aufbauen und optimieren
for year in YEARS:
    par = sizing_parameters(year)
    df_flh_electrolyzer = pd.DataFrame(columns=['FLH_electrolyzer'])
    for i in range(100):
        network = build_network(df_pv_wind[f'electricity_PV_{i}'].values, df_pv_wind[f'electricity_Wind_{i}'].values, par)
        status, condition = network.optimize(solver_name = "gurobi")
        if condition != "optimal":
            raise RuntimeError(f"{year}, Standort {i}: Optimierung nicht optimal ({status}, {condition})")
        print(f"{year}, Standort {i}: optimal")
        electrolyzer_mw = network.links.p_nom_opt['Electrolyzer']                     # MW_el
        flh_el = network.links_t.p0['Electrolyzer'].sum() / electrolyzer_mw           # h/a, Strom in den Elektrolyseur
        pv     = network.generators.p_nom_opt['pv'] / electrolyzer_mw                 # MW_PV je MW_el
        wind   = network.generators.p_nom_opt['wind'] / electrolyzer_mw               # MW_Wind je MW_el

        df_flh_electrolyzer.at[i, 'FLH_electrolyzer'] = flh_el
        df_flh_electrolyzer.at[i, 'PV_ratio']   = pv
        df_flh_electrolyzer.at[i, 'Wind_ratio'] = wind

    df_flh_electrolyzer.to_csv(f'../data/interim/re_profiles/FLH_electrolyzer_{year}.csv')
