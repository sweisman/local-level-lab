# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preflight exact saved generated inputs for a finite timing diagnostic."""
import hashlib
import json
from pathlib import Path

import numpy as np

from lll.studies.closed import ClosedStudy
from lll.studies.artifacts import digest, encoded


PARENT = 'data/bounded-nonlinear-aircraft-v2-20261111'
CASE = 'sphere_rotating-1-increment-z_gyro_boundary'
MANIFEST_SHA256 = '94929800fdf681887ae62f66dcd699ad26892378672a0465709a45b7da5dd8d9'
SUMMARY_SHA256 = '1e2ba970c5ebc7e61799f8fe2823f744964fb8fdb5fd16b12ce5a623d23870f5'
IDENTITY = 'bounded-noisy-timing-probe-20261111'
SCOPE = ('eight-point generated noisy timing objective probe on one saved failed case; '
         'no solver starts, forecast, original or protected data, or scientific decision')
LIMITS = dict(native_calls=239816, packet_visits=1506051012, bound_calls=0, bound_steps=0)


def timing_grid(times, ends, center_offset_s, full_time_step_s, time_limit_s):
    """Bracket the same near-boundary query geometry with at most eight points."""
    times = np.asarray(times, float)
    ends = np.asarray(ends, float)
    values = (center_offset_s, full_time_step_s, time_limit_s)
    if (times.ndim != 1 or ends.ndim != 1 or not len(times) or not len(ends)
            or not np.all(np.isfinite(times)) or not np.all(np.isfinite(ends))
            or np.any(np.diff(times) <= 0) or np.any(np.diff(ends) <= 0)
            or ends[0] <= 0 or not all(np.isfinite(v) for v in values)
            or time_limit_s <= 0 or abs(center_offset_s) > time_limit_s):
        raise ValueError('finite ordered supported timing geometry required')
    center = times + center_offset_s
    if np.min(center) < 0 or np.max(center) > ends[-1]:
        raise ValueError('center queries outside packet support')
    original = np.searchsorted(ends, center, side='left')
    next_gap = ends[original] - center
    starts = np.r_[0., ends[:-1]]
    previous_gap = center - starts[original]
    gap = np.where(next_gap <= previous_gap, next_gap, -previous_gap)
    if np.max(np.abs(gap - np.median(gap))) > 1e-7 or np.max(np.abs(gap)) > 1e-7:
        raise ValueError('same near-boundary receiver geometry required')
    boundary_delta = float(np.median(gap))
    shifts = [('saved_point', 0.),
              ('boundary_before_1ns', boundary_delta - 1e-9),
              ('boundary_after_1ns', boundary_delta + 1e-9),
              ('minus_100ns', -1e-7), ('plus_100ns', 1e-7),
              ('minus_10us', -1e-5), ('plus_10us', 1e-5),
              ('full_timing_component', float(full_time_step_s))]
    if len({shift for _, shift in shifts}) != len(shifts):
        raise ValueError('timing grid contains duplicate objective points')
    result = []
    for label, shift in shifts:
        if abs(center_offset_s + shift) > time_limit_s or np.min(center + shift) < 0 or np.max(center + shift) > ends[-1]:
            raise ValueError('timing grid outside declared native support')
        indices = np.searchsorted(ends, center + shift, side='left')
        result.append(dict(label=label, physical_offset_s=shift,
                           normalized_time_step=shift / time_limit_s,
                           changed_packet_epochs=int(np.count_nonzero(indices != original))))
    return result


