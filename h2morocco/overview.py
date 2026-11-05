"""Übersichtsbild im Folienformat (16:9, PNG) für einen Kostenlauf.

Zeigt auf einem Bild: Codestand und Notiz des Laufs, mittlere H2-Kosten 2025 und 2050
mit Änderung gegenüber dem vorherigen Lauf, die Kostenanteile, beide Kostenkarten und die
Parameter, die sich gegenüber dem vorherigen Lauf geändert haben.

Aufruf am Ende von 04_cost_analysis_h2_morocco.py:
    build_overview(run_dir, gdf_grid, df_results_2025, df_results_2050)

Ausgaben im Laufordner:
    overview.png    das Übersichtsbild (13,33 × 7,5 Zoll wie eine Folie)
    metrics.csv     Kennzahlen des Laufs (auch als Zeile in results/runs/runs_index.csv)
"""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from h2morocco.runs import append_to_index, latest_run_dir, read_run_info

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


def _delta(new, old):
    """Text und Farbe der Änderung gegenüber dem vorherigen Lauf."""
    if old is None or pd.isna(old):
        return 'erster Lauf', MUTED
    diff = new - old
    if abs(diff) < 0.005:
        return '± 0 ggü. Vorlauf', MUTED
    return f"{f'{diff:+.1f}'.replace('.', ',')} €/MWh ggü. Vorlauf", UP if diff > 0 else DOWN


