"""Karte der Infrastruktur: Straßen, Schienen und Industriehäfen (2025 und neue Häfen 2050).

Nur Abbildung, kein Einfluss auf die Ergebnisse. Die Linienfarben je
Straßenklasse sind zufällig (``np.random``), die Karte sieht also bei jedem Lauf
anders aus.

Eingaben:
    data/raw/osm/gis_osm_{roads,railways}_free_1.shp
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp
    data/raw/infrastructure/industrial_ports_morocco_{2025,2050}.shp

Ausgaben:
    results/figures/mca/morocco_infrastructure.{pdf,eps}

Hinweise:
    - Ausführen aus ``MCA/``: ``python infra_map.py``
"""

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import numpy as np

# Data
gdf_railways_utm29n = gpd.read_file('../data/raw/osm/gis_osm_railways_free_1.shp').to_crs("EPSG:32629")
gdf_railways_utm29n['fclass'] = 'railway'
gdf_roads_utm29n = gpd.read_file('../data/raw/osm/gis_osm_roads_free_1.shp').to_crs("EPSG:32629")

gdf_roads_railsways = gpd.GeoDataFrame(pd.concat([gdf_roads_utm29n, gdf_railways_utm29n], ignore_index=True), crs=gdf_roads_utm29n.crs)

classes = ['motorway', 'trunk', 'primary', 'secondary', 
           'tertiary', 'track', 'track_grade1', 'track_grade2', 
           'track_grade3', 'track_grade4', 'unclassified', 'railway']
gdf_roads_railsways = gdf_roads_railsways[gdf_roads_railsways['fclass'].isin(classes)]

# Comparison of ports in 2025 and 2050
gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
gdf_ports_2025 = gpd.read_file('../data/raw/infrastructure/industrial_ports_morocco_2025.shp').to_crs("EPSG:32629")
gdf_ports_2050 = gpd.read_file('../data/raw/infrastructure/industrial_ports_morocco_2050.shp').to_crs("EPSG:32629")
ports_2025 = set(gdf_ports_2025['name'])
ports_2050 = set(gdf_ports_2050['name'])
new_ports = ports_2050 - ports_2025
gdf_ports_new = gdf_ports_2050[gdf_ports_2050['name'].isin(new_ports)]

# Map Infrastructure
fig, ax = plt.subplots(figsize=(15, 10))
    # Ports
        # Für jeden Punkt Namen als Text hinzufügen
y_offset = 10000
x_offset = -35000
for idx, row in gdf_ports_2050.iterrows():
    x = row.geometry.x  # x-Koordinate
    y = row.geometry.y  # y-Koordinate
    name = row['name']  # Name aus Spalte 'name'
    if name in new_ports:
        if name == 'Mohammedia':
            ax.text(x + x_offset, y + y_offset*3, name, fontsize=10, color='red', 
                    ha='right', va='bottom')
        else:
            ax.text(x + x_offset, y + y_offset, name, fontsize=10, color='red', 
                ha='right', va='bottom')
    else:
        if name in ['Tanger Med', 'Tanger Ville']:
            if name == 'Tanger Med':
                ax.text(x + x_offset, y + y_offset, 'Tanger', fontsize=10, color='blue', 
                    ha='right', va='bottom')
        else:
            ax.text(x + x_offset, y + y_offset, name, fontsize=10, color='blue', 
                ha='right', va='bottom')
            
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1.5)
    # Roads and Railways
for track_class in classes:
    if track_class == 'railway':
        gdf_roads_railsways[gdf_roads_railsways['fclass'] == track_class].plot(ax=ax, label='Roads and railways',linewidth=0.1, color = np.random.rand(3,)) 
    else:
        gdf_roads_railsways[gdf_roads_railsways['fclass'] == track_class].plot(ax=ax, linewidth=0.1, color = np.random.rand(3,))
gdf_ports_2025.plot(ax=ax, color='blue', marker='o', markersize=50, label='Current ports of Morocco')
gdf_ports_new.plot(ax=ax, color='red', marker='o', markersize=50, label='Future ports of Morocco')
cx.add_basemap(ax, crs=gdf_roads_railsways.crs, source=cx.providers.CartoDB.Positron)
plt.axis('off')
plt.legend(loc = 'lower right', fontsize = 12)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_infrastructure.pdf", format="pdf", bbox_inches='tight', pad_inches=0)
plt.savefig("../results/figures/mca/morocco_infrastructure.eps", format="eps", bbox_inches='tight', pad_inches=0)
plt.show()