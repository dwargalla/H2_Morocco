"""Hilfsfunktionen für räumliche Verschneidungen zwischen Raster und Geodaten.

Wird von den Kriterien- und Wasserskripten der MCA importiert
(``from custom import list_index``). Es gibt keinen räumlichen Index; jeder
Aufruf prüft alle Geometrien von ``gdf`` und ist entsprechend langsam, wenn er
in einer Schleife über alle 7219 Zellen läuft.
"""

# Custom function for spatial indexing in GeoDataFrames

def list_index(gdf, i, grid):
    """Gibt Geometrie ``i`` aus ``grid`` und die Index-Labels aller Geometrien in ``gdf`` zurück, die sie schneiden.

    Returns:
        (cell, list): Geometrie von ``grid.iloc[i]`` und Liste der Index-Labels aus ``gdf``.
    """
    cell = grid['geometry'].iloc[i]
    intersects = gdf.intersects(cell)
    return cell, intersects[intersects == True].index.tolist()

def list_index_only_list(cell,gdf):
    """Gibt die Index-Labels aller Geometrien in ``gdf`` zurück, die ``cell`` schneiden."""
    intersects = gdf.intersects(cell)
    return intersects[intersects == True].index.tolist()