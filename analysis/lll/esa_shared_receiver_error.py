# SPDX-License-Identifier: AGPL-3.0-or-later
"""Distance to a change in the ranking of fixed ESA development forecasts."""
import argparse
from contextlib import closing
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_rinex_code_comparison import BASE, MATRIX, MATRIX_SHA, PARENT, PARENT_SHA, PPP, coordinates
from .esa_rinex_window import FOLDER
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_SHARED_RECEIVER_ERROR_PLAN.md'
REPORT = FOLDER+'esa-shared-receiver-error-result.json'


def closest_win(target, competitors):
    """Shortest common path correction putting target no farther than both rivals."""
    import numpy as np

    target = np.asarray(target, float)
    others = np.asarray(competitors, float)
    if (target.ndim != 2 or target.shape[1] != 3 or not len(target)
            or others.shape != (2, *target.shape) or not np.all(np.isfinite(target))
            or not np.all(np.isfinite(others))):
        raise ValueError('three aligned finite north/east/up error paths required')
    flat = target.ravel()
    others = others.reshape(2, -1)
    delta = flat-others
    lengths = np.linalg.norm(delta, axis=1)
    unique = lengths > 0
    normals = delta[unique]/lengths[unique, None]
    offsets = np.einsum('ij,ij->i', normals, flat+others[unique])/2
    tol = 1e-10*max(1., np.max(abs(offsets), initial=0.))
    candidates = [np.zeros_like(flat)]
    candidates.extend(normal*offset for normal, offset in zip(normals, offsets, strict=True))
    if len(normals) == 2:
        candidates.append(np.linalg.lstsq(normals, offsets, rcond=None)[0])
    feasible = [x for x in candidates if np.all(normals @ x >= offsets-tol)]
    if not feasible:
        raise ValueError('no numerical intersection for the fixed model score boundaries')
    return min(feasible, key=np.linalg.norm).reshape(target.shape)


def path_metrics(path):
    import numpy as np

    values = np.asarray(path, float)
    if (values.ndim != 2 or values.shape[1] != 3 or not len(values)
            or not np.all(np.isfinite(values))):
        raise ValueError('finite north/east/up chart required')
    horizontal = np.linalg.norm(values[:, :2], axis=1)
    up = abs(values[:, 2])
    return dict(horizontal_rms_m=float(np.linalg.norm(horizontal)/math.sqrt(len(values))),
                vertical_rms_m=float(np.linalg.norm(up)/math.sqrt(len(values))),
                maximum_horizontal_m=float(np.max(horizontal)),
                maximum_absolute_up_m=float(np.max(up)))


def position_limit_margins(path, limits):
    """Infimum path RMS correction needed to break each individual limit."""
    observed = path_metrics(path)
    if set(limits) != set(observed) or any(not math.isfinite(v) or v < 0 for v in limits.values()):
        raise ValueError('complete finite positive position-screen limits required')
    scale = math.sqrt(len(path))
    return {key: max(0., limit-observed[key])/(scale if key.startswith('maximum_') else 1.)
            for key, limit in limits.items()}


