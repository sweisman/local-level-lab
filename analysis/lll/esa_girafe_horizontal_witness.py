# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check GIRAFE horizontal force sensitivity to the saved north-only position error."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction
from itertools import islice
import json
from pathlib import Path

from . import esa_motion_axis_support as axis
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-girafe-horizontal-witness-v1'
SCOPE = 'Measured horizontal GIRAFE force and the original/north-error ESA 187 paths'
PLAN = axis.FOLDER+'ESA_GIRAFE_HORIZONTAL_WITNESS_PLAN.md'
REQUEST = axis.FOLDER+'esa-girafe-horizontal-witness-qualification.json'
XML = axis.FOLDER+'esa-girafe-horizontal-witness-tests.xml'
RESULT = axis.FOLDER+'esa-girafe-horizontal-witness-result.json'
ARTIFACT = 'girafe-horizontal-witness.json'
AXIS_SHA = '046621104bcf9a3d000bd338655832e06ccaa5a7c99c90374022dbf53018bc40'
ORBIT_SHA = '40b586d4e848468e41482df75353efc8d93256cf0593e8eca8a3635d7cd7261d'
CENTERS = (12, 36, 60, 84, 108)
HALF_SPANS = (5, 12)
OFFSETS = (0., -.1, .1)
MODELS = ('sphere_still', 'flat_still')
SUPPORT_STEPS = 16*48+len(OFFSETS)*1250
TASK = dict(identity='girafe-horizontal-witness', input_key='girafe', payload=dict(centers=len(CENTERS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=11,
                        bound_steps=axis.MAX_ROWS+10*SUPPORT_STEPS))


def acceleration_kernel(knots):
    """Map force to the same support as the cubic estimate of acceleration."""
    import numpy as np

    from .esa_force_position_derivative import position_weights

    weights = position_weights(knots)
    kernel = weights[1]@np.maximum(knots[:, None]-knots[None, :], 0.)
    if kernel.min() < -1e-12 or abs(np.trapezoid(kernel, knots)-1.) > 1e-12:
        raise ValueError('the position acceleration kernel must be positive and have unit mass')
    return weights, np.maximum(kernel, 0.)


def sample_weights(edges, knots, kernel):
    """Exactly integrate the piecewise-linear kernel over observation time cells."""
    import numpy as np

    if edges[0] > knots[0] or edges[-1] < knots[-1]:
        raise ValueError('measured time cells must bracket the acceleration support')
    durations = np.diff(knots)
    slopes = np.diff(kernel)/durations
    primitive = np.r_[0., np.cumsum(durations*(kernel[:-1]+kernel[1:])*.5)]
    x = np.clip(edges, knots[0], knots[-1])
    i = np.clip(np.searchsorted(knots, x, side='right')-1, 0, len(slopes)-1)
    dt = x-knots[i]
    mass = np.diff(primitive[i]+dt*(kernel[i]+.5*slopes[i]*dt))
    if mass.min() < -1e-12 or abs(mass.sum()-1.) > 1e-12:
        raise ValueError('the quartz time cells must retain the acceleration kernel mass')
    return np.maximum(mass, 0.)


def vector_summaries(axes, weights):
    import numpy as np

    return dict(average_vector_norm=float(np.linalg.norm(weights@axes)),
                average_norm=float(weights@np.linalg.norm(axes, axis=1)))


def supported_force(knots, kernel, position, weights, model):
    import numpy as np

    from .esa_doppler_force import _quadrature_rule
    from .ilvis0_receiver_force import evaluate_batch
    from .models import WGS84_A

    nodes, quadrature = _quadrature_rule()
    half = np.diff(knots)[:, None]*.5
    relative = (((knots[:-1]+knots[1:])*.5)[:, None]+half*nodes).ravel()
    mass = (half*quadrature).ravel()*np.interp(relative, knots, kernel)
    center = position[len(knots)//2]
    p = weights@(position-center)
    t = relative[:, None]
    q = center+t*(p[0]+t*(.5*p[1]+t*p[2]/3.))
    v = p[0]+t*(p[1]+t*p[2])
    a = p[1]+2.*t*p[2]
    force = evaluate_batch(q, v, a, model=model, background_rate_rads=0., gravity_mps2=np.full(len(t), 9.81),
                           disc_radius_m=WGS84_A)['specific_force_ned_mps2']
    return force, mass


def supported_horizontal_force(knots, kernel, position, weights, model):
    force, mass = supported_force(knots, kernel, position, weights, model)
    return force[:, :2], mass


def prediction(knots, kernel, position, weights, model):
    return vector_summaries(*supported_horizontal_force(knots, kernel, position, weights, model))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_girafe_horizontal_witness.py', 'test_esa_girafe.py', 'test_esa_force_position_derivative.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                   *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_position_kernel_recovers_constant_acceleration_and_preserves_mass',
        'test_horizontal_force_summaries_leave_constant_heading_free'), minimum_tests=7)
    return sources, environment


