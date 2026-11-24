# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional bound on a common trajectory error using GPS and Galileo."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path

from . import esa_carrier_continuous_bound as continuous
from . import esa_galileo_north_witness as gal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-galileo-joint-bound-v3'
SCOPE = 'ESA 187 fixed GPS score bound with a common Galileo range residual cap'
FOLDER = gal.FOLDER
PLAN = FOLDER+'ESA_GALILEO_JOINT_BOUND_PLAN.md'
PREFLIGHT = FOLDER+'ESA_GALILEO_JOINT_BOUND_PREFLIGHT.md'
RESULT = FOLDER+'esa-galileo-joint-bound-result.json'
GAL_CAP = .008
GPS_KEYS = ('budget', 'prior', 'motion', 'baseline', 'nkar', 'phase', 'score', 'anchor',
            'path', 'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit', 'remainder')
GAL_KEYS = (*gal.galileo.RECEIVERS, 'track', 'support', 'orbit', 'clock')
PREFLIGHT_SHA = (
    'e09f83882342296f190c216174cdb194c8c6669810af8855fe5b109131c695e7',
    '4f483feeb4daa0655883b64ebd116d1115c00b20a98df9eb69e4f9e63e169a16',
)
PARENTS = (
    (continuous.ID, continuous.RESULT, '2081e8d8fc863ddf2e3ccb6cb5ac607e416b3fd8567e6c02623590b330e5b837', GPS_KEYS),
    (gal.ID, gal.RESULT, '36a3412929981c0a84c8ba72518e1d9830c9196b1febff30b85f95ccbc6ff869', GAL_KEYS),
)
EXTRA = gal.END-gal.START
CASES = 1+len(continuous.parent.CASES)
TASK = dict(identity='joint-gps-galileo', input_key='gps_report', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+continuous.parent.PAIRS+EXTRA+CASES,
    bound_steps=1+66*continuous.parent.PAIRS+80*EXTRA+CASES*continuous.CASE_STEPS))


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the existing joint bound')
    inputs = dict(plan=PLAN, preflight=PREFLIGHT)
    for version, sha in enumerate(PREFLIGHT_SHA, 1):
        previous = f'data/esa-galileo-joint-bound-v{version}/manifest.json'
        if digest((root/previous).read_bytes()) != sha:
            raise ValueError('retain both unchanged preflight preparations')
        inputs[f'preflight_manifest_{version}'] = previous
    for prefix, (name, report, sha, keys) in zip(('gps', 'gal'), PARENTS, strict=True):
        raw = (root/report).read_bytes()
        if digest(raw) != sha:
            raise ValueError('original qualified comparison receipt required: '+report)
        with closing(ClosedStudy(root, 'data/'+name)) as parent:
            if parent.completion != json.loads(raw)['completion'] or not parent.summary['passed']:
                raise ValueError('the exact completed comparison is required: '+name)
            for key in keys:
                label = prefix+'_'+key
                path = f'data/{ID}-inputs/{label}'
                _write_equal(root/path, parent.input(key, raw=True))
                inputs[label] = path
        inputs[prefix+'_report'] = report
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, (adapter, PLAN, 'analysis/tests/test_quadratic_support_bound.py')),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _galileo_geometry(context, raw_gps, raw_gal):
    import numpy as np

    from .esa_carrier_score_bound import range_gradients
    from .esa_rinex_code_comparison import coordinates
    from .gnss_position import ecef
    from .shared_motion_carrier import centre

    class GalileoInputs:
        def input_path(self, key):
            return context.input_path('gal_'+key)

    tables = gal.galileo.receiver_epoch_tables(GalileoInputs())
    with io.StringIO(gzip.decompress(raw_gal('orbit')).decode('ascii')) as stream:
        orbit, _ = gal.galileo.read_orbit(iter(stream))
    with io.StringIO(gzip.decompress(raw_gal('clock')).decode('ascii')) as stream:
        clocks = gal.galileo.read_clock(iter(stream))
    support = json.loads(raw_gal('support'))
    reference = {r['seconds']: r['position'] for r in json.loads(raw_gal('track'))['positions']}
    original = json.loads(raw_gps('path'))
    positions = {r['seconds']: r['position'] for r in original}
    anchor = json.loads(raw_gps('anchor'))
    positions[gal.START] = coordinates([anchor])[0]
    metric = json.loads(raw_gps('metric'))
    rows, gradients, residuals = [], [], []
    if [row[0] for row in support] != list(range(gal.START, gal.END)):
        raise ValueError('the frozen Galileo support is required')
    for second, prns in support:
        context.charge(bound_calls=1, bound_steps=80)
        times = (second, second+1)
        mask_reference = [ecef(*reference[t]) for t in times]
        coords = [positions[t] for t in times]
        ecef_positions = [ecef(*position) for position in coords]
        paired, _ = gal.galileo.step_inputs(tables, second, orbit, clocks, mask_reference)
        if list(paired) != prns or not 5 <= len(prns) <= 20:
            raise ValueError('the original Galileo satellite support did not reproduce')
        per_receiver, directions = [], []
        for side in range(len(tables)):
            measured = [values[side] for values, _ in paired.values()]
            endpoints = tuple(zip(*(state[side] for _, state in paired.values()), strict=True))
            modeled = gal._predicted(ecef_positions, endpoints)
            per_receiver.append(centre(np.asarray(measured)-modeled))
            pair = []
            for position, endpoint in zip(coords, endpoints, strict=True):
                satellites = np.asarray([state[0] for state in endpoint])
                radius = np.linalg.norm(satellites, axis=1)
                if np.any(radius < 20e6) or np.any(radius > 40e6):
                    raise ValueError('Galileo positions exceed the conservative range domain')
                pair.append(range_gradients(position, satellites, metric))
            directions.append(pair)
        residual = np.mean(per_receiver, axis=0)
        gradients.append(tuple(np.mean(directions, axis=0)))
        residuals.extend(residual)
        rows.append(dict(gps_s=second, satellites=prns, residual_m=residual.tolist()))
    return gradients, np.asarray(residuals), rows


