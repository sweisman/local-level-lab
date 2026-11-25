# SPDX-License-Identifier: AGPL-3.0-or-later
"""Whole-stretch fits for two review checks on the selected NASA stretches.

One task is one preselected stretch. Every declared fit reuses the published
interval, receiver weights, start and solver. Only the candidate, processing
case or gyro-offset allowance named in the task differs. The disc with the
specified field uses the disc metric and the field branch of both kernels.
"""
import argparse
import csv
import gzip
import json
import math
from pathlib import Path

import numpy as np

from .ilvis0_matched_training import MATCHED_MODELS, MatchedTrainingProblem
from .ilvis0_receiver_force import DISC_WITH_FIELD

SELECTION = 'docs/ilvis0-highspeed-segments-20261008/selection.json.gz'
CONTEXTS = 'data/ilvis0-followup-20261007/summary.json'
ANALYTICS = 'docs/ilvis0-current-findings-20261015/stretch-analytics.csv'
FOLDER = 'docs/ilvis0-stretch-checks/'
ADAPTER = 'analysis/lll/ilvis0_stretch_checks.py'
TEST = 'analysis/tests/test_ilvis0_stretch_checks.py'
PACKETS = FOLDER+'packets.json'
REQUEST = FOLDER+'qualification.json'
TEST_REPORT = FOLDER+'tests.xml'
RECOVERY = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
EVALUATIONS = 200
CASES = dict(unsubtracted=False, profiled_removal=True)
OFFSETS_DPH = (1., 3., 10., 30.)
WEIGHTING = 'h1_v3_tau60'
TESTS = ('test_wider_allowances_change_only_the_gyro_offset',
         'test_declared_fit_grids_are_exact',
         'test_one_representative_is_the_longest_stretch_on_each_date',
         'test_every_native_sweep_is_reserved_before_it_runs',
         'test_disc_with_field_uses_the_disc_metric_and_field_kernel',
         'test_replay_reproduces_published_costs')


def _fit(model, case, offset_dph):
    return dict(model=model, case=case, offset_dph=offset_dph)


def disc_field_fits():
    return [_fit(DISC_WITH_FIELD, case, 1.) for case in CASES]


def allowance_fits():
    models = ('sphere_rotating', 'flat_still', DISC_WITH_FIELD)
    return [_fit(model, 'unsubtracted', offset) for offset in (3., 10., 30.) for model in models]


STUDIES = {
    'disc-field': dict(id='ilvis0-disc-field-stretches-v1', plan=FOLDER+'DISC_FIELD_PLAN.md',
        scope='disc with the specified field on all 53 selected NASA stretches; development only',
        fits=disc_field_fits, representatives=False, workers=1, maximum_wall_s=48*3600),
    'gyro-allowance': dict(id='ilvis0-gyro-allowance-stretches-v1', plan=FOLDER+'GYRO_ALLOWANCE_PLAN.md',
        scope='wider gyro-offset allowances on one selected NASA stretch per flight date; development only',
        fits=allowance_fits, representatives=True, workers=2, maximum_wall_s=60*3600)}
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=8,
    minimum_free_bytes=1024**3, smoke_task_count=0)


def label(fit):
    return f"{fit['model']}-{fit['case']}-{fit['offset_dph']:g}dph"


def limits(offset_dph):
    """Change only the constant gyro-offset allowance; every other bound is the published one."""
    from .ilvis0_estimator import AXES
    from .ilvis0_exploratory import LIMITS

    if offset_dph not in OFFSETS_DPH:
        raise ValueError('declared gyro-offset allowance required')
    bounds = dict(LIMITS)
    for axis in AXES:
        bounds['gyro_bias_'+axis] = math.radians(offset_dph)/3600
    return bounds


def write_packets(root):
    """Count the extracted IMU packets of each saved interval once; no model is evaluated."""
    from . import ilvis0_segments as segments
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    with gzip.open(root/SELECTION, 'rt') as stream:
        selection = json.load(stream)
    contexts = {row['task_id']: row for row in json.loads((root/CONTEXTS).read_bytes())['results']}
    counts = {}
    for chosen in selection['selected']:
        source = root/f"data/ilvis0-ready/{chosen['task']}/decoded/{chosen['filename']}.gz"
        values, _, _, _ = segments.extract_segment(source, contexts[chosen['task']], chosen['segment'])
        counts[chosen['segment']['segment_id']] = len(values)
    raw = encoded(counts)
    target = root/PACKETS
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('saved packet counts changed')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic(target, raw)
    return dict(stretches=len(counts), packets=sum(counts.values()))


