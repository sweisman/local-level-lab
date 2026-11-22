# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score closed ESA solver forecasts against their withheld receiver positions."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_dispatch_inputs import BASE, CLOCK, CLOCK_SHA
from .esa_dispatch_pair_report import PREFIX as PARENT, RESULT as PARENT_RESULT
from .esa_dispatch_pairs import METHODS, PREDICTION, TRAINING
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-dispatch-accuracy-v1'
SCOPE = 'Withheld receiver position accuracy for the saved 32 ESA 187 dispatch paths'
PLAN = BASE + 'ESA_DISPATCH_ACCURACY_PLAN.md'
RESULT = BASE + 'esa-dispatch-accuracy.json'
REQUEST = BASE + 'esa-dispatch-accuracy-qualification.json'
TEST_REPORT = BASE + 'esa-dispatch-accuracy-tests.xml'
TEST = 'analysis/tests/test_esa_dispatch_accuracy.py'
PARENT_MANIFEST_SHA = '9e4f8af256bab5270a216b5d83c97b614a69a1ede6270ec10574fa7caa3c4d1f'
PARENT_RESULT_SHA = '781bb1eae88ee8761bcfa800baf82c21cb470d3836f39e19b7ddb06674429d41'
INDICES = range(13098, 13897, 2)
CUTS = (120, 240, PREDICTION)
ALLOWED_PATHS = 32
TASK = dict(identity=ID, input_key='forecasts', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=ALLOWED_PATHS, bound_steps=0))
REQUIRED = ('test_primary_choice_uses_training_cost_and_breaks_exact_ties_by_start',
            'test_primary_choice_rejects_missing_or_nonfinite_alternates',
            'test_scoring_requires_unchanged_release',
            'test_accuracy_scores_all_later_epochs_and_retains_vertical_failure')


def choose_starts(candidates):
    if set(candidates) != {0, 1} or any(
        set(costs) != set(METHODS) or any(not math.isfinite(cost) or cost < 0 for cost in costs.values())
        for costs in candidates.values()
    ):
        raise ValueError('both complete starts with finite nonnegative training costs required')
    return {method: min((0, 1), key=lambda start: candidates[start][method]) for method in METHODS}


def verify_release(release, raw):
    if raw != encoded(release):
        raise ValueError('unchanged training-only release required')


def checked_json(root, path, sha):
    raw = safe_path(root, path).read_bytes()
    if digest(raw) != sha:
        raise ValueError(f'original evidence hash differs: {path}')
    return json.loads(raw)


def release(root):
    report = checked_json(root, PARENT_RESULT, PARENT_RESULT_SHA)
    if (report['terminal_pairs'] != 16 or report['passing_pairs'] != 16
            or report['equivalent_groups'] != 8 or report['forecast_positions_decoded'] != 0
            or report['protected_reads'] != 0):
        raise ValueError('complete position-blind paired comparison required')
    forecasts, paths, groups = {}, [], {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, PARENT)))
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST_SHA:
            raise ValueError('exact paired comparison manifest required')
        queries = parent.input('queries')
        times = queries['times_s']
        studies = {PARENT: parent}
        for prefix, closure in report['closures'].items():
            if prefix != PARENT:
                studies[prefix] = stack.enter_context(closing(ClosedStudy(root, prefix, store=parent.store)))
            if studies[prefix].completion != closure:
                raise ValueError('paired comparison closure differs from report')
        for row in report['pairs']:
            study, identity = studies[row['source']], row['identity']
            envelope = study.envelope(identity)
            if (envelope['status'] != 'complete' or envelope['result_sha256'] != row['result_sha256']
                    or envelope['result']['fits'] != row['fits']):
                raise ValueError('position-blind fit result differs from report')
            group = (row['model'], row['profile'], row['policy_id'])
            costs = groups.setdefault(group, {}).setdefault(row['start'], {})
            for method in METHODS:
                key = identity + '-' + method
                fit = row['fits'][method]
                raw = study.artifact(identity, method+'-forecast.json', raw=True)
                forecast = json.loads(raw)
                if (key in forecasts or not all(fit[field] is True for field in
                        ('converged', 'passed', 'all_columns_retained'))
                        or forecast['prediction_receiver_positions_used'] is not False
                        or forecast['times_s'] != times or len(forecast['coordinates']) != TRAINING+PREDICTION
                        or (forecast['training_epochs'], forecast['prediction_epochs']) != (TRAINING, PREDICTION)):
                    raise ValueError('complete position-blind forecast required')
                coordinates = forecast['coordinates'][TRAINING:]
                forecasts[key] = coordinates
                paths.append(dict(key=key, group=list(group), method=method, start=row['start'],
                    training_cost=fit['training_cost'], forecast_sha256=digest(raw),
                    later_coordinates_sha256=digest(encoded(coordinates))))
                costs[method] = fit['training_cost']
    if len(paths) != ALLOWED_PATHS or len(groups) != 8 or len(times) != TRAINING+PREDICTION:
        raise ValueError('eight settings and 32 paths required')
    choices = {group: choose_starts(costs) for group, costs in groups.items()}
    for path in paths:
        path['primary'] = path['start'] == choices[tuple(path['group'])][path['method']]
    binding = dict(paths=paths, times_s=times[TRAINING:], origin_s=queries['time_origin_gps_sow_s'],
                   parent_manifest_sha256=PARENT_MANIFEST_SHA, parent_report_sha256=PARENT_RESULT_SHA,
                   clock_sha256=CLOCK_SHA, receiver_indices=list(INDICES), policy_sha256=digest((root/PLAN).read_bytes()))
    return binding, forecasts


