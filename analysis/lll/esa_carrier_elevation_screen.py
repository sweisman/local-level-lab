# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check which ESA 187 carrier directions survive an above-antenna-plane screen."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

from . import esa_carrier_lever_sensitivity as lever
from .esa_gyro_phase_tilt import CASES, REPORTS
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-elevation-screen-v1'
SCOPE = 'ESA 187 carrier geometry under above-antenna-plane elevation screens'
PLAN = lever.FOLDER+'ESA_CARRIER_ELEVATION_SCREEN_PLAN.md'
RESULT = lever.FOLDER+'esa-carrier-elevation-screen-result.json'
PHASE = ('esa-gyro-phase-tilt-result.json',
         '6370d516bf1e64d490cd6d4285e8d31b4e19a7be852d29125e5abac28d804cce')
MARGIN_DEG = 1.
PAIRS = 240
SOLVE_STEPS = 4*3*(PAIRS-1)
TASK = dict(identity='screened-carrier-support', input_key='motion', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+PAIRS+1+len(CASES),
                        bound_steps=1+66*PAIRS+(1+len(CASES))*SOLVE_STEPS))


def eligible_rays(first, last, first_tilt_deg, last_tilt_deg):
    """Use the same satellite only if both ends clear the screen."""
    import numpy as np

    return ((np.asarray(first) >= first_tilt_deg+MARGIN_DEG) &
            (np.asarray(last) >= last_tilt_deg+MARGIN_DEG))


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite satellite screen')
    inputs = {'plan': PLAN}
    for key, (name, sha256) in {'motion': PHASE, 'baseline': REPORTS['score'],
                               'nkar': REPORTS['nkar'], 'phase': REPORTS['phase']}.items():
        path = lever.FOLDER+name
        if digest((root/path).read_bytes()) != sha256:
            raise ValueError('published report differs: '+path)
        inputs[key] = path
    baseline = json.loads((root/inputs['baseline']).read_bytes())
    with closing(ClosedStudy(root, lever.SCORE_PARENT)) as study:
        if lever.verify_parent(study) != baseline['completion']:
            raise ValueError('the original completed geometry must match the report')
        for key in ('score', 'anchor', 'path', 'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_carrier_elevation_screen.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def reconstruct_geometry(raw, charge):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_carrier_score_bound import range_gradients, score_grid
    from .esa_final_orbit_replay import interpolate_orbit
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates
    from .esa_shared_motion_carrier import START, paired_satellite_states
    from .gnss_position import ecef, local_rotation

    anchor, path, score, metric, continuity, original, baseline, ground, phase, motion = (
        json.loads(raw(key)) for key in
        ('anchor', 'path', 'score', 'metric', 'continuity', 'original', 'baseline', 'nkar', 'phase', 'motion'))
    times = motion['endpoint_bounds']['gps_s']
    tilt = np.degrees(motion['endpoint_bounds']['tilt_motion_bound_rad'])
    if (len(times) != PAIRS+1 or len(tilt) != len(times)
            or [times[0], times[-1]] != baseline['endpoint_gps_s']
            or not np.isfinite(tilt).all() or np.any(tilt < 0)
            or times[1:] != [row['seconds'] for row in path]
            or not baseline['score_gap'] == ground['score_gap'] == phase['score_gap'] == motion['score_gap']):
        raise ValueError('the unchanged GPS support and gyro envelope are required')
    epochs = list(phase_epochs(gzip.decompress(raw('rinex'))))
    navigation, _ = read_navigation(gzip.decompress(raw('navigation')).decode('ascii'))
    orbits = read_orbit_positions(gzip.decompress(raw('orbit')).decode('ascii'))
    previous = coordinates([anchor])[0]
    gradients, elevations, support = [], [], []
    for i, (point, row) in enumerate(zip(path, original['rows'], strict=True)):
        charge(bound_calls=1, bound_steps=66)
        index = START+i
        first, last = epochs[index:index+2]
        if (first['seconds'], last['seconds'], row['seconds']) != (times[i], times[i+1], times[i+1]):
            raise ValueError('the unchanged half-second pairs are required')
        prns = row['common_satellites']
        accepted = continuity['result']['per_pair'][index]['accepted_prns']
        _, states = paired_satellite_states(first, last, accepted, prns, navigation)
        pair, rays = [], []
        for position, endpoint in zip((previous, point['position']), states, strict=True):
            satellites = np.array([interpolate_orbit(orbits[prn], state[2])
                                   for prn, state in zip(prns, endpoint, strict=True)])
            vectors = satellites-ecef(*position)
            up = local_rotation(*position[:2])[2]
            sine = (vectors@up)/np.linalg.norm(vectors, axis=1)
            rays.append(np.degrees(np.arcsin(np.clip(sine, -1., 1.))))
            pair.append(range_gradients(position, satellites, metric))
        if not np.isclose(float(np.min(rays)), phase['per_pair_minima_deg'][i], atol=1e-10, rtol=0):
            raise ValueError('the prior elevation calculation did not reproduce')
        gradients.append(pair)
        elevations.append(rays)
        support.append(prns)
        previous = point['position']
    fixed = [0, *(times.index(t) for t in baseline['ground_anchors_gps_s']), len(times)-1]
    score_times, taps = score_grid(score, anchor)
    return times, tilt, gradients, elevations, support, fixed, score_times, taps, baseline, ground


def evaluate(task, context):
    import numpy as np

    from .carrier_score_bound import carrier_score_bound
    from .carrier_score_cadence import project_cadence

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen satellite geometry screen is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    times, tilt, gradients, elevations, support, fixed, score_times, taps, baseline, ground = (
        reconstruct_geometry(raw, context.charge))
    ground_satellites = {(r['first'], r['last']): r['satellites'] for r in ground['intervals']}

    def compare(selected, kept, initial, *, screened):
        context.charge(bound_calls=1, bound_steps=SOLVE_STEPS)
        bound = carrier_score_bound(times, selected, fixed, score_times, taps, allow_missing=screened)
        projection = project_cadence(kept, bound['dual_weights'], sorted(ground_satellites),
                                     interval_satellites=ground_satellites)
        count = np.array(list(map(len, kept)))
        score_from_motion = baseline['test_acceleration_rms_mps2']*bound['acceleration_rms_to_score']
        allowance = (max(0., baseline['score_gap']-score_from_motion)/bound['range_rms_to_score']
                     if bound['range_rms_to_score'] else None)
        return dict(initial_tilt_allowance_deg=initial, range_values=bound['range_values'],
                    intervals_with_4_rays=int((count >= 4).sum()), missing_intervals=int((count < 2).sum()),
                    median_usable_rays=float(np.median(count)), range_rms_to_score=bound['range_rms_to_score'],
                    acceleration_rms_to_score=bound['acceleration_rms_to_score'],
                    exact_anchor_range_rms_allowance_m=allowance, score_from_motion=score_from_motion,
                    ground_norm_fraction=projection['observable_norm_fraction'],
                    support=kept, dual_weights=bound['dual_weights'])

    rows = [compare(gradients, support, None, screened=False)]
    if (not np.allclose(rows[0]['dual_weights'], baseline['bound']['dual_weights'], atol=2e-12, rtol=1e-8)
            or not np.isclose(rows[0]['ground_norm_fraction'], ground['observable_norm_fraction'], atol=1e-12)):
        raise ValueError('the original carrier score and station coverage did not reproduce')
    for initial in CASES:
        masks = [eligible_rays(first, last, tilt[i]+initial, tilt[i+1]+initial)
                 for i, (first, last) in enumerate(elevations)]
        masks = [mask if mask.sum() >= 2 else np.zeros_like(mask) for mask in masks]
        selected = [(a[mask], b[mask]) for (a, b), mask in zip(gradients, masks, strict=True)]
        kept = [np.array(prns)[mask].tolist() for prns, mask in zip(support, masks, strict=True)]
        rows.append(compare(selected, kept, initial, screened=True))
    context.save('screened-support.json', rows)
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                original_score_gap=baseline['score_gap'], illustrative_acceleration_mps2=baseline['test_acceleration_rms_mps2'],
                elevation_margin_deg=MARGIN_DEG, original_reads=0, protected_reads=0, new_fits=0,
                cases=[{key: value for key, value in row.items() if key not in ('support', 'dual_weights')} for row in rows])


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the original completed geometry screen is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'], screened_support=study.artifact(TASK['identity'], 'screened-support.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('inputs', 'screened_support')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
