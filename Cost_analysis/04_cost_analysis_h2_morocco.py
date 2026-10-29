"""Schritt 4 der Kostenanalyse: Wasserstoffkosten je Rasterzelle für 2025 und 2050 (Hauptmodell).

Betrachtet einen 100-MW-PEM-Elektrolyseur. Ablauf:
    1. Abstände aller Zellen untereinander (7219 × 7219) und zum nächsten
       Industriehafen berechnen.
    2. Jahreskosten für Elektrolyseur, PV, Wind, HGÜ-Leitung (je km) plus
       Konverterpaar und H2-Pipeline (je km) berechnen. Alle Annahmen
       (CAPEX, OPEX, Lebensdauer, Zins, Quellen) stehen in
       data/model_parameters/model_parameters.csv.
    3. Jeder Zelle den repräsentativen Standort zuordnen, dessen (FLH_PV,
       FLH_Wind) ihren eigenen Werten am nächsten liegt.
    4. Für jede Bedarfszelle die günstigste Produktionszelle wählen
       (Strom + Elektrolyse + Netz über die Entfernung + Pipeline zum Hafen).
    5. Wasserkosten addieren: 13 kg Wasser je kg H2, bezogen in der Reihenfolge
       Oberflächenwasser → Grundwasser → Entsalzung (nur Küste) → Transport aus
       der nächsten Zelle mit Wasser.

Eingaben:
    data/model_parameters/model_parameters.csv               Annahmen und Literaturwerte (über h2morocco.utils)
    data/interim/grid/grid_morocco_clear.shp
    data/raw/infrastructure/industrial_ports_morocco_{2025,2050}.shp
    data/interim/re_profiles/data_re_flh_electrolyzer.shp   aus 03_assignment_re_data.py
    data/interim/re_profiles/flh_re.csv                     aus 01_re_data.py
    data/interim/qgis/cell_flh_re.csv                FLH je Zelle (nicht per Skript erzeugt, vermutlich QGIS)
    data/interim/qgis/morocco_coast_line.shp
    data/interim/water_cost/water_availability_{sw,gw}.csv, data/interim/water_cost/water_availability_{sw,gw}_2050.csv

Ausgaben:
    results/cost/results_cost_2025.csv   je Zelle: Produktionszelle, FLH, Kostenanteile
    results/cost/results_cost_2050.csv   (Wasser, Elektrolyse, EE, Netz, Pipeline) und
                                 Gesamtpreis in €/MWh_H2

Hinweise:
    - Die Distanzmatrix und ihre Sortierung brauchen mehrere GB Arbeitsspeicher.
    - Bekannte Fehler laut Korrekturplan (Patch in Korrektur/code_fixes.patch):
      PV/Wind-Leistung in % als MW gelesen (F-04), Konverterkosten auch bei
      Distanz 0 (F-05), PV-Jahreskosten mit CAPEX statt OPEX (F-07).
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

from h2morocco.utils import annuity_factor, read_model_parameters

# Data
    # Raster
gdf_grid                    = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp').to_crs("EPSG:32629")
cell_centroids              = gdf_grid.geometry.centroid
    # Industrial ports
    # Source: OSM, via QGIS
gdf_ports_2025              = gpd.read_file("../data/raw/infrastructure/industrial_ports_morocco_2025.shp").to_crs(gdf_grid.crs)
gdf_ports_2050              = gpd.read_file("../data/raw/infrastructure/industrial_ports_morocco_2050.shp").to_crs(gdf_grid.crs)
    # Repräsentative Standorte (Referenzpunkte) aus 02_FLH_el.py (PyPSA):
    # FLH Elektrolyseur, PV- und Windleistung
gdf_ref_points              = gpd.read_file('../data/interim/re_profiles/data_re_flh_electrolyzer.shp').to_crs(gdf_grid.crs)
df_ref_points_flh           = pd.read_csv('../data/interim/re_profiles/flh_re.csv')    # FLH PV und Wind je Referenzpunkt
df_cell_flh                 = pd.read_csv('../data/interim/qgis/cell_flh_re.csv')      # FLH PV und Wind je Zelle

# Wasserverfügbarkeit je Zelle [Mio. m³]
gdf_coast                   = gpd.read_file('../data/interim/qgis/morocco_coast_line.shp').to_crs("EPSG:32629")
df_surface_water_2025       = pd.read_csv('../data/interim/water_cost/water_availability_sw.csv')
df_ground_water_2025        = pd.read_csv('../data/interim/water_cost/water_availability_gw.csv')
df_surface_water_2050       = pd.read_csv('../data/interim/water_cost/water_availability_sw_2050.csv')
df_ground_water_2050        = pd.read_csv('../data/interim/water_cost/water_availability_gw_2050.csv')

cells_with_surface_water_2050 = df_surface_water_2050[df_surface_water_2050['0'] > 0 ].index
cells_with_ground_water_2050  = df_ground_water_2050[df_ground_water_2050['0'] > 0 ].index

is_coastal_cell = gdf_grid.intersects(gdf_coast.union_all())
coastal_cells   = is_coastal_cell[is_coastal_cell == True].index

# Zellen, aus denen 2050 Wasser bezogen werden kann (Oberflächen- oder Grundwasser oder Küste)
cells_with_water_or_coast_2050 = list(cells_with_surface_water_2050) + list(cells_with_ground_water_2050) + list(coastal_cells)
cells_with_water_or_coast_2050 = list(dict.fromkeys(cells_with_water_or_coast_2050))  # Duplikate entfernen

# Distance all cells to all cells
list_distance = []
for i in range(len(gdf_grid)):
    list_distance.append(cell_centroids.distance(cell_centroids[i]))

df_distance_km = pd.DataFrame(list_distance)
df_distance_km = df_distance_km / 1000  # Convert to km

# Für jede Zelle alle anderen Zellen nach Entfernung sortiert (für die Suche nach Wasser in der Nähe)
cells_by_distance = np.argsort(df_distance_km.values, axis=1)

# Distance all cells to ports for 2025
list_distance_ports_2025 = []
for i in range(len(gdf_grid)):
    list_distance_ports_2025.append(min(gdf_ports_2025.distance(cell_centroids[i])))

df_distance_port_km_2025 = pd.DataFrame(list_distance_ports_2025)
df_distance_port_km_2025 = df_distance_port_km_2025/1000  # Convert to km

# Distance all cells to ports for 2050
list_distance_ports_2050 = []
for i in range(len(gdf_grid)):
    list_distance_ports_2050.append(min(gdf_ports_2050.distance(cell_centroids[i])))

df_distance_port_km_2050 = pd.DataFrame(list_distance_ports_2050)
df_distance_port_km_2050 = df_distance_port_km_2050/1000  # Convert to km

# Assumptions: alle Werte, Einheiten und Quellen in data/model_parameters/model_parameters.csv
model_parameters = read_model_parameters()

discount_rate               = model_parameters['discount_rate', 2025]               # [–], gleich für 2050
electrolyzer_capacity       = model_parameters['electrolyzer_capacity', 2025]       # [MW], gleich für 2050
h2_lower_heating_value      = model_parameters['h2_lower_heating_value', 2025]      # [kWh/kg]
electrolysis_water_demand   = model_parameters['electrolysis_water_demand', 2025]   # [kg Wasser / kg H2]

    #Electrolysis
        # 2025
electrolyzer_efficiency_2025 = model_parameters['electrolyzer_efficiency', 2025]                               # [–]
electrolyzer_capex_2025      = model_parameters['electrolyzer_capex', 2025]                                    # [€/MW]
electrolyzer_opex_2025       = model_parameters['electrolyzer_opex_share', 2025] * electrolyzer_capex_2025     # [€/MW/a]
electrolyzer_lifetime_2025   = model_parameters['electrolyzer_lifetime', 2025]                                 # [a]

electrolyzer_annuity_2025     = annuity_factor(discount_rate, electrolyzer_lifetime_2025) * electrolyzer_capacity * electrolyzer_capex_2025  # €/a
electrolyzer_annual_cost_2025 = electrolyzer_annuity_2025 + electrolyzer_opex_2025 * electrolyzer_capacity                                  # €/a
        # 2050
electrolyzer_efficiency_2050 = model_parameters['electrolyzer_efficiency', 2050]                               # [–]
electrolyzer_capex_2050      = model_parameters['electrolyzer_capex', 2050]                                    # [€/MW]
electrolyzer_opex_2050       = model_parameters['electrolyzer_opex_share', 2050] * electrolyzer_capex_2050     # [€/MW/a]
electrolyzer_lifetime_2050   = model_parameters['electrolyzer_lifetime', 2050]                                 # [a]

electrolyzer_annuity_2050     = annuity_factor(discount_rate, electrolyzer_lifetime_2050) * electrolyzer_capacity * electrolyzer_capex_2050  # €/a
electrolyzer_annual_cost_2050 = electrolyzer_annuity_2050 + electrolyzer_opex_2050 * electrolyzer_capacity                                  # €/a

# Watercost [€/m³]
    # 2025
water_surface_cost_2025         = model_parameters['water_surface_cost', 2025]
water_ground_cost_2025          = model_parameters['water_ground_cost', 2025]
water_desalination_cost_2025    = model_parameters['water_desalination_cost', 2025]
    # 2050
water_surface_cost_2050         = model_parameters['water_surface_cost', 2050]
water_ground_cost_2050          = model_parameters['water_ground_cost', 2050]
water_desalination_cost_2050    = model_parameters['water_desalination_cost', 2050]

    # Water transport costs [€/m³/km]
water_transport_cost_2025       = model_parameters['water_transport_cost', 2025]
water_transport_cost_2050       = model_parameters['water_transport_cost', 2050]

# PV Cost
pv_capacity = gdf_ref_points['PV']   # [MW] (bekannter Fehler F-04: eigentlich Prozent)
pv_lifetime = model_parameters['pv_lifetime', 2025]                       # [a], gleich für 2050
    # 2025
pv_capex_2025   = model_parameters['pv_capex', 2025]                      # [€/MWp]
pv_opex_2025    = model_parameters['pv_opex_share', 2025] * pv_capex_2025 # [€/MWp/a] (wegen F-07 bisher ungenutzt)
pv_annuity_2025 = annuity_factor(discount_rate, pv_lifetime) * pv_capacity * pv_capex_2025  # €/a
pv_annual_cost_2025 = pv_annuity_2025 + pv_capex_2025 * pv_capacity  # €/a (bekannter Fehler F-07: CAPEX statt OPEX)

    # 2050
pv_capex_2050   = model_parameters['pv_capex', 2050]                      # [€/MWp]
pv_opex_2050    = model_parameters['pv_opex_share', 2050] * pv_capex_2050 # [€/MWp/a] (wegen F-07 bisher ungenutzt)
pv_annuity_2050 = annuity_factor(discount_rate, pv_lifetime) * pv_capacity * pv_capex_2050  # €/a
pv_annual_cost_2050 = pv_annuity_2050 + pv_capex_2050 * pv_capacity  # €/a (bekannter Fehler F-07: CAPEX statt OPEX)

# Wind Cost
wind_capacity = gdf_ref_points['Wind']    # [MW] (bekannter Fehler F-04: eigentlich Prozent)
wind_lifetime = model_parameters['wind_lifetime', 2025]                         # [a], gleich für 2050
    #2025
wind_capex_2025     = model_parameters['wind_capex', 2025]                      # [€/MW]
wind_opex_2025      = model_parameters['wind_opex_share', 2025] * wind_capex_2025   # [€/MW/a]
wind_annuity_2025   = annuity_factor(discount_rate, wind_lifetime) * wind_capex_2025 * wind_capacity  # €/a
wind_annual_cost_2025 = wind_annuity_2025 + wind_opex_2025 * wind_capacity                             # €/a

    # 2050
wind_capex_2050     = model_parameters['wind_capex', 2050]                      # [€/MW]
wind_opex_2050      = model_parameters['wind_opex_share', 2050] * wind_capex_2050   # [€/MW/a]
wind_annuity_2050   = annuity_factor(discount_rate, wind_lifetime) * wind_capex_2050 * wind_capacity  # €/a
wind_annual_cost_2050 = wind_annuity_2050 + wind_opex_2050 * wind_capacity                             # €/a

# Store costs into df
    # 2025
gdf_ref_points['Cost_pv_2025 [EUR/a]']     = pv_annual_cost_2025
gdf_ref_points['Cost_wind_2025 [EUR/a]']   = wind_annual_cost_2025
gdf_ref_points['Cost_re_2025 [EUR/a]']     = pv_annual_cost_2025 + wind_annual_cost_2025
    # 2050
gdf_ref_points['Cost_pv_2050 [EUR/a]']     = pv_annual_cost_2050
gdf_ref_points['Cost_wind_2050 [EUR/a]']   = wind_annual_cost_2050
gdf_ref_points['Cost_re_2050 [EUR/a]']     = pv_annual_cost_2050 + wind_annual_cost_2050

# Grid Cost: HGÜ-Leitung von der Produktions- zur Bedarfszelle plus je eine Konverterstation an beiden Enden
hvdc_line_lifetime      = model_parameters['hvdc_line_lifetime', 2025]          # [a], gleich für 2050
hvdc_converter_lifetime = model_parameters['hvdc_converter_lifetime', 2025]     # [a], gleich für 2050
hvdc_converter_count    = model_parameters['hvdc_converter_count', 2025]        # [–], gleich für 2050
    # 2025
hvdc_line_capex_2025        = model_parameters['hvdc_line_capex', 2025]                                                     # €/km/MW
hvdc_converter_capex_2025   = model_parameters['hvdc_converter_capex', 2025]                                                # €/MW
hvdc_line_opex_2025         = model_parameters['hvdc_line_opex_share', 2025] * hvdc_line_capex_2025 * electrolyzer_capacity  # €/km/a
hvdc_converter_opex_2025    = (model_parameters['hvdc_converter_opex_share', 2025] * hvdc_converter_capex_2025
                               * electrolyzer_capacity * hvdc_converter_count)                                              # €/a
hvdc_line_annuity_2025      = annuity_factor(discount_rate, hvdc_line_lifetime) * hvdc_line_capex_2025 * electrolyzer_capacity  # €/km/a
hvdc_converter_annuity_2025 = (annuity_factor(discount_rate, hvdc_converter_lifetime)
                               * electrolyzer_capacity * hvdc_converter_count * hvdc_converter_capex_2025)                  # €/a
hvdc_converter_annual_cost_2025 = hvdc_converter_annuity_2025 + hvdc_converter_opex_2025                                    # €/a
hvdc_line_annual_cost_2025      = hvdc_line_annuity_2025 + hvdc_line_opex_2025                                              # €/km/a

# Jahreskosten der Verbindung zwischen je zwei Zellen [€/a]
# Bekannter Fehler F-05: .where greift nie (keine NaN), die Konverter zählen auch bei Distanz 0
df_hvdc_cost_2025 = df_distance_km.where(df_distance_km.isnull(), df_distance_km * hvdc_line_annual_cost_2025 + hvdc_converter_annual_cost_2025)

    # 2050
hvdc_line_capex_2050        = model_parameters['hvdc_line_capex', 2050]                                                     # €/km/MW
hvdc_converter_capex_2050   = model_parameters['hvdc_converter_capex', 2050]                                                # €/MW
hvdc_line_opex_2050         = model_parameters['hvdc_line_opex_share', 2050] * hvdc_line_capex_2050 * electrolyzer_capacity  # €/km/a
hvdc_converter_opex_2050    = (model_parameters['hvdc_converter_opex_share', 2050] * hvdc_converter_capex_2050
                               * electrolyzer_capacity * hvdc_converter_count)                                              # €/a
hvdc_line_annuity_2050      = annuity_factor(discount_rate, hvdc_line_lifetime) * hvdc_line_capex_2050 * electrolyzer_capacity  # €/km/a
hvdc_converter_annuity_2050 = (annuity_factor(discount_rate, hvdc_converter_lifetime)
                               * electrolyzer_capacity * hvdc_converter_count * hvdc_converter_capex_2050)                  # €/a
hvdc_converter_annual_cost_2050 = hvdc_converter_annuity_2050 + hvdc_converter_opex_2050                                    # €/a
hvdc_line_annual_cost_2050      = hvdc_line_annuity_2050 + hvdc_line_opex_2050                                              # €/km/a

df_hvdc_cost_2050 = df_distance_km.where(df_distance_km.isnull(), df_distance_km * hvdc_line_annual_cost_2050 + hvdc_converter_annual_cost_2050)

#H2 Pipeline Cost: von der Bedarfszelle zum nächsten Hafen, ausgelegt auf die H2-Leistung
h2_pipeline_lifetime = model_parameters['h2_pipeline_lifetime', 2025]        # [a], gleich für 2050
    # 2025
h2_pipeline_capex_2025 = model_parameters['h2_pipeline_capex', 2025]                                 # €/km/MW_h2
h2_pipeline_opex_2025  = model_parameters['h2_pipeline_opex_share', 2025] * h2_pipeline_capex_2025   # €/km/MW_h2/a
h2_pipeline_annuity_2025 = (annuity_factor(discount_rate, h2_pipeline_lifetime)
                            * electrolyzer_capacity * electrolyzer_efficiency_2025 * h2_pipeline_capex_2025)                  # €/km/a
h2_pipeline_annual_cost_2025 = h2_pipeline_annuity_2025 + h2_pipeline_opex_2025 * electrolyzer_capacity * electrolyzer_efficiency_2025  # €/km/a

df_h2_pipeline_cost_2025 = df_distance_port_km_2025 * h2_pipeline_annual_cost_2025      # €/a je Zelle

    # 2050
h2_pipeline_capex_2050 = model_parameters['h2_pipeline_capex', 2050]                                 # €/km/MW_h2
h2_pipeline_opex_2050  = model_parameters['h2_pipeline_opex_share', 2050] * h2_pipeline_capex_2050   # €/km/MW_h2/a
h2_pipeline_annuity_2050 = (annuity_factor(discount_rate, h2_pipeline_lifetime)
                            * electrolyzer_capacity * electrolyzer_efficiency_2050 * h2_pipeline_capex_2050)                  # €/km/a
h2_pipeline_annual_cost_2050 = h2_pipeline_annuity_2050 + h2_pipeline_opex_2050 * electrolyzer_capacity * electrolyzer_efficiency_2050  # €/km/a

df_h2_pipeline_cost_2050 = df_distance_port_km_2050 * h2_pipeline_annual_cost_2050      # €/a je Zelle

#Zuweisung der RE Quelle: jede Zelle bekommt den Referenzpunkt mit den ähnlichsten (FLH_PV, FLH_Wind)
df_cell_re_2025 = pd.DataFrame()
df_cell_re_2050 = pd.DataFrame()
for i in range(len(cell_centroids)):
    ref_flh  = df_ref_points_flh[['FLH_PV', 'FLH_Wind']].values
    cell_flh = df_cell_flh.iloc[i].values
    flh_distance = np.sqrt(np.sum((ref_flh - cell_flh) ** 2, axis=1))
    nearest_ref_point = np.argmin(flh_distance)
    df_cell_re_2025.at[i, 'Cost_re_2025 [EUR/a]'] = gdf_ref_points.at[nearest_ref_point, 'Cost_re_2025 [EUR/a]']
    df_cell_re_2025.at[i, 'FLH_electrolyzer']     = gdf_ref_points.at[nearest_ref_point, 'FLH_electr']
    df_cell_re_2050.at[i, 'Cost_re_2050 [EUR/a]'] = gdf_ref_points.at[nearest_ref_point, 'Cost_re_2050 [EUR/a]']
    df_cell_re_2050.at[i, 'FLH_electrolyzer']     = gdf_ref_points.at[nearest_ref_point, 'FLH_electr']

df_results_2025 = pd.DataFrame(columns= ['index_source_cell', 'FLH_electrolyzer' ,
                                         'Water_cost [EUR/MWh_h2]', 'Electrolyzer_cost [EUR/MWh_h2]',
                                         'RE_cost [EUR/MWh_h2]', 'Distribution_cost [EUR/MWh_h2]',
                                         'Pipeline_cost [EUR/MWh_h2]', 'H2_Price_2025 [EUR/MWh_h2]'],
                                         index=range(len(gdf_grid)))

df_results_2050 = pd.DataFrame(columns= ['index_source_cell', 'FLH_electrolyzer' ,
                                         'Water_cost [EUR/MWh_h2]', 'Electrolyzer_cost [EUR/MWh_h2]',
                                         'RE_cost [EUR/MWh_h2]', 'Distribution_cost [EUR/MWh_h2]',
                                         'Pipeline_cost [EUR/MWh_h2]', 'H2_Price_2050 [EUR/MWh_h2]'],
                                         index=range(len(gdf_grid)))

# Calculating H2 costs for each cell
print('Beginn Schleife')
for i in range(len(gdf_grid)):
    # Fortschrittbalken:
    if i % 200 == 0:
        print(f'Berechnung für Zelle {i} von {len(gdf_grid)}')
    # 2025
    # H2-Kosten je MWh_h2 für Zelle i, wenn sie aus jeder möglichen Produktionszelle versorgt wird
    cost_per_source_cell_2025 = ((electrolyzer_annual_cost_2025 + df_hvdc_cost_2025[i] + df_cell_re_2025['Cost_re_2025 [EUR/a]'] + df_h2_pipeline_cost_2025.iat[i, 0])
                                 /(df_cell_re_2025['FLH_electrolyzer']*electrolyzer_capacity*electrolyzer_efficiency_2025))
    source_cell_2025      = cost_per_source_cell_2025.idxmin()  # günstigste Produktionszelle
    lcoh_2025_excl_water  = cost_per_source_cell_2025.min()     # €/MWh_h2 ohne Wasser
        # Water Costs
    h2_production_mwh = (df_cell_re_2025['FLH_electrolyzer']*electrolyzer_capacity*electrolyzer_efficiency_2025).loc[source_cell_2025]    # MWh_h2
    h2_kg = h2_production_mwh * 1000 / h2_lower_heating_value     # Convert MWh_h2 into kg_h2
    water_demand_m3 = h2_kg * electrolysis_water_demand           # Calculate water demand [dm^3] (1 kg water = 1 dm^3)
    water_demand_m3 = water_demand_m3 / 1000                      # Convert to m^3


    ##########################
    # Water Cost calculation #
    ##########################

    # Use at first the cheapest option for water and so on
    surface_water_used  = min(water_demand_m3, df_surface_water_2025.loc[i, 'water_availability_sw[MCM]'] * 10**6)
    remaining_demand    = water_demand_m3 - surface_water_used
    water_cost          = surface_water_used * water_surface_cost_2025


    if remaining_demand > 0: # we have to use groundwater
        ground_water_used = min(remaining_demand, df_ground_water_2025.loc[i, 'water_availability_gw[MCM]'] * 10**6)
        remaining_demand = remaining_demand - ground_water_used
        water_cost += ground_water_used * water_ground_cost_2025
        if remaining_demand > 0: # we have to use desalination or transport water from other cell
            cell_is_coastal = any(gdf_grid.geometry[i].intersects(gdf_coast.geometry))
            if cell_is_coastal:
                desalinated_water = remaining_demand
                water_cost += desalinated_water * water_desalination_cost_2025
            else: # we have to transport water from other cell
                for neighbour_cell in cells_by_distance[i]:
                    if neighbour_cell == i:
                        continue  # Skip the same cell
                    distance_to_neighbour_km = df_distance_km.iat[i, neighbour_cell]
                    neighbour_surface_water = min(remaining_demand,
                                                  df_surface_water_2025.loc[neighbour_cell, 'water_availability_sw[MCM]'] * 10**6)
                    remaining_demand = remaining_demand - neighbour_surface_water
                    water_cost += neighbour_surface_water * water_surface_cost_2025
                    water_from_neighbour = neighbour_surface_water
                    if remaining_demand > 0:
                        neighbour_ground_water = min(remaining_demand,
                                                     df_ground_water_2025.loc[neighbour_cell, 'water_availability_gw[MCM]'] * 10**6)
                        remaining_demand = remaining_demand - neighbour_ground_water
                        water_cost += neighbour_ground_water * water_ground_cost_2025
                        water_from_neighbour += neighbour_ground_water
                        if remaining_demand > 0:
                            neighbour_is_coastal = any(gdf_grid.geometry[neighbour_cell].intersects(gdf_coast.geometry))
                            if neighbour_is_coastal:
                                desalinated_water = remaining_demand
                                water_cost += desalinated_water * water_desalination_cost_2025
                                water_from_neighbour += desalinated_water
                                remaining_demand = 0
                    transport_cost = distance_to_neighbour_km * water_transport_cost_2025 * water_from_neighbour  # €
                    water_cost += transport_cost
                    if remaining_demand <= 0:
                        break
    # Store results 2025
    df_results_2025.at[i, 'index_source_cell']                = source_cell_2025
    df_results_2025.at[i, 'FLH_electrolyzer']                 = df_cell_re_2025['FLH_electrolyzer'].loc[source_cell_2025]
    df_results_2025.at[i, 'Water_cost [EUR/MWh_h2]']          = water_cost/h2_production_mwh
    df_results_2025.at[i, 'Electrolyzer_cost [EUR/MWh_h2]']   = electrolyzer_annual_cost_2025/h2_production_mwh
    df_results_2025.at[i, 'RE_cost [EUR/MWh_h2]']             = df_cell_re_2025['Cost_re_2025 [EUR/a]'].loc[source_cell_2025]/h2_production_mwh
    df_results_2025.at[i, 'Distribution_cost [EUR/MWh_h2]']   = df_hvdc_cost_2025[i].loc[source_cell_2025]/h2_production_mwh
    df_results_2025.at[i, 'Pipeline_cost [EUR/MWh_h2]']       = df_h2_pipeline_cost_2025.iat[i, 0]/h2_production_mwh
    df_results_2025.at[i, 'H2_Price_2025 [EUR/MWh_h2]']       = lcoh_2025_excl_water + water_cost/h2_production_mwh

    # 2050
    cost_per_source_cell_2050 = ((electrolyzer_annual_cost_2050 + df_hvdc_cost_2050[i] + df_cell_re_2050['Cost_re_2050 [EUR/a]'] + df_h2_pipeline_cost_2050.iat[i, 0])
                                 /(df_cell_re_2050['FLH_electrolyzer']*electrolyzer_capacity*electrolyzer_efficiency_2050))
    source_cell_2050      = cost_per_source_cell_2050.idxmin()  # günstigste Produktionszelle
    lcoh_2050_excl_water  = cost_per_source_cell_2050.min()     # €/MWh_h2 ohne Wasser
        # Water Costs
    h2_production_mwh = (df_cell_re_2050['FLH_electrolyzer']*electrolyzer_capacity*electrolyzer_efficiency_2050).loc[source_cell_2050]    # MWh_h2
    h2_kg = h2_production_mwh * 1000 / h2_lower_heating_value     # Convert MWh_h2 into kg_h2
    water_demand_m3 = h2_kg * electrolysis_water_demand           # Calculate water demand [dm^3] (1 kg water = 1 dm^3)
    water_demand_m3 = water_demand_m3 / 1000                      # Convert to m^3

    # Use at first the cheapest option for water and so on
    surface_water_used  = min(water_demand_m3, df_surface_water_2050.loc[i, '0'] * 10**6)
    remaining_demand    = water_demand_m3 - surface_water_used
    water_cost          = surface_water_used * water_surface_cost_2050

    if remaining_demand > 0:
        ground_water_used = min(remaining_demand, df_ground_water_2050.loc[i, '0'] * 10**6)
        remaining_demand = remaining_demand - ground_water_used
        water_cost += ground_water_used * water_ground_cost_2050
        if remaining_demand > 0:
            cell_is_coastal = any(gdf_grid.geometry[i].intersects(gdf_coast.geometry))
            if cell_is_coastal:
                desalinated_water = remaining_demand
                water_cost += desalinated_water * water_desalination_cost_2050
            else: # we have to transport water from other cell
                for neighbour_cell in cells_by_distance[i]:
                    if neighbour_cell == i:
                        continue  # Skip the same cell
                    if neighbour_cell not in cells_with_water_or_coast_2050:
                        continue  # Skip cells without water availability
                    distance_to_neighbour_km = df_distance_km.iat[i, neighbour_cell]
                    neighbour_surface_water = min(remaining_demand,
                                                  df_surface_water_2050.loc[neighbour_cell, '0'] * 10**6)
                    remaining_demand = remaining_demand - neighbour_surface_water
                    water_cost += neighbour_surface_water * water_surface_cost_2050
                    water_from_neighbour = neighbour_surface_water
                    if remaining_demand > 0:
                        neighbour_ground_water = min(remaining_demand,
                                                     df_ground_water_2050.loc[neighbour_cell, '0'] * 10**6)
                        remaining_demand = remaining_demand - neighbour_ground_water
                        water_cost += neighbour_ground_water * water_ground_cost_2050
                        water_from_neighbour += neighbour_ground_water
                        if remaining_demand > 0:
                            neighbour_is_coastal = any(gdf_grid.geometry[neighbour_cell].intersects(gdf_coast.geometry))
                            if neighbour_is_coastal:
                                desalinated_water = remaining_demand
                                water_cost += desalinated_water * water_desalination_cost_2050
                                water_from_neighbour += desalinated_water
                                remaining_demand = 0
                    transport_cost = distance_to_neighbour_km * water_transport_cost_2050 * water_from_neighbour  # €
                    water_cost += transport_cost
                    if remaining_demand <= 0:
                        break

        # Store results 2050
    df_results_2050.at[i, 'index_source_cell']                = source_cell_2050
    df_results_2050.at[i, 'FLH_electrolyzer']                 = df_cell_re_2050['FLH_electrolyzer'].loc[source_cell_2050]
    df_results_2050.at[i, 'Water_cost [EUR/MWh_h2]']          = water_cost/h2_production_mwh
    df_results_2050.at[i, 'Electrolyzer_cost [EUR/MWh_h2]']   = electrolyzer_annual_cost_2050/h2_production_mwh
    df_results_2050.at[i, 'RE_cost [EUR/MWh_h2]']             = df_cell_re_2050['Cost_re_2050 [EUR/a]'].loc[source_cell_2050]/h2_production_mwh
    df_results_2050.at[i, 'Distribution_cost [EUR/MWh_h2]']   = df_hvdc_cost_2050[i].loc[source_cell_2050]/h2_production_mwh
    df_results_2050.at[i, 'Pipeline_cost [EUR/MWh_h2]']       = df_h2_pipeline_cost_2050.iat[i, 0]/h2_production_mwh
    df_results_2050.at[i, 'H2_Price_2050 [EUR/MWh_h2]']       = lcoh_2050_excl_water + water_cost/h2_production_mwh


df_results_2025.to_csv('../results/cost/results_cost_2025.csv', index=False)

df_results_2050.to_csv('../results/cost/results_cost_2050.csv', index=False)
