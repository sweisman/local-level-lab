# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe smooth position error on the eight previously scored ESA windows."""

import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from . import esa_repeat_turn_release as turns
from .esa_repeat_turn_scoring import factors
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_precision_value import longitude_residual
from .ilvis0_solver_position import physical_metric
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


BASE = 'docs/prediction-observed-development/'
PLAN = BASE + 'ESA_SCORED_PATH_SHAPE.md'
FREEZE = BASE + 'esa-scored-path-shape-v2-freeze.json'
RESULT = BASE + 'esa-scored-path-shape-result.json'
EVIDENCE = {
    'turn': (BASE + 'esa-repeat-turn-forecast-evidence/',
             '6607441aa0ae1cf43ae263a39eb4240e552d447ffe7b4a5774995cd8fe96fd3e',
             'ae1fa59746e4f57cb539595afbde23d71899a7fdde73af438976c82daf3d988e'),
    'steady': (BASE + 'esa-straight-control-evidence/',
               '81785223db3c55f9723d921d5112223ac8c2367d872dc5aea12cd61779a8b7f8',
               'af3c50ac7841ad3ab91ee811ebe8e51e216a8e7e37673bfa2f228d0b9bf4b19c'),
}


def project_residual(times, previous_time, error, lower):
    """Project the whitened error onto offset, velocity and acceleration terms."""
    time, error, lower = (np.asarray(value, dtype=float) for value in (times, error, lower))
    if (time.ndim != 1 or len(time) < 4 or error.shape != (len(time), 3)
            or lower.shape != (error.size, error.size) or not previous_time < time[0]
            or not np.isfinite(previous_time) or np.any(np.diff(time) <= 0.)
            or not all(np.isfinite(value).all() for value in (time, error, lower))):
        raise ValueError('a complete ordered three-axis residual and covariance factor are required')
    elapsed = time - previous_time
    phase = elapsed / elapsed[-1]
    design = np.kron(np.column_stack((np.ones_like(phase), phase, phase**2)), np.eye(3))
    white = solve_triangular(lower, np.column_stack((error.ravel(), design)), lower=True)
    observed, basis = white[:, 0], white[:, 1:]
    coefficients, _, rank, _ = np.linalg.lstsq(basis, observed, rcond=None)
    if rank != design.shape[1]:
        raise ValueError('the three-axis mean-path diagnostic lost rank')
    projected = basis @ coefficients
    residual = observed - projected
    return dict(df=int(rank), residual_df=error.size-int(rank), total_energy=float(observed @ observed),
                projected_energy=float(projected @ projected), residual_energy=float(residual @ residual),
                tail_neu_m=coefficients.reshape(3, 3).sum(axis=0).tolist())


def checked_receipts(root):
    reports = {}
    for regime, (prefix, release_sha, score_sha) in EVIDENCE.items():
        release, scores = ((root/(prefix+name)).read_bytes() for name in ('receiver-release.json', 'receiver-scores.json'))
        if (digest(release), digest(scores)) != (release_sha, score_sha):
            raise ValueError('the original forecast release and score receipts are required')
        saved = json.loads(scores)
        receipt = json.loads(release)
        if (saved['release_sha256'] != release_sha or saved['protected_reads'] != 0
                or len(receipt['primary']) != 8 or len(saved['scores']) != 8):
            raise ValueError('eight previously scored cases are required in each flight condition')
        reports[regime] = receipt, saved, prefix
    return reports


