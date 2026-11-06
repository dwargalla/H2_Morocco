"""MCA-Lauf festhalten und mit einem früheren MCA-Lauf vergleichen (Folie 16:9, PNG).

**KI-generiert:** erstellt mit Claude (Claude Code) am 05.11.2026.

Das Skript baut auf den MCA-Ergebnissen auf und ändert keines der MCA-Skripte. Es wird nach
``MCA/mca_maps.py`` gestartet (in ``main.ipynb`` als eigener Schritt, abschaltbar) und macht zwei Dinge:

1. **Laufordner anlegen** ``results/runs/<Datum>_<Uhrzeit>_<Commit>[-dirty]_mca/`` mit
       results_mca.csv      MCA-Score je Zelle 2025 und 2050 (Kopie aus results/mca/)
       criteria/            alle Kriterien-CSVs aus data/interim/mca_criteria/ (Kopie)
       mca_weights.csv      Kopie der Gewichtsdatei (data/model_parameters/mca_weights.csv)
       weights.json         dieselben Gewichte kurz: Hauptkriterien und 'roads/<Straßenklasse>'
       metrics.csv          Kennzahlen (auch als Zeile in results/runs/runs_index.csv)
       run_info.json, inputs.sha256, changes.patch   wie bei allen Läufen (h2morocco/runs.py)
2. **Vergleichsfolie** ``overview_mca.png`` im selben Ordner: Kennzahlen, geänderte Gewichte,
   Kriterien, Eingabedateien und Code sowie Karten Bezug / jetzt / Differenz für 2025 und 2050.
   Bezug ist der letzte MCA-Lauf davor oder der mit ``--reference`` angegebene.

Eingaben:
    results/mca/results_mca_morocco_2025_2050.csv   aus MCA/mca_maps.py
    data/interim/mca_criteria/*.csv                 Kriterien, darunter results_nogo_zones.csv
    data/interim/grid/grid_morocco_clear.shp        für die Karten
    data/model_parameters/mca_weights.csv           Gewichte

Aufruf (aus beliebigem Arbeitsordner):
    python compare_mca_runs.py --note "Was wurde geändert"
    python compare_mca_runs.py --reference results/runs/<ordner>_mca
"""
import argparse
import json
import shutil
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from h2morocco.overview import (DARK, DOWN, MUTED, TEXT, UP, _axes, _panel, _txt, _width,
                                changed_inputs)
from h2morocco.utils import read_mca_weights
from h2morocco.runs import ROOT, _git, append_to_index, latest_run_dir, new_run_dir, read_run_info

YEARS = [2025, 2050]
MCA_CSV = ROOT / 'results/mca/results_mca_morocco_2025_2050.csv'
CRITERIA_DIR = ROOT / 'data/interim/mca_criteria'
MCA_WEIGHTS_CSV = ROOT / 'data/model_parameters/mca_weights.csv'

# Lesbare Namen der Kriterien-Dateien
CRITERIA_LABELS = {
    'results_pv_yeald.csv':                 'PV',
    'results_wind_flh.csv':                 'Wind',
    'results_accessibility.csv':            'Erreichbarkeit',
    'results_agriculture.csv':              'Landwirtschaft 2025',
    'results_agriculture_2050.csv':         'Landwirtschaft 2050',
    'results_urban.csv':                    'Stadt 2025',
    'results_urban_2050.csv':               'Stadt 2050',
    'results_rural.csv':                    'Ländlich 2025',
    'results_rural_2050.csv':               'Ländlich 2050',
    'results_industrie.csv':                'Industrie',
    'results_water_res_available.csv':      'Wasser 2025',
    'results_water_res_availabil_2050.csv': 'Wasser 2050',
    'results_non_conflict_areas.csv':       'Nicht-Konflikt',
    'results_nogo_zones.csv':               'No-Go-Maske',
}


# ---------------------------------------------------------------------------
# Teil 1: Laufordner anlegen
# ---------------------------------------------------------------------------

