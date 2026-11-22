# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test a constant timing correction on saved ESA forecasts and omitted pairs."""

import argparse
from contextlib import ExitStack, closing
from dataclasses import dataclass
import json
import math
from pathlib import Path

from .esa_component_scale_transfer import LAWS, read_case
from .esa_motion_innovation_scale import BASE, PARENT, PARENT_MANIFEST, PARENT_REPORT, PARENT_REPORT_SHA
from .esa_repeat_turn_inputs import LATENCY as MAX_SHIFT_S
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-forecast-time-shift-v1'
SCOPE = 'Constant first-order clock shift on four saved ESA 187 turn/steady forecast pairs'
PLAN = BASE+'ESA_FORECAST_TIME_SHIFT_PLAN.md'
RESULT = BASE+'esa-forecast-time-shift-result.json'
REQUEST = BASE+'esa-forecast-time-shift-qualification.json'
REPORT = BASE+'esa-forecast-time-shift-tests.xml'
TEST = 'analysis/tests/test_esa_forecast_time_shift.py'
TESTS = ('test_velocity_on_an_irregular_clock_wraps_longitude',
         'test_time_shift_matches_dense_covariance_and_direction',
         'test_shift_is_one_weighted_donor_value_and_clips_to_physical_screen')
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=15, bound_steps=0)


def path_velocity(times, coordinates, metric):
    import numpy as np

    time, path, scale = (np.asarray(a, dtype=float) for a in (times, coordinates, metric))
    if (time.ndim != 1 or len(time) < 4 or path.shape != (len(time), 3) or scale.shape != (3,)
            or not all(np.isfinite(a).all() for a in (time, path, scale))
            or np.any(scale <= 0.) or np.any(np.diff(time) <= 0.)):
        raise ValueError('ordered forecast times and finite local coordinates required')
    points = path.copy()
    points[:, 1] = np.unwrap(path[:, 1])
    return np.gradient((points-points[0])*scale, time-time[0], axis=0, edge_order=2)


@dataclass(frozen=True)
class ShiftProfile:
    white_error: object
    white_velocity: object
    information: float
    alignment: float
    velocity_fraction_after_smooth: float

    def quadratic(self, shift):
        residual = self.white_error-shift*self.white_velocity
        return float(residual @ residual)


def profile(times, error, velocity, covariance):
    import numpy as np
    from scipy.linalg import solve_triangular

    time, error, velocity, covariance = (np.asarray(a, float) for a in (times, error, velocity, covariance))
    if (time.ndim != 1 or len(time) < 4 or error.shape != velocity.shape or error.shape != (len(time), 3)
            or covariance.shape != (error.size, error.size) or np.any(np.diff(time) <= 0.)
            or not all(np.isfinite(a).all() for a in (time, error, velocity, covariance))):
        raise ValueError('complete aligned path, shift direction and working covariance required')
    phase = (time-time[0])/(time[-1]-time[0])
    smooth = np.kron(np.column_stack((np.ones_like(phase), phase, phase**2)), np.eye(3))
    lower = np.linalg.cholesky(covariance)
    white = solve_triangular(lower, np.column_stack((error.ravel(), velocity.ravel(), smooth)), lower=True)
    residual, direction, basis = white[:, 0], white[:, 1], white[:, 2:]
    coefficients, _, rank, _ = np.linalg.lstsq(basis, direction, rcond=None)
    information = float(direction @ direction)
    if rank != smooth.shape[1] or information <= 0.:
        raise ValueError('nonzero shift direction and complete smooth basis required')
    conditional = direction-basis@coefficients
    return ShiftProfile(residual, direction, information, float(direction @ residual),
                        float(conditional @ conditional)/information)


