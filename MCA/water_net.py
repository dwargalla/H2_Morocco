"""MCA-Kriterium Wasser 2025: Wasser-Score 0–100 je Zelle.

Score = 50 × min-max(Dargebot) + 50 × min-max(Überschuss), mit
Dargebot = Grund- + Oberflächenwasser und Überschuss = Dargebot − Verbrauch
(Überschuss ≤ 0 ergibt 0 Punkte). Zellen, die die Küstenlinie berühren,
erhalten pauschal 100 (Meerwasserentsalzung möglich).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/interim/qgis/morocco_coast_line.shp        (derzeit eine Rekonstruktion, siehe
                                        data/README.md)
    data/interim/water/water_availability_gw.csv     aus water_exploitable_gw.py
    data/interim/water/water_availability_sw.csv     aus water_exploitable_sw.py
    data/interim/water/Water_Consumption_2025.csv    aus water_consumption.py

Ausgaben:
    data/interim/mca_criteria/results_water_res_available.csv   eine Spalte, zeilengleich mit dem Raster

Hinweise:
    - Ausführen aus ``MCA/``: ``python water_net.py``
"""

import geopandas as gpd
import numpy as np
import pandas as pd

gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')

gdf_coast = gpd.read_file('../data/interim/qgis/morocco_coast_line.shp').to_crs("EPSG:32629")        

# Today
df_gw_availability = pd.read_csv('../data/interim/water/water_availability_gw.csv')
df_sw_availability = pd.read_csv('../data/interim/water/water_availability_sw.csv')
df_water_consumption = pd.read_csv('../data/interim/water/Water_Consumption_2025.csv')

# 50/50 between Wateravailability and Wateravailability residual
ds_water_res = (- df_water_consumption['Water_Consumption[BCM]'] * 10**9 
            + df_gw_availability['water_availability_gw[MCM]'] *10**6 
            + df_sw_availability['water_availability_sw[MCM]'] *10**6)

ds_water_avail = (df_gw_availability['water_availability_gw[MCM]'] 
            + df_sw_availability['water_availability_sw[MCM]'])

    # Cost = 100, negativ values = 0, positiv values min-max scale
ds_water_res.loc[ds_water_res <= 0] = 0
ds_water_res.loc[ds_water_res > 0] = ((ds_water_res.loc[ds_water_res > 0] - ds_water_res.loc[ds_water_res > 0].min())/
                              (ds_water_res.loc[ds_water_res > 0].max() - ds_water_res.loc[ds_water_res > 0].min())) * 50

ds_water_avail = ((ds_water_avail - ds_water_avail.min())/
            (ds_water_avail.max()-ds_water_avail.min())) * 50

ds_water_50_50 = ds_water_avail + ds_water_res

     # Check if cell is at coast, if yes give score 100
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

df_water.to_csv('../data/interim/mca_criteria/results_water_res_available.csv', index=False)