def prediction_operator(pairs, count):
    """Convert the GPS residual operator to changes in the predicted ranges."""
    from .carrier_score_bound import range_operator

    return -range_operator(pairs, count)


def evaluate(task, context):
    import numpy as np
    from scipy.interpolate import CubicSpline

    from .carrier_motion_witness import _constraint_maps
    from .quadratic_support_bound import affine_upper, solve_support

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen joint carrier task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw_gps(key):
        return context.input_path('gps_'+key).read_bytes()

    def raw_gal(key):
        return context.input_path('gal_'+key).read_bytes()

    prior = json.loads(raw_gps('report'))
    problem, coordinate_cap, offset, gps_geometry, support, screen = (
        continuous.parent.reconstruct_problem(raw_gps, context.charge))
    gal_geometry, observed, rows = _galileo_geometry(context, raw_gps, raw_gal)
    times = problem['times']
    galileo_times = np.arange(gal.START, gal.END+1)-offset
    knots = np.union1d(np.union1d(times, problem['score_times']), galileo_times)
    if len(knots) > continuous.MAX_KNOTS or (knots[0], knots[-1]) != (times[0], times[-1]):
        raise ValueError('the joint times must stay within the original spline allowance')
    spline = CubicSpline(knots, np.eye(len(knots)), bc_type='natural')
    operator = prediction_operator(gal_geometry, len(galileo_times))
    gal_map = operator@np.kron(spline(galileo_times), np.eye(3))
    root_count = np.sqrt(len(observed))
    buffer_m = problem['geometric_buffer_m']
    gps_caps = problem['caps'].copy()
    for key in ('visible_range_rms_m', 'invisible_range_rms_m'):
        gps_caps[key] += buffer_m
    bound_inputs = dict(problem, caps=gps_caps, geometric_buffer_m=0., knots=knots)
    # The origin-centred relaxation proposes a dual direction. The final
    # certificate uses the actual residual offset and intended Galileo cap.
    scale = np.linalg.norm(observed)+(GAL_CAP+buffer_m)*root_count
    b = observed/scale
    radius = (GAL_CAP+buffer_m)*root_count/scale
    output, certificates = [], []
    for (tilt, gps_op, retained), saved in zip(continuous.parent.screened_operators(
            times, gps_geometry, support, screen, context.charge, continuous.CASE_STEPS), prior['cases'], strict=True):
        if tilt != saved['initial_tilt_allowance_deg']:
            raise ValueError('the original GPS satellite sets must be reproduced')
        matrices, objective, anchor_components = _constraint_maps(**bound_inputs, operator=gps_op, support=retained)
        unit_axes = np.zeros((len(anchor_components), len(objective)))
        unit_axes[np.arange(len(anchor_components)), anchor_components] = 1/gps_caps['anchor_axis_m']
        index = len(matrices)
        all_maps = (*matrices, gal_map/scale, *(row[None, :] for row in unit_axes))
        cert = solve_support(all_maps, objective, coordinate_cap,
                             max_iterations=continuous.ITERATIONS, with_certificate=True)
        upper = affine_upper(cert, group=index, offset=b, radius=radius)
        intercept = affine_upper(cert, group=index, offset=b, radius=0.)
        slope = float(cert['norm_terms'][index]*root_count/scale)
        earlier = saved['verified_upper']
        affine_zero = affine_upper(cert, group=index, offset=np.zeros_like(b), radius=1.)
        if not np.isclose(affine_zero, cert['upper'], atol=2e-12, rtol=2e-12):
            raise ValueError('the affine certificate must reproduce the origin-centred bound')
        best = min(earlier, upper)
        cap_at_gap = (1-intercept)/slope-buffer_m if slope > 0 and intercept < 1 else None
        output.append(dict(initial_tilt_allowance_deg=tilt, prior_gps_upper=earlier, joint_upper=upper,
                           verified_upper=best, status='excluded_under_caps' if best < 1 else 'undetermined',
                           optimizer_iterations=cert['iterations'], optimizer_status=cert['optimizer_status'],
                           galileo_cap_at_gap_m=cap_at_gap, upper_intercept=intercept, upper_per_m=slope))
        certificates.append(dict(initial_tilt_allowance_deg=tilt, multipliers=cert['multipliers'].tolist(),
                                 norm_terms=cert['norm_terms'].tolist(), remainder=cert['remainder'],
                                 galileo_dual=cert['dual_groups'][index].tolist()))
    context.save('joint-carrier-certificate.json', dict(galileo_rows=rows, certificates=certificates,
                                                       galileo_normalization=float(scale)))
    return dict(passed=True, scientific_decision='abstain', independent_aircraft_error_cap_established=False,
                gps_caps=problem['caps'], galileo_cap_m=GAL_CAP, geometric_buffer_rms_m=buffer_m,
                galileo_reference_rms_m=float(np.linalg.norm(observed)/root_count), galileo_ranges=len(observed),
                knots=len(knots), cases=output, new_fits=0, original_downloads=0, protected_reads=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the full joint carrier result is required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                       inputs=study.manifest['inputs'])
        evidence = study.artifact(TASK['identity'], 'joint-carrier-certificate.json')
    _write_equal(root/RESULT, encoded(dict(summary, evidence=evidence)))
    return {key: value for key, value in summary.items() if key != 'inputs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
