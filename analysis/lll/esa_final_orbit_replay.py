# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolate IGS orbit substitution on the already-opened ESA 187 code window."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path
import sys

from .esa_precise_gps_support import (
    MAXIMUM_LOOKBACK_S, ORBIT_STEP_S, SAVED_POSITIONS_SHA256, read_orbit_positions,
)
from .esa_rinex_code import observation_epochs, read_navigation
from .esa_rinex_code_study import _BASE, _INPUTS, _NAV, _OBS
from .esa_rinex_window import FOLDER, WEEK, read_header
from .studies.artifacts import atomic, digest, encoded


ID = 'esa-final-orbit-replay-v2'
SCOPE = 'ESA 187 orbit-only dual-frequency code replay'
PLAN = FOLDER + 'ESA_FINAL_ORBIT_REPLAY_PLAN.md'
ACCOUNTING = FOLDER + 'ESA_FINAL_ORBIT_REPLAY_ACCOUNTING.md'
RESULT = FOLDER + 'esa-final-orbit-replay-result.json'
BASELINE = _BASE + 'code-position/positions.json.gz'
ORBIT = _BASE + 'products/IGS0OPSFIN_20231870000_01D_15M_ORB.SP3.gz'
ORBIT_SHA = '62f32dab4aa5dfda81c97bd1b88b5339902787faebfb80148ec5d3e1543ad8d2'
COUNT = 1041
BLOCK = 120
MAXIMUM_ORBIT_EVALUATIONS = 4


def interpolate_orbit(knots, seconds, *, step_s=ORBIT_STEP_S):
    base = math.floor(seconds / step_s)
    times = [i * step_s for i in range(base - 3, base + 5)]
    if not all(t in knots for t in times):
        raise ValueError('missing interior SP3 interpolation knot')
    if seconds in times:
        return knots[seconds]
    coefficients = [
        (-1)**i * math.comb(7, i) / ((seconds - t) / step_s)
        for i, t in enumerate(times)
    ]
    denominator = math.fsum(coefficients)
    return tuple(
        math.fsum(w * knots[t][axis] for w, t in zip(coefficients, times, strict=True))
        / denominator
        for axis in range(3)
    )


def _task(start):
    end = min(start + BLOCK, COUNT)
    return dict(identity=f'epochs-{start:04d}-{end:04d}', input_key='observations',
                payload=dict(start=start, end=end),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=end - start,
                            bound_steps=(end - start) * (1 + MAXIMUM_ORBIT_EVALUATIONS)))


def _baseline_rows(raw):
    saved = json.loads(gzip.decompress(raw))
    rows = saved['positions']
    if (saved['positions_sha256'] != SAVED_POSITIONS_SHA256
            or digest(encoded(rows)) != SAVED_POSITIONS_SHA256 or len(rows) != COUNT):
        raise ValueError('original position rows changed')
    return rows


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('orbit replay already frozen')
    inputs = dict(observations=_OBS, navigation=_NAV, baseline=BASELINE, orbit=ORBIT)
    if (digest(gzip.decompress((root / _OBS).read_bytes())) != _INPUTS[_OBS]
            or digest((root / _NAV).read_bytes()) != _INPUTS[_NAV]
            or digest((root / ORBIT).read_bytes()) != ORBIT_SHA):
        raise ValueError('original GPS observations and satellite products required')
    _baseline_rows((root / BASELINE).read_bytes())
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, adapter=adapter,
        inputs=inputs, tasks=[_task(s) for s in range(0, COUNT, BLOCK)],
        sources=source_closure(root, [adapter, PLAN, ACCOUNTING,
                                      'analysis/tests/test_esa_final_orbit_replay.py']),
        workers=1, threads=1, maximum_wall_s=180., scope=SCOPE)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(dict(id=ID, limits=manifest['limits'])).decode(), end='')


def _range_step(state, selected, seconds, ionosphere):
    import numpy as np
    from .gnss_position import range_system

    design, error, used, _ = range_system(state, selected, seconds, 'dual_frequency', ionosphere)
    if (len(used) < 5 or [row['sv_id'] for row in used] != [row['sv_id'] for row in selected]
            or np.linalg.matrix_rank(design) != 4):
        raise ValueError('original elevation-masked GPS set did not remain fully usable')
    rms = float(np.sqrt(np.mean(error**2)))
    return np.linalg.lstsq(design, error, rcond=None)[0], rms


