# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local calibration information retained by a later training window."""

import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

import numpy as np

from . import esa_saved_weak_directions as matrix_report
from . import esa_training_duration_weakness as duration_report
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .local_tangent import conditional_column_norm
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'TRAINING_WINDOW_GEOMETRY_PLAN.md'
FREEZE = FOLDER + 'training-window-geometry-freeze.json'
RESULT = FOLDER + 'training-window-geometry-result.json'
RANK_RTOL = 1e-10


def retained(matrix, *, first_rows):
    """Generalized calibration information eigenvalues for a fixed suffix."""
    j = np.asarray(matrix, float)
    if (j.ndim != 2 or not j.shape[1] or type(first_rows) is not int or first_rows < 1
            or len(j) - first_rows < j.shape[1] or not np.isfinite(j).all()):
        raise ValueError('finite rectangular full and calibration-only designs required')
    u, singular, _ = np.linalg.svd(j, full_matrices=False)
    if singular[-1] <= RANK_RTOL * singular[0]:
        raise ValueError('a full-rank reference design is required')
    late = j[first_rows:]
    local_singular = np.linalg.svd(late, full_matrices=False, compute_uv=False)
    rank = int(np.count_nonzero(local_singular > RANK_RTOL * local_singular[0]))
    # In full-design information units the retained design has left
    # singular vectors restricted to the later rows. Avoid a normal matrix.
    retained_singular = np.linalg.svd(u[first_rows:], full_matrices=False, compute_uv=False)
    fractions = np.minimum(retained_singular[::-1] ** 2, 1.0)
    return dict(calibration_rank=rank, total_parameters=j.shape[1],
                first_rows=first_rows, retained_information_ratios=fractions.tolist(),
                maximum_local_std_growth=float(1 / retained_singular[-1])
                    if rank == j.shape[1] and retained_singular[-1] > RANK_RTOL else None,
                reference_singular_values=singular.tolist(),
                calibration_singular_values=local_singular.tolist())


def _geometry(fit, *, epochs, cuts):
    info = fit['local_linearization']
    names = info['active_parameters']
    j = np.asarray(info['jacobian'], float)
    if (info['convention'] != 'whitened residual derivative by normalized parameter'
            or fit['converged'] is not True or names != fit['active_parameters']
            or len(names) not in (26, 27) or len(set(names)) != len(names)
            or j.shape != (epochs * 3, len(names))):
        raise ValueError('saved full normalized sequential training derivative required')
    indices = {name: names.index(name) for name in duration_report.PARAMETERS}
    whole = {name: conditional_column_norm(j, index) for name, index in indices.items()}
    if min(whole.values()) <= 0:
        raise ValueError('nonzero reference information required')
    rows = {}
    for cut in cuts:
        data = retained(j, first_rows=cut * 3)
        if not np.allclose(data['reference_singular_values'], fit['singular_values'], rtol=1e-8, atol=1e-9):
            raise ValueError('sealed full-training singular values must reproduce')
        information = {name: (conditional_column_norm(j[cut * 3:], index) / whole[name]) ** 2
                       for name, index in indices.items()}
        rows[str(cut)] = dict(data, direction_choice_reports=cut, calibration_reports=epochs - cut,
                              conditional_bias_information_retained=information)
    return rows


def _reports(matrix, longer, prior, duration):
    if (matrix.completion['manifest_sha256'] != prior['manifest_sha256']
            or matrix.completion['summary_sha256'] != prior['summary_sha256']
            or set(matrix.tasks) != set(prior['cases'])
            or set(matrix.rows) != set(prior['cases'])
            or prior['tasks_total'] != 24 or prior['numerical_converged'] != 20):
        raise ValueError('same sealed 24-fit development matrix required')
    rows = []
    for identity, case in sorted(prior['cases'].items()):
        record = dict(identity=identity, status=case['status'], passed=case['numerical_converged'])
        if matrix.rows[identity]['passed'] is not record['passed']:
            raise ValueError('sealed numeric disposition differs')
        if record['passed']:
            record['windows'] = _geometry(matrix.artifact(identity, 'fit.json'), epochs=400, cuts=(200,))
        rows.append(record)
    if (duration['studies'][1] != longer.prefix
            or duration['manifest_sha256'][1] != longer.completion['manifest_sha256']
            or duration['summary_sha256'][1] != longer.completion['summary_sha256']
            or set(longer.tasks) != {'increment', 'point'}):
        raise ValueError('same sealed 600-report development fits required')
    longer_rows = {}
    for law in ('increment', 'point'):
        raw = longer.artifact(law, 'fit.json', raw=True)
        if digest(raw) != duration['laws'][law]['late_fit_sha256']:
            raise ValueError('600-report tangent differs')
        longer_rows[law] = _geometry(json.loads(raw), epochs=600, cuts=(200, 400))
    return dict(matrix=rows, longer=longer_rows)


def run(root, action):
    paths = (FOLDER + 'esa-saved-weak-directions.json', FOLDER + 'esa-training-duration-weakness.json')
    inputs = {path: (root / path).read_bytes() for path in paths}
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={path: digest(value) for path, value in inputs.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_training_window_geometry.py'))},
        fits=0, split_windows=24, protected_reads=0, threads=1, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same frozen calibration window geometry required')
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        matrix, longer = [stack.enter_context(closing(ClosedStudy(root, prefix, store=store)))
                          for prefix in (matrix_report.STUDY, duration_report.LATE)]
        result = _reports(matrix, longer, *(json.loads(inputs[path]) for path in paths))
    payload = encoded(dict(result, freeze_sha256=digest(config), new_fits=0,
                           protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), passing_matrix=sum(row['passed'] for row in result['matrix']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
