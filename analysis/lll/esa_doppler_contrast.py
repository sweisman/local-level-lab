# SPDX-License-Identifier: AGPL-3.0-or-later
"""Project two saved ESA Doppler paths onto the certified shape contrast."""
import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import gzip
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
from .esa_doppler_comparison import REPORT as DOPPLER, VELOCITY_FREEZE, VELOCITY_SHA
from .esa_doppler_study import DIRECTORY
from .esa_integrated_contrast_support import ARTIFACT as PRIOR_ARTIFACT
from .esa_integrated_contrast_support import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_linked_training_support import LATER, TRAIN
from .esa_rinex_code_comparison import FOLDER, PARENT, PARENT_SHA
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-doppler-contrast-v1'
SCOPE = 'Fixed ESA shape contrast on the matched in-flight Doppler displacement patterns'
PLAN = FOLDER+'ESA_DOPPLER_CONTRAST_PLAN.md'
REQUEST = FOLDER+'esa-doppler-contrast-qualification.json'
XML = FOLDER+'esa-doppler-contrast-tests.xml'
RESULT = FOLDER+'esa-doppler-contrast-result.json'
PRIOR_SHA = '4e3eae50b6e904ba4c521b7c25669ea59f36c715973a5edba855f05ea6b2ed93'
DOPPLER_SHA = '5cb194d520aeca6f72576e6c49d1a4522c36cefcf93d882c4e1019d3be9e6670'
ARTIFACT = 'doppler-contrast.json'
REPORTS = TRAIN+LATER
SAMPLES = 1041
TESTS = ('test_integrate_at_exact_queries_and_anchor', 'test_project_in_original_coordinate_order',
         'test_check_receivers_requires_exact_alignment_and_complete_velocities')
TASK = dict(identity='matched-doppler-patterns', input_key='positions', payload=dict(reports=REPORTS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=4, bound_steps=3*REPORTS+2*SAMPLES+1))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_doppler_contrast.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS,
            minimum_tests=len(TESTS))
    return sources, environment


