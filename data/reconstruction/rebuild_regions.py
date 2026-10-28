"""Ersetzt die 12 Verwaltungsregionen ``Regions.shp`` (Gliederung ab 2015).

Das Original ist verloren und nicht wiederzufinden. Ersatz: ``Morocco-Regions.geojson``
aus https://github.com/Salah-Zkara/Morocco-GeoJson. Die Spalte ``nom_region`` wird
zu ``Nom_Region``; zwei Schreibweisen werden an die Schlüssel von
``dict_urbanisation_rates`` in ``MCA/forecast_landuse.py`` angepasst.

Eingaben:
    data/raw/boundaries/Morocco-Regions.geojson   wird geladen, falls nicht vorhanden

Ausgaben:
    data/raw/boundaries/Regions.shp   Spalte ``Nom_Region``

Hinweise:
    - Kontrolle: ``forecast_landuse.py`` + Stadtanteil 2050 trifft dieselben 194
      Stadtzellen wie ``results_urban_2050.csv``, Summe −0,06 %. geoBoundaries
      (+0,5 %) passt schlechter, HDX hat nur 10 Regionen.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python rebuild_regions.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import os

import geopandas as gpd
import requests

URL = 'https://raw.githubusercontent.com/Salah-Zkara/Morocco-GeoJson/master/Morocco-Regions.geojson'
PATH_SOURCE = '../raw/boundaries/Morocco-Regions.geojson'

if not os.path.exists(PATH_SOURCE):
    response = requests.get(URL, timeout=120)
    response.raise_for_status()
    with open(PATH_SOURCE, 'wb') as f:
        f.write(response.content)

gdf_regions = gpd.read_file(PATH_SOURCE).rename(columns={'nom_region': 'Nom_Region'})
gdf_regions['Nom_Region'] = gdf_regions['Nom_Region'].replace({'Tanger-Tétouan-Al Hoceima': 'Tanger-Tetouan-Al Hoceima',
                                                               'Fés-Meknés': 'Fès-Meknès'})
gdf_regions[['Nom_Region', 'geometry']].to_file('../raw/boundaries/Regions.shp')
print(sorted(gdf_regions['Nom_Region']))