def evaluate(matrix, parent, previous):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .esa_alternate_ppp_scoring import MODELS
    from .ilvis0_prediction_observed import recipe

    original = json.loads(gzip.decompress(parent.input('training', raw=True)))
    if len(original) != 800 or previous['common_parent_indices'] != list(range(120)):
        raise ValueError('all 120 original later receiver epochs required')
    later = coordinates(original[400:520])
    limits = recipe()['accuracy_limits']
    results = []
    for setting in previous['settings']:
        law = setting['law']
        errors = {}
        for model in MODELS:
            start = setting['primary_start'][model]
            raw = matrix.artifact(f'{model}-1-{law}-{start}', 'forecast.json', raw=True)
            track = json.loads(raw)
            if (digest(raw) != setting['forecast_sha256'][model]
                    or track['training_epochs'] != 400 or track['prediction_epochs'] != 120
                    or track['prediction_receiver_positions_used'] is not False
                    or len(track['coordinates']) != 520):
                raise ValueError('forecast binding differs')
            error = receiver_errors(track['coordinates'][400:], later)
            recalculated = np.linalg.norm(error)/math.sqrt(120)
            reference = setting['by_receiver']['air1']['scores'][model]['total_rms_m']
            if not math.isclose(recalculated, reference, abs_tol=1e-9, rel_tol=1e-12):
                raise ValueError('original total RMS changed')
            errors[model] = error
        assured = ('sphere_rotating', 'sphere_still', 'flat_still')
        if not all(np.linalg.norm(errors[a]) < np.linalg.norm(errors[b])
                   for a, b in zip(assured, assured[1:])):
            raise ValueError('original lower-error candidates changed')
        reversal = {}
        for target in ('flat_still', 'sphere_still'):
            competitors = [v for model, v in errors.items() if model != target]
            correction = closest_win(errors[target], competitors)
            corrected_rms = {model: float(np.linalg.norm(v-correction)/math.sqrt(120))
                             for model, v in errors.items()}
            if corrected_rms[target] > min(corrected_rms.values())+1e-7:
                raise ValueError('minimal correction does not reach the target region')
            reversal[target] = dict(path_rms_m=float(np.linalg.norm(correction)/math.sqrt(120)),
                                    corrected_rms_m=corrected_rms,
                                    common_correction_neu_m=correction.tolist())
        results.append(dict(law=law, reversal=reversal,
                            accuracy_limit_margins_m=position_limit_margins(errors['sphere_rotating'], limits)))
    return dict(settings=results, limits=limits, later_positions=120,
                fitted_paths_fixed=True, receiver_metric_fixed=True, new_fits=0,
                new_forecast_propagations=0, protected_reads=0,
                aircraft_error_calibrated=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('configure a single numerical thread before imports')
    import numpy as np

    root = Path.cwd()
    prior = (root/PPP).read_bytes()
    previous = json.loads(prior)
    plan = root/PLAN
    output = root/(BASE+'shared-error')
    output.mkdir(exist_ok=True)
    manifest = output/'freeze.json'
    result_path = root/REPORT
    with (output/'run.lock').open('a') as lock, closing(ArchiveStore(root)) as store:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with closing(ClosedStudy(root, MATRIX, store=store)) as matrix, \
                closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if (matrix.completion['manifest_sha256'] != MATRIX_SHA
                    or previous['matrix_manifest_sha256'] != MATRIX_SHA
                    or previous['matrix_summary_sha256'] != matrix.completion['summary_sha256']
                    or previous['parent_manifest_sha256'] != PARENT_SHA
                    or parent.completion['manifest_sha256'] != PARENT_SHA
                    or matrix.input('parent_identity')['parent_prefix'] != PARENT
                    or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'
                    or {(s['profile'], s['law']) for s in previous['settings']}
                       != {(True, 'increment'), (True, 'point')} or len(previous['settings']) != 2):
                raise ValueError('same two complete development settings required')
            paths = [Path(__file__), plan]
            paths.extend(root/'analysis/lll'/name for name in (
                'airquantumgrav_scoring.py', 'airquantumgrav_truth.py', 'esa_alternate_ppp_scoring.py',
                'esa_rinex_code_comparison.py', 'ilvis0_prediction_observed.py',
                'compute_budget.py', 'studies/artifacts.py', 'studies/closed.py'))
            freeze = encoded(dict(
                sources={str(path.relative_to(root)): digest(path.read_bytes()) for path in paths},
                inputs=dict(previous=digest(prior), matrix=MATRIX_SHA, parent=PARENT_SHA),
                environment=dict(python=platform.python_version(), numpy=np.__version__,
                                 os=platform.system(), arch=platform.machine(), threads=threads),
                max_new_fits=0, max_new_forecasts=0, observed_groups=['187']))
            if args.action == 'freeze' and not manifest.exists():
                atomic(manifest, freeze)
            if manifest.read_bytes() != freeze:
                raise ValueError('shared receiver error freeze differs')
            if args.action == 'freeze':
                print(digest(freeze))
                return
            if not result_path.exists():
                result = evaluate(matrix, parent, previous)
                atomic(result_path, encoded(dict(freeze=json.loads(freeze), freeze_sha256=digest(freeze),
                    result=result, result_sha256=digest(encoded(result)))))
            saved = json.loads(result_path.read_bytes())
            if (digest(freeze) != saved['freeze_sha256']
                    or digest(encoded(saved['freeze'])) != saved['freeze_sha256']
                    or digest(encoded(saved['result'])) != saved['result_sha256']):
                raise ValueError('saved receiver error comparison differs')
            print(f'verified shared receiver error comparison, SHA-256 {saved["result_sha256"]}')


if __name__ == '__main__':
    main()