def read_all_weights():
    """Alle MCA-Gewichte als ein Dictionary: Hauptkriterien unter ihrem Namen, Straßenklassen als 'roads/<Klasse>'."""
    weights = read_mca_weights('main')
    for road_class, weight in read_mca_weights('roads').items():
        weights['roads/' + road_class] = weight
    return weights


def save_mca_run(note):
    """Legt den Laufordner an und kopiert Ergebnis, Kriterien und Gewichte hinein."""
    run_dir = new_run_dir('mca', note=note, script='compare_mca_runs.py')
    shutil.copy2(MCA_CSV, run_dir / 'results_mca.csv')
    (run_dir / 'criteria').mkdir()
    for csv_file in sorted(CRITERIA_DIR.glob('*.csv')):
        shutil.copy2(csv_file, run_dir / 'criteria' / csv_file.name)
    shutil.copy2(MCA_WEIGHTS_CSV, run_dir / 'mca_weights.csv')
    weights = read_all_weights()
    (run_dir / 'weights.json').write_text(json.dumps(weights, indent=2), encoding='utf-8')
    return run_dir


# ---------------------------------------------------------------------------
# Teil 2: Vergleich rechnen
# ---------------------------------------------------------------------------

def load_run(run_dir):
    """MCA-Score, zulässige Zellen und Gewichte eines MCA-Laufordners."""
    mca = pd.read_csv(run_dir / 'results_mca.csv')
    allowed = pd.read_csv(run_dir / 'criteria' / 'results_nogo_zones.csv')['NoGo'] == 1
    weights = json.loads((run_dir / 'weights.json').read_text(encoding='utf-8'))
    return mca, allowed, weights


def top_overlap(score_old, score_new, n):
    """Anteil [%] der n besten Zellen, die in beiden Läufen unter den n besten sind."""
    best_old = set(score_old.sort_values(ascending=False).index[:n])
    best_new = set(score_new.sort_values(ascending=False).index[:n])
    return len(best_old & best_new) / n * 100


def compute_metrics(mca, allowed, mca_ref, allowed_ref):
    """Kennzahlen je Jahr, nur auf Zellen, die in beiden Läufen zulässig sind."""
    metrics = {}
    for year in YEARS:
        column = f'MCA_Morocco_{year}'
        metrics[f'mca_{year}_mean'] = round(mca[column][allowed].mean(), 2)
        if mca_ref is None:
            continue
        both = allowed & allowed_ref
        new = mca[column][both]
        old = mca_ref[column][both]
        difference = new - old
        metrics[f'mca_{year}_rho_ref'] = round(spearmanr(old, new).statistic, 3)
        metrics[f'mca_{year}_top100_same'] = round(top_overlap(old, new, 100))
        metrics[f'mca_{year}_top500_same'] = round(top_overlap(old, new, 500))
        metrics[f'mca_{year}_cells_dif_gt5'] = int((difference.abs() > 5).sum())
        metrics[f'mca_{year}_max_abs_dif'] = round(difference.abs().max(), 1)
    return metrics


def compare_criteria(run_dir, reference_dir):
    """Je Kriterien-Datei: Zahl geänderter Zellen und Rangkorrelation zum Bezug (nur geänderte Dateien)."""
    rows = []
    for csv_file in sorted((run_dir / 'criteria').glob('*.csv')):
        label = CRITERIA_LABELS.get(csv_file.name, csv_file.stem)
        old_file = reference_dir / 'criteria' / csv_file.name
        if not old_file.exists():
            rows.append({'Kriterium': label, 'Zellen geändert': 'neu', 'rho': None})
            continue
        # Mehrspaltige Kriterien (Erreichbarkeit) werden je Zelle aufsummiert.
        new = pd.read_csv(csv_file).select_dtypes('number').sum(axis=1)
        old = pd.read_csv(old_file).select_dtypes('number').sum(axis=1)
        changed_cells = int(((new - old).abs() > 1e-9).sum())
        if changed_cells > 0:
            rows.append({'Kriterium': label, 'Zellen geändert': changed_cells,
                         'rho': round(spearmanr(old, new).statistic, 3)})
    return rows


