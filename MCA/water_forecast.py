"""MCA-Kriterium Wasser 2050: Wasser-Score 0–100 je Zelle unter Klimawandel.

1. Bildet die klimatische Wasserbilanz CWB = Niederschlag − PET 2050 als
   Verschneidung der beiden Projektions-Layer und speichert sie.
2. Setzt das Gesamtdargebot 2050 fest auf 8535 Mio. m³/a und verteilt den
   Rückgang gegenüber 2025 proportional zu CWB × Fläche auf die Zellen.
3. Berechnet den Score wie water_net.py (50 % Dargebot, 50 % Überschuss nach
   Abzug des Verbrauchs 2050), skaliert mit den 2025-Maxima als Referenz.
   Küstenzellen erhalten 100.

Eingaben:
    Grid_morocco/grid_morocco_clear.shp
    Data/Precipitation_morocco_2050_corr.shp   (Spalte Precipitat)
    Data/PET_morocco_2050_corr.shp             (Spalte PET)
    Data/morocco_coast_line.shp
    Data/water_availability_{sw,gw}.csv
    Data/Water_Consumption_{2025,2050}.csv

Ausgaben:
    Data/cwb.shp                                   klimatische Wasserbilanz (für water_maps.py)
    results/results_water_res_availabil_2050.csv   eine Spalte, zeilengleich mit dem Raster

Hinweise:
    - Das Dargebot 2050 ist hartkodiert (Korrekturplan F-22); der Rückgang
      belastet gerade die trockensten Zellen am stärksten (F-23).
    - Die Wasserverfügbarkeit 2050 je Zelle wird nicht als CSV gespeichert;
      die Kostenanalyse nutzt eigene, ältere Dateien.
    - Doppelte Schleifen ohne räumlichen Index, läuft sehr lange.
    - Ausführen aus ``MCA/``: ``python water_forecast.py``
"""

import geopandas as gpd
import pandas as pd
import numpy as np

gdf_grid = gpd.read_file('Grid_morocco/grid_morocco_clear.shp')

# Precipitation and PET data
# Source: Future projection of droughts in Morocco and potential impact on agriculture (PDF in Teams)
gdf_precipitation   = gpd.read_file('Data/Precipitation_morocco_2050_corr.shp').to_crs('EPSG:32629')
gdf_pet             = gpd.read_file('Data/PET_morocco_2050_corr.shp').to_crs('EPSG:32629')

gdf_coast = gpd.read_file('Data/morocco_coast_line.shp').to_crs("EPSG:32629")        
df_water_2025_sw    = pd.read_csv('Data/water_availability_sw.csv')
df_water_2025_gw    = pd.read_csv('Data/water_availability_gw.csv')
df_water_consumption_2025 = pd.read_csv('Data/Water_Consumption_2025.csv')
df_water_consumption_2050 = pd.read_csv('Data/Water_Consumption_2050.csv')
ds_water_ges_2025        = (+ df_water_2025_gw['water_availability_gw[MCM]']  
                       + df_water_2025_sw['water_availability_sw[MCM]'])

list_geoms  = []
list_values = []
for i in range(len(gdf_precipitation)):
    for j in range(len(gdf_pet)):
        if gdf_precipitation.geometry[i].intersects(gdf_pet.geometry[j]):
            geom    = gdf_precipitation.geometry[i].intersection(gdf_pet.geometry[j])
            value   = gdf_precipitation.at[i,'Precipitat'] - gdf_pet.at[j, 'PET']
            list_values.append(value)
            list_geoms.append(geom)

gdf_cwb = gpd.GeoDataFrame(geometry=list_geoms, data={'CWB':list_values}, crs=gdf_precipitation.crs)
gdf_cwb.to_file('Data/cwb.shp', driver='ESRI Shapefile')

water_supply_2025   = ds_water_ges_2025.sum()    #MCM
water_supply_2050   = 8535                  #MCM
water_loss_2050     = water_supply_2025 - water_supply_2050 #MCM, is positiv but loss --> x MCM water of loss > 1 --> water withdrawl

list_cwb_cell       = [] 
for i in range(len(gdf_grid)):
    cwb_cell = 0
    for j in range(len(gdf_cwb)):
        if gdf_grid.geometry[i].intersects(gdf_cwb.geometry[j]):
            area_cell_in_gdf_cwb    = (gdf_grid.geometry[i].intersection(gdf_cwb.geometry[j])).area
            cwb_cell                += gdf_cwb.at[j,'CWB'] * area_cell_in_gdf_cwb   #Is always negativ mm*m^2
        if j == len(gdf_cwb)-1:
            list_cwb_cell.append(cwb_cell)

df_cwb_cell = pd.DataFrame(data={'CWP_zell':list_cwb_cell}) #CWB for each cell 
df_total_loss_water_cell = (df_cwb_cell['CWP_zell']/df_cwb_cell['CWP_zell'].sum()) * water_loss_2050    #Is positiv, Anteil_zelle_loss * Gesamtloss = Zellenloss
df_water_cell_2050 = ds_water_ges_2025 - df_total_loss_water_cell    #Pos or neg water in each cell

# Score for 2050
ds_water_res_2025 = (- df_water_consumption_2025['Water_Consumption[BCM]'] * 10**9 
            + df_water_2025_gw['water_availability_gw[MCM]'] *10**6 
            + df_water_2025_sw['water_availability_sw[MCM]'] *10**6)
ds_water_res_2050 = (- df_water_consumption_2050['Water_Consumption[BCM]'] * 10**9 
            + df_water_cell_2050 *10**6)

# 50/50 between Wateravailability and Wateravailability residual
ds_water_res = ds_water_res_2050.copy()
ds_water_avail = df_water_cell_2050.copy()

ds_water_res.loc[ds_water_res <= 0] = 0
ds_water_res.loc[ds_water_res > 0] = ((ds_water_res.loc[ds_water_res > 0] - ds_water_res.loc[ds_water_res > 0].min())/
                              (ds_water_res_2025.max() - ds_water_res.loc[ds_water_res > 0].min())) * 50                 #2025 as benchmark

ds_water_avail.loc[ds_water_avail <= 0] = 0
ds_water_avail.loc[ds_water_avail > 0] = ((ds_water_avail.loc[ds_water_avail > 0] - ds_water_avail.loc[ds_water_avail > 0].min())/
                              (ds_water_ges_2025.max() - ds_water_avail.loc[ds_water_avail > 0].min())) * 50                 #2025 as benchmark

ds_water_50_50 = ds_water_avail + ds_water_res

    # Cost = 100, negativ values = 0, positiv values min-max scale
list_water = []
for i in range(len(gdf_grid)):
    cell = gdf_grid.geometry[i]
    cell_intersection = cell.intersects(gdf_coast.geometry)
    
    if any(cell_intersection):
        score = 100
    else:
        score = ds_water_50_50[i]

    list_water.append(score)

df_water = pd.DataFrame(data = list_water)

df_water.to_csv('results/results_water_res_availabil_2050.csv', index=False)