def stretches(root):
    """The 53 saved intervals with their extracted packet counts; nothing is reselected."""
    root = Path(root)
    with gzip.open(root/SELECTION, 'rt') as stream:
        selection = json.load(stream)
    with (root/ANALYTICS).open(newline='') as stream:
        published = {row['segment_id']: row for row in csv.DictReader(stream)}
    packets = json.loads((root/PACKETS).read_bytes())
    records = {row['task']: row for row in selection['records']}
    rows = []
    for chosen in selection['selected']:
        segment = chosen['segment']
        identity = segment['segment_id']
        source = f"data/ilvis0-ready/{chosen['task']}/decoded/{chosen['filename']}.gz"
        if not chosen['source_path'].endswith('/'+source):
            raise ValueError('saved source location differs from the selection')
        rows.append(dict(segment_id=identity, source_task=chosen['task'], filename=chosen['filename'],
            source_path=source, source_sha256=records[chosen['task']]['source_sha256'],
            compressed_bytes=(root/source).stat().st_size,
            native_packets=packets[identity],
            date=published[identity]['start_utc'][:10], duration_s=segment['duration_s']))
    if len(rows) != 53 or len({row['segment_id'] for row in rows}) != 53 or set(published) != {
            row['segment_id'] for row in rows}:
        raise ValueError('the 53 published stretches are required')
    return rows


def representatives(rows):
    """Longest stretch on each recorded date; the smaller identity breaks a tie."""
    chosen = {}
    for row in sorted(rows, key=lambda r: (-r['duration_s'], r['segment_id'])):
        chosen.setdefault(row['date'], row)
    return [chosen[date] for date in sorted(chosen)]


def tasks(rows, fits):
    out = []
    for row in rows:
        calls = len(fits)*(EVALUATIONS+1)
        out.append(dict(row, identity=row['segment_id'], input_key='selection', native_kind='tangent',
            fits=fits, limits=dict(native_calls=calls, packet_visits=calls*row['native_packets'],
                                   bound_calls=0, bound_steps=0)))
    return out


def code_sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, TEST, 'analysis/lll/ilvis0_native.c',
                                 'analysis/lll/ilvis0_tangent.cpp'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=code_sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root, name):
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS as RECOVERY_TESTS, qualification_sources

    root = Path(root).resolve()
    study = STUDIES[name]
    identity = study['id']
    if (root/'data'/identity).exists():
        raise ValueError('the existing fit allowance must be retained')
    environment = runtime_environment()
    code = code_sources(root)
    qualification, tests = checked(root, REQUEST, sources=code, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    rows = stretches(root)
    if study['representatives']:
        rows = representatives(rows)
    fits = study['fits']()
    policy = dict(RECOVERY_POLICY, maximum_wall_s=study['maximum_wall_s'])
    staged = dict(recipe=encoded(dict(id=identity, fits=fits, evaluations=EVALUATIONS, weighting=WEIGHTING,
                                      independent_neu_m=[.3, .3, .7], clock='nominal_200Hz', gravity_mps2=9.81,
                                      disc_radius_m=6371000., stretches=[row['segment_id'] for row in rows])),
                  qualification=qualification, qualification_tests=tests, recovery=recovery,
                  recovery_tests=recovery_tests, recovery_policy=encoded(policy))
    inputs = dict(plan=study['plan'], selection=SELECTION, contexts=CONTEXTS, analytics=ANALYTICS,
                  packets=PACKETS)
    folder = root/'data'/(identity+'-inputs')
    folder.mkdir(parents=True, exist_ok=True)
    for key, raw in staged.items():
        path = folder/key
        if path.is_file() and path.read_bytes() != raw:
            raise ValueError('prepared study materials changed')
        if not path.is_file():
            atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity, scope=study['scope'], adapter=ADAPTER,
        sources=sorted(set(code+[study['plan']])), inputs=inputs, tasks=tasks(rows, fits),
        workers=study['workers'], threads=1, maximum_wall_s=study['maximum_wall_s'])
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=identity, stretches=len(rows), fits=len(rows)*len(fits),
                limits=manifest['limits'], allocation=manifest['allocation'])


class CountedProblem(MatchedTrainingProblem):
    """Reserve every native derivative sweep before it runs."""

    def __init__(self, *args, reserve, **kwargs):
        super().__init__(*args, **kwargs)
        self.reserve = reserve

    def prediction_tangent(self, point, model):
        self.reserve(native_calls=1, packet_visits=len(self.dt))
        return super().prediction_tangent(point, model)


def receiver_covariance(times, gps):
    from .ilvis0_gps_sensitivity import assumptions, coordinate_covariance

    law = next(item for item in assumptions() if item.name == WEIGHTING)
    blocks = np.tile(np.diag([.3**2, .3**2, .7**2]), (len(gps), 1, 1))
    return coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, law)