def select_shift(profiles):
    if not profiles:
        raise ValueError('one or more donor forecasts required')
    shift = math.fsum(p.alignment for p in profiles)/math.fsum(p.information for p in profiles)
    return max(-MAX_SHIFT_S, min(MAX_SHIFT_S, shift))


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law), limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, TEST, PLAN))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('keep the existing timing study and its allowance')
    sources = qualification(root, check=True)
    prior = (root/PARENT_REPORT).read_bytes()
    if digest(prior) != PARENT_REPORT_SHA:
        raise ValueError('exact original error localization report required')
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('exact localized forecast evidence required')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        if len(design['pairs']) != 4 or len(windows) != 8 or len(set(windows)) != 8:
            raise ValueError('eight distinct forecasts in their four original pairs required')
        keys = ['design', *(f'observed-{i}' for i in windows)]
        keys.extend(f'forecast-{i}-{law}' for i in windows for law in LAWS)
        materials = {key: parent.input(key, raw=True) for key in keys}
    materials.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PARENT_REPORT, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in materials.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, sources=sources,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=120.,
        tasks=[task_for(pair, law) for pair in design['pairs'] for law in LAWS])
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    from scipy.stats import chi2

    from .ilvis0_solver_position import physical_metric

    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or law not in LAWS or pair not in design['pairs']
            or declared != task_for(pair, law)):
        raise ValueError('exact matched forecast fold required')

    def charge():
        context.charge(bound_calls=1, bound_steps=0)

    def read(index):
        charge()
        previous = design['scores'][f'{index}-{law}']
        case = read_case(context, index, law, previous)
        forecast = json.loads(context.input_path(f'forecast-{index}-{law}').read_bytes())
        times = forecast['times_s']
        metric = physical_metric([forecast['anchor_geodetic']])[0]
        velocity = path_velocity(times, forecast['mean_geodetic'], metric)
        saved = profile(times, case.error.reshape(-1, 3), velocity, case.component_covariance.sum(axis=0))
        return saved, previous['both']

    donor_ids = [i for group in design['pairs'] for i in group if i not in pair]
    if len(donor_ids) != 6 or len(set((*donor_ids, *pair))) != 8:
        raise ValueError('six distinct donors and two held-out targets required')
    donors = [read(i)[0] for i in donor_ids]
    charge()
    delay = select_shift(donors)
    selection = dict(shift_s=delay, donors=donor_ids, held_out=pair, law=law)
    context.save('donor-shift.json', selection)
    held = []
    for index in pair:
        saved, prior = read(index)
        lower, upper = chi2.ppf([.05/16, 1.-.05/16], len(saved.white_error))
        scores = {}
        for mode, shift in (('original', 0.), ('donor', delay), ('retrospective', select_shift([saved]))):
            charge()
            value = saved.quadratic(shift)
            scores[mode] = dict(shift_s=shift, quadratic=value, within_reference=bool(lower <= value <= upper),
                negative_log_score=prior['negative_log_score']+.5*(value-prior['quadratic']))
        if not math.isclose(scores['original']['quadratic'], prior['quadratic'], rel_tol=1e-8, abs_tol=1e-8):
            raise ValueError('unchanged covariance score differs from archived evidence')
        held.append(dict(index=index, scores=scores, velocity_fraction_after_smooth=saved.velocity_fraction_after_smooth,
                         retrospective_unbounded_shift_s=saved.alignment/saved.information))
    result = dict(selection=selection, heldout=held, passed=True, new_trajectory_fits=0, protected_reads=0,
                  scientific_decision='abstain')
    context.save('shift-scores.json', result)
    return result


def report(root):
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    prefix = 'data/'+ID
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        studies = [original]
        if len(original.rows) != len(original.tasks) or any(original.envelope(identity)['status'] == 'interrupted'
                                                             for identity in original.rows):
            continuation = root/(prefix+'-recovery')
            if resume_campaign(root, continuation, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified continuation closure required')
            studies.extend(stack.enter_context(closing(ClosedStudy(
                root, path.relative_to(root).as_posix(), store=original.store))) for path in _stage_paths(continuation))
        rows = {}
        for study in studies:
            for identity in study.rows:
                envelope = study.envelope(identity)
                if envelope['status'] == 'interrupted':
                    continue
                if identity in rows or identity not in original.tasks or envelope['status'] != 'complete':
                    raise ValueError('one terminal outcome expected per frozen fold')
                result = envelope['result']
                if result['passed'] and (envelope['charged'] != LIMITS or result != study.artifact(identity, 'shift-scores.json')):
                    raise ValueError('sealed fold differs from its charges or scores')
                rows[identity] = result
        if len(rows) != 8 or original.manifest['scope'] != SCOPE:
            raise ValueError('all original timing folds must reach a terminal state')
        closures = {study.prefix: study.completion for study in studies}
    summaries = {}
    for law in LAWS:
        held = [row for result in rows.values() if result['passed'] and result['selection']['law'] == law
                for row in result['heldout']]
        if len({row['index'] for row in held}) != len(held):
            raise ValueError('each omitted window must be represented only once')
        summaries[law] = dict(scored=len(held), by_mode={mode: dict(
            within_reference=sum(row['scores'][mode]['within_reference'] for row in held),
            negative_log_score=math.fsum(row['scores'][mode]['negative_log_score'] for row in held))
            for mode in ('original', 'donor', 'retrospective')})
    development_gate = all(row['scored'] == 8 and row['by_mode']['donor']['within_reference'] == 8
        and row['by_mode']['donor']['negative_log_score'] < row['by_mode']['original']['negative_log_score']
        for row in summaries.values())
    result = dict(rows=rows, summaries=summaries, closures=closures, development_gate=development_gate,
                  new_trajectory_fits=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return dict(summaries=summaries, development_gate=development_gate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
