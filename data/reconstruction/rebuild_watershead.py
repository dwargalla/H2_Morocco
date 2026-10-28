"""Rekonstruiert die 9 Einzugsgebiete ``watershead_morocco.shp``.

Das Original ist verloren. Sein Aufbau steht aber in ``MCA/water_exploitable2.py``
(Commit ``ed25684``): 8 Gruppen von Provinzen aus GADM 1.0 (``MAR_adm2``, Spalte
``ID_2``), je Gruppe per ``dissolve()`` zusammengefasst, plus die Westsahara
(``west_sahara.shp``) als ``sahara``. ``west_sahara.shp`` ist ebenfalls verloren;
es ist die Landesgrenze mit Westsahara minus ``MAR_adm0``, einschließlich der
kleinen Splitter entlang der Grenze (beides gegen das alte
``MCA/water_exploitable.shp`` aus Commit ``1c71831`` geprüft).

Eingaben:
    data/raw/boundaries/gadm1/MAR_adm0.shp, MAR_adm2.shp   GADM 1.0 (2009), aus
        General/04_Recherche/QGIS/Datein/Daten/MAR_adm/
    data/raw/boundaries/morocco_Morocco_Country_Boundary.shp

Ausgaben:
    data/raw/hydrology/watershead_morocco.shp   Spalte ``name``, EPSG:32629

Hinweise:
    - Kontrolle: ``MCA/water_exploitable_gw.py`` reproduziert damit
      ``data/interim/water/water_availability_gw.csv`` (max. Abweichung 4·10⁻⁸).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python rebuild_watershead.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import os

import geopandas as gpd
import pandas as pd

gdf_country = gpd.read_file('../raw/boundaries/morocco_Morocco_Country_Boundary.shp').to_crs('EPSG:4326')
gdf_mar_adm0 = gpd.read_file('../raw/boundaries/gadm1/MAR_adm0.shp').to_crs('EPSG:4326')
gdf_regions = gpd.read_file('../raw/boundaries/gadm1/MAR_adm2.shp').to_crs('EPSG:32629')

# west_sahara.shp: Landesgrenze minus Marokko ohne Westsahara, Splitter bleiben drin
gdf_west_sahara = gpd.overlay(gdf_country, gdf_mar_adm0, how='difference')[['geometry']].dissolve().to_crs('EPSG:32629')

# Provinzgruppen aus water_exploitable2.py
dict_basins = {'loukkos':     [20114, 20115, 20116, 20117, 20118, 20119],
               'moulouiya':   [20073, 20096, 20098, 20099, 20100, 20121],
               'sebou':       [20074, 20075, 20076, 20077, 20078, 20091, 20093, 20095, 20120],
               'bouregreg':   [20068, 20079, 20080, 20101, 20102, 20103, 20104],
               'oum':         [20069, 20070, 20071, 20088, 20094, 20112, 20113],
               'tensif':      [20072, 20086, 20087, 20089, 20090],
               'south_atlas': [20081, 20082, 20083, 20084, 20085, 20092, 20097, 20108, 20111],
               'souss_massa': [20105, 20106, 20107, 20109, 20110]}

list_basins = [gdf_west_sahara.assign(name='sahara')]
for name, ids in dict_basins.items():
    list_basins.append(gdf_regions.loc[gdf_regions['ID_2'].isin(ids)].dissolve()[['geometry']].assign(name=name))

gdf_watershead = gpd.GeoDataFrame(pd.concat(list_basins, ignore_index=True), crs='EPSG:32629')[['name', 'geometry']]

os.makedirs('../raw/hydrology', exist_ok=True)
gdf_watershead.to_file('../raw/hydrology/watershead_morocco.shp')
print(gdf_watershead.assign(km2=gdf_watershead.area / 1e6)[['name', 'km2']].round(0))