def _replay(row, saved, navigation, ionosphere, orbits):
    import numpy as np
    from . import gnss_position as gps

    seconds = row['gps_week_seconds']
    if (row['gps_week'] != WEEK or saved['gps_week'] != WEEK
            or seconds != saved['gps_week_seconds']):
        raise ValueError('matched GPS epoch required')
    saved = saved['dual_frequency']
    if saved['status'] != 'converged':
        raise ValueError('converged baseline required')
    available, _ = gps.observations(row, navigation, 'dual_frequency')
    by_id = {item['sv_id']: item for item in available}
    selected = [by_id[prn] for prn in saved['used_satellites']]
    state = np.array([*saved['ecef_m'], saved['receiver_clock_m']], dtype=float)
    step, rms = _range_step(state, selected, seconds, ionosphere)
    if np.linalg.norm(step) > 1e-4 or abs(rms - saved['range_rms_m']) > 1e-7:
        raise ValueError('sealed broadcast position objective did not reproduce')
    replacement = []
    orbit_distances = []
    for item in selected:
        tx = item['transmit_gps_seconds']
        if not seconds - MAXIMUM_LOOKBACK_S <= tx <= seconds:
            raise ValueError('transmit epoch outside checked product envelope')
        precise = interpolate_orbit(orbits[item['sv_id']], tx)
        orbit_distances.append(math.dist(item['satellite_ecef_m'], precise))
        replacement.append(item | dict(satellite_ecef_m=precise))

    origin = state[:3].copy()
    for evaluations in range(1, MAXIMUM_ORBIT_EVALUATIONS + 1):
        step, precise_rms = _range_step(state, replacement, seconds, ionosphere)
        if np.linalg.norm(step) <= 1e-5:
            latitude, longitude, height = gps.geodetic(state[:3])
            rotation = gps.local_rotation(saved['latitude_rad'], saved['longitude_rad'])
            return dict(gps_week_seconds=seconds, passed=True,
                latitude_rad=latitude, longitude_rad=longitude, ellipsoid_height_m=height,
                final_minus_broadcast_neu_m=(rotation @ (state[:3] - origin)).tolist(),
                broadcast_rms_m=rms, final_orbit_rms_m=precise_rms, orbit_range_evaluations=evaluations,
                satellite_displacements_m=orbit_distances, satellites=saved['used_satellites'])
        state += step
    raise ValueError('final orbit objective did not settle within the frozen limit')


def evaluate(declared, context):
    start, end = (declared['payload'][key] for key in ('start', 'end'))
    if context.manifest['scope'] != SCOPE or end != _task(start)['payload']['end']:
        raise ValueError('unexpected orbit replay task')
    obs = gzip.decompress(context.input_path('observations').read_bytes())
    header, metadata = read_header(obs)
    rows = list(observation_epochs(obs[len(header):].decode('ascii'), metadata['observation_types']))
    if len(rows) != COUNT:
        raise ValueError('expected the complete opened receiver window')
    navigation, ionosphere = read_navigation(gzip.decompress(
        context.input_path('navigation').read_bytes()).decode('ascii'))
    orbits = read_orbit_positions(gzip.decompress(context.input_path('orbit').read_bytes()).decode('ascii'))
    baseline = _baseline_rows(context.input_path('baseline').read_bytes())
    results = []
    for index in range(start, end):
        context.charge(bound_calls=1, bound_steps=1 + MAXIMUM_ORBIT_EVALUATIONS)
        try:
            result = _replay(rows[index], baseline[index], navigation, ionosphere, orbits)
        except (ValueError, KeyError, ArithmeticError) as exc:
            result = dict(gps_week_seconds=rows[index]['gps_week_seconds'], passed=False, reason=str(exc))
        results.append(result)
    context.save_bytes('orbit-epochs.json', encoded(results))
    passing = sum(row['passed'] for row in results)
    return dict(passed=passing == end - start, epochs=end - start, passing=passing,
                scientific_decision='abstain')


def report(root):
    from .airquantumgrav_geographic_report import error_metrics
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/' + ID)) as sealed:
        epochs = [row for start in range(0, COUNT, BLOCK) for row in
                  json.loads(sealed.artifact(_task(start)['identity'], 'orbit-epochs.json', raw=True))]
        manifest_sha = sealed.completion['manifest_sha256']
        summary_sha = sealed.completion['summary_sha256']
    matches = [row for row in epochs if row['passed']]
    if len(epochs) != COUNT or len({row['gps_week_seconds'] for row in epochs}) != COUNT:
        raise ValueError('all fixed distinct epochs required')
    metrics = error_metrics([row['final_minus_broadcast_neu_m'] for row in matches]) if matches else None
    receipt = encoded(dict(study=ID, manifest_sha256=manifest_sha, summary_sha256=summary_sha,
        epochs=len(epochs), passing=len(matches), differences=metrics,
        maximum_satellite_displacement_m=max((d for row in matches for d in
                                             row['satellite_displacements_m']), default=None),
        new_inertial_fits=0, new_forecast_propagations=0, protected_reads=0,
        signed_epoch_results=epochs))
    target = root / RESULT
    if target.exists() and target.read_bytes() != receipt:
        raise ValueError('saved orbit comparison report differs')
    if not target.exists():
        atomic(target, receipt)
    print(encoded(dict(epochs=len(epochs), passing=len(matches), differences=metrics,
                       result_sha256=digest(receipt))).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_final_orbit_replay {prepare,report}')