def prepare(root):
    from . import esa_nuuk_orbit_clock as orbit
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite horizontal force study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        flight, ranges = _parent(root, orbit.RESULT, ORBIT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        support, witness = _parent(root, axis.RESULT, AXIS_SHA, axis.ID, axis.TASK, axis.ARTIFACT, stack)
        original = axis.prior
        _, path = _parent(root, original.RESULT, axis.PARENT_SHA, original.ID, original.TASK, original.ARTIFACT, stack)
        if (flight.envelope(orbit.TASK['identity'])['charged'] != orbit.TASK['limits']
                or support.envelope(axis.TASK['identity'])['charged'] != axis.TASK['limits']
                or len(ranges['rows']) != 240 or len(path['knots']) != 125
                or witness['coverage']['rows'] != 1200 or witness['coverage']['half_interrogation_s'] != [.02, .02]):
            raise ValueError('the complete sealed carrier and GIRAFE support records are required')
        values = {key: flight.input(key, raw=True) for key in ('path', 'anchor', 'metric')}
    girafe = axis.girafe.BASE/axis.SOURCE
    axis.girafe.verify_file(root/girafe, axis.SOURCE)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, girafe=girafe.as_posix(),
                  axes=axis.RESULT, witness=original.RESULT)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=RECOVER['maximum_wall_s']), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_girafe_force_overlap import sample_edges
    from .esa_rinex_code_comparison import coordinates
    from .shared_motion_carrier import displacement_at

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen GIRAFE comparison task is required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    context.charge(bound_calls=1, bound_steps=axis.MAX_ROWS)
    samples = []
    with context.input_path('girafe').open('rb') as stream:
        for sample in islice(axis.girafe.read_rows(stream), axis.MAX_ROWS):
            time = axis.girafe.utc_seconds_to_gps(sample.utc_seconds)
            if time > axis.STOP+.3:
                break
            if time >= axis.START-.3:
                if sample.half_interrogation_s != .02:
                    raise ValueError('the declared continuous 20 ms half interrogation is required')
                samples.append((time, sample.xyz_mps2[:2]))
        else:
            raise ValueError('the allowed GIRAFE scan did not reach the support endpoint')
    obs_times, force = zip(*samples, strict=True)
    if len(force) > 1250:
        raise ValueError('the fixed GIRAFE time-cell allowance was exceeded')
    force, edges = np.asarray(force), sample_edges(obs_times)
    path, anchor, metric, recorded = (read(k) for k in ('path', 'anchor', 'metric', 'witness'))
    if [r['seconds'] for r in path] != [axis.START+.5*i for i in range(1, 241)]:
        raise ValueError('the original half-second path is required')
    times = np.asarray([anchor['time_s'], *(r['seconds'] for r in path)])
    xyz = np.asarray([coordinates([anchor])[0], *(r['position'] for r in path)])
    knots = [dict(elapsed_s=float(Fraction(row['elapsed_s_exact'])), position_m=row['position_m'],
                  velocity_mps=row['speed_mps']) for row in recorded['knots']]
    acceleration = np.asarray([[float(Fraction(v)) for v in row['acceleration_exact_mps2']] for row in recorded['knots']])
    north_fraction = read('axes')['energy_fraction']['north']
    shifted = xyz.copy()
    shifted[:, 0] += [displacement_at(knots, t-anchor['time_s'], acceleration)[0]/(metric[0]*north_fraction)
                      for t in times]
    supports = []
    for half in HALF_SPANS:
        for seconds in CENTERS:
            context.charge(bound_calls=1, bound_steps=SUPPORT_STEPS)
            center = axis.START+seconds
            sl = slice(2*(seconds-half), 2*(seconds+half)+1)
            local = times[sl]-center
            derivative, kernel = acceleration_kernel(local)
            models = {model: dict(original=prediction(local, kernel, xyz[sl], derivative, model),
                                  north_only=prediction(local, kernel, shifted[sl], derivative, model)) for model in MODELS}
            observations = {str(offset): vector_summaries(force, sample_weights(edges+offset-center, local, kernel))
                            for offset in OFFSETS}
            supports.append(dict(center_gps_s=center, width_seconds=2*half, models=models, observed=observations))

    from .esa_girafe_force_overlap import _moments

    summaries = []
    for half in HALF_SPANS:
        rows = [r for r in supports if r['width_seconds'] == 2*half]
        for model in MODELS:
            for statistic in ('average_vector_norm', 'average_norm'):
                nominal, displaced = [np.asarray([r['models'][model][label][statistic] for r in rows])
                                      for label in ('original', 'north_only')]
                observed = np.asarray([r['observed']['0.0'][statistic] for r in rows])
                clock = np.asarray([[r['observed'][str(o)][statistic] for r in rows] for o in OFFSETS])
                summaries.append(dict(width_seconds=2*half, model=model, statistic=statistic,
                                      north_effect=_moments(displaced-nominal), original_error=_moments(observed-nominal),
                                      north_only_error=_moments(observed-displaced),
                                      max_clock_rms_mps2=max(_moments(y-observed)['rms_mps2'] for y in clock)))
    result = dict(supports=supports, summaries=summaries, raw_samples=len(force), source_sha256=axis.girafe.TARGETS[axis.SOURCE][1],
                  new_fits=0, protected_reads=0, scientific_decision='abstain', passed=True)
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('complete fixed horizontal force evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion, axis_sha256=AXIS_SHA,
                                               orbit_sha256=ORBIT_SHA, motion_sha256=axis.PARENT_SHA)))
    return {k: v for k, v in result.items() if k != 'supports'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'prepare':
        result = prepare(root)
    elif args.action == 'recover':
        from .esa_shared_motion_carrier import recover_signature

        result = recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
