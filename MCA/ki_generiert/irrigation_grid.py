"""Tatsächlich bewässerte Fläche je Rasterzelle aus der FAO Global Map of Irrigation Areas.

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026, Übersicht in
``ki_generiert/README.md``.

``water_consumption.py`` verteilt damit den Agrarwasserbedarf auf die Zellen. Vorher
wurden dafür GlobCover-Klassen genutzt; die Klasse „bewässertes Ackerland“ ist in
Marokko aber leer, so dass das Wasser auf Mosaikflächen mit Regenfeldbau landete
(Fehlerprotokoll Nr. 31).

Vorgehen:
    1. Je GMIA-Pixel (5 Bogenminuten, etwa 9 × 9 km) die tatsächlich bewässerte Fläche
       berechnen: ausgerüstete Fläche [ha] × Anteil tatsächlich bewässert [%] / 100.
    2. Jedes Pixel mit Bewässerung als Quadrat (Polygon) darstellen.
    3. Pixel mit dem Raster verschneiden. Liegt z. B. ein Viertel eines Pixels in einer
       Zelle, bekommt die Zelle ein Viertel seiner Bewässerungsfläche (Annahme: die
       Fläche ist im Pixel gleichmäßig verteilt).

Eingaben:
    data/interim/grid/grid_morocco_clear.shp      Raster (EPSG:32629)
    data/raw/gmia/gmia_v5_aei_ha.asc              GMIA v5: für Bewässerung ausgerüstete Fläche [ha]
    data/raw/gmia/gmia_v5_aai_pct_aei.asc         GMIA v5: davon tatsächlich bewässert [%]

Ausgaben:
    data/interim/water/irrigated_area_gmia.csv    Spalte ``irrigated_area[ha]``, zeilengleich mit dem Raster

Hinweise:
    - Quelle: Siebert, S.; Henrich, V.; Frenken, K.; Burke, J. (2013): Global Map of
      Irrigation Areas version 5. Universität Bonn / FAO, Rom. Datenstand etwa 2005.
      Neuere Bewässerung (v. a. mit Grundwasser, z. B. Saïss) fehlt.
    - Summe im Raster etwa 1,43 Mio. ha (Statistik heute 1,5–1,8 Mio. ha). Die absolute
      Fläche spielt keine Rolle, weil ``water_consumption.py`` auf die nationale
      Agrarwassermenge skaliert; es zählt nur die räumliche Verteilung.
    - Direkt in VS Code oder aus beliebigem Arbeitsordner starten: ``python irrigation_grid.py``
"""

# Arbeitsordner automatisch setzen: direkter Start in VS Code ist möglich.
import os as _os
from pathlib import Path as _Path

if __name__ == "__main__":
    _os.chdir(_Path(__file__).resolve().parent)


import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box

# Raster laden und jeder Zelle ihre Zeilennummer geben (Schlüssel für die Ausgabe)
gdf_grid = gpd.read_file('../../data/interim/grid/grid_morocco_clear.shp')
gdf_grid['cell'] = range(len(gdf_grid))

# Ausschnitt um Marokko in Längen-/Breitengrad (mit 0,5° Rand)
west, south, east, north = gdf_grid.to_crs('EPSG:4326').total_bounds
west, south, east, north = west - 0.5, south - 0.5, east + 0.5, north + 0.5


def read_gmia(path):
    """Liest den Marokko-Ausschnitt einer GMIA-Datei. Gibt Werte und Lage des Ausschnitts zurück."""
    with rasterio.open(path) as src:
        window = from_bounds(west, south, east, north, src.transform).round_offsets().round_lengths()
        values = src.read(1, window=window)
        window_transform = src.window_transform(window)
    values[values < 0] = 0          # Kein-Wert (-9) als 0 behandeln
    return values, window_transform


equipped_ha, transform = read_gmia('../../data/raw/gmia/gmia_v5_aei_ha.asc')
irrigated_percent, _ = read_gmia('../../data/raw/gmia/gmia_v5_aai_pct_aei.asc')
irrigated_ha = equipped_ha * irrigated_percent / 100

# Schritt 2: ein Quadrat je Pixel mit Bewässerung
pixel_size = transform.a            # Pixelbreite in Grad
left_edge = transform.c             # Längengrad des linken Rands
top_edge = transform.f              # Breitengrad des oberen Rands

pixel_squares = []
pixel_irrigated_ha = []
n_rows, n_cols = irrigated_ha.shape
for row in range(n_rows):
    for col in range(n_cols):
        if irrigated_ha[row, col] > 0:
            pixel_west = left_edge + col * pixel_size
            pixel_north = top_edge - row * pixel_size
            square = box(pixel_west, pixel_north - pixel_size, pixel_west + pixel_size, pixel_north)
            pixel_squares.append(square)
            pixel_irrigated_ha.append(irrigated_ha[row, col])

gdf_pixels = gpd.GeoDataFrame({'irrigated_ha': pixel_irrigated_ha}, geometry=pixel_squares, crs='EPSG:4326')
gdf_pixels = gdf_pixels.to_crs(gdf_grid.crs)
gdf_pixels['pixel_area'] = gdf_pixels.area

# Schritt 3: Pixel und Zellen verschneiden, Fläche anteilig zuordnen
gdf_parts = gpd.overlay(gdf_grid[['cell', 'geometry']], gdf_pixels, how='intersection')
gdf_parts['share_of_pixel'] = gdf_parts.area / gdf_parts['pixel_area']
gdf_parts['irrigated_ha_in_cell'] = gdf_parts['irrigated_ha'] * gdf_parts['share_of_pixel']

irrigated_per_cell = gdf_parts.groupby('cell')['irrigated_ha_in_cell'].sum()
irrigated_per_cell = irrigated_per_cell.reindex(gdf_grid['cell'], fill_value=0)   # Zellen ohne Bewässerung = 0

print(f'Bewässerte Fläche im Raster: {irrigated_per_cell.sum() / 1000:.0f} Tsd. ha '
      f'in {(irrigated_per_cell > 0).sum()} von {len(gdf_grid)} Zellen')

df_out = pd.DataFrame({'irrigated_area[ha]': irrigated_per_cell.values})
df_out.to_csv('../../data/interim/water/irrigated_area_gmia.csv', index=False)