def check_receivers(positions, times, velocity):
    if (len(positions) != REPORTS or len(times) != REPORTS or len(velocity) != SAMPLES
            or {row['gps_week'] for row in (*positions, *velocity)} != {2269}):
        raise ValueError('the exact 520 position and 1,041 Doppler report selections are required')
    query = [row['time_s'] for row in positions]
    lattice = [row['gps_week_seconds'] for row in velocity]
    origin = query[0]-times[0]
    if (any(abs(origin+t-q) > 1e-8 for t, q in zip(times, query, strict=True))
            or any(b-a != .5 for a, b in zip(lattice, lattice[1:]))
            or not lattice[0] <= query[0] < query[-1] <= lattice[-1]):
        raise ValueError('the source and score query grids differ')
    if any(row[system]['status'] != 'converged' for row in velocity for system in ('G', 'R')):
        raise ValueError('both Doppler series must be complete')
    return query, lattice


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite Doppler contrast allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    if digest((root/DOPPLER).read_bytes()) != DOPPLER_SHA:
        raise ValueError('matched Doppler evidence differs')
    with ExitStack() as stack:
        support, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        receiver = stack.enter_context(closing(ClosedStudy(root, PARENT)))
        if (support.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']
                or receiver.completion['manifest_sha256'] != PARENT_SHA):
            raise ValueError('the original score and opened receiver input are required')
        positions = json.loads(gzip.decompress(receiver.input('training', raw=True)))
        if len(positions) != 800:
            raise ValueError('the original development export is required')
        positions = [{key: r[key] for key in ('time_s', 'gps_week', 'latitude_deg', 'longitude_deg', 'height_m')}
                     for r in positions[:REPORTS]]
        values = {key: support.input(key, raw=True) for key in ('shape', 'times', 'later-operator', 'direction')}
        values['gap'] = encoded(row['score_gap_lower_exact'])
    raw = (root/DIRECTORY/'velocity.json.gz').read_bytes()
    velocity = json.loads(gzip.decompress(raw))
    if (velocity['freeze_sha256'] != VELOCITY_FREEZE or velocity['velocity_sha256'] != VELOCITY_SHA
            or digest(encoded(velocity['velocity'])) != VELOCITY_SHA):
        raise ValueError('sealed Doppler velocity differs')
    check_receivers(positions, json.loads(values['times']), velocity['velocity'])
    values.update(positions=encoded(positions), velocity=raw, recovery=recovery, recovery_tests=tests,
                  recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, doppler=DOPPLER, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def integrate_at_queries(origin, lattice, velocity, query):
    import numpy as np

    from .esa_doppler_comparison import integrate_half_second

    lattice, query = np.asarray(lattice, float), np.asarray(query, float)
    rates = np.asarray(velocity, float)
    if (len(lattice) < 2 or len(lattice) != len(rates) or not np.all(np.diff(lattice) == .5)
            or not len(query) or not np.all(np.diff(query) > 0)
            or not lattice[0] <= query[0] <= query[-1] <= lattice[-1]):
        raise ValueError('ordered bounded queries and a 2 Hz velocity grid are required')
    displacement = integrate_half_second(np.zeros(3), rates)
    idx = np.clip(np.searchsorted(lattice, query, side='right')-1, 0, len(lattice)-2)
    offset = (query-lattice[idx])[:, None]
    requested = displacement[idx]+offset*rates[idx]+offset**2*(rates[idx+1]-rates[idx])
    return np.asarray(origin, float)+(requested-requested[0])


def project(path, reference, metric, times, taps, gap, *, cut):
    import math

    from .contrast_replay import summarize_error
    from .ilvis0_saved_prediction_audit import endpoint

    comparison = [(p[0], p[1]+math.tau*round((r[1]-p[1])/math.tau), p[2])
                  for p, r in zip(path, reference, strict=True)]
    result = summarize_error(comparison, reference, [(0, 0, 0)]*len(times), metric, times, taps, cut=cut)
    low, high = result.pop('score_bounds')
    return dict(score_exact=list(map(str, (low, high))),
                score_fraction_of_gap=[endpoint(low/gap, False), endpoint(high/gap, True)],
                **{key: [endpoint(value, True) for value in row] for key, row in result.items()})


def evaluate(task, context):
    from .conditioned_position_margin import reverse_intervals
    from .gnss_position import ecef, geodetic
    from .innovations_snapshot import restore
    from .esa_rinex_code_comparison import coordinates

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen matched Doppler comparison is required')

    def read(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    positions, times, shape, direction = [json.loads(read(key)) for key in ('positions', 'times', 'shape', 'direction')]
    records = json.loads(gzip.decompress(read('velocity')))['velocity']
    query, lattice = check_receivers(positions, times, records)
    operator = restore(read('later-operator'), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    late = list(map(F, direction['exact_later_taps']))
    gap = F(json.loads(read('gap')))
    if (operator.epoch_count != REPORTS or operator.observation_dimension != 3
            or len(late) != 3*LATER or gap <= 0):
        raise ValueError('the original positive-gap three-axis score is required')
    taps = [(-hi, -lo) for lo, hi in reverse_intervals(operator, late, cut=TRAIN)]+[(v, v) for v in late]
    reference = coordinates(positions)
    metric = shape['metric']
    origin = ecef(*reference[0])
    paths, results = {}, {}
    for system in ('G', 'R'):
        context.charge(bound_calls=1, bound_steps=SAMPLES+REPORTS)
        xyz = integrate_at_queries(origin, lattice, [row[system]['velocity_ecef_mps'] for row in records], query)
        paths[system] = [reference[0], *map(geodetic, xyz[1:])]
        results[system+'_minus_ppp'] = project(paths[system], reference, metric, times, taps, gap, cut=TRAIN)
    context.charge(bound_calls=1, bound_steps=REPORTS)
    results['G_minus_R'] = project(paths['G'], paths['R'], metric, times, taps, gap, cut=TRAIN)
    verdict = dict(results=results, reference_epochs=REPORTS, gps_velocity_epochs=SAMPLES,
                   new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
    context.save(ARTIFACT, verdict)
    return verdict


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery policy required')
            if TASK['identity'] in study.rows and study.envelope(TASK['identity'])['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, verdict = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['status'] != 'complete' or envelope['charged'] != TASK['limits'] or verdict != envelope['result']:
            raise ValueError('exact declared Doppler contrast evidence required')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=study.completion)))
    return {name: row['score_fraction_of_gap'] for name, row in verdict['results'].items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
