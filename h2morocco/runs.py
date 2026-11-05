"""Laufordner: Jeder Rechenlauf schreibt in einen eigenen Ordner, nichts wird überschrieben.

Ordnername:  results/runs/<Datum>_<Uhrzeit>_<Commit>[-dirty]_<Art>/
             z. B. results/runs/2026-11-05_1530_3c6df83-dirty_cost/

    Datum, Uhrzeit   Start des Laufs
    Commit           kurzer Git-Hash des Codestands
    -dirty           es gab nicht committete Änderungen; sie stehen in changes.patch
    Art              welcher Schritt gerechnet hat (z. B. cost)

Inhalt jedes Laufordners:
    run_info.json            Zeitpunkt, Commit, Branch, geänderte Dateien, Notiz, Skript
    model_parameters.csv     Kopie der Parameter, mit denen gerechnet wurde
    changes.patch            git diff gegenüber dem Commit (nur bei -dirty)
    ... plus die Ergebnisse des Schritts

Zusätzlich führt results/runs/runs_index.csv eine Zeile je Lauf mit den wichtigsten
Kennzahlen, damit sich Läufe schnell vergleichen lassen.

Beispiel:
    run_dir = new_run_dir('cost', note='Wirkungsgrad 2050 auf 0,76')
    df.to_csv(run_dir / 'results_cost_2025.csv', index=False)
"""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd

from h2morocco.utils import MODEL_PARAMETERS_CSV

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / 'results' / 'runs'
RUNS_INDEX = RUNS_DIR / 'runs_index.csv'


def _git(*args):
    """Führt einen Git-Befehl im Projektordner aus und gibt die Ausgabe zurück ('' bei Fehler).

    Nur Zeilenumbrüche am Ende werden entfernt: Bei ``git status --porcelain`` gehören
    führende Leerzeichen zum Statuscode.
    """
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.rstrip('\n')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ''


def git_state():
    """Commit, Branch und geänderte Dateien des aktuellen Codestands."""
    # Frühere Laufordner selbst zählen nicht als Codeänderung.
    changed_files = [line[3:] for line in _git('status', '--porcelain').splitlines()
                     if line and not line[3:].startswith('results/runs')]
    return {
        'commit': _git('rev-parse', '--short', 'HEAD') or 'nogit',
        'commit_full': _git('rev-parse', 'HEAD'),
        'branch': _git('rev-parse', '--abbrev-ref', 'HEAD'),
        'last_commit_message': _git('log', '-1', '--pretty=%s'),
        'dirty': bool(changed_files),
        'changed_files': changed_files,
    }


def new_run_dir(kind, note='', script=''):
    """Legt einen neuen Laufordner an, dokumentiert Codestand und Parameter und gibt den Pfad zurück.

    kind:   Art des Laufs, wird an den Ordnernamen angehängt (z. B. 'cost')
    note:   freie Beschreibung, was in diesem Lauf geändert wurde
    script: Name des aufrufenden Skripts
    """
    started = datetime.now()
    git = git_state()
    name = f"{started:%Y-%m-%d_%H%M}_{git['commit']}{'-dirty' if git['dirty'] else ''}_{kind}"
    run_dir = RUNS_DIR / name
    suffix = 2
    while run_dir.exists():                       # zwei Läufe in derselben Minute
        run_dir = RUNS_DIR / f'{name}_{suffix}'
        suffix += 1
    run_dir.mkdir(parents=True)

    shutil.copy2(MODEL_PARAMETERS_CSV, run_dir / 'model_parameters.csv')
    if git['dirty']:
        (run_dir / 'changes.patch').write_text(_git('diff', 'HEAD'), encoding='utf-8')

    info = {
        'run': run_dir.name,
        'kind': kind,
        'started': started.isoformat(timespec='seconds'),
        'note': note,
        'script': script,
        **git,
    }
    (run_dir / 'run_info.json').write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
    return run_dir


def read_run_info(run_dir):
    """Liest run_info.json eines Laufordners."""
    return json.loads((Path(run_dir) / 'run_info.json').read_text(encoding='utf-8'))


def latest_run_dir(kind, before=None):
    """Neuester Laufordner einer Art (oder None). Mit ``before`` der neueste Lauf vor diesem Ordner."""
    runs = sorted(p for p in RUNS_DIR.glob(f'*_{kind}*') if (p / 'run_info.json').exists())
    if before is not None:
        runs = [p for p in runs if p.name < Path(before).name]
    return runs[-1] if runs else None


def append_to_index(run_dir, metrics):
    """Hängt eine Zeile mit Laufinfo und Kennzahlen an results/runs/runs_index.csv an."""
    info = read_run_info(run_dir)
    row = {key: info[key] for key in ('run', 'kind', 'started', 'commit', 'dirty', 'note')}
    row.update(metrics)
    df_row = pd.DataFrame([row])
    if RUNS_INDEX.exists():
        df_row = pd.concat([pd.read_csv(RUNS_INDEX), df_row], ignore_index=True)
    df_row.to_csv(RUNS_INDEX, index=False)