def configuration(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure

    receipts = checked_receipts(root)
    project_files = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_scored_path_shape.py')
    return dict(sources={name: digest((root/name).read_bytes()) for name in source_closure(root, project_files)},
                environment=runtime_environment(), receipts=EVIDENCE,
                manifest_hashes={name: item[0]['manifest_sha256'] for name, item in receipts.items()},
                recording=187, fit_starts=0, maximum_projections=16, maximum_decoded_positions=960,
                error_covariance='both', basis=['constant', 'linear_in_time', 'quadratic_in_time'], threads=1)


def calculate(root):
    reports = checked_receipts(root)
    checked, windows = {}, {}
    metadata = reports['turn'][0]['receiver_metadata']
    with ExitStack() as stack:
        for regime, input_key in (('turn', 'input-preflight'), ('steady', 'bundle')):
            receipt, saved, prefix = reports[regime]
            archive = stack.enter_context(closing(ClosedStudy(root, prefix+'runtime')))
            owners = {outcome['study'] for outcome in receipt['outcomes'].values()}
            closures = {owner: digest(encoded(archive.completion)) for owner in owners}
            if (archive.completion['manifest_sha256'] != receipt['manifest_sha256']
                    or closures != receipt['closures'] or len(owners) != 1
                    or set(archive.rows) != set(receipt['outcomes']) or len(archive.rows) != 16
                    or receipt['receiver_metadata'] != metadata):
                raise ValueError('exact archived release closure required')
            for identity, outcome in receipt['outcomes'].items():
                envelope = archive.envelope(identity)
                if envelope['status'] != 'complete' or envelope['result_sha256'] != outcome['result_sha256']:
                    raise ValueError('terminal result differs from the original release')
            input_raw = archive.input(input_key, raw=True)
            bound = json.loads(input_raw)
            source_matches = (digest(input_raw) == receipt['preflight_sha256'] if regime == 'turn'
                              else bound['clock_sha256'] == receipt['control_clock_sha256'])
            selected = {window['window']['first_index']: window for window in bound['windows']}
            if (not source_matches or windows.keys() & selected.keys() or len(selected) != 4
                    or {case['identity'] for case in receipt['primary']} != set(saved['scores'])):
                raise ValueError('exact, disjoint previously scored windows are required')
            for case in receipt['primary']:
                identity, expected = case['identity'], case['forecast_sha256']
                payload = archive.artifact(identity, 'sealed-receiver-forecast.json', raw=True)
                forecast = json.loads(payload)
                window = selected[case['first_index']]
                if (case['state'] != 'sealed' or digest(payload) != expected
                        or forecast['law'] != case['law']
                        or forecast['training_sha256'] != window['training_receiver_sha256']
                        or forecast['times_s'] != window['query_times_s'][400:]
                        or saved['scores'][identity]['forecast_sha256'] != expected):
                    raise ValueError('forecast bytes differ from their scoring seal')
                checked[identity] = (regime, case, forecast, saved['scores'][identity])
            windows.update(selected)
    observed = turns.receiver_positions(root, windows, expected_metadata=metadata)
    if len(observed) != 8 or any(len(row[0]) != 120 for row in observed.values()):
        raise ValueError('only the eight previously released GPS periods are allowed')
    rows = []
    for identity, (regime, case, forecast, score) in checked.items():
        times, actual = observed[case['first_index']]
        if times != forecast['times_s']:
            raise ValueError('the forecast and released GPS clocks differ')
        error = np.asarray(actual) - np.asarray(forecast['mean_geodetic'])
        error[:, 1] = longitude_residual(error[:, 1])
        error *= physical_metric([forecast['anchor_geodetic']])[0]
        previous_time = forecast['previous_time']
        lower = factors(times, previous_time=previous_time, native_root=forecast['native_root_neu_m'],
                        exposure=forecast['angular_exposure'], law=forecast['law'])['both']
        result = project_residual(times, previous_time, error, lower)
        if not np.isclose(result['total_energy'], score['scores']['both']['quadratic'], rtol=1e-8, atol=1e-8):
            raise ValueError('joint error energy differs from the original score')
        rows.append(dict(identity=identity, regime=regime, law=forecast['law'], first_index=case['first_index'],
                         forecast_sha256=case['forecast_sha256'], **result))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'calculate'))
    args = parser.parse_args()
    root = Path.cwd()
    raw = encoded(configuration(root))
    if args.action == 'freeze':
        _write_equal(root/FREEZE, raw)
        print(digest(raw))
        return
    if (root/FREEZE).read_bytes() != raw:
        raise ValueError('unchanged finite diagnostic freeze required')
    rows = calculate(root)
    result = encoded(dict(freeze_sha256=digest(raw), rows=rows, new_trajectory_fits=0,
                          protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    print(json.dumps(dict(projections=len(rows), sha256=digest(result)), sort_keys=True))


if __name__ == '__main__':
    main()
