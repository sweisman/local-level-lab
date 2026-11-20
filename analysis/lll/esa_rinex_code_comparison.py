# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the sealed development-only ESA code paths with the existing export."""
import argparse
from bisect import bisect_left
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
from .esa_rinex_window import FOLDER, LOCAL, MATRIX, MATRIX_SHA, WEEK
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

BASE = LOCAL+'/rinex-400-120-stream/code-position/'
PLAN = FOLDER+'ESA_RINEX_CODE_COMPARISON_PLAN.md'
PPP = FOLDER+'esa-alternate-ppp-scoring-result.json'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
PARENT_SHA = '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
CODE_SHA = '4285acf25ab46473b0998273e7935ec8447b482a04f88ce36e862eace1f1709a'
CODE_FREEZE_SHA = '0f498b01188e94af1abc04b40d25bb0fe3c279ba3808c3a678a8c5b696cd7460'
METHODS = ('l1_broadcast', 'dual_frequency')


def paired_epochs(queries, raw, clock):
    """Match raw markers and unapplied-offset-adjusted markers independently."""
    corrected = [t-offset for t, offset in zip(raw, clock, strict=True)]
    if (len(raw) < 2 or not queries or
            any(not math.isfinite(t) for grid in (queries, raw, corrected) for t in grid)):
        raise ValueError('finite GPS query and observation times required')
    assignments, largest = [], []
    for grid in (raw, corrected):
        if any(a >= b for a, b in zip(grid, grid[1:])):
            raise ValueError('strictly increasing code times required')
        indices = []
        for t in queries:
            high = bisect_left(grid, t)
            candidates = range(max(0, high-1), min(len(grid), high+1))
            indices.append(min(candidates, key=lambda i: abs(grid[i]-t)))
        if indices != sorted(set(indices)):
            raise ValueError('distinct ordered code epochs required')
        maximum = max(abs(grid[i]-t) for i, t in zip(indices, queries, strict=True))
        if maximum > .001:
            raise ValueError('GPS match exceeds 1 ms')
        assignments.append(indices)
        largest.append(maximum)
    if assignments[0] != assignments[1]:
        raise ValueError('receiver clock convention changed epoch assignment')
    return assignments[0], largest


def coordinates(rows):
    return [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']),
             row['height_m']] for row in rows]