def receiver_targets(root, binding):
    from .airquantumgrav_inventory import METADATA, RECEIVER_PATH, validate_context
    from .esa_repeat_turns import read_selected

    clock = checked_json(root, CLOCK, CLOCK_SHA)
    metadata = {key: safe_path(root, path).read_bytes() for key, path in METADATA.items()}
    if {key: digest(raw) for key, raw in metadata.items()} != clock['metadata_sha256']:
        raise ValueError('receiver or development membership metadata has changed')
    source = validate_context(**{key: json.loads(raw) for key, raw in metadata.items()})
    window = clock['selection']['window']
    if (source['receiver_sha256'] != clock['receiver_sha256'] or source['group_id'] != clock['development_group']
            or range(window['prediction_first_index'], window['query_last_index'] + 1, window['query_stride']) != INDICES
            or binding['receiver_indices'] != list(INDICES)):
        raise ValueError('exact opened window and receiver source required')
    selected = read_selected(safe_path(root, RECEIVER_PATH), [(i, i) for i in INDICES],
                             expected_hash=source['receiver_sha256'], total=source['expected_receiver_epochs'])
    rows = [row for (row,) in selected]
    times = [row['time_s'] - binding['origin_s'] for row in rows]
    if times != binding['times_s']:
        raise ValueError('later receiver positions must match all released forecast times')
    coordinates = [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]
                   for row in rows]
    return dict(times_s=times, coordinates=coordinates, receiver_sha256=source['receiver_sha256'],
                receiver_indices=list(INDICES), release_sha256=digest(encoded(binding)))


def score_path(times, path, actual):
    from .airquantumgrav_scoring import receiver_errors
    from .ilvis0_forecast_error_transfer import score
    from .ilvis0_prediction_observed import accuracy_screen

    if len(times) != PREDICTION or len(path) != PREDICTION or len(actual) != PREDICTION:
        raise ValueError('all 400 later positions required')
    errors = receiver_errors(path, actual)
    results = {}
    for cut in CUTS:
        metrics = score(times[:cut], errors[:cut])
        results[str(cut)] = dict(score=metrics, limits=accuracy_screen(metrics))
    return results


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact accuracy calculation required')
    raw = context.input_path('release').read_bytes()
    binding = json.loads(raw)
    paths = json.loads(context.input_path().read_bytes())
    actual = json.loads(context.input_path('later-positions').read_bytes())
    if (len(paths) != ALLOWED_PATHS or len(binding['paths']) != ALLOWED_PATHS
            or set(paths) != {item['key'] for item in binding['paths']}
            or actual['release_sha256'] != digest(raw) or actual['times_s'] != binding['times_s']
            or actual['receiver_indices'] != list(INDICES)):
        raise ValueError('saved receiver evidence differs from training-only release')
    scores = []
    for item in binding['paths']:
        path = paths[item['key']]
        if digest(encoded(path)) != item['later_coordinates_sha256']:
            raise ValueError('forecast differs from training-only release')
        context.charge(bound_calls=1, bound_steps=0)
        scores.append(dict(item, horizons=score_path(actual['times_s'], path, actual['coordinates'])))
    result = dict(scores=scores, receiver_epochs=PREDICTION, development_recordings=1, navigation_fits=0,
                  protected_reads=0, scientific_decision='abstain', calibrated_coverage=False, passed=True)
    context.save('accuracy.json', result)
    return result


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, TEST, PLAN))
    environment = runtime_environment()
    if check:
        checked(root, REQUEST, sources=sources, environment=environment,
                required_tests=REQUIRED, minimum_tests=len(REQUIRED))
        return sources
    return request(root, sources=sources, environment=environment, output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    sources = qualification(root, check=True)
    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('reuse the existing frozen accuracy allowance')
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=runtime_environment(), required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    binding, forecasts = release(root)
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=TEST_REPORT, clock=CLOCK,
                  parent_report=PARENT_RESULT)

    def save(name, raw):
        path = f'data/{ID}-inputs/{name}.json'
        _write_equal(root/path, raw)
        inputs[name] = path

    save('release', encoded(binding))
    save('forecasts', encoded(forecasts))
    verify_release(binding, (root/inputs['release']).read_bytes())
    save('later-positions', encoded(receiver_targets(root, binding)))
    save('recovery', recovery)
    save('recovery_tests', tests)
    save('recovery_policy', encoded(RECOVERY_POLICY))
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, tasks=[TASK], sources=sources, workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def collect(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        result = study.artifact(ID, 'accuracy.json')
        if (study.summary['bound_evaluations'] != ALLOWED_PATHS or study.summary['completed'] != 1
                or not study.summary['passed'] or result != study.envelope(ID)['result']):
            raise ValueError('complete charged accuracy result required')
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['summary_sha256'] = study.completion['summary_sha256']
    _write_equal(root/RESULT, encoded(result))
    counts = {}
    for cut in map(str, CUTS):
        passing = [row for row in result['scores'] if row['horizons'][cut]['limits']['passed']]
        counts[cut] = dict(all=len(passing), primary=sum(row['primary'] for row in passing))
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'collect'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'collect': collect}[action](root)
    print(json.dumps(result, sort_keys=True))
