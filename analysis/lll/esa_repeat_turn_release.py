# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release primary repeat-turn forecasts before decoding held-out positions."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from . import esa_repeat_turn_execution as design
from .esa_repeat_turn_execution_v2 import ID
from .studies.artifacts import digest, encoded, safe_path

PREFIX = 'data/' + ID
ADAPTER = 'analysis/lll/esa_repeat_turn_execution_v2.py'
VERSION = 'esa-repeat-turn-release-v1'
ORIGINAL_SHA256 = 'e79d1f7e516f7282298e03ca13291bbc5b02e42a8412eafdf740e2e1097e6f46'
REQUEST = design.BASE + 'esa-repeat-turn-release-qualification.json'
REPORT = design.BASE + 'esa-repeat-turn-release-tests.xml'
TEST = 'analysis/tests/test_esa_repeat_turn_release.py'
REQUIRED = (
    'test_recovery_worker_exposes_only_training_inputs',
    'test_release_requires_all_terminal_starts_and_never_substitutes_a_forecast',
    'test_scoring_opens_positions_only_after_replaying_the_saved_release',
    'test_terminal_start_audit_keeps_converged_fit_if_forecast_failed',
)


def primary_starts(outcomes):
    tasks = design.tasks()
    if set(outcomes) != {task['identity'] for task in tasks}:
        raise ValueError('all 16 terminal starts are required before release')
    selections = []
    for index in design.WINDOWS:
        for law in design.LAWS:
            group = dict(first_index=index, law=law)
            candidates = [(f'{index}-{law}-{start}', outcomes[f'{index}-{law}-{start}'])
                          for start in (0, 1)]
            converged = [(identity, result) for identity, result in candidates if result['converged']]
            if not converged:
                selections.append(dict(group, identity=None, state='no_converged_start'))
                continue
            if any(not math.isfinite(result['cost']) or result['cost'] < 0 for _, result in converged):
                raise ValueError('converged training fits require finite nonnegative costs')
            identity, result = min(converged, key=lambda pair: pair[1]['cost'])
            sha = result.get('forecast_sha256')
            selections.append(dict(group, identity=identity, training_cost=result['cost'],
                                   state='sealed' if sha else 'primary_forecast_missing',
                                   forecast_sha256=sha))
    return selections


def terminal_starts(studies):
    outcomes, owners = {}, {}
    for study in studies:
        for identity in study.rows:
            envelope = study.envelope(identity)
            if envelope['status'] == 'interrupted':
                continue
            if envelope['status'] != 'complete' or identity in owners:
                raise ValueError('one terminal scientific outcome required per start')
            owners[identity] = study
            result = envelope['result']
            fit_path = f'artifacts/{identity}/fit.json'
            fit = study.artifact(identity, 'fit.json') if fit_path in envelope['artifacts'] else {}
            converged = fit.get('converged') is True
            outcome = dict(converged=converged, passed=result['passed'],
                           study=study.prefix, result_sha256=envelope['result_sha256'])
            if converged:
                outcome['cost'] = fit['residual_sum_squares']
            if result['passed']:
                if (not converged or outcome['cost'] != result['training_cost']
                        or result['later_receiver_positions_used'] is not False
                        or result['protected_reads'] != 0):
                    raise ValueError('sealed forecast disagrees with its training-only fit')
                outcome['forecast_sha256'] = result['forecast_sha256']
            outcomes[identity] = outcome
    return outcomes, owners


def _closed(root, stack, expected_manifest_sha256):
    from .ilvis0_control_shards import verify_completion
    from .studies.closed import ClosedStudy
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    parent = root / PREFIX
    if not (parent / 'completion.json').is_file():
        raise ValueError('closed repeat-turn execution is required before release')
    verify_completion(parent)
    original = stack.enter_context(closing(ClosedStudy(root, PREFIX)))
    tasks = [{key: value for key, value in task.items() if key not in ('index', 'shard')}
             for task in original.manifest['tasks']]
    if (original.completion['manifest_sha256'] != expected_manifest_sha256
            or original.manifest['adapter'] != ADAPTER or original.manifest['scope'] != design.SCOPE
            or tasks != design.tasks()):
        raise ValueError('exact frozen repeat-turn execution required')
    if len(original.rows) == len(tasks) and all(
            original.envelope(identity)['status'] == 'complete' for identity in original.rows):
        return [original], None
    recovery = root / (PREFIX + '-recovery')
    completion = recovery / 'completion.json'
    if not completion.is_file() or resume_campaign(root, recovery, launch=False)['state'] != 'all_tasks_finished':
        raise ValueError('verified recovery closure required for unfinished original starts')
    stages = [stack.enter_context(closing(ClosedStudy(root, path.relative_to(root).as_posix(),
                                                    store=original.store)))
              for path in _stage_paths(recovery)]
    return [original, *stages], digest(completion.read_bytes())