def changed_weights(weights, weights_ref):
    """Liste von Texten 'Kriterium: alt → neu' für jedes geänderte Gewicht.

    Verglichen werden nur Gewichte, die beide Läufe erfasst haben (ältere Läufe kennen
    die Straßengewichte noch nicht).
    """
    lines = []
    for name in sorted(set(weights) & set(weights_ref)):
        old = weights_ref[name]
        new = weights[name]
        if old != new:
            lines.append(f'{name}: {old} → {new}')
    return lines


def changed_code_files(reference_info):
    """Geänderte Dateien (Code, Parameter) seit dem Commit des Bezugslaufs, inkl. nicht committeter."""
    files = _git('diff', '--name-only', reference_info['commit_full']).splitlines()
    untracked = _git('ls-files', '--others', '--exclude-standard').splitlines()
    relevant = []
    for name in files + untracked:
        if name.startswith('results/'):
            continue                          # Ergebnisse sind keine Codeänderung
        if name.endswith(('.py', '.ipynb')) or name.startswith('data/model_parameters/'):
            relevant.append(name)
    return sorted(set(relevant))


# ---------------------------------------------------------------------------
# Teil 3: Folie zeichnen
# ---------------------------------------------------------------------------

def draw_map(fig, gdf_grid, x, y, values, title, subtitle, cmap, vmin, vmax):
    """Eine Karte mit Farbskala an Position (Zoll, oben links). Graue Zellen = No-Go."""
    ax = _axes(fig, x, y + 0.42, 2.2, 2.2)
    cax = _axes(fig, x + 2.25, y + 0.7, 0.07, 1.7)
    gdf = gdf_grid[['geometry']].copy()
    gdf['value'] = values.values
    gdf.plot(column='value', ax=ax, cmap=cmap, linewidth=0, vmin=vmin, vmax=vmax,
             missing_kwds={'color': '#C8CDD0'})
    fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin, vmax), cmap=cmap), cax=cax)
    cax.tick_params(labelsize=7, colors=MUTED)
    ax.set_axis_off()
    _txt(fig, x, y, title, 10, TEXT, 'bold')
    _txt(fig, x, y + 0.22, subtitle, 7.5, MUTED)


def draw_tile(fig, x, y, label, value_text, delta_text, delta_color):
    """Kennzahl-Kachel: Titel, großer Wert, Zeile darunter."""
    _panel(fig, x, y, 1.3, 0.87)
    _txt(fig, x + 0.1, y + 0.07, label, 7.5, MUTED, 'bold')
    _txt(fig, x + 0.1, y + 0.25, value_text, 17, DARK, 'bold')
    _txt(fig, x + 0.1, y + 0.64, delta_text, 7.5, delta_color, 'bold')


def german(number, digits=1):
    """Zahl mit Komma statt Punkt."""
    return f'{number:.{digits}f}'.replace('.', ',')


