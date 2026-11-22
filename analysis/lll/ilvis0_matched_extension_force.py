# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply the matched force-magnitude check to two added NASA flights."""

import argparse
from collections import Counter, defaultdict
from contextlib import closing
import gzip
import json
from pathlib import Path

from . import ilvis0_gps_force_comparison as receiver, ilvis0_matched_extension_inputs as aligned
from . import ilvis0_matched_extension_forecast as forecast, ilvis0_matched_force_average as average
from .ilvis0_matched_force_gain import compare
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-extension-force-v1'
PLAN = aligned.shared.FOLDER+'MATCHED_EXTENSION_FORCE_PLAN.md'
REQUEST = aligned.shared.FOLDER+'matched-extension-force-qualification.json'
TEST_REPORT = aligned.shared.FOLDER+'matched-extension-force-tests.xml'
RESULT = aligned.shared.FOLDER+'matched-extension-force-result.json'
SCOPE = 'force magnitude on two added recorded flights with no gyro or attitude information'
NAMES = ('packets.npy.gz', 'training.json', 'scoring.json', 'packet-provenance.json')
TEST = 'analysis/tests/test_ilvis0_matched_extension_force.py'
TESTS = ('test_extension_force_charges_full_declared_support_and_envelope_allowance',
         'test_extension_force_gain_uses_only_training_and_retains_later_violations')
ENVELOPES_PER_WINDOW = len(average.MATCHED_MODELS)*len(average.TRACKS)*len(average.support.CLOCKS)
STEPS_PER_WINDOW = 1+ENVELOPES_PER_WINDOW*average.SUBDIVISIONS
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=2,
    maximum_wall_s=1200, minimum_free_bytes=1024**3, smoke_task_count=0)


def limits_for(windows):
    return dict(native_calls=0, packet_visits=0, bound_calls=windows, bound_steps=windows*STEPS_PER_WINDOW)


def evaluate_gain(rows):
    models = defaultdict(lambda: {'training': [], 'later': []})
    for row in rows:
        models[row['model']][row['side']].append((row['measured_lower_mps2'], row['required_upper_mps2']))
    return {model: compare(sides['training'], sides['later']) for model, sides in models.items()}


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=aligned.shared.runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing force comparison allowance')
    environment, dependencies = aligned.shared.runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=dependencies, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, aligned.gps.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=binding, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, alignment_receipt=aligned.RECEIPT)
    tasks = []
    with closing(ClosedStudy(root, 'data/'+aligned.ID)) as study:
        receipt = json.loads((root/aligned.RECEIPT).read_bytes())
        completion = study.completion
        if ((completion['manifest_sha256'], completion['summary_sha256']) !=
                (forecast.INPUT_MANIFEST, forecast.INPUT_SUMMARY) or not study.summary['passed']
                or any(receipt[key] != value for key, value in completion.items())
                or study.manifest['environment'] != environment or receipt['imu_fit_starts'] != 0):
            raise ValueError('the exact sealed two-recording alignment is required')
        for case in receipt['recordings']:
            segment = case['segment_id']
            if case != dict(segment_id=segment, **study.envelope(segment)['result']) or not case['passed']:
                raise ValueError('the source packet preparation did not verify')
            metadata = dict(case, artifacts={name: {'path': segment+'-'+name} for name in NAMES})
            materials[segment] = encoded(metadata)
            for alias in NAMES:
                materials[metadata['artifacts'][alias]['path']] = study.artifact(segment, alias, raw=True)
            windows = case['training_epochs']+case['scoring_epochs']
            tasks.append(dict(identity=segment, input_key=segment, targets=windows, limits=limits_for(windows)))
    if sorted(row['targets'] for row in tasks) != [538, 585]:
        raise ValueError('both frozen receiver supports are required')
    for key, raw in materials.items():
        path = f'data/{ID}-inputs/{key}'
        aligned.shared._write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, tasks=tasks, inputs=inputs, sources=dependencies,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=600.)
    aligned.shared._write_equal(root/f'data/{ID}-inputs/definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    case = json.loads(context.input_path().read_bytes())
    if (context.manifest['scope'] != SCOPE or task['identity'] != case['segment_id']
            or task['limits'] != limits_for(task['targets'])):
        raise ValueError('the recorded force window allowance must remain fixed')
    raw = {entry['path']: context.input_path(entry['path']).read_bytes() for entry in case['artifacts'].values()}
    record = average._record(case, raw)
    if len(record['tags']) != task['targets']:
        raise ValueError('exact original receiver epochs required')
    windows, rows = [], []
    for target in record['tags']:
        context.charge(bound_calls=1, bound_steps=STEPS_PER_WINDOW)
        gps = receiver._row(case, int(target), average.support.HALF_WINDOW_S, True,
                            record['tags'], record['coordinates'])
        window = average.support._window(gps, record)
        windows.append(window)
        if window['state'] != 'supported':
            continue
        for required in average._window(window, gps, record):
            clock = required['clock']
            for model in average.MATCHED_MODELS:
                rows.append(dict(model=model, clock=clock, gps_stream=required['gps_stream'],
                    side=window['side'], gps_millisecond_tag=int(target),
                    measured_lower_mps2=window[clock+'_lower_mps2'],
                    measured_upper_mps2=window[clock+'_upper_mps2'],
                    required_lower_mps2=required[model+'_lower_mps2'],
                    required_upper_mps2=required[model+'_upper_mps2']))
    counts = Counter(window['state'] for window in windows)
    if len(rows) != counts['supported']*ENVELOPES_PER_WINDOW:
        raise ValueError('one common support and every candidate case are required')
    comparison = evaluate_gain(rows)
    if set(comparison) != set(average.MATCHED_MODELS):
        raise ValueError('both training and withheld force windows are required')
    summary = dict(segment_id=case['segment_id'], imu_type=case['imu_type'], targets=len(windows),
        training_windows=sum(w['state'] == 'supported' and w['side'] == 'training' for w in windows),
        later_windows=sum(w['state'] == 'supported' and w['side'] == 'later' for w in windows),
        window_dispositions=dict(counts), model_envelopes=len(rows), by_model=comparison,
        gyro_observations_used=False, fused_navigation_used=False, new_fits=0,
        passed=True, scientific_decision='abstain')
    context.save_bytes('windows.json.gz', gzip.compress(encoded(dict(windows=windows, comparisons=rows)), mtime=0))
    context.save_bytes('summary.json', encoded(summary))
    return summary


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.tasks) != 2 or len(study.rows) != 2 or study.manifest['scope'] != SCOPE:
            raise ValueError('expected the sealed two-flight force comparison')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed']:
                summary = study.artifact(identity, 'summary.json')
                details = study.artifact(identity, 'windows.json.gz', raw=True)
                if (result != summary or result['targets'] != study.tasks[identity]['targets']
                        or envelope['charged'] != limits_for(result['targets'])):
                    raise ValueError('result and charges differ from the sealed diagnostic')
                result = dict(result, windows_sha256=digest(details))
            rows.append(result)
        value = dict(study.completion, flights=rows, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    aligned.shared._write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), charged=value['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