def build_problem(values, times, gps, covariance, fit, *, kernel, tangent, reserve):
    """The published stretch problem and start for one declared candidate."""
    from .ilvis0_corpus_modeling import initialize
    from .ilvis0_estimator import Bounds

    model = fit['model']
    if model not in MATCHED_MODELS or fit['case'] not in CASES:
        raise ValueError('declared candidate and processing case required')
    bounds = limits(fit['offset_dph'])
    seed, force = initialize(times, gps, values, 'flat_still' if model == DISC_WITH_FIELD else model)
    problem = CountedProblem(values[:, 9:12], values[:, 12:15], np.full(len(values), .005), times, gps,
        covariance, seed, Bounds(bounds), matched_model=model, reserve=reserve,
        fit_earth_removal=CASES[fit['case']], kernel=kernel, tangent_kernel=tangent,
        clock_hypothesis='nominal_200Hz', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
    point = np.zeros(len(problem.bounds.active))
    for index, name in enumerate(problem.bounds.active):
        if name.startswith('accel_gain'):
            point[index] = np.clip((force/9.81-1)/bounds[name], -.9, .9)
        if name == 'earth_removal':
            point[index] = -1.
    return problem, point


def run_fit(problem, point, model):
    from .ilvis0_shape import fit_shape_candidate

    fit = fit_shape_candidate(problem, model, start=point, maximum_evaluations=EVALUATIONS)
    predicted, _, _ = problem.prediction_tangent(np.array(fit['normalized_parameters']), model)
    delta = predicted-problem.gps
    delta[:, 1] = (delta[:, 1]+math.pi) % (2*math.pi)-math.pi
    radius = 6378137.+problem.gps[:, 2]
    scale = np.column_stack((radius, radius*np.cos(problem.gps[:, 0]), np.ones(len(radius))))
    fit['residual_rms_neu_m'] = np.sqrt(np.mean((delta*scale)**2, axis=0)).tolist()
    fit['residual_scale'] = 'receiver coordinates scaled by one common WGS84 radius for every candidate'
    fit['evaluations'] += 1
    return fit


def load_stretch(task, context):
    from . import ilvis0_segments as segments
    from .studies.artifacts import safe_path

    root = Path(context.root).resolve().parents[1]
    with gzip.open(context.input_path('selection'), 'rt') as stream:
        selection = json.load(stream)
    chosen = [row for row in selection['selected'] if row['segment']['segment_id'] == task['identity']]
    contexts = json.loads(context.input_path('contexts').read_bytes())
    prior = [row for row in contexts['results'] if row['task_id'] == task['source_task']]
    if (len(chosen) != 1 or len(prior) != 1 or chosen[0]['task'] != task['source_task']
            or prior[0]['inspection']['source_sha256'] != task['source_sha256']
            or task['segment_id'] != task['identity']):
        raise ValueError('sealed stretch and source bindings required')
    source = safe_path(root, task['source_path'])
    if source.stat().st_size != task['compressed_bytes']:
        raise ValueError('original source byte count changed')
    values, times, gps, provenance = segments.extract_segment(source, prior[0], chosen[0]['segment'])
    if provenance['source_sha256'] != task['source_sha256'] or len(values) != task['native_packets']:
        raise ValueError('extracted stretch differs from the published one')
    return values, times, gps, provenance


def evaluate(task, context):
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_shape import load_tangent

    study = next((row for row in STUDIES.values() if row['scope'] == context.manifest['scope']), None)
    calls = len(task['fits'])*(EVALUATIONS+1)
    if (study is None or task['fits'] != study['fits']() or task['limits'] != dict(native_calls=calls,
            packet_visits=calls*task['native_packets'], bound_calls=0, bound_steps=0)):
        raise ValueError('unchanged declared study, fit grid and allowance required')
    values, times, gps, provenance = load_stretch(task, context)
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel, value_build = load_kernel(directory)
    tangent, tangent_build = load_tangent(directory)
    frozen = context.manifest['sources']
    if (value_build['source_sha256'] != frozen['analysis/lll/ilvis0_native.c']
            or tangent_build['source_sha256'] != frozen['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('compiled native source differs from freeze')
    context.save('provenance.json', dict(provenance, value_kernel=value_build, tangent_kernel=tangent_build))
    covariance = receiver_covariance(times, gps)
    rows = []
    for fit in task['fits']:
        name = label(fit)
        try:
            problem, point = build_problem(values, times, gps, covariance, fit, kernel=kernel,
                                           tangent=tangent, reserve=context.charge)
            result = run_fit(problem, point, fit['model'])
        except (ValueError, FloatingPointError) as error:
            result = dict(model=fit['model'], error=str(error), scientific_decision='abstain')
        result.update(case=fit['case'], offset_dph=fit['offset_dph'], label=name)
        context.save('fit-'+name+'.json', result)
        rows.append({key: result.get(key) for key in ('label', 'model', 'case', 'offset_dph',
            'residual_sum_squares', 'converged', 'evaluations', 'error')})
    return dict(passed=all(row['error'] is None for row in rows), segment_id=task['identity'], fits=rows,
                observed_fit_starts=len(rows), confidence_calibrated=False, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('packets', 'request', 'prepare'))
    parser.add_argument('--study', choices=sorted(STUDIES))
    args = parser.parse_args()
    if args.action == 'packets':
        result = write_packets(Path.cwd())
    elif args.action == 'request':
        result = request(Path.cwd())
    else:
        if args.study is None:
            parser.error('prepare requires --study')
        result = prepare(Path.cwd(), args.study)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