def release(root, *, expected_manifest_sha256):
    from . import esa_repeat_turn_scoring as scoring
    from .esa_repeat_turn_material import INPUT_SHA

    with ExitStack() as stack:
        studies, recovery_hash = _closed(root, stack, expected_manifest_sha256)
        preflight = studies[0].input('input-preflight', raw=True)
        if digest(preflight) != INPUT_SHA:
            raise ValueError('unchanged preflight required')
        frozen_input = json.loads(preflight)
        receiver_metadata = metadata_hashes(root, expected_preflight=frozen_input['freeze_sha256'])
        windows = {w['window']['first_index']: w for w in frozen_input['windows']}
        outcomes, owners = terminal_starts(studies)
        primary = primary_starts(outcomes)
        forecasts = {}
        for case in primary:
            if case['state'] != 'sealed':
                continue
            identity = case['identity']
            raw = owners[identity].artifact(identity, 'sealed-receiver-forecast.json', raw=True)
            if digest(raw) != case['forecast_sha256']:
                raise ValueError('selected forecast seal differs from its result')
            contents = json.loads(raw)
            window = windows[case['first_index']]
            if (contents['policy'] != scoring.VERSION or contents['law'] != case['law']
                    or contents['training_sha256'] != window['training_receiver_sha256']
                    or contents['previous_time'] != window['query_times_s'][design.TRAIN-1]
                    or contents['times_s'] != window['query_times_s'][design.TRAIN:]):
                raise ValueError('selected forecast does not match the preflight')
            forecasts[identity] = raw
        receipt = dict(version=VERSION, manifest_sha256=expected_manifest_sha256,
                       recovery_sha256=recovery_hash, preflight_sha256=INPUT_SHA,
                       receiver_metadata=receiver_metadata,
                       closures={study.prefix: digest(encoded(study.completion)) for study in studies},
                       outcomes=outcomes, primary=primary, scientific_decision='abstain')
    return receipt, forecasts, windows


def metadata_hashes(root, *, expected_preflight):
    from .esa_repeat_turn_inputs import FREEZE
    raw = safe_path(root, FREEZE).read_bytes()
    if digest(raw) != expected_preflight:
        raise ValueError('original preflight source metadata binding differs')
    return json.loads(raw)['metadata_hashes']


def receiver_positions(root, windows, *, expected_metadata):
    from .airquantumgrav_inventory import METADATA, RECEIVER_PATH, validate_context
    from .esa_repeat_turn_inputs import query_indices
    from .esa_repeat_turns import read_selected

    raw = {key: safe_path(root, name).read_bytes() for key, name in METADATA.items()}
    if {key: digest(value) for key, value in raw.items()} != expected_metadata:
        raise ValueError('receiver source metadata differs from the frozen preflight')
    source = validate_context(**{key: json.loads(value) for key, value in raw.items()})
    indices = {index: query_indices(bound['window'])[1] for index, bound in windows.items()}
    ordered = sorted(i for group in indices.values() for i in group)
    if len(ordered) != len(set(ordered)):
        raise ValueError('scoring windows overlap')
    rows = read_selected(safe_path(root, RECEIVER_PATH), [(i, i) for i in ordered],
                         expected_hash=source['receiver_sha256'], total=source['expected_receiver_epochs'])
    by_index = {i: row for i, (row,) in zip(ordered, rows, strict=True)}
    observations = {}
    for index, group in indices.items():
        bound = windows[index]
        selected = [by_index[i] for i in group]
        tags = [(row['sequence'], row['time_s'], row['gps_week']) for row in selected]
        times = [tag[1] - bound['raw_first_s'] for tag in tags]
        if digest(encoded(tags)) != bound['scoring_clock_sha256'] or times != bound['query_times_s'][design.TRAIN:]:
            raise ValueError('later receiver clock differs from the preflight')
        actual = [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]
                  for row in selected]
        observations[index] = times, actual
    return observations


