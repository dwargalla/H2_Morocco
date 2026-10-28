"""Schritt 4 der Kostenanalyse: Wasserstoffkosten je Rasterzelle für 2025 und 2050 (Hauptmodell).

Betrachtet einen 100-MW-PEM-Elektrolyseur. Ablauf:
    1. Abstände aller Zellen untereinander (7219 × 7219) und zum nächsten
       Industriehafen berechnen.
    2. Jahreskosten für Elektrolyseur, PV, Wind, HGÜ-Leitung (je km) plus
       Konverterpaar und H2-Pipeline (je km) aus den Annahmen im Kopf berechnen
       (CAPEX, OPEX, Lebensdauer, Zins 8 %, Quellen in den Kommentaren).
    3. Jeder Zelle den repräsentativen Standort zuordnen, dessen (FLH_PV,
       FLH_Wind) ihren eigenen Werten am nächsten liegt.
    4. Für jede Bedarfszelle die günstigste Produktionszelle wählen
       (Strom + Elektrolyse + Netz über die Entfernung + Pipeline zum Hafen).
    5. Wasserkosten addieren: 13 kg Wasser je kg H2, bezogen in der Reihenfolge
       Oberflächenwasser → Grundwasser → Entsalzung (nur Küste) → Transport aus
       der nächsten Zelle mit Wasser.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/raw/infrastructure/industrial_ports_morocco_{2025,2050}.shp
    data/interim/re_profiles/data_re_flh_electrolyzer.shp   aus 03_assignment_re_data.py
    data/interim/re_profiles/flh_re.csv                     aus 01_re_data.py
    data/interim/qgis/cell_flh_re.csv                FLH je Zelle (nicht per Skript erzeugt, vermutlich QGIS)
    data/interim/qgis/morocco_coast_line.shp
    data/interim/water_cost/water_availability_{sw,gw}.csv, data/interim/water_cost/water_availability_{sw,gw}_2050.csv
                                        (eigene Fassung, weicht von data/interim/water/ ab)

Ausgaben:
    results/cost/results_cost_2025.csv   je Zelle: Produktionszelle, FLH, Kostenanteile
    results/cost/results_cost_2050.csv   (Wasser, Elektrolyse, EE, Netz, Pipeline) und
                                 Gesamtpreis in €/MWh_H2

Hinweise:
    - Die Distanzmatrix und ihre Sortierung brauchen mehrere GB Arbeitsspeicher.
    - Bekannte Fehler laut Korrekturplan (Patch in Korrektur/code_fixes.patch):
      PV/Wind-Leistung in % als MW gelesen (F-04), Konverterkosten auch bei
      Distanz 0 (F-05), PV-Jahreskosten mit CAPEX statt OPEX (F-07).
    - Der 2050-Block rechnet Wasser mit den 2025-Preisvariablen (Werte derzeit gleich).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python 04_cost_analysis_h2_morocco.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd 
import numpy as np
import pandas as pd

# Data
    # Current cost map
gdf_grid_morocco            = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp').to_crs("EPSG:32629")
gdf_grid_centroid           = gdf_grid_morocco.geometry.centroid
    # Industrial ports
    # Source: OSM, via QGIS
gdf_ports_2025              = gpd.read_file("../data/raw/infrastructure/industrial_ports_morocco_2025.shp").to_crs(gdf_grid_morocco.crs)
gdf_ports_2050              = gpd.read_file("../data/raw/infrastructure/industrial_ports_morocco_2050.shp").to_crs(gdf_grid_morocco.crs)
    # RE and Eletrolysis data, FLH electrolyzer, flh pv und wind, Leistung PV und Wind
    # Via Pypsa
gdf_re_data                 = gpd.read_file('../data/interim/re_profiles/data_re_flh_electrolyzer.shp').to_crs(gdf_grid_morocco.crs)
df_re_flh                   = pd.read_csv('../data/interim/re_profiles/flh_re.csv')
df_re_flh_cell              = pd.read_csv('../data/interim/qgis/cell_flh_re.csv')

# Wateravaulability each cell
gdf_coast       = gpd.read_file('../data/interim/qgis/morocco_coast_line.shp').to_crs("EPSG:32629")        
df_sw_2025      = pd.read_csv('../data/interim/water_cost/water_availability_sw.csv')
df_gw_2025      = pd.read_csv('../data/interim/water_cost/water_availability_gw.csv')
df_sw_2050      = pd.read_csv('../data/interim/water_cost/water_availability_sw_2050.csv')
df_gw_2050      = pd.read_csv('../data/interim/water_cost/water_availability_gw_2050.csv')
index_sw_2050_with_water = df_sw_2050[df_sw_2050['0'] > 0 ].index
index_gw_2050_with_water = df_gw_2050[df_gw_2050['0'] > 0 ].index

list_cells_at_cost = gdf_grid_morocco.intersects(gdf_coast.union_all())
list_index_cost = list_cells_at_cost[list_cells_at_cost == True].index

list_indexes = list(index_sw_2050_with_water) + list(index_gw_2050_with_water) + list(list_index_cost)
list_without_duplicates = list(dict.fromkeys(list_indexes))

# Distance all cells to all cells
list_distance = []
for i in range(len(gdf_grid_morocco)):
    list_distance.append(gdf_grid_centroid.distance(gdf_grid_centroid[i]))

df_distance_cells = pd.DataFrame(list_distance)
df_distance_cells = df_distance_cells / 1000  # Convert to km

# Für performance verbesserung:
distance_matric = df_distance_cells.values
sorted_indices = np.argsort(distance_matric, axis=1)

# Distance all cells to ports for 2025
list_distance_ports_2025 = []
for i in range(len(gdf_grid_morocco)):
    list_distance_ports_2025.append(min(gdf_ports_2025.distance(gdf_grid_centroid[i])))

df_distance_ports_2025 = pd.DataFrame(list_distance_ports_2025)
df_distance_ports_2025 = df_distance_ports_2025/1000  # Convert to km
gdf_distance_ports_2025 = gpd.GeoDataFrame(geometry=gdf_grid_morocco.geometry, data=df_distance_ports_2025)

# Distance all cells to ports for 2050
list_distance_ports_2050 = []
for i in range(len(gdf_grid_morocco)):
    list_distance_ports_2050.append(min(gdf_ports_2050.distance(gdf_grid_centroid[i])))

df_distance_ports_2050 = pd.DataFrame(list_distance_ports_2050)
df_distance_ports_2050 = df_distance_ports_2050/1000  # Convert to km
gdf_distance_ports_2050 = gpd.GeoDataFrame(geometry=gdf_grid_morocco.geometry, data=df_distance_ports_2050)

# Assumptions
    #Electrolysis
        # 2025
p_nom_el            = 100                   # [MW]
eff_el_2025         = 0.6                   # [–] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf
capex_el_2025       = 1075000               # [€/MW] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf
opex_el_2025        = 0.05 * capex_el_2025  # [€/MW/a] # Source: https://wupperinst.org/fileadmin/redaktion/downloads/projects/MENA-Fuels_Teilbericht_12_Handelsmodell.pdf
r                   = 0.08                  # discount rate # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf
lifetime_el_2025    = 10                    # [a] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf

annuity_el_2025  = (((1 + r) ** lifetime_el_2025 * r)
                / ((1 + r) ** lifetime_el_2025 - 1)) * p_nom_el * capex_el_2025 # €/a
annual_cost_el_2025 = annuity_el_2025 + opex_el_2025 * p_nom_el                 # €/a
        # 2050
eff_el_2050         = 0.8                   # [–] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf
capex_el_2050       = 214000                # [€/MW] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf, 2050 dann 200€/kW
opex_el_2050        = 0.05 * capex_el_2050  # [€/MW/a] # Source: https://wupperinst.org/fileadmin/redaktion/downloads/projects/MENA-Fuels_Teilbericht_12_Handelsmodell.pdf
lifetime_el_2050    = 13                    # [a] # Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Dec/IRENA_Green_hydrogen_cost_2020.pdf

annuity_el_2050  = (((1 + r) ** lifetime_el_2050 * r)
                / ((1 + r) ** lifetime_el_2050 - 1)) * p_nom_el * capex_el_2050    # €/a
annual_cost_el_2050 = annuity_el_2050 + opex_el_2050 * p_nom_el  # €/a

# Watercost
    # 2025
lco_gw_2025             = 0.05      # €/m³ extraction costs. Source: https://ageconsearch.umn.edu/record/56961/?v=pdf
lco_desalination_2025   = 1         # €/m³ Source: Economic concepts to address future water supply–demand imbalances in Iran, Morocco and Saudi Arabia (ist schon im Latex drin)
lco_sw_2025             = 0.19      # €/m³ Source: Economic concepts to address future water supply–demand imbalances in Iran, Morocco and Saudi Arabia (ist schon im Latex drin)

    # 2050
lco_gw_2050             = 0.05      # Annahme, da keine Quelle für den forecast gefunden. SW und Desalination bleiben ebenfalls gleich 
lco_desalination_2050   = 1         # €/m³ Source: Economic concepts to address future water supply–demand imbalances in Iran, Morocco and Saudi Arabia (ist schon im Latex drin)
lco_sw_2050             = 0.19      # €/m³ Source: Economic concepts to address future water supply–demand imbalances in Iran, Morocco and Saudi Arabia (ist schon im Latex drin)

    # Water transport costs
spez_transport_costs    = 0.0007     # €/m^3/km, Source: Evaluating the costs of desalination and water transport 

# PV Cost
p_nom_pv  = gdf_re_data['PV']   # [MW]
    # 2025
capex_pv_2025   = 675000                    # [€/MWp] Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2025/Jul/IRENA_TEC_RPGC_in_2024_2025.pdf
opex_pv_2025    = 0.02 * capex_pv_2025      # [€/MWp/a] Annahme
lifetime_pv     = 25                        # [a] Annahme
annuity_pv_2025 = (((1 + r) ** lifetime_pv * r) / 
              ((1 + r) ** lifetime_pv - 1)) * p_nom_pv * capex_pv_2025 # €/a
annual_cost_pv_2025 = annuity_pv_2025 + capex_pv_2025 * p_nom_pv  # €/a

    # 2050
capex_pv_2050   = 466000                    # [€/MWp] Source: https://wupperinst.org/fileadmin/redaktion/downloads/projects/MENA-Fuels_Teilbericht_12_Handelsmodell.pdf
opex_pv_2050    = 0.02 * capex_pv_2050      # [€/MWp/a] Annahme
annuity_pv_2050 = (((1 + r) ** lifetime_pv * r) / 
              ((1 + r) ** lifetime_pv - 1)) * p_nom_pv * capex_pv_2050 # €/a
annual_cost_pv_2050 = annuity_pv_2050 + capex_pv_2050 * p_nom_pv  # €/a

# Wind Cost
p_nom_wind = gdf_re_data['Wind']    # [MW]
    #2025
capex_wind_2025     = 1155000                       # [€/MW] Source: https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2025/Jul/IRENA_TEC_RPGC_in_2024_2025.pdf
opex_wind_2025      = 0.02 * capex_wind_2025        # [€/MW] Annahme
lifetime_wind       = 25                            # [a] Annahme
annuity_wind_2025   = (((1 + r) ** lifetime_wind * r) / 
                ((1 + r) ** lifetime_wind - 1)) * capex_wind_2025 * p_nom_wind  # €/a
annual_cost_wind_2025 = annuity_wind_2025 + opex_wind_2025 * p_nom_wind         # €/a

    # 2050
capex_wind_2050 = 1008000                            # [€/MW] Source: https://wupperinst.org/fileadmin/redaktion/downloads/projects/MENA-Fuels_Teilbericht_12_Handelsmodell.pdf
opex_wind_2050 = 0.02 * capex_wind_2050             # [€/MW] Annahme
annuity_wind_2050   = (((1 + r) ** lifetime_wind * r) / 
                ((1 + r) ** lifetime_wind - 1)) * capex_wind_2050 * p_nom_wind  # €/a
annual_cost_wind_2050 = annuity_wind_2050 + opex_wind_2050 * p_nom_wind         # €/a

# Store costs into df
    # 2025
gdf_re_data['Cost_pv_2025 [EUR/a]']     = annual_cost_pv_2025
gdf_re_data['Cost_wind_2025 [EUR/a]']   = annual_cost_wind_2025
gdf_re_data['Cost_re_2025 [EUR/a]']     = annual_cost_pv_2025 + annual_cost_wind_2025
    # 2050
gdf_re_data['Cost_pv_2050 [EUR/a]']     = annual_cost_pv_2050
gdf_re_data['Cost_wind_2050 [EUR/a]']   = annual_cost_wind_2050
gdf_re_data['Cost_re_2050 [EUR/a]']     = annual_cost_pv_2050 + annual_cost_wind_2050

#Grid Cost
    # 2025
capex_dc_line_2025          = 597                                           # €/km/MW Source: https://www.netzentwicklungsplan.de/sites/default/files/paragraphs-files/Kostenschaetzungen_NEP_2030_2_Entwurf.pdf
capex_converter_2025        = 358000                                        # €/MW Source: https://www.netzentwicklungsplan.de/sites/default/files/paragraphs-files/Kostenschaetzungen_NEP_2030_2_Entwurf.pdf
lifetime_dc                 = 40                                            # years Source: https://plus.netzausbau.de/N2000/DE/Technik/Freileitungen/freileitungen-node.html
opex_dc_line_2025           = 0.01 * capex_dc_line_2025 * p_nom_el          # €/km/a
opex_converter_2025         = 0.01 * capex_converter_2025 * p_nom_el * 2    # €/a
annuity_dc_line_2025        = (((1 + r) ** lifetime_dc * r) 
                                / ((1 + r) ** lifetime_dc - 1)) * capex_dc_line_2025 * p_nom_el            # €/km/a
annuity_converrter_2025     = (((1 + r) ** lifetime_dc * r) 
                                / ((1 + r) ** lifetime_dc - 1)) * p_nom_el * 2 * capex_converter_2025       # €/a
annual_cost_converter_2025  = annuity_converrter_2025 + opex_converter_2025                                 # €/a
annual_cost_dc_line_2025    = annuity_dc_line_2025 + opex_dc_line_2025                                      # €/km/a

df_dc_cost_cells_2025 = df_distance_cells.where(df_distance_cells.isnull(), df_distance_cells * annual_cost_dc_line_2025 + annual_cost_converter_2025) 

    # 2050
capex_dc_line_2050          = 597                                           # €/km/MW Source: https://www.netzentwicklungsplan.de/sites/default/files/2023-02/NEP_2035_2021_1_Entwurf_Kostenschaetzungen_0.pdf
capex_converter_2050        = 358000                                        # €/MW Source: https://www.netzentwicklungsplan.de/sites/default/files/2023-02/NEP_2035_2021_1_Entwurf_Kostenschaetzungen_0.pdf
opex_dc_line_2050           = 0.01 * capex_dc_line_2050 * p_nom_el          # €/km/a
opex_converter_2050         = 0.01 * capex_converter_2050 * p_nom_el * 2    # €/a
annuity_dc_line_2050        = (((1 + r) ** lifetime_dc * r) 
                                / ((1 + r) ** lifetime_dc - 1)) * capex_dc_line_2050 * p_nom_el             # €/km/a
annuity_converrter_2050     = (((1 + r) ** lifetime_dc * r) 
                                / ((1 + r) ** lifetime_dc - 1)) * p_nom_el * 2 * capex_converter_2050       # €/a
annual_cost_converter_2050  = annuity_converrter_2050 + opex_converter_2050                                 # €/a
annual_cost_dc_line_2050    = annuity_dc_line_2050 + opex_dc_line_2050                                      # €/km/a

df_dc_cost_cells_2050 = df_distance_cells.where(df_distance_cells.isnull(), df_distance_cells * annual_cost_dc_line_2050 + annual_cost_converter_2050) 

#H2 Pipeline Cost
    # 2025
capex_h2_pipe_2025  = 1.125 * 1000         # €/km/MW_h2 Source: https://www.sciencedirect.com/science/article/pii/S030626192300733X?ref=pdf_download&fr=RR-2&rr=97c7db524cd03633
h2_pipe_lifetime    = 40                        # years
opex_h2_2025             = 0.01 * capex_h2_pipe_2025            # €//km/MW_h2/a
annuity_h2_pipe_2025     = (((1 + r) ** h2_pipe_lifetime * r) 
                       / ((1 + r) ** h2_pipe_lifetime - 1)) * p_nom_el * eff_el_2025 * capex_h2_pipe_2025   # €/km/a
annual_cost_h2_pipe_2025 = annuity_h2_pipe_2025 + opex_h2_2025 * p_nom_el * eff_el_2025                     # €/km/a

df_h2_pipe_cost_cells_2025 = df_distance_ports_2025 * annual_cost_h2_pipe_2025

    # 2050
capex_h2_pipe_2050  = 0.589 * 1000         # €/km/MW_h2 Source: https://www.sciencedirect.com/science/article/pii/S030626192300733X?ref=pdf_download&fr=RR-2&rr=97c7db524cd03633
opex_h2_2050        = 0.01 * capex_h2_pipe_2050      # €//km/MW_h2/a
annuity_h2_pipe_2050     = (((1 + r) ** h2_pipe_lifetime * r) 
                       / ((1 + r) ** h2_pipe_lifetime - 1)) * p_nom_el * eff_el_2050 * capex_h2_pipe_2050   # €/km/a
annual_cost_h2_pipe_2050 = annuity_h2_pipe_2050 + opex_h2_2050 * p_nom_el * eff_el_2050                     # €/km/a

df_h2_pipe_cost_cells_2050 = df_distance_ports_2050 * annual_cost_h2_pipe_2050

#Zuweisung der RE Quelle
df_cost_cells_2025 = pd.DataFrame()
df_cost_cells_2050 = pd.DataFrame()
for i in range(len(gdf_grid_centroid)):
    ref_points = df_re_flh[['FLH_PV', 'FLH_Wind']].values
    comp_point = df_re_flh_cell.iloc[i].values
    d = np.sqrt(np.sum((ref_points - comp_point) ** 2, axis=1))
    idx = np.argmin(d)
    df_cost_cells_2025.at[i, 'Cost_re_2025 [EUR/a]'] = gdf_re_data.at[idx, 'Cost_re_2025 [EUR/a]']
    df_cost_cells_2025.at[i, 'FLH_electrolyzer']     = gdf_re_data.at[idx, 'FLH_electr']
    df_cost_cells_2050.at[i, 'Cost_re_2050 [EUR/a]'] = gdf_re_data.at[idx, 'Cost_re_2050 [EUR/a]']
    df_cost_cells_2050.at[i, 'FLH_electrolyzer']     = gdf_re_data.at[idx, 'FLH_electr']

df_h2_cost_share_2025 = pd.DataFrame(columns= ['index_source_cell', 'FLH_electrolyzer' , 
                                               'Water_cost [EUR/MWh_h2]', 'Electrolyzer_cost [EUR/MWh_h2]', 
                                               'RE_cost [EUR/MWh_h2]', 'Distribution_cost [EUR/MWh_h2]', 
                                               'Pipeline_cost [EUR/MWh_h2]', 'H2_Price_2025 [EUR/MWh_h2]'], 
                                               index=range(len(gdf_grid_morocco)))

df_h2_cost_share_2050 = pd.DataFrame(columns= ['index_source_cell', 'FLH_electrolyzer' , 
                                               'Water_cost [EUR/MWh_h2]', 'Electrolyzer_cost [EUR/MWh_h2]', 
                                               'RE_cost [EUR/MWh_h2]', 'Distribution_cost [EUR/MWh_h2]', 
                                               'Pipeline_cost [EUR/MWh_h2]', 'H2_Price_2050 [EUR/MWh_h2]'], 
                                               index=range(len(gdf_grid_morocco)))

# Calculating H2 costs for each cell
print('Beginn Schleife')
for i in range(len(gdf_grid_morocco)):
    # Fortschrittbalken:
    if i % 200 == 0:
        print(f'Berechnung für Zelle {i} von {len(gdf_grid_morocco)}')
    # 2025
    cost_cell_2025   = ((annual_cost_el_2025 + df_dc_cost_cells_2025[i] + df_cost_cells_2025['Cost_re_2025 [EUR/a]'] + df_h2_pipe_cost_cells_2025.iat[i, 0])
                    /(df_cost_cells_2025['FLH_electrolyzer']*p_nom_el*eff_el_2025))  # Cost per MWh_h2
    idx_cell_2025    = cost_cell_2025.idxmin()  # Index of the cell with the lowest cost for the cell
    cost_2025        = cost_cell_2025.min() # Cost per MWh_h2
        # Water Costs
    h2_production = (df_cost_cells_2025['FLH_electrolyzer']*p_nom_el*eff_el_2025).loc[idx_cell_2025]    # MWh_h2
    h2_kg = h2_production * 1000 / 33.33    # Convert MWh_h2 into kg_h2
    water_consumption = h2_kg * 13          # Calculate water demand [dm^3] (1 kg h2 = 13 kg water)
    water_consumption = water_consumption / 1000    # Convert to m^3
    
    # Use at first the cheepest option for water and so on
    use_sw      = min(water_consumption, df_sw_2025.loc[i, 'water_availability_sw[MCM]'] * 10**6)
    res_demand  = water_consumption - use_sw
    water_cost  = use_sw * lco_sw_2025

    if res_demand > 0:
        use_gw = min(res_demand, df_gw_2025.loc[i, 'water_availability_gw[MCM]'] * 10**6)
        res_demand = res_demand - use_gw
        water_cost += use_gw * lco_gw_2025
        if res_demand > 0:
            cell = gdf_grid_morocco.geometry[i]
            cell_intersection = cell.intersects(gdf_coast.geometry)
            if any(cell_intersection):
                use_desalination = res_demand
                water_cost += use_desalination * lco_desalination_2025
            else: # we have to transport water from other cell
                for idx_next_nearest_cell in sorted_indices[i]:
                    if idx_next_nearest_cell == i:
                        continue  # Skip the same cell
                    next_nearest_cell = df_distance_cells.iat[i, idx_next_nearest_cell]
                    add_use_sw = min(res_demand, 
                                    df_sw_2025.loc[idx_next_nearest_cell, 'water_availability_sw[MCM]'] * 10**6)
                    res_demand = res_demand - add_use_sw
                    water_cost += add_use_sw * lco_sw_2025
                    add_water_use = add_use_sw
                    if res_demand > 0:
                        add_use_gw = min(res_demand, 
                                         df_gw_2025.loc[idx_next_nearest_cell, 'water_availability_gw[MCM]'] * 10**6)
                        res_demand = res_demand - add_use_gw
                        water_cost += add_use_gw * lco_gw_2025
                        add_water_use += add_use_gw
                        if res_demand > 0:
                            cell = gdf_grid_morocco.geometry[idx_next_nearest_cell]
                            cell_intersection = cell.intersects(gdf_coast.geometry)
                            if any(cell_intersection):
                                use_desalination = res_demand
                                water_cost += use_desalination * lco_desalination_2025
                                add_water_use += use_desalination
                                res_demand = 0
                    transport_costs = next_nearest_cell * spez_transport_costs * add_water_use  # €
                    water_cost += transport_costs
                    if res_demand <= 0:
                        break
    # Store results 2025
    df_h2_cost_share_2025.at[i, 'index_source_cell']                = idx_cell_2025
    df_h2_cost_share_2025.at[i, 'FLH_electrolyzer']                 = df_cost_cells_2025['FLH_electrolyzer'].loc[idx_cell_2025]
    df_h2_cost_share_2025.at[i, 'Water_cost [EUR/MWh_h2]']          = water_cost/h2_production
    df_h2_cost_share_2025.at[i, 'Electrolyzer_cost [EUR/MWh_h2]']   = annual_cost_el_2025/h2_production
    df_h2_cost_share_2025.at[i, 'RE_cost [EUR/MWh_h2]']             = df_cost_cells_2025['Cost_re_2025 [EUR/a]'].loc[idx_cell_2025]/h2_production
    df_h2_cost_share_2025.at[i, 'Distribution_cost [EUR/MWh_h2]']   = df_dc_cost_cells_2025[i].loc[idx_cell_2025]/h2_production
    df_h2_cost_share_2025.at[i, 'Pipeline_cost [EUR/MWh_h2]']       = df_h2_pipe_cost_cells_2025.iat[i, 0]/h2_production
    df_h2_cost_share_2025.at[i, 'H2_Price_2025 [EUR/MWh_h2]']       = cost_2025 + water_cost/h2_production

    # 2050
    cost_cell_2050   = ((annual_cost_el_2050 + df_dc_cost_cells_2050[i] + df_cost_cells_2050['Cost_re_2050 [EUR/a]'] + df_h2_pipe_cost_cells_2050.iat[i, 0])
                    /(df_cost_cells_2050['FLH_electrolyzer']*p_nom_el*eff_el_2050))  # Cost per MWh_h2
    idx_cell_2050    = cost_cell_2050.idxmin()  # Index of the cell with the lowest cost for the cell
    cost_2050        = cost_cell_2050.min()
        # Water Costs
    h2_production = (df_cost_cells_2050['FLH_electrolyzer']*p_nom_el*eff_el_2050).loc[idx_cell_2050]    # MWh_h2
    h2_kg = h2_production * 1000 / 33.33    # Convert MWh_h2 into kg_h2
    water_consumption = h2_kg * 13          # Calculate water demand [dm^3] (1 kg h2 = 13 kg water)
    water_consumption = water_consumption / 1000    # Convert to m^3
    
    # Use at first the cheepest option for water and so on
    use_sw      = min(water_consumption, df_sw_2050.loc[i, '0'] * 10**6)
    res_demand  = water_consumption - use_sw
    water_cost  = use_sw * lco_sw_2025

    if res_demand > 0:
        use_gw = min(res_demand, df_gw_2050.loc[i, '0'] * 10**6)
        res_demand = res_demand - use_gw
        water_cost += use_gw * lco_gw_2025
        if res_demand > 0:
            cell = gdf_grid_morocco.geometry[i]
            cell_intersection = cell.intersects(gdf_coast.geometry)
            if any(cell_intersection):
                use_desalination = res_demand
                water_cost += use_desalination * lco_desalination_2025
            else: # we have to transport water from other cell
                for idx_next_nearest_cell in sorted_indices[i]:
                    if idx_next_nearest_cell == i:
                        continue  # Skip the same cell
                    if idx_next_nearest_cell not in list_without_duplicates:
                        continue  # Skip cells without water availability
                    next_nearest_cell = df_distance_cells.iat[i, idx_next_nearest_cell]
                    add_use_sw = min(res_demand, 
                                    df_sw_2050.loc[idx_next_nearest_cell, '0'] * 10**6)
                    res_demand = res_demand - add_use_sw
                    water_cost += add_use_sw * lco_sw_2025
                    add_water_use = add_use_sw
                    if res_demand > 0:
                        add_use_gw = min(res_demand, 
                                         df_gw_2050.loc[idx_next_nearest_cell, '0'] * 10**6)
                        res_demand = res_demand - add_use_gw
                        water_cost += add_use_gw * lco_gw_2025
                        add_water_use += add_use_gw
                        if res_demand > 0:
                            cell = gdf_grid_morocco.geometry[idx_next_nearest_cell]
                            cell_intersection = cell.intersects(gdf_coast.geometry)
                            if any(cell_intersection):
                                use_desalination = res_demand
                                water_cost += use_desalination * lco_desalination_2025
                                add_water_use += use_desalination
                                res_demand = 0
                    transport_costs = next_nearest_cell * spez_transport_costs * add_water_use  # €
                    water_cost += transport_costs
                    if res_demand <= 0:
                        break

    h2_water_costs_2050 = water_cost/(df_cost_cells_2050['FLH_electrolyzer']*p_nom_el*eff_el_2050).loc[idx_cell_2050]
        
        # Store results 2050
    df_h2_cost_share_2050.at[i, 'index_source_cell']                = idx_cell_2050
    df_h2_cost_share_2050.at[i, 'FLH_electrolyzer']                 = df_cost_cells_2050['FLH_electrolyzer'].loc[idx_cell_2050]
    df_h2_cost_share_2050.at[i, 'Water_cost [EUR/MWh_h2]']          = water_cost/h2_production
    df_h2_cost_share_2050.at[i, 'Electrolyzer_cost [EUR/MWh_h2]']   = annual_cost_el_2050/h2_production
    df_h2_cost_share_2050.at[i, 'RE_cost [EUR/MWh_h2]']             = df_cost_cells_2050['Cost_re_2050 [EUR/a]'].loc[idx_cell_2050]/h2_production
    df_h2_cost_share_2050.at[i, 'Distribution_cost [EUR/MWh_h2]']   = df_dc_cost_cells_2050[i].loc[idx_cell_2050]/h2_production
    df_h2_cost_share_2050.at[i, 'Pipeline_cost [EUR/MWh_h2]']       = df_h2_pipe_cost_cells_2050.iat[i, 0]/h2_production
    df_h2_cost_share_2050.at[i, 'H2_Price_2050 [EUR/MWh_h2]']       = cost_2050 + water_cost/h2_production


gdf_cost_cells_2025 = gpd.GeoDataFrame(df_h2_cost_share_2025, geometry=gdf_grid_morocco.geometry, crs=gdf_grid_morocco.crs)
gdf_cost_cells_2050 = gpd.GeoDataFrame(df_h2_cost_share_2050, geometry=gdf_grid_morocco.geometry, crs=gdf_grid_morocco.crs)

df_h2_cost_share_2025.to_csv('../results/cost/results_cost_2025.csv', index=False)

df_h2_cost_share_2050.to_csv('../results/cost/results_cost_2050.csv', index=False)