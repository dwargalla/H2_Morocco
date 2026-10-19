"""Schritt 2 der Kostenanalyse: kostenoptimale Auslegung von PV, Wind und Elektrolyseur je Standort.

Baut mit PyPSA ein Modell aus Strom- und Wasserstoffbus: PV und Wind (Profile
aus ``pv_wind_electricity.csv``) speisen über einen Elektrolyseur (Wirkungsgrad
0,7) eine feste jährliche H2-Abgabe von 3,1 TWh. Die Leistungen werden über
annualisierte Kosten (Zins 4 %) minimiert. Das wird für alle 100 Standorte
wiederholt.

Eingaben:
    Data/pv_wind_electricity.csv   aus re_data.py

Ausgaben:
    Data/FLH_electrolyzer.csv   je Standort: FLH_electrolyzer [h/a],
                                PV und Wind in % der optimierten H2-Abgabeleistung

Hinweise:
    - Solver fest auf Gurobi (Lizenz nötig); HiGHS wäre eine freie Alternative.
    - Annahmen (Wirkungsgrad, Zins, Lebensdauer, OPEX) weichen von
      cost_analysis_h2_morocco.py ab (Korrekturplan F-06). PV/Wind werden in %
      gespeichert, dort aber als MW gelesen (F-04).
    - Ausführen aus ``Cost_analysis/``: ``python FLH_el.py``
"""

import pandas as pd
import pypsa

#Annahmen
#Eletrolyse (PEM)
p_nom_el = 100000                                                           #kW
eff_el = 0.7                                                                #efficiency
capex_el    = 1000                                                          # €/kW
opex_el     = 0.02 * capex_el                                               # €/kW
el_r        = 0.04                                                          # discount rate
el_lifetime = 20                                                            # years
el_annuity  = (((1 + el_r) ** el_lifetime * el_r)
                / ((1 + el_r) ** el_lifetime - 1)) * capex_el + opex_el     # €/kW

energy_production_min = 3.1e9 # kWh

capex_pv = 1000 # €/kWp
opex_pv = 0.02 * capex_pv # €/kWp
lifetime_pv = 25 # years
r_pv = 0.04 # discount rate

annuity_pv = ((1 + r_pv) ** lifetime_pv * r_pv) / ((1 + r_pv) ** lifetime_pv - 1) * capex_pv + opex_pv # €/kWp

capex_wind = 1600 # €/kW
opex_wind = 0.02 * capex_wind # €/kWp
lifetime_wind = 25 # years
r_wind = 0.04 # discount rate
annuity_wind = ((1 + r_wind) ** lifetime_wind * r_wind) / ((1 + r_wind) ** lifetime_wind - 1) * capex_wind + opex_wind # €/kWp

df_pv_wind = pd.read_csv('../data/interim/re_profiles/pv_wind_electricity.csv')
df_wind_el = df_pv_wind[f'electricity_Wind_{0}']
df_pv_el = df_pv_wind[f'electricity_PV_{0}']

network = pypsa.Network()
network.set_snapshots(range(len(df_pv_wind)))

#Bus
network.add("Bus", name = "bus_electricity")
network.add("Bus", name = "bus_hydrogen")
#Generators
network.add("Generator", name = "pv", bus = "bus_electricity", 
            p_nom_extendable = True, p_max_pu = df_pv_el, capital_cost = annuity_pv)
network.add("Generator", name = "wind", bus = "bus_electricity",
            p_nom_extendable = True, p_max_pu = df_wind_el, capital_cost = annuity_wind)
#Link Electrolyzer
network.add("Link", name = "Electrolyzer", bus0 = "bus_electricity", bus1 = "bus_hydrogen",
            p_nom_extendable = True, efficiency = eff_el, capital_cost = el_annuity)

network.add("Generator", name = "negative_gen", bus = "bus_hydrogen",
             p_nom_extendable = True, sign = -1, e_sum_min = energy_production_min, e_sum_max = energy_production_min)

df_flh_electrolyzer = pd.DataFrame(columns=['FLH_electrolyzer'])

network.optimize(solver_name = "gurobi")

pv = (network.generators.p_nom_opt['pv']/network.generators.p_nom_opt['negative_gen'])*100
wind = (network.generators.p_nom_opt['wind']/network.generators.p_nom_opt['negative_gen'])*100
flh_el = (network.generators_t.p['negative_gen'].sum())/network.generators.p_nom_opt['negative_gen']

df_flh_electrolyzer.at[0, 'FLH_electrolyzer'] = flh_el
df_flh_electrolyzer.at[0, 'PV'] = pv
df_flh_electrolyzer.at[0, 'Wind'] = wind

for i in range(1, 100):
    df_wind_el = df_pv_wind[f'electricity_Wind_{i}']
    df_pv_el = df_pv_wind[f'electricity_PV_{i}']
    network.generators_t.p_max_pu['pv'] = df_pv_el.values
    network.generators_t.p_max_pu['wind'] = df_wind_el.values
    network.optimize(solver_name = "gurobi")
    flh_el = (network.generators_t.p['negative_gen'].sum())/network.generators.p_nom_opt['negative_gen']
    pv = (network.generators.p_nom_opt['pv']/network.generators.p_nom_opt['negative_gen'])*100
    wind = (network.generators.p_nom_opt['wind']/network.generators.p_nom_opt['negative_gen'])*100


    df_flh_electrolyzer.at[i, 'FLH_electrolyzer'] = flh_el
    df_flh_electrolyzer.at[i, 'PV'] = pv
    df_flh_electrolyzer.at[i, 'Wind'] = wind

df_flh_electrolyzer.to_csv('../data/interim/re_profiles/FLH_electrolyzer.csv')