def preflight(root):
    """Return verified arrays and saved point; perform no native evaluation."""
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.bounded_nonlinear_study import recipe

    root = Path(root).resolve()
    study = ClosedStudy(root, PARENT)
    try:
        if (study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['summary_sha256'] != SUMMARY_SHA256 or
                study.completion['state'] != 'complete' or
                study.input('recipe') != recipe() or CASE not in study.tasks):
            raise ValueError('exact closed generated study required')
        changed = [name for name, expected in study.manifest['sources'].items()
                   if not (root / name).is_file() or
                   hashlib.sha256((root / name).read_bytes()).hexdigest() != expected]
        if changed:
            raise ValueError('frozen generated source mismatch')
        task = study.tasks[CASE]
        payload = task['payload']
        law = payload['law']
        r = recipe()
        spec = {key: value for key, value in payload.items()
                if key not in ('law', 'sensor_case')}
        configured = dict(r, noise=r['noise_by_law'][law],
                          sensor_case=payload['sensor_case'])
        material = construct(spec, configured, reserve=lambda **work: None)
        binding = study.artifact(CASE, 'input-binding.json')
        hashes = {key: digest(np.asarray(material[key], dtype='<f8').tobytes())
                  for key in ('theta', 'dv', 'dt', 'times')}
        if (hashes != binding['full_array_sha256'] or
                digest(encoded(material['training_rows'])) != binding['training_receiver_sha256'] or
                len(material['training_rows']) != binding['training_epochs'] or
                len(material['dt']) != binding['native_packets'] or
                material['training_rows'] != study.artifact(CASE, 'training-receiver.json')):
            raise ValueError('reconstructed measured arrays or receiver rows differ')
        fit = study.artifact(CASE, 'fit.json')
        point = np.asarray(fit['normalized_parameters'], float)
        if (fit['active_parameters'].index('time_offset') != 25 or
                len(point) != len(fit['active_parameters']) or
                fit['message'] != 'no positive predicted decrease'):
            raise ValueError('saved failed timing point required')
        return dict(material=material, fit=fit, payload=payload,
                    recipe=configured, input_hashes=hashes,
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=SUMMARY_SHA256,
                    native_calls=0)
    finally:
        study.close()


def tasks():
    return [dict(identity='saved-failed-case', input_key='protocol',
                 native_kind='tangent',
                 payload=dict(parent=PARENT, case=CASE, evaluations=8),
                 limits=LIMITS)]


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/bounded_noisy_timing_probe.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/ilvis0_stopping_audit.py',
        'analysis/tests/test_bounded_noisy_timing_probe.py',
        'docs/bounded-calibration-prediction/TIMING_PROBE_PLAN.md'])


def request_qualification(root):
    from lll.airquantumgrav_inventory import environment
    from lll.studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=qualification_sources(root),
                   environment=environment(),
                   output='docs/bounded-calibration-prediction/qualification/timing-probe-request.json',
                   report='docs/bounded-calibration-prediction/qualification/timing-probe-tests.xml')


