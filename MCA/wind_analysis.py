"""MCA-Kriterium Windertrag: mittlere Wind-Volllaststunden je Rasterzelle.

Verschneidet das Raster mit den Wind-Polygonen (abgeleitet aus dem Global Wind
Atlas, räumlicher Join ``intersects``) und bildet je Zelle den Mittelwert von
``FLH_wind`` [h/a]. Zellen ohne Treffer erhalten 0.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/interim/qgis/Wind_pot_morocco_FLH.shp

Ausgaben:
    data/interim/mca_criteria/results_wind_flh.csv   eine Spalte ``FLH_wind``, zeilengleich mit dem Raster

Hinweise:
    - Die Volllaststunden sind teils physikalisch unplausibel hoch
      (Korrekturplan F-19).
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python wind_analysis.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd

# Data
    # Current potential
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
    # Wind
    # Source: Global Wind Atlas
gdf_wind_morocco_utm29n = gpd.read_file('../data/interim/qgis/Wind_pot_morocco_FLH.shp').to_crs("EPSG:32629")

# Spatial join: alle Wind-Geometrien auf die Grid-Zellen mappen
joined = gpd.sjoin(gdf_grid,
                   gdf_wind_morocco_utm29n[['FLH_wind', 'geometry']],
                   how='left',
                   predicate='intersects')

# Durchschnitt pro Zelle berechnen
df_mean = joined.groupby(joined.index)['FLH_wind'].mean()
df_mean = df_mean.fillna(0)

# CSV
df_mean.to_csv('../data/interim/mca_criteria/results_wind_flh.csv', index=False)