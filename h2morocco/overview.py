"""Übersichtsfolie (16:9, PNG) für einen Vergleichslauf MCA ↔ Kosten.

Eine Folie mit Herkunft, Kennzahlen (LCOH-Median, mittlerer MCA-Score, Rangkorrelation),
mittleren Kostenanteilen, geänderten Parametern und Karten (MCA, Δ MCA, LCOH, Δ LCOH),
jeweils im Vergleich zu einem Bezugslauf (Standard: letzter Vergleichslauf).

Aufruf über compare_mca_cost.py (letzter Schritt in main.ipynb):
    build_comparison_overview(run_dir, gdf_grid, results, allowed, sources, reference_dir)

Ausgaben im Laufordner:
    overview.png           die Folie (13,33 × 7,5 Zoll)
    results_compare.csv    MCA und LCOH je Zelle (Bezug für spätere Vergleiche)
    sources.json           verglichener Kostenlauf und MCA-Stand
    metrics.csv            Kennzahlen (auch als Zeile in results/runs/runs_index.csv)
"""
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from h2morocco.runs import RUNS_DIR, append_to_index, latest_run_dir, read_run_info

H2_LHV_KWH_PER_KG = 33.33   # nur für die Anzeige in €/kg

# Kostenanteile: Spalte in results_cost_<Jahr>.csv -> Beschriftung
COMPONENTS = {
    'Electrolyzer_cost [EUR/MWh_h2]':  'Elektrolyseur',
    'RE_cost [EUR/MWh_h2]':            'Strom (PV + Wind)',
    'Distribution_cost [EUR/MWh_h2]':  'HGÜ-Netz',
    'Pipeline_cost [EUR/MWh_h2]':      'H2-Pipeline',
    'Water_cost [EUR/MWh_h2]':         'Wasser',
}
COMPONENT_COLORS = ['#0F3D4C', '#2A8C9E', '#8FC1C9', '#D96C1E', '#F2C14E']

DARK, TEXT, MUTED, PANEL = '#0F3D4C', '#222B31', '#5E6B73', '#EEF3F4'
ACCENT, UP, DOWN = '#D96C1E', '#B03A2E', '#2E7D4F'


def cost_metrics(df_results_2025, df_results_2050):
    """Kennzahlen eines Laufs: Median, 5./95. Perzentil der LCOH und mittlere Kostenanteile je Jahr."""
    metrics = {}
    for year, df in ((2025, df_results_2025), (2050, df_results_2050)):
        total = pd.to_numeric(df[f'H2_Price_{year} [EUR/MWh_h2]'])
        metrics[f'lcoh_{year}_median'] = round(total.median(), 2)
        metrics[f'lcoh_{year}_p05'] = round(total.quantile(0.05), 2)
        metrics[f'lcoh_{year}_p95'] = round(total.quantile(0.95), 2)
        for column, label in COMPONENTS.items():
            metrics[f'{year}_{label}'] = round(pd.to_numeric(df[column]).mean(), 2)
    return metrics


def changed_parameters(run_dir, previous_dir):
    """Parameter (Name, Jahr, alt, neu), die sich gegenüber dem vorherigen Lauf geändert haben."""
    if previous_dir is None:
        return None
    columns = ['variable_name', 'year', 'value_eur2025', 'unit']
    new = pd.read_csv(Path(run_dir) / 'model_parameters.csv', usecols=columns)
    old = pd.read_csv(Path(previous_dir) / 'model_parameters.csv', usecols=columns)
    merged = new.merge(old, on=['variable_name', 'year'], how='outer', suffixes=('_new', '_old'))
    changed = merged[merged['value_eur2025_new'].ne(merged['value_eur2025_old'])]
    return changed.sort_values(['variable_name', 'year'])


