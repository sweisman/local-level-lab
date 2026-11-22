# SPDX-License-Identifier: AGPL-3.0-or-later
"""Remove only the changing-jerk driver from the sealed ESA transfer test."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

import numpy as np

from . import esa_changing_drift_transfer as full
from . import esa_drift_correction_audit as audit
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .integrated_drift_v2 import integrated_drift_v2_operator
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = full.FOLDER+'ESA_NO_SNAP_ABLATION_PLAN.md'
FREEZE = full.FOLDER+'esa-no-snap-ablation-freeze.json'
RANGES = full.FOLDER+'esa-no-snap-ablation-ranges.json.gz'
SEAL = full.FOLDER+'esa-no-snap-ablation-range-seal.json'
RESULT = full.FOLDER+'esa-no-snap-ablation-result.json'


def no_snap_operator(times, weights):
    epochs = np.asarray(times)-times[0]
    policy = full.POLICY
    return integrated_drift_v2_operator(epochs, origin_s=0.,
        acceleration_psd=policy['acceleration_psd'], jerk_psd=policy['jerk_psd'], snap_psd=0.,
        initial_position_std_m=0., initial_velocity_std_mps=0.,
        initial_acceleration_std_mps2=0., initial_jerk_std_mps3=0.,
        receiver_random_walk_psd=policy['receiver_random_walk_psd'],
        initial_receiver_offset_std_m=policy['initial_receiver_offset_std_m'],
        receiver_loading=weights, maximum_bytes=8_000_000)


def _generate(matrix, training, times, original):
    earlier = full._coordinates(training)
    anchor = earlier[0]
    gps = full._chart(earlier, anchor)
    if anchor.tolist() != original['anchor']:
        raise ValueError('earlier coordinate chart changed')
    fixed = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3))
    before = np.linalg.cholesky(np.stack([reported_covariance(row) for row in training]))
    reported = np.concatenate((before, np.repeat(before[-1:], full.LATER, axis=0)))
    operators = {key:no_snap_operator(times, weight)
                 for key, weight in zip(full.WEIGHTS, (fixed, reported), strict=True)}
    records = []
    for row in original['rows']:
        if not row['passed']:
            records.append(row)
            continue
        raw = matrix.artifact(row['identity'], 'forecast.json', raw=True)
        forecast = json.loads(raw)
        if (digest(raw) != row['forecast_sha256'] or forecast['times_s'] != times
                or forecast['prediction_receiver_positions_used'] is not False
                or forecast['training_epochs'] != full.CUT or forecast['prediction_epochs'] != full.LATER):
            raise ValueError('same passing earlier-only forecasts required')
        path = full._chart(forecast['coordinates'], anchor)
        later = path[full.CUT:]
        if not np.array_equal(later, row['raw_future_m']):
            raise ValueError('raw path changed')
        residual = (path[:full.CUT]-gps).ravel()
        cases = {}
        for key, op in operators.items():
            innovations, state = op.apply_block(residual, first_epoch=0)
            future = op.conditional_marginals(state=state)
            mean = future['mean']
            sigma = np.sqrt(np.diagonal(future['covariance'], axis1=1, axis2=2))
            cases[key] = dict(center_m=(later-mean).tolist(), sigma_m=sigma.tolist(),
                standardized_training_rms=float(np.sqrt(np.mean(innovations**2))),
                correction_rms_m=float(np.sqrt(np.mean(np.sum(mean**2, axis=1)))),
                later_receiver_positions_used=False)
        records.append(dict(row, ranges=cases))
    return dict(anchor=anchor.tolist(), rows=records, later_receiver_positions_used=False,
                operator_configurations={key:op.configuration for key,op in operators.items()})


def _score(saved, later, original):
    result = full._scores(saved, later)
    by_id = {row['identity']: row for row in original['rows']}
    source = {row['identity']: row for row in saved['rows']}
    for row in result['rows']:
        baseline = by_id[row['identity']]
        if baseline['passed'] != row['passed']:
            raise ValueError('numerical disposition changed')
        if row['passed']:
            if any(v['raw'] != baseline['horizons'][key]['raw'] for key,v in row['horizons'].items()):
                raise ValueError('later support or uncorrected forecast changed')
            row['earlier_only'] = {key:{name:v[name] for name in ('standardized_training_rms', 'correction_rms_m')}
                                   for key,v in source[row['identity']]['ranges'].items()}
    if ([r['primary'] for r in result['matched_settings']]
            != [r['primary'] for r in original['matched_settings']]):
        raise ValueError('earlier-only primary selection changed')
    return result


def run(root, action):
    with closing(ArchiveStore(root)) as store:
        matrix = ClosedStudy(root, 'data/'+full.ID, store=store)
        parent = ClosedStudy(root, full.PARENT, store=store)
        files = (full.FREEZE, full.RANGES, full.SEAL, full.RESULT, audit.RESULT)
        blobs = {path:(root/path).read_bytes() for path in files}
        prior = json.loads(blobs[full.FREEZE])
        seal = json.loads(blobs[full.SEAL])
        previous = json.loads(gzip.decompress(blobs[full.RANGES]))
        if (prior['parents'] != [matrix.completion, parent.completion]
                or seal != dict(freeze_sha256=digest(blobs[full.FREEZE]),
                    ranges_sha256=digest(blobs[full.RANGES]), later_receiver_reads=0)
                or previous['freeze_sha256'] != seal['freeze_sha256']
                or previous['later_receiver_positions_used'] is not False
                or len(previous['rows']) != 24 or sum(r['passed'] for r in previous['rows']) != 20
                or matrix.manifest['scope'] != full.SCOPE
                or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'
                or any(matrix.rows[r['identity']]['passed'] is not r['passed'] for r in previous['rows'])):
            raise ValueError('same sealed earlier-only development ranges required')
        own = Path(__file__).relative_to(root).as_posix()
        seeds = (own, PLAN, 'analysis/tests/test_esa_no_snap_ablation.py')
        config = encoded(dict(inputs={p:digest(b) for p,b in blobs.items()},
            parents=prior['parents'], sources={p:digest((root/p).read_bytes()) for p in source_closure(root, seeds)},
            snap_psd=0., unmodified_threshold=full.THRESHOLD, operators=2, maximum_case_scores=48,
            fit_starts=0, threads=1, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed ablation freeze')
        training = json.loads(gzip.decompress(matrix.input('training', raw=True)))
        times = matrix.input('forecast_times')
        binding = matrix.input('saved-input-binding')
        origin = binding['time_origin_s']
        if (len(times) != full.CUT+full.LATER or len(training) != full.CUT
                or [row['time_s']-origin for row in training] != times[:full.CUT]):
            raise ValueError('same earlier observations and forecast times required')
        if action == 'condition':
            saved = _generate(matrix, training, times, previous)
            raw = gzip.compress(encoded(dict(saved, freeze_sha256=digest(config))), mtime=0)
            _write_equal(root/RANGES, raw)
            result = dict(freeze_sha256=digest(config), ranges_sha256=digest(raw), later_receiver_reads=0)
            _write_equal(root/SEAL, encoded(result))
            return result
        payload = (root/RANGES).read_bytes()
        seal = json.loads((root/SEAL).read_bytes())
        if seal != dict(freeze_sha256=digest(config), ranges_sha256=digest(payload), later_receiver_reads=0):
            raise ValueError('earlier-only ablation ranges must be sealed before scoring')
        saved = json.loads(gzip.decompress(payload))
        original = json.loads(blobs[full.RESULT])
        full_rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        later = full_rows[full.CUT:full.CUT+full.LATER]
        later_sha = digest(encoded(later))
        if (full_rows[:full.CUT] != training or original['later_receiver_sha256'] != later_sha
                or [r['time_s']-origin for r in later] != times[full.CUT:]):
            raise ValueError('unchanged later reference required')
        result = _score(saved, later, original)
    content = encoded(dict(result, **seal, later_receiver_sha256=later_sha, snap_psd=0.))
    _write_equal(root/RESULT, content)
    return dict(tasks=len(result['rows']), scored=sum(row['passed'] for row in result['rows']), sha256=digest(content))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'condition', 'score'))
    print(run(Path.cwd(), parser.parse_args().action))
