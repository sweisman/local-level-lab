# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score the two sealed GLONASS code paths without opening a new fit."""
import argparse
from contextlib import closing
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import platform

from .airquantumgrav_geographic_report import error_metrics
from .compute_budget import environment
from .esa_fit_adjusted_forecast_report import position_errors_neu
from .esa_glonass_code_study import DIRECTORY
from .esa_rinex_code_comparison import BASE, MATRIX, MATRIX_SHA, PARENT, PARENT_SHA, PPP, coordinates
from .glonass_code import METHODS
from .esa_rinex_window import FOLDER
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_GLONASS_COMPARISON_PLAN.md'
REPORT = FOLDER+'esa-glonass-comparison-result.json'
POSITION_SHA = 'c5a3c8c2dc55cbbbbf0472ac1d087c846ebd7d1a3290c7bdefcbf284bb577827'
POSITION_FREEZE = '21745bdc8487a50c0be775362657806667cc43dda3badd7cbaa9a31b90ac809a'
MATCH_SHA = '3941af07c750e1e31d862f3a7b70dd0051adf4718306d36cdf8822989524a72d'


def compare(matrix, parent, previous, position_rows, indices):
    import numpy as np
    from statistics import median
    from .esa_alternate_ppp_scoring import MODELS, rank_setting, score_errors

    original = json.loads(gzip.decompress(parent.input('training', raw=True)))
    if (len(original) != 800 or len(indices) != 520 or indices != sorted(set(indices))
            or not 0 <= indices[0] < indices[-1] < len(position_rows)):
        raise ValueError('exact saved parent and 520 distinct matches required')
    selected = [position_rows[i] for i in indices]
    if any(abs(row['gps_week_seconds']-ref['time_s']) > .001
           for row, ref in zip(selected, original[:520], strict=True)):
        raise ValueError('GLONASS rows do not match the GPS source grid')
    receiver = coordinates(original[:520])
    compared, paths = {}, {}
    for method in METHODS:
        full = [row[method] for row in position_rows if row[method]['status'] == 'converged']
        compared[method] = dict(full_solved=len(full), full_total=len(position_rows),
             full_median_range_rms_m=median(row['range_rms_m'] for row in full) if full else None,
             full_min_satellites=min((len(row['used_satellites']) for row in full), default=0),
             full_max_satellites=max((len(row['used_satellites']) for row in full), default=0))
        if any(row[method]['status'] != 'converged' for row in selected):
            compared[method]['status'] = 'incomplete_matched_coverage'
            continue
        paths[method] = [[row[method][key] for key in
            ('latitude_rad', 'longitude_rad', 'ellipsoid_height_m')] for row in selected]
        delta = position_errors_neu(paths[method], receiver).tolist()
        compared[method]['signed_errors_neu_m'] = delta
        for label, subset in (('earlier', delta[:400]), ('later', delta[400:])):
            compared[method][label] = error_metrics(subset) | dict(
                signed_mean_neu_m=[math.fsum(axis)/len(subset) for axis in zip(*subset)])
    results = []
    if set(paths) == set(METHODS):
        for setting in previous['settings']:
            profiles = {}
            for model in MODELS:
                identity = f"{model}-1-{setting['law']}-{setting['primary_start'][model]}"
                raw = matrix.artifact(identity, 'forecast.json', raw=True)
                forecast = json.loads(raw)
                if (digest(raw) != setting['forecast_sha256'][model]
                        or forecast['prediction_receiver_positions_used'] is not False
                        or (forecast['training_epochs'], forecast['prediction_epochs']) != (400, 120)
                        or len(forecast['coordinates']) != 520):
                    raise ValueError('same already sealed training-only forecast required')
                profiles[model] = forecast['coordinates'][400:]
            scores = {}
            for method, path in paths.items():
                models = {model: score_errors(position_errors_neu(predicted, path[400:]),
                                               np.zeros((120, 3)), range(120))
                          for model, predicted in profiles.items()}
                scores[method] = dict(scores=models, ranking=rank_setting(models))
            results.append(dict(law=setting['law'], by_glonass_code=scores))
    return dict(code_minus_receiver=compared, matched_indices=indices, later_epochs=120,
                settings=results, refits=0, forecast_propagations=0, protected_reads=0,
                absolute_receiver_accuracy_established=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np

    root = Path.cwd()
    folder = root/DIRECTORY
    positions = json.loads(gzip.decompress((folder/'positions.json.gz').read_bytes()))
    matching = json.loads((root/(BASE+'comparison.json')).read_bytes())
    saved = json.loads((root/PPP).read_bytes())
    if (digest(encoded(positions['positions'])) != POSITION_SHA
            or positions['positions_sha256'] != POSITION_SHA
            or positions['freeze_sha256'] != POSITION_FREEZE
            or digest((folder/'freeze.json').read_bytes()) != POSITION_FREEZE
            or digest(encoded(matching['result'])) != MATCH_SHA or matching['result_sha256'] != MATCH_SHA):
        raise ValueError('sealed GLONASS positions or GPS matching differ')
    with (folder/'comparison.lock').open('a') as lock, closing(ArchiveStore(root)) as store:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with closing(ClosedStudy(root, MATRIX, store=store)) as matrix, \
                closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if (matrix.completion['manifest_sha256'] != MATRIX_SHA
                    or saved['matrix_manifest_sha256'] != MATRIX_SHA
                    or matrix.completion['summary_sha256'] != saved['matrix_summary_sha256']
                    or parent.completion['manifest_sha256'] != PARENT_SHA
                    or saved['parent_manifest_sha256'] != PARENT_SHA
                    or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'
                    or {(s['profile'], s['law']) for s in saved['settings']} !=
                       {(True, 'increment'), (True, 'point')} or len(saved['settings']) != 2):
                raise ValueError('same original development fit and parent required')
            sources = [Path(__file__), root/PLAN]
            sources.extend(root/'analysis/lll'/name for name in (
                'airquantumgrav_truth.py', 'airquantumgrav_geographic_report.py',
                'esa_alternate_ppp_scoring.py', 'esa_fit_adjusted_forecast_report.py',
                'esa_rinex_code_comparison.py', 'ilvis0_prediction_observed.py',
                'studies/closed.py', 'studies/artifacts.py', 'compute_budget.py'))
            freeze = encoded(dict(
                inputs=dict(glonass=POSITION_SHA, match=MATCH_SHA, matrix=MATRIX_SHA,
                            parent=PARENT_SHA, previous=digest((root/PPP).read_bytes())),
                sources={str(path.relative_to(root)): digest(path.read_bytes()) for path in sources},
                environment=dict(python=platform.python_version(), numpy=np.__version__,
                                 os=platform.system(), arch=platform.machine(), threads=threads),
                maximum_fits=0, maximum_forecast_propagations=0, observed_groups=['187'],
            ))
            binding = folder/'comparison-freeze.json'
            if args.action == 'freeze' and not binding.exists():
                atomic(binding, freeze)
            if binding.read_bytes() != freeze:
                raise ValueError('GLONASS comparison freeze differs')
            if args.action == 'freeze':
                print(digest(freeze))
                return
            report = root/REPORT
            if not report.exists():
                result = compare(matrix, parent, saved, positions['positions'],
                                 matching['result']['matched_code_indices'])
                atomic(report, encoded(dict(freeze=json.loads(freeze), freeze_sha256=digest(freeze),
                       result=result, result_sha256=digest(encoded(result)))))
            sealed = json.loads(report.read_bytes())
            if (sealed['freeze_sha256'] != digest(freeze)
                    or digest(encoded(sealed['freeze'])) != sealed['freeze_sha256']
                    or digest(encoded(sealed['result'])) != sealed['result_sha256']):
                raise ValueError('sealed comparison differs')
            print(f'{len(sealed["result"]["settings"])} complete settings, SHA-256 {sealed["result_sha256"]}')


if __name__ == '__main__':
    main()
