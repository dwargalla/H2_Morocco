"""Karte der No-Go-Gebiete: Militär, Naturschutz, Erholungsgebiete (OSM) und Steilhänge (Topografie).

Nur Abbildung, kein Einfluss auf die Ergebnisse (die Maske selbst erzeugt
no_go_zones.py).

Eingaben:
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp
    data/raw/osm/gis_osm_landuse_a_free_1.shp
    data/interim/qgis/ToPo_1500.shp

Ausgaben:
    results/figures/mca/morocco_nogos.png

Hinweise:
    - Ausführen aus ``MCA/``: ``python nogo_maps.py``
"""

import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as cx
import matplotlib.patches as mpatches
import os
from dotenv import load_dotenv

# Hintergrundkarte: CARTO-Kacheln brauchen einen API-Key (CARTO_API_KEY in H2_Morocco/.env)
load_dotenv('../.env')
if not os.getenv('CARTO_API_KEY'):
    raise SystemExit('CARTO_API_KEY fehlt: .env.example nach .env kopieren und Key eintragen.')
basemap = cx.providers.CartoDB.Positron(apikey=os.getenv('CARTO_API_KEY'))

gdf_morocco_boundary    = gpd.read_file('../data/raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs("EPSG:32629")
# Data 
###
gdf_landuse_utm29n = gpd.read_file('../data/raw/osm/gis_osm_landuse_a_free_1.shp').to_crs("EPSG:32629")

    # NO-GO Zones: Military, Nature Reserve, Recreation Ground
gdf_nogo_zones = gdf_landuse_utm29n[gdf_landuse_utm29n['fclass'].isin(['military', 'nature_reserve', 'recreation_ground'])]
gdf_nogo_zones.reset_index(drop=True, inplace=True)
gdf_nogo_zones.index = range(len(gdf_nogo_zones))
###
gdf_topo_utm29n = gpd.read_file('../data/interim/qgis/ToPo_1500.shp').to_crs("EPSG:32629")   #Already 1 or 0, done in QGIS with grid-statistics


# Map MCA diff
fig, ax = plt.subplots(figsize=(15, 10))
gdf_morocco_boundary.plot(ax=ax, edgecolor='black', facecolor="none", linewidth=1)
gdf_topo_utm29n[gdf_topo_utm29n['NoGo'] == 0].plot(ax=ax, color='grey',edgecolor='none', alpha=0.8, label='Steep slope area')
gdf_nogo_zones[gdf_nogo_zones['fclass'] == 'military'].plot(ax=ax, color='red', label='Military area')
gdf_nogo_zones[gdf_nogo_zones['fclass'] == 'nature_reserve'].plot(ax=ax, color='green', label='Nature reserve')
gdf_nogo_zones[gdf_nogo_zones['fclass'] == 'recreation_ground'].plot(ax=ax, color='blue', label='Recreation ground')
cx.add_basemap(ax, crs=gdf_morocco_boundary.crs, source=basemap)
plt.axis('off')
legend_handles = [
    mpatches.Patch(color='red', label='Military area'),
    mpatches.Patch(color='green', label='Nature reserve'),
    mpatches.Patch(color='blue', label='Recreation ground'),
    mpatches.Patch(color='grey', label='Steep slope area')
]
plt.legend(handles=legend_handles, loc='lower right', fontsize=12)
plt.tight_layout()
plt.savefig("../results/figures/mca/morocco_nogos.png", format="png", dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()