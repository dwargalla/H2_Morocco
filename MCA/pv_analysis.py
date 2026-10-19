"""MCA-Kriterium PV-Ertrag: mittlerer spezifischer PV-Ertrag je Rasterzelle.

Verschneidet das Raster mit den PV-Polygonen aus dem Global Solar Atlas
(räumlicher Join, ``intersects``) und bildet je Zelle den Mittelwert von
``pv_yeald`` [kWh/kWp]. Zellen ohne Treffer erhalten 0.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    data/interim/qgis/PV_yeald_clear_ma_we.shp

Ausgaben:
    data/interim/mca_criteria/results_pv_yeald.csv   eine Spalte ``pv_yeald``, zeilengleich mit dem Raster

Hinweise:
    - Ausführen aus ``MCA/``: ``python pv_analysis.py``
"""

import geopandas as gpd

# Data
    # Current potential
gdf_grid = gpd.read_file('../data/interim/grid/grid_morocco_clear.shp')
    # PV
    # Source: Global solar atlas
gdf_pv_morocco_utm29n = gpd.read_file('../data/interim/qgis/PV_yeald_clear_ma_we.shp').to_crs("EPSG:32629")

# Spatial join: alle PV-Geometrien auf die Grid-Zellen mappen
joined = gpd.sjoin(gdf_grid,
                   gdf_pv_morocco_utm29n[['pv_yeald', 'geometry']],
                   how='left',
                   predicate='intersects')

# Durchschnitt pro Zelle berechnen
df_mean = joined.groupby(joined.index)['pv_yeald'].mean()
df_mean = df_mean.fillna(0)

# CSV
df_mean.to_csv('../data/interim/mca_criteria/results_pv_yeald.csv', index=False)