def changed_inputs(run_dir, previous_dir):
    """Eingabedateien, deren Prüfsumme sich zwischen zwei Läufen unterscheidet (neu, entfernt oder geändert).

    Liest inputs.sha256 beider Laufordner. Teile eines Shapefiles (.shp, .dbf, …) werden zu einem
    Namen zusammengefasst. Gibt None zurück, wenn einem Lauf die Prüfsummen fehlen.
    """
    hashes = []
    for folder in (run_dir, previous_dir):
        path = Path(folder) / 'inputs.sha256'
        if not path.exists():
            return None
        hashes.append(dict(reversed(line.split('  ', 1)) for line in path.read_text(encoding='utf-8').splitlines() if line))
    new, old = hashes
    changed = {p for p in new.keys() | old.keys() if new.get(p) != old.get(p)}
    return sorted({Path(p).stem for p in changed})


def _panel(fig, x, y, w, h):
    """Hellgraue Fläche als Hintergrund eines Blocks (Koordinaten in Zoll, Ursprung oben links)."""
    W, H = fig.get_size_inches()
    fig.patches.append(plt.Rectangle((x / W, 1 - (y + h) / H), w / W, h / H, transform=fig.transFigure,
                                     facecolor=PANEL, edgecolor='none', zorder=0))


def _txt(fig, x, y, text, size=11, color=TEXT, weight='normal', **kwargs):
    """Text an Position (Zoll, oben links)."""
    W, H = fig.get_size_inches()
    return fig.text(x / W, 1 - y / H, text, fontsize=size, color=color, weight=weight, va='top', ha='left', **kwargs)


def _width(fig, text):
    """Breite eines Textes in Zoll (zum Aneinanderreihen von Texten)."""
    return text.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.dpi


def _number(value):
    """Zahl lesbar: große Werte mit Tausenderpunkt, kleine mit bis zu 6 Stellen."""
    if pd.isna(value):
        return '–'
    if abs(value) >= 1000:
        return f'{value:,.0f}'.replace(',', '.')
    return f'{value:.6g}'.replace('.', ',')


def _axes(fig, x, y, w, h):
    """Achsen an Position (Zoll, oben links)."""
    W, H = fig.get_size_inches()
    return fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])


def comparison_metrics(results, allowed, cost_dir):
    """Kennzahlen eines Vergleichslaufs je Jahr: LCOH-Median und Kostenanteile (wie cost_metrics),
    mittlerer MCA-Score und Spearman-ρ MCA ↔ LCOH, beide nur auf zulässigen Zellen."""
    from scipy.stats import spearmanr
    df_cost = {year: pd.read_csv(Path(cost_dir) / f'results_cost_{year}.csv') for year in (2025, 2050)}
    metrics = cost_metrics(df_cost[2025], df_cost[2050])
    for year in (2025, 2050):
        mca, lcoh = results[f'MCA_{year}'][allowed], results[f'LCOH_{year}'][allowed]
        metrics[f'mca_{year}_mean'] = round(mca.mean(), 2)
        metrics[f'rho_{year}'] = round(spearmanr(mca, lcoh).statistic, 3)
    return metrics


def mca_label(sources):
    """Kurzer Text zur MCA-Herkunft: Laufordner, sonst Dateistand von results/mca/."""
    if sources.get('mca_run'):
        return sources['mca_run']
    return f"Dateistand {sources.get('mca_mtime', '–')} (kein Laufordner)"


def changed_mca_weights(sources, previous_sources):
    """Texte 'Kriterium: alt → neu' für geänderte MCA-Gewichte, None wenn ein Lauf keine Gewichte hat."""
    paths = []
    for s in (sources, previous_sources):
        if not s.get('mca_run'):
            return None
        path = RUNS_DIR / s['mca_run'] / 'weights.json'
        if not path.exists():
            return None
        paths.append(path)
    new = json.loads(paths[0].read_text(encoding='utf-8'))
    old = json.loads(paths[1].read_text(encoding='utf-8'))
    lines = []
    for name in sorted(set(new) | set(old)):
        if new.get(name) != old.get(name):
            lines.append(f'{name}: {old.get(name)} → {new.get(name)}')
    return lines