def build(root, matrix, parent, saved, code):
    import numpy as np
    from .esa_alternate_ppp_scoring import MODELS, rank_setting, score_errors

    original = json.loads(gzip.decompress(parent.input('training', raw=True)))
    times = matrix.input('forecast_times')
    if len(original) != 800 or len(times) != 520:
        raise ValueError('complete already opened parent required')
    first = original[0]['time_s']-times[0]
    queries = [r['time_s'] for r in original[:520]]
    if any(abs(first+t-q) > 1e-8 for t, q in zip(times, queries, strict=True)):
        raise ValueError('parent and matrix query times differ')
    positions = code['positions']
    if (len(positions) != 1041 or code['freeze_sha256'] != CODE_FREEZE_SHA
            or digest(encoded(positions)) != code['positions_sha256']
            or any(row['gps_week'] != WEEK for row in positions)
            or any(row[method]['status'] != 'converged'
                   for row in positions for method in METHODS)):
        raise ValueError('expected unchanged complete code positions')
    indices, offsets = paired_epochs(queries, [r['gps_week_seconds'] for r in positions],
                                     [r['receiver_clock_offset_s'] for r in positions])
    receiver = coordinates(original[:520])
    compared, code_paths = {}, {}
    for method in METHODS:
        code_paths[method] = [[positions[i][method][key] for key in
            ('latitude_rad', 'longitude_rad', 'ellipsoid_height_m')] for i in indices]
        delta = position_errors_neu(code_paths[method], receiver).tolist()
        compared[method] = dict(signed_errors_neu_m=delta)
        for label, subset in (('earlier', delta[:400]), ('later', delta[400:])):
            compared[method][label] = error_metrics(subset) | dict(
                signed_mean_neu_m=[math.fsum(axis)/len(subset) for axis in zip(*subset)])
    settings = []
    for setting in saved['settings']:
        profile, law = setting['profile'], setting['law']
        tracks = {}
        for model in MODELS:
            start = setting['primary_start'][model]
            raw = matrix.artifact(f'{model}-{int(profile)}-{law}-{start}', 'forecast.json', raw=True)
            record = json.loads(raw)
            if (digest(raw) != setting['forecast_sha256'][model]
                    or record['training_epochs'] != 400 or record['prediction_epochs'] != 120
                    or record['prediction_receiver_positions_used'] is not False
                    or len(record['coordinates']) != 520):
                raise ValueError('expected exact three-export forecast')
            tracks[model] = record['coordinates'][400:]
        scores = {}
        for method in METHODS:
            per_model = {model: score_errors(position_errors_neu(track, code_paths[method][400:]),
                                           np.zeros((120, 3)), range(120))
                         for model, track in tracks.items()}
            scores[method] = dict(scores=per_model, ranking=rank_setting(per_model))
        settings.append(dict(profile=profile, law=law, by_code=scores))
    return dict(matched_epochs=len(indices), later_epochs=120, matched_code_indices=indices,
                maximum_raw_time_difference_s=offsets[0],
                maximum_adjusted_time_difference_s=offsets[1],
                code_minus_receiver=compared, forecast_comparisons=settings,
                new_fits=0, new_forecast_propagations=0, protected_reads=0,
                absolute_receiver_accuracy_established=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    settings = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in settings.items()):
        raise ValueError('one numerical thread must be configured before imports')
    import numpy as np
    from .esa_alternate_ppp_scoring import __file__ as ranking
    from .studies.artifacts import ArchiveStore

    root = Path.cwd()
    raw = (root/(BASE+'positions.json.gz')).read_bytes()
    if digest(raw) != CODE_SHA or digest((root/(BASE+'freeze.json')).read_bytes()) != CODE_FREEZE_SHA:
        raise ValueError('code result or freeze has changed')
    saved_raw = (root/PPP).read_bytes()
    saved = json.loads(saved_raw)
    with (root/(BASE+'comparison.lock')).open('a') as lock, closing(ArchiveStore(root)) as store:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with closing(ClosedStudy(root, MATRIX, store=store)) as matrix, \
                closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if (matrix.completion['manifest_sha256'] != MATRIX_SHA
                    or saved['matrix_manifest_sha256'] != MATRIX_SHA
                    or saved['matrix_summary_sha256'] != matrix.completion['summary_sha256']
                    or saved['parent_manifest_sha256'] != PARENT_SHA
                    or parent.completion['manifest_sha256'] != PARENT_SHA
                    or matrix.input('parent_identity')['parent_prefix'] != PARENT
                    or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'
                    or {(s['profile'], s['law']) for s in saved['settings']}
                       != {(True, 'increment'), (True, 'point')} or len(saved['settings']) != 2):
                raise ValueError('same previously scored ESA development matrix required')
            sources = [Path(__file__), Path(ranking), root/PLAN]
            sources.extend(root/'analysis/lll'/name for name in (
                'esa_fit_adjusted_forecast_report.py', 'airquantumgrav_truth.py',
                'airquantumgrav_geographic_report.py', 'ilvis0_prediction_observed.py',
                'studies/closed.py', 'studies/artifacts.py', 'compute_budget.py',
            ))
            freeze = encoded(dict(
                sources={str(path.relative_to(root)): digest(path.read_bytes()) for path in sources},
                code=CODE_SHA, code_freeze=CODE_FREEZE_SHA, prior_ppp=digest(saved_raw),
                matrix=MATRIX_SHA, parent=PARENT_SHA, observed_groups=['187'],
                environment=dict(python=platform.python_version(), numpy=np.__version__,
                                 os=platform.system(), arch=platform.machine(), settings=settings),
                maximum_new_fits=0, maximum_new_forecast_propagations=0,
            ))
            manifest = root/(BASE+'comparison-freeze.json')
            if args.action == 'freeze' and not manifest.exists():
                atomic(manifest, freeze)
            if manifest.read_bytes() != freeze:
                raise ValueError('code comparison freeze differs')
            if args.action == 'freeze':
                print(digest(freeze))
                return
            path = root/(BASE+'comparison.json')
            if not path.exists():
                result = build(root, matrix, parent, saved, json.loads(gzip.decompress(raw)))
                atomic(path, encoded(dict(freeze_sha256=digest(freeze), result=result,
                                          result_sha256=digest(encoded(result)))))
            value = json.loads(path.read_bytes())
            if (value['freeze_sha256'] != digest(freeze)
                    or value['result_sha256'] != digest(encoded(value['result']))):
                raise ValueError('saved code comparison has changed')
            print(f'verified {value["result"]["matched_epochs"]} matches, SHA-256 {value["result_sha256"]}')


if __name__ == '__main__':
    main()