def build_overview(run_dir, gdf_grid, df_results_2025, df_results_2050):
    """Erzeugt overview.png und metrics.csv im Laufordner und trägt die Kennzahlen in runs_index.csv ein."""
    run_dir = Path(run_dir)
    info = read_run_info(run_dir)
    previous_dir = latest_run_dir(info['kind'], before=run_dir)
    metrics = cost_metrics(df_results_2025, df_results_2050)
    previous_metrics = None
    if previous_dir is not None and (previous_dir / 'metrics.csv').exists():
        previous_metrics = pd.read_csv(previous_dir / 'metrics.csv').iloc[0].to_dict()
    pd.DataFrame([metrics]).to_csv(run_dir / 'metrics.csv', index=False)
    append_to_index(run_dir, metrics)

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(13.333, 7.5), facecolor='white')

    # Kopf: Lauf, Codestand, Notiz
    title = _txt(fig, 0.5, 0.35, 'H2-Kostenlauf', 26, DARK, 'bold')
    _txt(fig, 0.5 + _width(fig, title) + 0.25, 0.47, info['started'].replace('T', ' '), 17, MUTED)
    status = 'nicht committete Änderungen (changes.patch)' if info['dirty'] else 'sauberer Commit'
    commit = _txt(fig, 0.5, 1.0, f"Commit {info['commit']} ({info['branch']})  ·  ", 11)
    _txt(fig, 0.5 + _width(fig, commit), 1.0, status, 11, ACCENT if info['dirty'] else MUTED)
    _txt(fig, 0.5, 1.3, 'Notiz: ' + (info['note'] or '–'), 11, TEXT)

    # Kennzahlen 2025 / 2050
    for i, year in enumerate((2025, 2050)):
        x = 0.5 + i * 2.05
        _panel(fig, x, 1.8, 1.9, 2.0)
        median = metrics[f'lcoh_{year}_median']
        old = previous_metrics.get(f'lcoh_{year}_median') if previous_metrics else None
        delta_text, delta_color = _delta(median, old)
        _txt(fig, x + 0.15, 1.9, str(year), 13, MUTED, 'bold')
        _txt(fig, x + 0.15, 2.2, f'{median:.1f}'.replace('.', ','), 30, DARK, 'bold')
        _txt(fig, x + 0.15, 2.85, '€/MWh$_{H2}$ (Median)', 9.5, MUTED)
        _txt(fig, x + 0.15, 3.1, f'= {median * H2_LHV_KWH_PER_KG / 1000:.2f} €/kg'.replace('.', ','), 11)
        _txt(fig, x + 0.15, 3.35, f"5–95 %: {metrics[f'lcoh_{year}_p05']:.0f}–{metrics[f'lcoh_{year}_p95']:.0f}", 9.5, MUTED)
        _txt(fig, x + 0.15, 3.57, delta_text, 9.5, delta_color, 'bold')

    # Kostenanteile
    ax = _axes(fig, 0.75, 4.35, 1.9, 2.75)
    bottom = [0.0, 0.0]
    for label, color in zip(COMPONENTS.values(), COMPONENT_COLORS):
        values = [metrics[f'2025_{label}'], metrics[f'2050_{label}']]
        bars = ax.bar(['2025', '2050'], values, bottom=bottom, color=color, width=0.6, label=label)
        for bar, value, base in zip(bars, values, bottom):
            if value >= 6:
                ax.text(bar.get_x() + bar.get_width() / 2, base + value / 2, f'{value:.0f}', ha='center', va='center',
                        fontsize=8.5, color='white' if color in COMPONENT_COLORS[:2] else TEXT)
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.set_title('Mittlere Kostenanteile [€/MWh$_{H2}$]', fontsize=11, color=TEXT, loc='left', x=-0.25)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(labelsize=9.5, colors=MUTED)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=8.5, frameon=False)

    # Karten (ohne Hintergrundkarte: schnell und ohne API-Key)
    for i, (year, df) in enumerate(((2025, df_results_2025), (2050, df_results_2050))):
        ax = _axes(fig, 4.75, 1.75 + i * 2.8, 3.5, 2.6)
        gdf = gdf_grid[['geometry']].copy()
        gdf['lcoh'] = pd.to_numeric(df[f'H2_Price_{year} [EUR/MWh_h2]']).values
        gdf.plot(column='lcoh', ax=ax, cmap='YlOrRd', linewidth=0, legend=True,
                 legend_kwds={'shrink': 0.8, 'label': '€/MWh$_{H2}$'})
        ax.set_title(f'LCOH {year}', fontsize=11, color=TEXT)
        ax.set_axis_off()

    # Geänderte Parameter
    _panel(fig, 8.55, 1.8, 4.3, 3.0)
    _txt(fig, 8.7, 1.9, 'Geänderte Parameter ggü. Vorlauf', 12.5, DARK, 'bold')
    _txt(fig, 8.7, 2.2, previous_dir.name if previous_dir else '–', 8, MUTED)
    changed = changed_parameters(run_dir, previous_dir)
    if changed is None:
        lines = ['Erster Lauf, kein Vergleich möglich.']
    elif changed.empty:
        lines = ['Keine Parameter geändert.']
    else:
        lines = [f"{row['variable_name']} {int(row['year'])}: {_number(row['value_eur2025_old'])} → "
                 f"{_number(row['value_eur2025_new'])} {row['unit_new'] if pd.notna(row['unit_new']) and row['unit_new'] != '-' else ''}"
                 for _, row in changed.head(9).iterrows()]
        if len(changed) > 9:
            lines.append(f'… und {len(changed) - 9} weitere (model_parameters.csv)')
    for j, line in enumerate(lines):
        _txt(fig, 8.7, 2.5 + j * 0.24, line, 8.5)

    # Geänderte Dateien
    _panel(fig, 8.55, 4.95, 4.3, 2.25)
    _txt(fig, 8.7, 5.05, 'Geänderte Dateien (nicht committet)', 12.5, DARK, 'bold')
    files = info['changed_files']
    files_text = ', '.join(files[:10]) + (' …' if len(files) > 10 else '') if files else '–'
    _txt(fig, 8.7, 5.4, textwrap.fill(files_text, 62), 8.5)
    _txt(fig, 8.7, 6.85, 'Ordner: ' + run_dir.name, 8, MUTED)

    fig.savefig(run_dir / 'overview.png', dpi=150, facecolor='white')
    plt.close(fig)
    return run_dir / 'overview.png'
