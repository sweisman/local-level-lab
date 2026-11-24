# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound ideal receiver phase corrections using a sealed gyro excerpt."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from . import esa_carrier_lever_sensitivity as lever
from .esa_phase_windup_budget import INPUTS, endpoint_weights
from .studies.artifacts import digest, encoded


ID = 'esa-gyro-phase-tilt-v1'
SCOPE = 'ESA 187 gyro-constrained ideal receiver phase score sensitivity'
PLAN = lever.FOLDER+'ESA_GYRO_PHASE_TILT_PLAN.md'
RESULT = lever.FOLDER+'esa-gyro-phase-tilt-result.json'
REPORTS = {
    **{key: INPUTS[key] for key in ('score', 'products', 'nkar')},
    'upright': ('esa-phase-windup-budget.json',
                '103daedec51b2bfd5c82a94bd531572b5ec93195322a437ad69952d43f363244'),
    'phase': ('esa-nkar-phase-windup-result.json',
              '4f3ef1bce94b412553e895010b5ef6bdf46eba5a5505cbf9cd2a2036203e0b57'),
    'gyro_receipt': (Path(lever.RESULT).name,
                     '0a449aac45cffef41ac3fcbc9b52ab5ebc79b8ebb5ce170fcd2688e88c9bff84'),
}
CASES = (0, 5, 10)
ENDPOINTS = 241
TASK = dict(identity='ideal-receiver-phase', input_key='gyro', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2,
                        bound_steps=lever.MAX_PACKETS+2496+ENDPOINTS*len(CASES)))


def phase_limit(tilt, minimum_elevation):
    """Integrate the largest ideal phase slope on a swing from local up."""
    import numpy as np

    tilt, minimum_elevation = (np.asarray(value, dtype=float) for value in (tilt, minimum_elevation))
    if (not np.isfinite(tilt).all() or not np.isfinite(minimum_elevation).all()
            or np.any(tilt < 0) or np.any(abs(minimum_elevation) > np.pi/2)):
        raise ValueError('finite tilt and ray elevation required')
    start = np.pi/4-minimum_elevation/2
    end = start+tilt/2
    if np.any(end >= np.pi/2):
        raise ValueError('the tilt can put the normal opposite a satellite ray')
    return 2*np.log(np.cos(start)/np.cos(end))


def lower_endpoint_elevations(pair_minima_deg):
    import numpy as np

    values = np.asarray(pair_minima_deg, dtype=float)
    if (values.ndim != 1 or not values.size or not np.isfinite(values).all()
            or np.any(values <= 0) or np.any(values > 90)):
        raise ValueError('positive pair-minimum elevations required')
    return np.radians(np.r_[values[0], np.minimum(values[:-1], values[1:]), values[-1]])


