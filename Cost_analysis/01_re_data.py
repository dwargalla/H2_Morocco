"""Schritt 1 der Kostenanalyse: stündliche PV- und Windprofile von renewables.ninja.

Ruft für jeden Standort aus ``PV_WIND_50_Punkte.xlsx`` die Erzeugung 2019 einer
1-kW-Anlage ab (PV: MERRA-2, Neigung 35°, Süd, 10 % Verluste; Wind: Vestas
V136 3450, 150 m Nabenhöhe), hängt sie als Spalten ``electricity_PV_i`` /
``electricity_Wind_i`` an die vorhandene CSV an und berechnet daraus die
Volllaststunden (Jahressumme).

Eingaben:
    data/raw/renewables/PV_WIND_50_Punkte.xlsx    Blatt PV_Punkte (Latitude, Longitude)
    data/interim/re_profiles/pv_wind_electricity.csv   bisher abgerufene Profile (wird erweitert)

Ausgaben:
    data/interim/re_profiles/pv_wind_electricity.csv   stündliche Profile, 8760 Zeilen
    data/interim/re_profiles/flh_re.csv                FLH_PV, FLH_Wind für die Standorte 0–49

Hinweise:
    - Braucht einen API-Token in ``H2_Morocco/.env`` als ``RENEWABLES_NINJA_TOKEN``
      (Vorlage: ``.env.example``). Limit 50 Anfragen pro Stunde; die Schleife
      (``range(1)``) ist für schrittweisen Abruf gedacht.
    - Es wird nur das Blatt PV_Punkte gelesen; Volllaststunden werden nur für die
      ersten 50 Standorte berechnet.
    - Ausführen aus ``Cost_analysis/``: ``python re_data.py``
"""

import os
from pathlib import Path

import requests
import pandas as pd
import json
from dotenv import load_dotenv

# Get location-specific profiles in morocco from renewables ninja 

coordinates = pd.read_excel('../data/raw/renewables/PV_WIND_50_Punkte.xlsx', sheet_name='PV_Punkte')
df_electricity = pd.read_csv('../data/interim/re_profiles/pv_wind_electricity.csv', index_col=0)
df_electricity.reset_index(drop=True, inplace=True)

# API token from renewables.ninja (https://www.renewables.ninja/api/), stored in H2_Morocco/.env
load_dotenv(Path(__file__).resolve().parent.parent / '.env')
token = os.getenv('RENEWABLES_NINJA_TOKEN')
if not token:
    raise SystemExit('RENEWABLES_NINJA_TOKEN fehlt: .env.example nach .env kopieren und Token eintragen.')
api_base = 'https://www.renewables.ninja/api/'

s = requests.session()
# Send token header with each request
s.headers = {'Authorization': 'Token ' + token}

url_pv = api_base + 'data/pv'
url_wind = api_base + 'data/wind'

for i in range(1):   # Nur sechs Anfragen pro Min (2*3), um API-Limits zu beachten: Maximal 50 pro Stunden
    lat = coordinates.at[i, 'Latitude']
    lon = coordinates.at[i, 'Longitude']
    # PV
    args_pv = {
        'lat': lat,
        'lon': lon,
        'date_from': '2019-01-01',
        'date_to': '2019-12-31',
        'dataset': 'merra2',
        'capacity': 1.0,
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 35,
        'azim': 180,
        'format': 'json'
    }

    r_pv = s.get(url_pv, params=args_pv)
    parsed_response_pv = json.loads(r_pv.text)
    data_pv = pd.read_json(json.dumps(parsed_response_pv['data']), orient='index')
    metadata_pv = parsed_response_pv['metadata']

    #Wind
    args_wind = {
        'lat': lat,
        'lon': lon,
        'date_from': '2019-01-01',
        'date_to': '2019-12-31',
        'capacity': 1.0,
        'height': 150,
        'turbine': 'Vestas V136 3450',
        'format': 'json'
    }

    r_wind = s.get(url_wind, params=args_wind)
    parsed_response_wind = json.loads(r_wind.text)
    data_wind = pd.read_json(json.dumps(parsed_response_wind['data']), orient='index')
    metadata_wind = parsed_response_wind['metadata']

    data_pv.rename(columns={'electricity': f'electricity_PV_{i}'}, inplace=True)
    data_wind.rename(columns={'electricity': f'electricity_Wind_{i}'}, inplace=True)

    df_concat = pd.concat([data_pv, data_wind], axis=1)
    df_concat.reset_index(drop=True, inplace=True)
    df_electricity = pd.concat([df_electricity, df_concat], axis=1)

# Calculation of Fullloadhours of pv and wind for locaions
# df_re = pd.read_csv('../data/interim/re_profiles/pv_wind_electricity.csv')
# df_re = df_re.drop(columns= ['Unnamed: 0'])

ds_sum = df_electricity.sum()

df_flh = pd.DataFrame(columns=['FLH_PV', 'FLH_Wind'])
for i in range(0, 50):
    pv = ds_sum[f'electricity_PV_{i}']
    wind = ds_sum[f'electricity_Wind_{i}']

    df_flh.at[i, 'FLH_PV'] = pv
    df_flh.at[i, 'FLH_Wind'] = wind

df_flh.to_csv('../data/interim/re_profiles/flh_re.csv', index=False)
df_electricity.to_csv('../data/interim/re_profiles/pv_wind_electricity.csv')