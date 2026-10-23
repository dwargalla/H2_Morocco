"""Schritt 0 der Kostenanalyse (neu): stündliche ERA5-Wetterdaten für Marokko vom Copernicus CDS.

Lädt "ERA5 hourly data on single levels" für das Rechteck um das 10-km-Raster
(plus eine ERA5-Zelle Rand) herunter, eine NetCDF-Datei pro Monat. Die
Variablen reichen für PV (Strahlung, Temperatur) und Wind (100 m und 10 m für
die Höhenextrapolation, Rauigkeit) und entsprechen dem, was atlite für seine
PV- und Windmodelle braucht.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp   nur für das Rechteck

Ausgaben:
    data/raw/era5/era5_morocco_YYYY_MM.nc     ca. 50 MB pro Monat (0,6 GB pro Jahr),
                                              64 × 69 ERA5-Gitterpunkte, 10 Variablen

Hinweise:
    - Braucht ``CDS_API_KEY`` in ``H2_Morocco/.env`` (Token von
      https://cds.climate.copernicus.eu/profile) und einmalig akzeptierte Lizenz
      für den Datensatz "ERA5 hourly data on single levels".
    - Fertige Monate werden übersprungen; ein abgebrochener Lauf kann einfach
      neu gestartet werden. Dateien entstehen erst nach vollständigem Download.
    - Dauer hängt vor allem von der CDS-Warteschlange ab (1 Jahr: Stunden,
      10 Jahre: etwa ein Tag). Rechner darf nicht in den Ruhezustand.
    - Ausführen aus ``Cost_analysis/``:
          python 00_era5_download.py 2019             ein Jahr
          python 00_era5_download.py 2015-2024        mehrere Jahre
          python 00_era5_download.py 2019 --test      nur 1 Tag, prüft Zugang
"""

import argparse
import calendar
import math
import os
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cdsapi
import geopandas as gpd
import xarray as xr
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / 'data' / 'raw' / 'era5'
GRID = BASE / 'data' / 'interim' / 'grid' / 'grid_morocco_clear.shp'

DATASET = 'reanalysis-era5-single-levels'
VARIABLES = [
    # Wind
    '100m_u_component_of_wind',
    '100m_v_component_of_wind',
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    'forecast_surface_roughness',
    # PV
    'surface_solar_radiation_downwards',             # GHI
    'total_sky_direct_solar_radiation_at_surface',   # Direktanteil
    'toa_incident_solar_radiation',
    'surface_net_solar_radiation',                   # für Albedo
    '2m_temperature',
]
RES = 0.25  # ERA5-Gitterweite in Grad


def bounding_box():
    """[Nord, West, Süd, Ost] um das Raster, auf das ERA5-Gitter gerundet plus eine Zelle Rand."""
    west, south, east, north = gpd.read_file(GRID).to_crs(4326).total_bounds
    return [math.ceil(north / RES) * RES + RES,
            math.floor(west / RES) * RES - RES,
            math.floor(south / RES) * RES - RES,
            math.ceil(east / RES) * RES + RES]


def parse_years(text):
    if '-' in text:
        start, end = text.split('-')
        return list(range(int(start), int(end) + 1))
    return [int(text)]


def retrieve(client, area, year, month, target, days=None):
    request = {
        'product_type': ['reanalysis'],
        'variable': VARIABLES,
        'year': [str(year)],
        'month': [f'{month:02d}'],
        'day': days or [f'{d:02d}' for d in range(1, calendar.monthrange(year, month)[1] + 1)],
        'time': [f'{h:02d}:00' for h in range(24)],
        'area': area,
        'data_format': 'netcdf',
        'download_format': 'unarchived',
    }
    tmp = target.with_suffix('.part')
    client.retrieve(DATASET, request).download(str(tmp))
    # CDS liefert Momentan- (Wind, Temperatur) und Summenwerte (Strahlung) als
    # zwei NetCDF-Dateien in einem Zip; hier zu einer Datei pro Monat zusammenführen
    if zipfile.is_zipfile(tmp):
        with tempfile.TemporaryDirectory() as unpack_dir, zipfile.ZipFile(tmp) as archive:
            archive.extractall(unpack_dir)
            parts = [xr.open_dataset(p) for p in sorted(Path(unpack_dir).glob('*.nc'))]
            merged = xr.merge(parts, compat='override', join='exact')
            encoding = {v: {'zlib': True, 'complevel': 4} for v in merged.data_vars}
            merged.to_netcdf(target.with_suffix('.merge'), encoding=encoding)
            for part in parts:
                part.close()
        tmp.unlink()
        target.with_suffix('.merge').rename(target)
    else:
        tmp.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description='ERA5-Download für Marokko')
    parser.add_argument('years', help='Jahr (2019) oder Bereich (2015-2024)')
    parser.add_argument('--workers', type=int, default=3,
                        help='gleichzeitige CDS-Anfragen (Standard 3)')
    parser.add_argument('--test', action='store_true',
                        help='nur 1. Januar des ersten Jahres, Ausgabe *_test.nc')
    args = parser.parse_args()

    load_dotenv(BASE / '.env')
    key = os.getenv('CDS_API_KEY')
    if not key:
        raise SystemExit('CDS_API_KEY fehlt in H2_Morocco/.env.')
    client = cdsapi.Client(url='https://cds.climate.copernicus.eu/api', key=key, quiet=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    area = bounding_box()
    years = parse_years(args.years)
    print(f'Rechteck [N, W, S, O]: {area}')

    if args.test:
        target = OUT_DIR / f'era5_morocco_{years[0]}_01_test.nc'
        retrieve(client, area, years[0], 1, target, days=['01'])
        print(f'Test ok: {target} ({target.stat().st_size / 1e6:.1f} MB)')
        return

    todo = [(y, m, OUT_DIR / f'era5_morocco_{y}_{m:02d}.nc')
            for y in years for m in range(1, 13)]
    todo = [t for t in todo if not t[2].exists()]
    print(f'{len(todo)} Monate zu laden, {args.workers} parallel')

    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(retrieve, client, area, y, m, target): target
                   for y, m, target in todo}
        for future in as_completed(futures):
            target = futures[future]
            try:
                future.result()
                print(f'fertig: {target.name}')
            except Exception as err:   # einzelne Monate dürfen scheitern, Rest läuft weiter
                failed.append(target.name)
                print(f'FEHLER {target.name}: {err}')

    if failed:
        raise SystemExit(f'{len(failed)} Monate fehlgeschlagen, Skript erneut starten: {failed}')
    print('Alle Monate vorhanden.')


if __name__ == '__main__':
    main()