def score(root, *, expected_manifest_sha256, saved_release):
    from .esa_repeat_turn_scoring import score_sealed

    receipt, forecasts, windows = release(root, expected_manifest_sha256=expected_manifest_sha256)
    if saved_release != encoded(receipt):
        raise ValueError('exact saved release required before decoding later receiver positions')
    selected = [case for case in receipt['primary'] if case['state'] == 'sealed']
    observed = receiver_positions(root, {case['first_index']: windows[case['first_index']]
                                        for case in selected},
                                  expected_metadata=receipt['receiver_metadata']) if selected else {}
    scores = {}
    for case in selected:
        identity = case['identity']
        times, actual = observed[case['first_index']]
        scores[identity] = score_sealed(forecasts[identity], expected_sha256=case['forecast_sha256'],
                                       times=times, actual=actual)
    return dict(release_sha256=digest(saved_release), scores=scores, protected_reads=0,
                scientific_decision='abstain')


def qualification(root, *, verify):
    from .airquantumgrav_inventory import environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (ADAPTER, TEST, design.PLAN,
                                    'analysis/lll/esa_repeat_turn_release.py'))
    env = environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment, verify
    from .studies.recovery import inspect
    from .studies.runtime import Definition

    sources = qualification(root, verify=True)
    original_prefix = 'data/' + design.ID
    original = root / original_prefix
    verified = inspect(root, original_prefix)
    if (verified['state'] != 'uncharged_work_available'
            or verified['charged_identities'] != 0 or (original / 'start.json').exists()):
        raise ValueError('unstarted original execution freeze required')
    parent = verify(original)
    if (digest((original / 'manifest.json').read_bytes()) != ORIGINAL_SHA256
            or parent['environment'] != runtime_environment()):
        raise ValueError('original manifest or runtime environment differs')
    inputs = {name: record['source'] for name, record in
              sorted(parent['inputs'].items(), key=lambda item: item[1]['path'])}
    if (any(digest(safe_path(root, name).read_bytes()) != sha for name, sha in parent['sources'].items())
            or any(digest(safe_path(root, name).read_bytes()) != parent['inputs'][key]['sha256']
                   for key, name in inputs.items())):
        raise ValueError('original frozen sources and inputs must reproduce exactly')
    definition = dict(id=ID, scope=design.SCOPE, adapter=ADAPTER, inputs=inputs, tasks=design.tasks(),
        sources=sorted(set(parent['sources']) | set(sources) | {REQUEST, REPORT}),
        workers=parent['allocation']['workers'], threads=parent['allocation']['threads'],
        maximum_wall_s=parent['limits']['maximum_wall_s'])
    manifest = Definition.from_dict(definition, root).prepare(root)
    if manifest['limits'] != parent['limits'] or manifest['inputs'] != parent['inputs']:
        raise ValueError('replacement changed the original scientific inputs or allowance')
    return dict(path=PREFIX, manifest_sha256=digest((root / PREFIX / 'manifest.json').read_bytes()),
                original_sha256=ORIGINAL_SHA256, total=len(manifest['tasks']), launched=False)


def main(argv=None):
    from .ilvis0_matched_observed_inputs import _write_equal

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'release', 'score'))
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args(argv)
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, verify=False)
    elif args.action == 'prepare':
        result = prepare(root)
    else:
        if not args.manifest_sha256:
            parser.error('the prepared --manifest-sha256 is required')
        run_path = root / PREFIX
        manifest = json.loads((run_path / 'manifest.json').read_bytes())
        sources = qualification(root, verify=True)
        if any(digest(safe_path(root, name).read_bytes()) != manifest['sources'].get(name)
               for name in (*sources, REQUEST, REPORT)):
            raise ValueError('scoring sources differ from the execution freeze')
        receipt_path = run_path / 'receiver-release.json'
        if args.action == 'release':
            result, _, _ = release(root, expected_manifest_sha256=args.manifest_sha256)
            raw = encoded(result)
            _write_equal(receipt_path, raw)
            result = dict(release_sha256=digest(raw), terminal_starts=len(result['outcomes']),
                          primary_forecasts=sum(case['state'] == 'sealed' for case in result['primary']))
        else:
            result = score(root, expected_manifest_sha256=args.manifest_sha256,
                           saved_release=receipt_path.read_bytes())
            _write_equal(run_path / 'receiver-scores.json', encoded(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