def prepare(root, *, qualification):
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    root = Path(root).resolve()
    if thread_environment(workers=1, threads=1) != environment()['numerical_environment']:
        raise ValueError('one-thread guarded environment required')
    request_bytes, report_bytes = checked(
        root, qualification, sources=qualification_sources(root),
        environment=environment(), required_tests=[
            'test_timing_grid_brackets_packet_boundary_without_duplicating_points',
            'test_timing_grid_rejects_unmatched_or_out_of_support_queries',
            'test_failed_case_preflight_matches_sealed_inputs_without_native_work'],
        minimum_tests=3)
    base = root / 'data' / (IDENTITY + '-inputs')
    if base.exists() or (root / 'data' / IDENTITY).exists():
        raise ValueError('fresh finite timing diagnostic required')
    base.mkdir(parents=True)
    protocol = dict(version='bounded-noisy-timing-probe-v1', parent=PARENT,
                    case=CASE, manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=SUMMARY_SHA256, evaluations=8,
                    limits=LIMITS, workers=1, threads=1,
                    maximum_wall_s=1200., scientific_decision='abstain')
    records = dict(protocol=encoded(protocol), qualification_request=request_bytes,
                   qualification_report=report_bytes,
                   qualification_environment=encoded(environment()))
    inputs = {}
    for name, raw in records.items():
        path = base / (name + '.json' if name != 'qualification_report' else name + '.xml')
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/bounded_noisy_timing_probe.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(), workers=1, threads=1,
                      maximum_wall_s=protocol['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + IDENTITY, allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task, context):
    """Run eight separately charged objective evaluations; preserve failure."""
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_noisy_inputs import error_law
    from lll.airquantumgrav_error_policy import build as receiver_weight
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.ilvis0_stopping_audit import affine_slices
    from lll.structured_noisy_study import _kernels
    from lll.ilvis0_control_shards import _check_continue

    expected = tasks()[0]
    if ({key: value for key, value in task.items() if key not in ('index', 'shard')}
            != expected or context.manifest['scope'] != SCOPE or
            json.loads(context.input_path('qualification_environment').read_bytes())
            != environment()):
        raise ValueError('unchanged source-bound one-case probe required')
    protocol = json.loads(context.input_path('protocol').read_bytes())
    if (protocol['parent'] != PARENT or protocol['case'] != CASE or
            protocol['manifest_sha256'] != MANIFEST_SHA256 or
            protocol['summary_sha256'] != SUMMARY_SHA256 or
            protocol['limits'] != LIMITS or protocol['evaluations'] != 8 or
            protocol['scientific_decision'] != 'abstain'):
        raise ValueError('frozen finite timing protocol differs')
    checked = preflight(context.root.parent.parent)
    material = checked['material']
    fit = checked['fit']
    recipe = checked['recipe']
    payload = checked['payload']
    point = np.asarray(fit['normalized_parameters'], float)
    saved = fit['local_linearization']
    affine = affine_slices(point, saved['residual'], saved['jacobian'], 25, -1., 1.)[0]
    time_limit = recipe['limits']['time_offset']
    grid = timing_grid(material['times'][:79], np.cumsum(material['dt']),
                       point[25] * time_limit,
                       affine['normalized_time_step'] * time_limit,
                       time_limit)
    if len(grid) != 8 or grid[1]['changed_packet_epochs'] != 79 or grid[2]['changed_packet_epochs'] != 0:
        raise ValueError('declared matched packet-boundary grid required')
    noise_kernel, kernel_factory = _kernels(context, environment())
    rows = material['training_rows']
    anchor = float(rows[0]['height_m'])
    factory = ErrorTrainingFactory(
        noise=error_law(recipe['noise']), noise_kernel=noise_kernel,
        gravity_anchor_height_m=anchor, maximum_packets=len(material['dt']),
        maximum_queries=len(material['times']), maximum_bytes=64 * 1024**2,
        anchor_policy=recipe['covariance_anchor_policy'])
    kernel, tangent, compilation = kernel_factory(anchor)
    context.save('compilation.json', compilation)
    times = np.asarray(material['times'], float)
    dt = np.asarray(material['dt'], float)
    count = int(np.searchsorted(np.cumsum(dt), times[78] + time_limit, side='left')) + 1
    if count != 23553:
        raise ValueError('saved training packet prefix differs')
    gps = np.asarray([[np.radians(row['latitude_deg']), np.radians(row['longitude_deg']), row['height_m']]
                      for row in rows], float)
    weight = receiver_weight(rows, policy_id=payload['policy_id'])
    budget = None
    try:
        with context.prepay_native(native_calls=LIMITS['native_calls'],
                                   packet_visits=LIMITS['packet_visits']) as budget:
            def reserve(**work):
                _check_continue(context.root, context.manifest)
                budget.reserve(**work)
            problem = factory(times[:79], gps,
                              theta=np.asarray(material['theta'][:count], float),
                              dv=np.asarray(material['dv'][:count], float),
                              dt=dt[:count], model=payload['model'],
                              limits=recipe['limits'], profile=payload['profile'],
                              clock=recipe['clock'], maximum_interval_s=1.5 / recipe['rate_hz'],
                              kernel=kernel, tangent_kernel=tangent,
                              training_weight=weight, time_origin_s=0., reserve=reserve)
            outcomes = []
            center_residual = center_jacobian = None
            for item in grid:
                current = point.copy()
                current[25] += item['normalized_time_step']
                reserve(native_calls=1, packet_visits=len(problem.dt) * len(problem.gps_times))
                residual, jacobian, _ = problem.residual_tangent(current, payload['model'])
                if center_residual is None:
                    center_residual, center_jacobian = residual, jacobian
                    if (not np.allclose(residual, saved['residual'], rtol=1e-11, atol=1e-8) or
                            not np.allclose(jacobian, saved['jacobian'], rtol=1e-9, atol=1e-8)):
                        raise ValueError('saved failed-point residual or tangent differs')
                cost = float(residual @ residual)
                predicted = center_residual + center_jacobian[:, 25] * item['normalized_time_step']
                outcomes.append(dict(item, actual_cost=cost,
                                     predicted_local_cost=float(predicted @ predicted),
                                     actual_change_from_center=cost - float(center_residual @ center_residual),
                                     predicted_change_from_center=float(predicted @ predicted) -
                                     float(center_residual @ center_residual)))
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())
    result = dict(passed=True, case=CASE, evaluations=len(outcomes),
                  parent_manifest_sha256=MANIFEST_SHA256,
                  input_hashes=checked['input_hashes'], outcomes=outcomes,
                  native_charges=budget.snapshot()['attempted'],
                  model_decision='abstain', original_fit_changed=False,
                  observed_starts=0, protected_reads=0)
    context.save('timing-probe.json', result)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    if args.action == 'request':
        result = request_qualification(args.root)
    else:
        result = prepare(args.root,
                         qualification='docs/bounded-calibration-prediction/qualification/timing-probe-request.json')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