def build_slide(run_dir, reference_dir, metrics, metrics_ref):
    info = read_run_info(run_dir)
    mca, allowed, weights = load_run(run_dir)
    gdf_grid = gpd.read_file(ROOT / 'data/interim/grid/grid_morocco_clear.shp')

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(13.333, 7.5), facecolor='white')

    # --- Kopf ---
    title = _txt(fig, 0.4, 0.25, 'MCA-Vergleich', 24, DARK, 'bold')
    _txt(fig, 0.4 + _width(fig, title) + 0.25, 0.36, info['started'].replace('T', ' '), 15, MUTED)
    _txt(fig, 0.4, 0.82, 'Notiz: ' + (info['note'] or '–'), 11)
    status = 'nicht committet' if info['dirty'] else 'sauber'
    _txt(fig, 0.4, 1.13, f"Jetzt:  {run_dir.name}  (Commit {info['commit']}, {status})", 8.5, MUTED)
    if reference_dir is None:
        _txt(fig, 0.4, 1.35, 'Bezug:  kein früherer MCA-Lauf, daher keine Differenzen', 8.5, MUTED)
    else:
        info_ref = read_run_info(reference_dir)
        _txt(fig, 0.4, 1.35, f"Bezug:  {reference_dir.name}  ·  Notiz: {info_ref['note'] or '–'}", 8.5, MUTED)

    # --- Kennzahlen: Zeilen = Jahre, Spalten = Ø Score, Rangkorrelation, Top 100 / Top 500 ---
    _txt(fig, 0.4, 1.57, 'nur zulässige Zellen (ohne No-Go)', 6.5, MUTED)
    for row, year in enumerate(YEARS):
        y = 1.75 + row * 0.95
        mean_now = metrics[f'mca_{year}_mean']
        mean_ref = metrics_ref.get(f'mca_{year}_mean')
        if mean_ref is None:
            delta_text, delta_color = 'kein Bezug', MUTED
        else:
            difference = mean_now - mean_ref
            delta_text = f'{difference:+.2f} ggü. Bezug'.replace('.', ',')
            delta_color = DOWN if difference > 0 else UP if difference < 0 else MUTED
        draw_tile(fig, 0.4, y, f'Ø MCA-Score {year}', german(mean_now), delta_text, delta_color)

        if reference_dir is None:
            continue
        rho = metrics[f'mca_{year}_rho_ref']
        draw_tile(fig, 1.77, y, f'Rangkorr. {year}', german(rho, 3),
                  f"{metrics[f'mca_{year}_cells_dif_gt5']} Zellen |Δ| > 5", MUTED)
        draw_tile(fig, 3.14, y, f'Top 100/500 {year}',
                  f"{metrics[f'mca_{year}_top100_same']}/{metrics[f'mca_{year}_top500_same']} %",
                  f"max. |Δ| {german(metrics[f'mca_{year}_max_abs_dif'])} Punkte", MUTED)

    # --- Änderungen ggü. Bezug ---
    _panel(fig, 0.4, 3.72, 4.05, 3.63)
    _txt(fig, 0.5, 3.8, 'Änderungen ggü. Bezug', 10.5, DARK, 'bold')
    lines = []                                        # (Text, fett?)
    if reference_dir is None:
        lines.append(('kein Bezugslauf vorhanden', False))
    else:
        _, _, weights_ref = load_run(reference_dir)
        weight_lines = changed_weights(weights, weights_ref)
        lines.append(('Gewichte (mca_weights.csv)', True))
        lines += [(line, False) for line in weight_lines] or [('unverändert', False)]

        lines.append(('Kriterien (Zellen geändert · Rangkorrelation)', True))
        criteria_rows = compare_criteria(run_dir, reference_dir)
        if not criteria_rows:
            lines.append(('alle unverändert', False))
        for row in criteria_rows:
            rho_text = '' if row['rho'] is None else f" · ρ {german(row['rho'], 3)}"
            lines.append((f"{row['Kriterium']}: {row['Zellen geändert']}{rho_text}", False))

        lines.append(('Eingabedateien data/interim (Prüfsummen)', True))
        files = changed_inputs(run_dir, reference_dir)
        if files is None:
            lines.append(('keine Prüfsummen im Bezug', False))
        elif not files:
            lines.append(('keine geändert', False))
        else:
            for wrapped in textwrap.wrap(', '.join(files), 72)[:3]:
                lines.append((wrapped, False))

        lines.append((f"Code seit Bezugs-Commit {read_run_info(reference_dir)['commit']}", True))
        code_files = changed_code_files(read_run_info(reference_dir))
        if not code_files:
            lines.append(('keine Änderung', False))
        else:
            for wrapped in textwrap.wrap(', '.join(code_files), 72)[:3]:
                lines.append((wrapped, False))

    for k, (text, bold) in enumerate(lines[:12]):     # Platz für 12 Zeilen, darunter das Histogramm
        _txt(fig, 0.5, 4.08 + k * 0.165, text, 7, TEXT, 'bold' if bold else 'normal')

    # --- Histogramm: wie stark ändern sich die Zellen? ---
    if reference_dir is not None:
        mca_ref, allowed_ref, _ = load_run(reference_dir)
        both = allowed & allowed_ref
        _txt(fig, 0.5, 5.92, 'Verteilung Δ MCA (Zellen mit |Δ| > 0,1)', 7, TEXT, 'bold')
        changed_cells = {}                            # Jahr -> Differenzen der geänderten Zellen
        for year in YEARS:
            column = f'MCA_Morocco_{year}'
            difference = (mca[column] - mca_ref[column])[both]
            changed_cells[year] = difference[difference.abs() > 0.1]

        if all(len(values) == 0 for values in changed_cells.values()):
            _txt(fig, 0.5, 6.2, 'keine Zelle hat sich geändert', 7, MUTED)
        else:
            ax = _axes(fig, 0.8, 6.12, 3.4, 0.85)
            ax.set_zorder(2)                          # vor die graue Fläche legen
            for year, color in zip(YEARS, [DARK, '#D96C1E']):
                ax.hist(changed_cells[year], bins=40, histtype='step', linewidth=1.2, color=color,
                        label=f'{year}: {len(changed_cells[year])} Zellen')
            ax.set_yscale('log')
            ax.tick_params(labelsize=6.5, colors=MUTED)
            ax.spines[['top', 'right']].set_visible(False)
            ax.set_xlabel('Δ Score (jetzt minus Bezug)', fontsize=6.5, color=MUTED)
            ax.legend(fontsize=6.5, frameon=False)

    # --- Karten: Zeilen = Jahre, Spalten = Bezug, jetzt, Differenz ---
    for row, year in enumerate(YEARS):
        y = 1.6 + row * 2.9
        column = f'MCA_Morocco_{year}'
        score_now = mca[column].where(allowed)       # No-Go -> leer (grau)
        if reference_dir is None:
            draw_map(fig, gdf_grid, 7.6, y, score_now, f'MCA {year}', 'Score, No-Go grau',
                     'viridis', 0, score_now.max())
            continue
        mca_ref, allowed_ref, _ = load_run(reference_dir)
        score_ref = mca_ref[column].where(allowed_ref)
        top = max(score_now.max(), score_ref.max())
        draw_map(fig, gdf_grid, 4.75, y, score_ref, f'MCA {year} · Bezug', 'Score, No-Go grau',
                 'viridis', 0, top)
        draw_map(fig, gdf_grid, 7.6, y, score_now, f'MCA {year} · jetzt', 'Score, No-Go grau',
                 'viridis', 0, top)
        difference = score_now - score_ref
        limit = max(difference.abs().max(), 0.5)
        draw_map(fig, gdf_grid, 10.45, y, difference, f'Δ MCA {year}', 'jetzt minus Bezug, blau = besser',
                 'RdBu', -limit, limit)

    path = run_dir / 'overview_mca.png'
    fig.savefig(path, dpi=150, facecolor='white')
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Ablauf
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--note', default='', help='kurze Notiz: was wurde geändert?')
    parser.add_argument('--reference', type=Path, default=None,
                        help='MCA-Laufordner als Bezug (Standard: letzter *_mca davor)')
    args = parser.parse_args()

    run_dir = save_mca_run(args.note)

    if args.reference is None:
        reference_dir = latest_run_dir('mca', before=run_dir)
    elif args.reference.is_absolute():
        reference_dir = args.reference
    else:
        reference_dir = ROOT / args.reference          # relative Pfade ab Projektordner

    mca, allowed, _ = load_run(run_dir)
    metrics_ref = {}
    if reference_dir is None:
        metrics = compute_metrics(mca, allowed, None, None)
    else:
        mca_ref, allowed_ref, _ = load_run(reference_dir)
        metrics = compute_metrics(mca, allowed, mca_ref, allowed_ref)
        if (reference_dir / 'metrics.csv').exists():
            metrics_ref = pd.read_csv(reference_dir / 'metrics.csv').iloc[0].to_dict()

    pd.DataFrame([metrics]).to_csv(run_dir / 'metrics.csv', index=False)
    append_to_index(run_dir, metrics)
    print(build_slide(run_dir, reference_dir, metrics, metrics_ref))