def prepare(root):
    from .esa_rinex_code_comparison import coordinates
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite ideal phase check')
    inputs = {'plan': PLAN}
    for key, (filename, sha256) in REPORTS.items():
        path = lever.FOLDER+filename
        if digest((root/path).read_bytes()) != sha256:
            raise ValueError('published report differs: '+path)
        inputs[key] = path
    reference = json.loads((root/inputs['gyro_receipt']).read_bytes())
    with closing(ClosedStudy(root, 'data/'+lever.ID)) as study:
        if (study.completion != reference['completion']
                or study.envelope(lever.TASK['identity'])['charged'] != lever.TASK['limits']):
            raise ValueError('the verified gyro offset experiment is required')
        gyro = study.input('gyro', raw=True)
        start = study.input('fixed')['start_gps_s']
    with closing(ClosedStudy(root, lever.SCORE_PARENT)) as study:
        completion = lever.verify_parent(study)
        anchor, path = map(study.input, ('anchor', 'path'))
        if completion != reference['parent_completions'][lever.SCORE_PARENT] or anchor['time_s'] != start:
            raise ValueError('unchanged shared position anchor required')
        local = dict(gyro_start_gps_s=start, anchor=coordinates([anchor])[0],
                     path_times_gps_s=[row['seconds'] for row in path],
                     positions=[row['position'] for row in path],
                     score_parent=completion)
    for key, value in {'gyro': gyro, 'local': encoded(local)}.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_gyro_phase_tilt.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    from .esa_carrier_phase_support import C, F1, F2
    from .gnss_position import local_rotation

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen ideal phase check is required')
    context.charge(bound_calls=1, bound_steps=lever.MAX_PACKETS)

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    score, products, ground, phase, upright, local = map(
        read, ('score', 'products', 'nkar', 'phase', 'upright', 'local'))
    times = np.array([score['endpoint_gps_s'][0], *local['path_times_gps_s']])
    start = local['gyro_start_gps_s']
    if (len(times) != ENDPOINTS or np.any(np.diff(times) != .5)
            or times[-1] != score['endpoint_gps_s'][1]
            or local['path_times_gps_s'] != [row['seconds'] for row in products['rows']]
            or len(phase['per_pair_minima_deg']) != ENDPOINTS-1
            or not score['score_gap'] == ground['score_gap'] == phase['score_gap'] == upright['score_gap']):
        raise ValueError('the complete unchanged carrier support is required')
    with np.load(context.input_path('gyro'), allow_pickle=False) as archive:
        edges, increments = archive['edges'], archive['increments']
    if len(increments) > lever.MAX_PACKETS:
        raise ValueError('gyro interval ceiling exceeded')
    turns = Rotation.from_matrix(lever.relative_rotations(edges, increments, start, times)).magnitude()
    zeniths = np.array([local_rotation(*p[:2])[2] for p in (local['anchor'], *local['positions'])])
    zenith_change = np.arctan2(np.linalg.norm(np.cross(zeniths[0], zeniths), axis=1), zeniths@zeniths[0])
    motion = turns + zenith_change + lever.ANGULAR_ALLOWANCE_RADS*(times-start)
    minimum_elevation = lower_endpoint_elevations(phase['per_pair_minima_deg'])

    context.charge(bound_calls=1, bound_steps=2496+ENDPOINTS*len(CASES))
    support = [row['common_satellites'] for row in products['rows']]
    full, covered = score['bound']['dual_weights'], ground['projected_weights']
    if len(full) != 2496 or len(covered) != len(full):
        raise ValueError('the complete half-second range weights are required')
    coeff = {
        key: np.array([math.fsum(map(abs, row.values())) for row in endpoint_weights(support, weights)])
        for key, weights in (('full', full), ('covered', covered))
    }
    for key, values in coeff.items():
        if not math.isclose(float(values.sum()), upright['results'][key]['endpoint_absolute_weight_sum'],
                            rel_tol=1e-13, abs_tol=1e-14):
            raise ValueError('upright score weights did not reproduce')
    scale = C/(2*math.pi*(F1+F2))
    cases = []
    for initial_tilt_deg in CASES:
        tilt = motion+math.radians(initial_tilt_deg)
        cap = phase_limit(tilt, minimum_elevation)
        above = tilt <= minimum_elevation
        parts = {}
        for key, values in coeff.items():
            parts[key] = dict(score_bound=float(scale*(values@cap)),
                              guaranteed_upper_plane_weight_fraction=float(values[above].sum()/values.sum()))
        cases.append(dict(initial_tilt_allowance_deg=initial_tilt_deg, peak_tilt_bound_deg=float(np.degrees(tilt.max())),
                          guaranteed_upper_plane_endpoints=int(above.sum()), parts=parts))
    result = dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                  score_gap=score['score_gap'], peak_gyro_turn_deg=float(np.degrees(turns.max())),
                  carrier_endpoints=len(times), gyro_packets=len(increments), cases=cases,
                  original_reads=0, new_fits=0, protected_reads=0)
    context.save('endpoint-bounds.json', dict(gps_s=times.tolist(), tilt_motion_bound_rad=motion.tolist(),
                 minimum_elevation_rad=minimum_elevation.tolist(), weights={k: v.tolist() for k, v in coeff.items()}))
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the completed charged phase result is required')
        result = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                      inputs=study.manifest['inputs'], endpoint_bounds=study.artifact(
                          TASK['identity'], 'endpoint-bounds.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('inputs', 'endpoint_bounds')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
