# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the sealed same-field shape score across opened ESA receiver paths."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path
import sys

from .esa_final_orbit_replay import ID as ORBIT_ID, _baseline_rows, _task as orbit_task
from .esa_final_orbit_score import (
    ORIGINAL_COMPARISON, ORIGINAL_SHA, ORBIT_MANIFEST_SHA, PPP_SHA, _coordinates, _load,
)
from .esa_relative_clock_replay import ID as CLOCK_ID, _task as clock_task
from .esa_relative_clock_score import MANIFEST_SHA as CLOCK_MANIFEST_SHA
from .esa_rinex_code_comparison import FOLDER, PARENT, PARENT_SHA, PPP, coordinates
from .esa_shared_profile_score import WITNESS_MANIFEST
from .shape_remainder_witness import EARLIER, ID as WITNESS, LATER, MODELS
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


PLAN = FOLDER + 'ESA_SHAPE_RECEIVER_REPLAY_PLAN.md'
FREEZE = FOLDER + 'esa-shape-receiver-replay-freeze.json'
RESULT = FOLDER + 'esa-shape-receiver-replay-result.json'
PATHS = ('original', 'gps_l1', 'gps_dual', 'final_orbit', 'broadcast_without_g17',
         'clock_change_without_g17', 'glonass_l1', 'glonass_dual')


def score_paths(whiten, times, cut, direction, nominal, sphere, disc, observations):
    """Check a fixed shape direction and score each path with the same smooth allowance."""
    import numpy as np

    times = np.asarray(times, float)
    sphere, disc = (np.asarray(value, float) for value in (sphere, disc))
    later = times[cut:]
    offset = 3 * cut
    phase = 2 * (later - later[0]) / (later[-1] - later[0]) - 1
    smooth = np.zeros((3 * len(times), 9))
    smooth[offset:] = np.kron(np.polynomial.legendre.legvander(phase, 2), np.eye(3))
    basis, triangular = np.linalg.qr(whiten(smooth)[offset:], mode='reduced')
    if np.linalg.matrix_rank(triangular) != 9:
        raise ValueError('all nine original smooth directions required')
    direction = np.asarray(direction, float)

    def remove_smooth(vector):
        return vector - basis @ (basis.T @ vector)

    def later_whiten(values):
        values = np.asarray(values, float)
        if values.shape != (len(times), 3) or not np.all(np.isfinite(values)):
            raise ValueError('complete earlier and later chart coordinates required')
        return whiten(values.ravel())[offset:]

    separation = remove_smooth(later_whiten(disc - sphere))
    if (direction.shape != separation.shape
            or not np.allclose(separation, nominal * direction, atol=1e-7, rtol=1e-8)):
        raise ValueError('archived signed shape separation did not reproduce')
    reference = np.asarray(observations['original'], float)
    output = {}
    for name, path in observations.items():
        point = np.asarray(path, float)
        sphere_error = remove_smooth(later_whiten(point - sphere))
        disc_error = remove_smooth(later_whiten(point - disc))
        sphere_loss = float(sphere_error @ sphere_error)
        disc_loss = float(disc_error @ disc_error)
        signed = float(direction @ ((sphere_error + disc_error) / 2))
        change = point - reference
        earlier = change.copy()
        earlier[cut:] = 0
        later_only = change - earlier
        early_effect = float(direction @ later_whiten(earlier))
        later_effect = float(direction @ later_whiten(later_only))
        if not math.isclose(sphere_loss - disc_loss, 2 * nominal * signed, abs_tol=1e-5, rel_tol=1e-8):
            raise ValueError('shape-direction and squared-error scores disagree')
        output[name] = dict(signed_midpoint=signed, sphere_squared_error=sphere_loss,
                            disc_squared_error=disc_loss, earlier_receiver_effect=early_effect,
                            later_receiver_effect=later_effect)
    baseline = output['original']['signed_midpoint']
    for row in output.values():
        if not math.isclose(row['signed_midpoint'] - baseline,
                            row['earlier_receiver_effect'] + row['later_receiver_effect'], abs_tol=1e-7):
            raise ValueError('earlier and later receiver effects did not sum to the observed change')
    return output


def _sealed_epochs(root, store, study_id, manifest_sha, name, task, indices):
    from .esa_final_orbit_replay import BLOCK, COUNT

    with closing(ClosedStudy(root, 'data/' + study_id, store=store)) as study:
        if study.completion['manifest_sha256'] != manifest_sha or not study.summary['passed']:
            raise ValueError('the complete opened receiver replay is required')
        rows = [row for start in range(0, COUNT, BLOCK) for row in
                study.artifact(task(start)['identity'], name)]
        if len(rows) != COUNT or not all(row['passed'] for row in rows):
            raise ValueError('unexpected reconstructed epoch coverage')
        return [rows[index] for index in indices], study.completion['summary_sha256']