def _delta_short(new, old, unit='', digits=1, higher_is_better=None):
    """Kurzer Δ-Text mit Farbe: grün = besser, rot = schlechter, grau = neutral oder kein Vorlauf."""
    if old is None or pd.isna(old):
        return 'kein Bezug', MUTED
    diff = new - old
    if abs(diff) < 0.5 * 10 ** -digits:
        return '± 0 ggü. Bezug', MUTED
    color = MUTED if higher_is_better is None else (DOWN if (diff > 0) == higher_is_better else UP)
    return f'{diff:+.{digits}f}{unit} ggü. Bezug'.replace('.', ','), color


def build_comparison_overview(run_dir, gdf_grid, results, allowed, sources, reference_dir=None):
    """Eine Folie MCA ↔ Kosten mit Kennzahlen, Kostenanteilen, geänderten Parametern und Karten,
    jeweils im Vergleich zum letzten Vergleichslauf.

    results:  DataFrame je Zelle (zeilengleich mit gdf_grid), Spalten MCA_<Jahr> und LCOH_<Jahr>
    allowed:  Series, True = keine No-Go-Zone (No-Go-Zellen werden in den MCA-Karten grau dargestellt)
    sources:  dict mit 'cost_run' (Name des Kostenlaufs in results/runs/), 'mca_run' (Name des MCA-Laufs,
              leer wenn keiner) und 'mca_mtime' (Dateistand von results/mca/, Ersatz ohne MCA-Lauf)
    reference_dir: Vergleichslauf, gegen den die Δ-Werte gerechnet werden (Standard: der letzte davor)

    Speichert im Laufordner results_compare.csv, sources.json und metrics.csv (Bezug für den nächsten
    Vergleichslauf), trägt die Kennzahlen in runs_index.csv ein und zeichnet overview.png (13,33 × 7,5 Zoll).
    """
    run_dir = Path(run_dir)
    info = read_run_info(run_dir)
    cost_dir = RUNS_DIR / sources['cost_run']
    cost_info = read_run_info(cost_dir)
    metrics = comparison_metrics(results, allowed, cost_dir)
    results.to_csv(run_dir / 'results_compare.csv', index=False)
    (run_dir / 'sources.json').write_text(pd.Series(sources).to_json(indent=2, force_ascii=False), encoding='utf-8')
    pd.DataFrame([metrics]).to_csv(run_dir / 'metrics.csv', index=False)
    append_to_index(run_dir, metrics)

    # Letzter Vergleichslauf als Bezug
    previous_dir = Path(reference_dir) if reference_dir else latest_run_dir('compare', before=run_dir)
    previous, previous_sources, previous_metrics = None, {}, {}
    if previous_dir is not None and (previous_dir / 'results_compare.csv').exists():
        previous = pd.read_csv(previous_dir / 'results_compare.csv')
        previous_sources = pd.read_json(previous_dir / 'sources.json', typ='series').to_dict()
        if (previous_dir / 'metrics.csv').exists():
            previous_metrics = pd.read_csv(previous_dir / 'metrics.csv').iloc[0].to_dict()
    years = sorted(int(c.split('_')[1]) for c in results if c.startswith('MCA_'))

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(13.333, 7.5), facecolor='white')

    # Kopf und Herkunft
    title = _txt(fig, 0.4, 0.25, 'MCA ↔ Kosten', 24, DARK, 'bold')
    _txt(fig, 0.4 + _width(fig, title) + 0.25, 0.36, info['started'].replace('T', ' '), 15, MUTED)
    _txt(fig, 0.4, 0.82, 'Notiz: ' + (info['note'] or '–'), 11)
    status = lambda i: 'nicht committet' if i['dirty'] else 'sauber'
    _txt(fig, 0.4, 1.13, f"Jetzt:  Kosten {sources['cost_run']} (Commit {cost_info['commit']}, {status(cost_info)})  ·  "
                         f"MCA {mca_label(sources)}", 8.5, MUTED)
    if previous is not None:
        _txt(fig, 0.4, 1.35, f"Δ-Bezug:  {previous_dir.name}  ·  Kosten {previous_sources.get('cost_run', '–')}  ·  "
                             f"MCA {mca_label(previous_sources)}", 8.5, MUTED)
    else:
        _txt(fig, 0.4, 1.35, 'Δ-Bezug:  kein früherer Vergleichslauf', 8.5, MUTED)

    # Kennzahlen: Zeilen = Jahre; Spalten = LCOH-Median, MCA-Mittel, ρ
    # (Titel, Kennzahl, Format, Nachkommastellen Δ, höher = besser?)
    tiles = [('LCOH {} [€/MWh]', 'lcoh_{}_median', '{:.1f}', 1, False),
             ('MCA {} [Ø Score]', 'mca_{}_mean', '{:.1f}', 1, True),
             ('ρ MCA↔LCOH {}', 'rho_{}', '{:.2f}', 2, None)]
    for i, year in enumerate(years):
        for j, (label, key, fmt, digits, better) in enumerate(tiles):
            x, y = 0.4 + j * 1.37, 1.75 + i * 0.95
            _panel(fig, x, y, 1.3, 0.87)
            value = metrics[key.format(year)]
            _txt(fig, x + 0.1, y + 0.07, label.format(year), 7.5, MUTED, 'bold')
            _txt(fig, x + 0.1, y + 0.25, fmt.format(value).replace('.', ','), 17, DARK, 'bold')
            delta_text, delta_color = _delta_short(value, previous_metrics.get(key.format(year)),
                                                   '', digits, better)
            _txt(fig, x + 0.1, y + 0.64, delta_text, 7.5, delta_color, 'bold')

    # Kostenanteile: je Jahr letzter und dieser Lauf
    _txt(fig, 0.4, 1.57, 'LCOH: Median aller Zellen  ·  MCA und ρ: nur zulässige Zellen', 6.5, MUTED)
    _txt(fig, 0.4, 3.72, 'Mittlere Kostenanteile [€/MWh$_{H2}$]', 11, TEXT, 'bold')
    ax = _axes(fig, 0.75, 4.05, 2.35, 1.4)
    bars = []                       # (Beschriftung, Kennzahlen)
    for year in years:
        if previous_metrics.get(f'{year}_{list(COMPONENTS.values())[0]}') is not None:
            bars.append((f'{year}\nvorher', year, previous_metrics))
        bars.append((f'{year}\njetzt', year, metrics))
    positions = [k + (0.4 if k >= len(bars) / 2 else 0) for k in range(len(bars))]
    bottom = [0.0] * len(bars)
    for label, color in zip(COMPONENTS.values(), COMPONENT_COLORS):
        values = [m[f'{year}_{label}'] for _, year, m in bars]
        ax.bar(positions, values, bottom=bottom, color=color, width=0.7, label=label)
        bottom = [b + v for b, v in zip(bottom, values)]
    for pos, total in zip(positions, bottom):
        ax.text(pos, total + 2, f'{total:.0f}', ha='center', va='bottom', fontsize=8, color=TEXT)
    ax.set_xticks(positions, [b[0] for b in bars])
    ax.set_ylim(0, max(bottom) * 1.18)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=7.5, colors=MUTED)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=7.5, frameon=False)

    # Änderungen ggü. Bezug: Kostenparameter (Snapshots der Kostenläufe) und Eingabedateien (inputs.sha256)
    _panel(fig, 0.4, 5.85, 4.05, 1.5)
    _txt(fig, 0.5, 5.92, 'Änderungen ggü. Bezug', 10.5, DARK, 'bold')
    lines = [('Kostenparameter', True)]
    previous_cost_dir = RUNS_DIR / previous_sources['cost_run'] if previous_sources.get('cost_run') else None
    if previous_cost_dir is None or not (previous_cost_dir / 'model_parameters.csv').exists():
        lines.append(('kein Bezug mit Parameter-Snapshot', False))
    else:
        changed = changed_parameters(cost_dir, previous_cost_dir)
        if changed.empty:
            lines.append(('keine geändert', False))
        else:
            shown = changed.head(2 if len(changed) <= 2 else 1)
            lines += [(f"{row['variable_name']} {int(row['year'])}: {_number(row['value_eur2025_old'])} → "
                       f"{_number(row['value_eur2025_new'])}", False) for _, row in shown.iterrows()]
            if len(changed) > len(shown):
                lines.append((f'… und {len(changed) - len(shown)} weitere (model_parameters.csv)', False))
    weight_lines = changed_mca_weights(sources, previous_sources) if previous is not None else None
    if weight_lines is None:
        lines.append(('MCA-Gewichte: kein Bezug mit MCA-Laufordner', False))
    elif not weight_lines:
        lines.append(('MCA-Gewichte: unverändert', False))
    else:
        lines.append(('MCA-Gewichte: ' + '; '.join(weight_lines), False))
    lines.append(('Eingabedateien (data/interim)', True))
    files = changed_inputs(run_dir, previous_dir) if previous is not None else None
    if files is None:
        lines.append(('kein Bezug mit Prüfsummen (inputs.sha256)', False))
    elif not files:
        lines.append(('keine geändert', False))
    else:
        wrapped = textwrap.wrap(f'{len(files)} geändert: ' + ', '.join(files), 70)
        lines += [(line, False) for line in wrapped[:2]]
        if len(wrapped) > 2:
            lines[-1] = (lines[-1][0] + ' …', False)
    for k, (line, bold) in enumerate(lines):
        _txt(fig, 0.5, 6.17 + k * 0.165, line, 7, TEXT, 'bold' if bold else 'normal')

    # Karten: Zeilen = Jahre; Spalten = MCA, Δ MCA, LCOH, Δ LCOH (Δ = dieser minus letzter Lauf)
    def draw(x, y, values, cmap, unit, title, symmetric=False):
        # Karte und Farbskala in eigenen Achsen, damit nichts in die Nachbarkarte ragt.
        ax = _axes(fig, x, y + 0.42, 1.55, 2.25)
        cax = _axes(fig, x + 1.6, y + 0.7, 0.07, 1.8)
        gdf = gdf_grid[['geometry']].copy()
        gdf['value'] = pd.to_numeric(values).values
        vmin, vmax = gdf['value'].min(), gdf['value'].max()
        if symmetric:
            limit = gdf['value'].abs().max()
            if not limit > 1e-9:
                unit = 'unverändert ggü. Bezug'
                limit = 1.0
            vmin, vmax = -limit, limit
        gdf.plot(column='value', ax=ax, cmap=cmap, linewidth=0, vmin=vmin, vmax=vmax,
                 missing_kwds={'color': '#C8CDD0'})
        fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin, vmax), cmap=cmap), cax=cax)
        cax.tick_params(labelsize=7, colors=MUTED)
        _txt(fig, x, y, title, 10, TEXT, 'bold')
        _txt(fig, x, y + 0.22, unit, 7.5, MUTED)
        ax.set_axis_off()

    for i, year in enumerate(years):
        mca, lcoh = results[f'MCA_{year}'].where(allowed), results[f'LCOH_{year}']
        panels = [(mca, 'viridis', 'Score [0–100], No-Go grau', f'MCA {year}', False),
                  (mca - previous[f'MCA_{year}'].where(allowed), 'RdBu', 'blau = besser',
                   f'Δ MCA {year}', True) if previous is not None else None,
                  (lcoh, 'YlOrRd', '€/MWh$_{H2}$', f'LCOH {year}', False),
                  (lcoh - previous[f'LCOH_{year}'], 'RdBu_r', '€/MWh$_{H2}$, blau = günstiger',
                   f'Δ LCOH {year}', True) if previous is not None else None]
        for j, panel in enumerate(panels):
            x, y = 4.75 + j * 2.1, 1.75 + i * 2.8
            if panel is None:
                _txt(fig, x + 0.3, y + 1.3, 'Δ: kein\nBezugslauf', 10, MUTED)
                continue
            draw(x, y, *panel)

    fig.savefig(run_dir / 'overview.png', dpi=150, facecolor='white')
    plt.close(fig)
    return run_dir / 'overview.png'
