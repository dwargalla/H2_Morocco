"""Vergleich MCA ↔ Kostenanalyse als Folie (16:9, PNG).

Legt einen neuen Laufordner results/runs/<datum>_<commit>_compare/ an und zeichnet dort
overview.png: Herkunft, Kennzahlen, Kostenanteile, geänderte Kostenparameter und je Jahr
MCA, Δ MCA, LCOH, Δ LCOH. Δ = dieser Lauf minus Bezugslauf (Standard: letzter Vergleichslauf,
sonst --reference); ohne Bezug bleiben die Δ-Felder leer. Letzter Schritt in main.ipynb.

Eingaben:
    data/interim/grid/grid_morocco_clear.shp
    <MCA-Lauf>/results_mca.csv, <MCA-Lauf>/criteria/results_nogo_zones.csv
                                  neuester results/runs/*_mca (aus compare_mca_runs.py) oder --mca-run;
                                  gibt es keinen oder ist results/mca/ neuer, werden
                                  results/mca/results_mca_morocco_2025_2050.csv und
                                  data/interim/mca_criteria/results_nogo_zones.csv gelesen
    <Kostenlauf>/results_cost_{2025,2050}.csv   neuester results/runs/*_cost oder --cost-run

Ausgaben:
    results/runs/<datum>_<commit>_compare/
        overview.png          die Folie
        results_compare.csv   MCA und LCOH je Zelle (Bezug für den nächsten Vergleich)
        sources.json          verglichener Kosten- und MCA-Lauf (bzw. MCA-Dateistand)
        metrics.csv           Kennzahlen (auch als Zeile in results/runs/runs_index.csv)
        run_info.json, model_parameters.csv, changes.patch (wie bei allen Läufen)

Aufruf (aus beliebigem Arbeitsordner):
    python compare_mca_cost.py --note "Text"
    python compare_mca_cost.py --cost-run results/runs/<ordner>_cost --reference results/runs/<ordner>_compare
"""
import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

from h2morocco.overview import build_comparison_overview
from h2morocco.runs import ROOT, latest_run_dir, new_run_dir, read_run_info

YEARS = (2025, 2050)
MCA_CSV = ROOT / 'results/mca/results_mca_morocco_2025_2050.csv'   # Ersatz, wenn es keinen MCA-Laufordner gibt
NOGO_CSV = ROOT / 'data/interim/mca_criteria/results_nogo_zones.csv'

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument('--note', default='', help='kurze Notiz zum Vergleich')
parser.add_argument('--cost-run', type=Path, default=None, help='Kostenlauf (Standard: neuester *_cost)')
parser.add_argument('--mca-run', type=Path, default=None, help='MCA-Lauf (Standard: neuester *_mca)')
parser.add_argument('--reference', type=Path, default=None,
                    help='Vergleichslauf als Bezug für die Δ-Werte (Standard: letzter *_compare)')
args = parser.parse_args()

def _resolve(path):
    # Relative Pfade gelten ab dem Projektordner.
    return None if path is None else (path if path.is_absolute() else ROOT / path)


cost_run = _resolve(args.cost_run) or latest_run_dir('cost')
mca_run = _resolve(args.mca_run) or latest_run_dir('mca')

# MCA-Laufordner nur verwenden, wenn results/mca/ seitdem nicht neu gerechnet wurde
# (z. B. mca_maps.py ohne compare_mca_runs.py). Sonst die Datei direkt lesen.
if mca_run is not None and args.mca_run is None:
    mca_file_time = pd.Timestamp.fromtimestamp(MCA_CSV.stat().st_mtime)
    run_time = pd.Timestamp(read_run_info(mca_run)['started'])
    if mca_file_time > run_time:
        print(f'Hinweis: {MCA_CSV.name} ist neuer als der MCA-Lauf {mca_run.name}; die Datei wird verwendet.')
        mca_run = None
reference = _resolve(args.reference)
if reference is not None and not (reference / 'results_compare.csv').exists():
    raise SystemExit(f'--reference: {reference} ist kein Vergleichslauf (results_compare.csv fehlt)')
if cost_run is None:
    raise SystemExit('Kein Kostenlauf in results/runs/ gefunden: zuerst 04_cost_analysis_h2_morocco.py ausführen.')

gdf_grid = gpd.read_file(ROOT / 'data/interim/grid/grid_morocco_clear.shp').to_crs('EPSG:32629')
if mca_run is not None:
    df_mca = pd.read_csv(mca_run / 'results_mca.csv')
    nogo_csv = mca_run / 'criteria' / 'results_nogo_zones.csv'
else:
    df_mca = pd.read_csv(MCA_CSV)
    nogo_csv = NOGO_CSV
df_cost  = {year: pd.read_csv(cost_run / f'results_cost_{year}.csv') for year in YEARS}
allowed  = pd.read_csv(nogo_csv)['NoGo'] == 1

# Alle Tabellen sind zeilengleich mit dem Raster (Zeile i = Zelle i).
for name, n in [('MCA', len(df_mca)), ('No-Go', len(allowed))] + [(f'Kosten {y}', len(df_cost[y])) for y in YEARS]:
    if n != len(gdf_grid):
        raise SystemExit(f'{name}: {n} Zeilen, Raster hat {len(gdf_grid)}')

results = pd.DataFrame({
    **{f'MCA_{year}':  df_mca[f'MCA_Morocco_{year}'] for year in YEARS},
    **{f'LCOH_{year}': df_cost[year][f'H2_Price_{year} [EUR/MWh_h2]'] for year in YEARS},
})
sources = {
    'cost_run': cost_run.name,
    'mca_run': mca_run.name if mca_run is not None else '',
    'mca_csv': str(MCA_CSV.relative_to(ROOT)),
    'mca_mtime': pd.Timestamp.fromtimestamp(MCA_CSV.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
}

run_dir = new_run_dir('compare', note=args.note, script='compare_mca_cost.py')
print(build_comparison_overview(run_dir, gdf_grid, results, allowed, sources, reference))
