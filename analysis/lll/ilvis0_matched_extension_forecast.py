# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched recorded forecasts on the other two preselected NASA groups."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from . import ilvis0_matched_extension_inputs as aligned, ilvis0_matched_observed_preflight as parent
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-extension-forecast-v1'
PLAN = parent.FOLDER+'MATCHED_EXTENSION_FORECAST_PLAN.md'
REQUEST = parent.FOLDER+'matched-extension-forecast-qualification.json'
TEST_REPORT = parent.FOLDER+'matched-extension-forecast-tests.xml'
RECEIPT = parent.FOLDER+'matched-extension-forecast-result.json'
SCOPE = 'four matched shape and field forecasts on two additional NASA development groups'
WALL_S = 3600.
RECOVERY_POLICY = dict(max_attempts_per_task=2, max_technical_interruptions=2,
    maximum_wall_s=5400, minimum_free_bytes=1024**3, smoke_task_count=0)
TEST = 'analysis/tests/test_ilvis0_matched_extension_forecast.py'
TESTS = (*parent.REQUIRED_TESTS, 'test_new_flight_requires_complete_same_field_shape_comparisons_before_field_rank')
INPUT_MANIFEST = 'c691ba2c1c74c071794bda13ea6582aa6741df4e96d327945ff7f66d2fc5489f'
INPUT_SUMMARY = '54a02b3eab26d0435b190599d2492232761423e7d8a7979c4bec387b6f075497'
SHAPES = dict(specified=('sphere_rotating', 'flat_geographic_field'), zero=('sphere_still', 'flat_still'))


def compare_shapes(models):
    totals = {}
    for model, row in models.items():
        rms = row['heldout_rms_by_gps_stream']
        if set(rms) != set(parent.TRACKS):
            raise ValueError('all three receiver tracks are required')
        totals[model] = {}
        for track, components in rms.items():
            horizontal, height = (components[key] for key in ('horizontal_rms_m', 'height_rms_m'))
            if any(not math.isfinite(value) or value < 0. for value in (horizontal, height)):
                raise ValueError('finite nonnegative RMS errors are required')
            totals[model][track] = math.hypot(horizontal, height)

    def rank(first, second, labels):
        if first not in totals or second not in totals:
            return 'unresolved'
        signs = {(-1 if totals[first][t] < totals[second][t] else
                   1 if totals[first][t] > totals[second][t] else 0) for t in parent.TRACKS}
        return {-1: labels[0], 1: labels[1], 0: 'tie'}[signs.pop()] if len(signs) == 1 else 'mixed'

    shape = {field: rank(*models, ('globe', 'disc')) for field, models in SHAPES.items()}
    field = (rank('sphere_rotating', 'sphere_still', ('specified', 'zero'))
             if set(shape.values()) == {'globe'} else 'unresolved')
    return dict(shape_by_field=shape, globe_field=field, total_position_rms_m=totals)


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (*parent.sources(root), Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=parent.runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('the existing matched flight fit allowance must be retained')
    environment, dependencies = parent.runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=dependencies, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, parent.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(recipe=encoded(parent.recipe()), qualification=binding, qualification_tests=tests,
        recovery=recovery, recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, input_receipt=aligned.RECEIPT, generated_gate=parent.GENERATED_GATE)
    with closing(ClosedStudy(root, 'data/'+parent.WIDE_ID)) as generated:
        gate = json.loads((root/parent.GENERATED_GATE).read_bytes())
        if gate['qualified'] is not True or any(gate[key] != generated.completion[key]
                for key in ('manifest_sha256', 'summary_sha256')):
            raise ValueError('the verified wide-arithmetic gate is required')
    with closing(ClosedStudy(root, 'data/'+aligned.ID)) as packets:
        receipt = json.loads((root/aligned.RECEIPT).read_bytes())
        completion = packets.completion
        if ((completion['manifest_sha256'], completion['summary_sha256']) != (INPUT_MANIFEST, INPUT_SUMMARY)
                or any(receipt[key] != value for key, value in completion.items())
                or not packets.summary['passed'] or packets.manifest['environment'] != environment
                or receipt['imu_fit_starts'] != 0 or len(receipt['recordings']) != 2):
            raise ValueError('the exact passing two-recording input study is required')
        for case in receipt['recordings']:
            identity = case['segment_id']
            if case != dict(segment_id=identity, **packets.envelope(identity)['result']) or not case['passed']:
                raise ValueError('recorded packet preparation changed')
            for name in ('packets.npy.gz', 'queries.json', 'training.json', 'scoring.json', 'packet-provenance.json'):
                staged[identity+'-'+name.split('.')[0]] = packets.artifact(identity, name, raw=True)
    for key, raw in staged.items():
        suffix = '.npy.gz' if key.endswith('-packets') else ''
        path = f'data/{ID}-inputs/{key}{suffix}'
        aligned.shared._write_equal(root/path, raw)
        inputs[key] = path
    rows = parent.tasks(receipt['recordings'])
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=dependencies, inputs=inputs, tasks=rows, workers=4, threads=1, maximum_wall_s=WALL_S)
    aligned.shared._write_equal(root/f'data/{ID}-inputs/definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE:
        raise ValueError('explicit matched extension forecast scope required')
    return parent.evaluate_recorded(task, context, require_converged=True)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        cases = study.input('input_receipt')['recordings']
        if len(study.tasks) != 8 or len(study.rows) != 8 or study.manifest['scope'] != SCOPE:
            raise ValueError('the two sealed four-model groups are required')
        comparisons = []
        for case in cases:
            segment = case['segment_id']
            usable, attempts = {}, []
            for task in (row for row in study.tasks.values() if row['segment_id'] == segment):
                identity, model = task['identity'], task['model']
                envelope = study.envelope(identity)
                result = envelope['result']
                if result['passed']:
                    fit = study.artifact(identity, 'fit.json')
                    forecast = study.artifact(identity, 'forecast.json')
                    query = study.input(segment+'-queries')
                    if (result != study.artifact(identity, 'scores.json') or not fit['converged']
                            or fit['prediction_receiver_positions_used_in_training']
                            or forecast['later_positions_used'] or forecast['query_times_s'] != query['query_times_s']
                            or envelope['charged']['native_calls'] != fit['evaluations']+1):
                        raise ValueError('forecast, fit or charge does not match the training-only replay')
                    usable[model] = result
                attempts.append(dict(model=model, charged=envelope['charged'], result=result))
            comparisons.append(dict(segment_id=segment, imu_type=case['imu_type'],
                scoring_epochs=case['scoring_epochs'], attempts=attempts, **compare_shapes(usable)))
        value = dict(study.completion, comparisons=comparisons, charged=study.summary['charged'],
                     completed=len(study.rows), confidence_calibrated=False, scientific_decision='abstain')
    raw = encoded(value)
    aligned.shared._write_equal(root/RECEIPT, raw)
    return dict(comparisons=len(comparisons), result_sha256=digest(raw), charged=value['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