def _inputs(root):
    from .esa_final_orbit_replay import BASELINE
    from .esa_glonass_comparison import DIRECTORY, METHODS, POSITION_SHA
    from .esa_rinex_window import WEEK

    matching = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']
    indices = matching['matched_code_indices']
    if len(indices) != EARLIER + LATER or indices != sorted(set(indices)):
        raise ValueError('exact prior ordered match indices required')
    gps = _baseline_rows((root / BASELINE).read_bytes())
    glonass = json.loads(gzip.decompress((root / DIRECTORY / 'positions.json.gz').read_bytes()))
    if digest(encoded(glonass['positions'])) != POSITION_SHA:
        raise ValueError('sealed GLONASS positions changed')
    earlier_setting = next(row for row in _load(root, PPP, PPP_SHA)['settings']
                           if row['profile'] and row['law'] == 'increment')
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('exact opened parent flight required')
            original = json.loads(gzip.decompress(parent.input('training', raw=True)))[:EARLIER + LATER]
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST or not witness.summary['passed']:
                raise ValueError('exact sealed direction witness required')
            times = witness.input('forecast_times')
            direction = witness.input('shape-direction')
            snapshot = witness.input('later-operator', raw=True)
            forecasts = []
            for model in MODELS:
                raw = witness.input(model + '-forecast', raw=True)
                record = json.loads(raw)
                if (digest(raw) != earlier_setting['forecast_sha256'][model]
                        or record['times_s'] != times
                        or record['prediction_receiver_positions_used'] is not False):
                    raise ValueError('sealed earlier-only forecasts changed')
                forecasts.append(record['coordinates'])
        orbits, orbit_summary = _sealed_epochs(root, store, ORBIT_ID, ORBIT_MANIFEST_SHA,
            'orbit-epochs.json', orbit_task, indices)
        clocks, clock_summary = _sealed_epochs(root, store, CLOCK_ID, CLOCK_MANIFEST_SHA,
            'clock-epochs.json', clock_task, indices)
    origin = original[0]['time_s'] - times[0]
    if any(abs(origin + time - row['time_s']) > 1e-8 for time, row in zip(times, original, strict=True)):
        raise ValueError('archived direction and receiver timeline differ')
    for index, receiver, orbit, clock in zip(indices, original, orbits, clocks, strict=True):
        original_time = gps[index]['gps_week_seconds']
        if (gps[index]['gps_week'] != WEEK or glonass['positions'][index]['gps_week'] != WEEK
                or abs(original_time - receiver['time_s']) > .001
                or abs(glonass['positions'][index]['gps_week_seconds'] - receiver['time_s']) > .001
                or orbit['gps_week_seconds'] != original_time or clock['gps_week_seconds'] != original_time):
            raise ValueError('one-to-one saved receiver time alignment required')
    methods = ('l1_broadcast', 'dual_frequency')
    if any(gps[i][method]['status'] != 'converged' or
           glonass['positions'][i][glonass_method]['status'] != 'converged'
           for i in indices for method, glonass_method in zip(methods, METHODS, strict=True)):
        raise ValueError('complete saved GPS and GLONASS positions required')
    paths = dict(zip(PATHS, (
        coordinates(original),
        *(_coordinates([gps[i][method] for i in indices]) for method in methods),
        _coordinates(orbits),
        [row['restricted_position'] for row in clocks],
        [row['clock_adjusted_position'] for row in clocks],
        *(_coordinates([glonass['positions'][i][method] for i in indices]) for method in METHODS),
    ), strict=True))
    bindings = dict(witness_manifest_sha256=WITNESS_MANIFEST, receiver_manifest_sha256=PARENT_SHA,
                    orbit_summary_sha256=orbit_summary, clock_summary_sha256=clock_summary)
    return times, direction, snapshot, forecasts, paths, bindings


def run(root, action):
    from .esa_changing_drift_transfer import _chart
    from .ilvis0_control_shards import runtime_environment
    from .innovations_snapshot import restore
    from .studies.dependencies import source_closure

    times, shape, snapshot, forecasts, paths, bindings = _inputs(root)
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(),
        PLAN, 'analysis/tests/test_esa_shape_receiver_replay.py'])
    freeze = encoded(dict(
        source_sha256={name: digest((root / name).read_bytes()) for name in sources},
        receiver_paths_sha256={name: digest(encoded(path)) for name, path in paths.items()},
        forecast_sha256=digest(encoded(forecasts)), direction_sha256=digest(encoded(shape)),
        operator_sha256=digest(snapshot), time_sha256=digest(encoded(times)),
        environment=runtime_environment(), earlier=EARLIER, later=LATER, maximum_receiver_paths=8,
        operator_count=1, fit_starts=0, forecast_propagations=0, threads=1, **bindings,
    ))
    target = root / FREEZE
    if action == 'freeze':
        if target.exists() and target.read_bytes() != freeze:
            raise ValueError('existing matched shape replay freeze differs')
        if not target.exists():
            atomic(target, freeze)
        print(digest(freeze))
        return
    if target.read_bytes() != freeze:
        raise ValueError('exact frozen shape-score paths required')
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    import numpy as np
    anchor = np.asarray(paths['original'][0])
    projected = score_paths(operator.whiten, times, EARLIER, shape['direction'], shape['nominal'],
        *(_chart(row, anchor) for row in forecasts),
        {name: _chart(path, anchor) for name, path in paths.items()})
    raw = encoded(dict(freeze_sha256=digest(freeze), later=LATER, nominal_separation=shape['nominal'],
        scores=projected, protected_reads=0, new_fits=0, new_forecast_propagations=0,
        calibrated=False, scientific_decision='abstain'))
    result = root / RESULT
    if result.exists() and result.read_bytes() != raw:
        raise ValueError('saved shape score differs')
    if not result.exists():
        atomic(result, raw)
    print(digest(raw))


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('freeze', 'calculate'):
        raise SystemExit('usage: python -m lll.esa_shape_receiver_replay {freeze,calculate}')
    run(Path.cwd(), sys.argv[1])
