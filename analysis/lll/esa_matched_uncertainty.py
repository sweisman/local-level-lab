# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the sealed ESA forecast ranges with their matched GPS errors."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .esa_conditional_coverage_report import describe_coverage
from .esa_conditional_forecast_report import TASK as ORIGINAL_TASK
from .esa_height_error_transfer import CUTS, DOCS, HORIZON, LAWS, PARENT, PARENT_MANIFEST, PARENT_SUMMARY
from .esa_matched_conditioning import ID as MATCHED_ID, RESULT as MATCHED_REPORT
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-matched-uncertainty-v1-20261121'
SCOPE = 'Fixed-parameter uncertainty diagnostics on matched ESA 187 rolling cuts'
PLAN = DOCS + 'ESA_MATCHED_UNCERTAINTY_PLAN.md'
RESULT = DOCS + 'esa-matched-uncertainty.json'
MATCHED_SHA = 'b58bded7fa2c9830cf3d82a5451fa048b1c0549a4863a1dda9a4896e41c8c9e1'
FULL_HORIZONS = {200: 120, 400: 120, 600: 200, 800: 400}


def check_ranges(forecast, receiver, covariance):
    result = describe_coverage(forecast, receiver, covariance)
    fractions = {key: axis['nominal_95_fraction'] for key, axis in result['axes'].items()}
    fractions['ellipsoid'] = result['nominal_95_ellipsoid_fraction']
    result['outside_counts'] = {name: result['epochs'] - round(fraction * result['epochs'])
                                for name, fraction in fractions.items()}
    return result


def task_for(cut, law):
    identity = f'{cut}-{law}'
    checks = 0 if (cut, law) == (800, 'point') else 1 + (FULL_HORIZONS[cut] > HORIZON)
    return dict(identity=identity, input_key=identity, payload={'cut': cut, 'law': law},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=checks, bound_steps=0))


def evaluate(task, context):
    cut, law = task['payload']['cut'], task['payload']['law']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    data = json.loads(context.input_path().read_bytes())
    if (declared != task_for(cut, law) or context.manifest['scope'] != SCOPE
            or data['identity'] != task['identity']):
        raise ValueError('exact saved uncertainty comparison required')
    result = dict(identity=data['identity'], same_120=None, full=None, reason=data.get('reason'),
                  scientific_decision='abstain', passed=True)
    if result['reason'] is None:
        arrays = [data[name] for name in ('forecast', 'receiver', 'covariance')]
        if any(len(array) != FULL_HORIZONS[cut] for array in arrays):
            raise ValueError('full archived prediction support required')
        context.charge(bound_calls=1, bound_steps=0)
        result['same_120'] = check_ranges(*(array[:HORIZON] for array in arrays))
        if FULL_HORIZONS[cut] > HORIZON:
            context.charge(bound_calls=1, bound_steps=0)
            result['full'] = check_ranges(*arrays)
        result['source'] = data['source']
    context.save('matched-uncertainty.json', result)
    return result


def extract(root, prior):
    if [row['identity'] for row in prior['rolling']] != [f'{cut}-{law}' for cut in CUTS for law in LAWS]:
        raise ValueError('exact eight rolling forecast cases required')
    with closing(ClosedStudy(root, 'data/' + MATCHED_ID)) as matched, closing(
            ClosedStudy(root, PARENT, store=matched.store)) as parent:
        if (any(matched.completion[key] != prior[key] for key in ('manifest_sha256', 'summary_sha256'))
                or (parent.completion['manifest_sha256'], parent.completion['summary_sha256']) != (PARENT_MANIFEST, PARENT_SUMMARY)):
            raise ValueError('exact sealed comparison and receiver source required')
        origin = parent.input('saved-input-binding')['time_origin_s']
        gps = json.loads(gzip.decompress(parent.input('scoring', raw=True)))
        records = {}
        for cut in CUTS:
            receipt = matched.input(f'receipt-{cut}')
            prefix = 'conditioning_' if cut < 800 else ''
            study_path = receipt[prefix + 'study']
            observations = gps[cut:cut + FULL_HORIZONS[cut]]
            receiver = [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']),
                         row['height_m']] for row in observations]
            times = [row['time_s'] - origin for row in observations]
            with closing(ClosedStudy(root, study_path, store=matched.store)) as source:
                if any(source.completion[key] != receipt[prefix + key] for key in ('manifest_sha256', 'summary_sha256')):
                    raise ValueError('earlier-conditioned covariance does not match its score receipt')
                for law in LAWS:
                    identity = f'{cut}-{law}'
                    previous = next(row for row in prior['rolling'] if row['identity'] == identity)
                    if previous != matched.artifact(identity, 'matched-conditioning.json'):
                        raise ValueError('match report differs from the saved result')
                    frozen = matched.input(identity)
                    if frozen['receiver'] != receiver[:HORIZON] or frozen['times'] != times[:HORIZON]:
                        raise ValueError('exact matched GPS support required')
                    if previous['adjusted'] is None:
                        records[identity] = dict(identity=identity, reason=previous['reason'])
                        continue
                    key = law if cut < 800 else ORIGINAL_TASK
                    artifact = source.artifact(key, 'conditional-forecast.json', raw=True)
                    sealed = json.loads(artifact)
                    mean = sealed['conditional_receiver_mean']
                    if (previous['source'] != source.prefix or sealed['training_epochs'] != cut
                            or sealed.get('law', 'increment') != law or sealed['later_receiver_values_used'] is not False
                            or sealed['prediction_epochs'] != FULL_HORIZONS[cut] or mean[:HORIZON] != frozen['adjusted']
                            or any(abs(a - b) > 1e-8 for a, b in zip(sealed['times_s'][cut:], times, strict=True))):
                        raise ValueError('forecast mean, law and times must match the earlier score')
                    records[identity] = dict(identity=identity, receiver=receiver, forecast=mean,
                        covariance=sealed['conditional_receiver_covariance'],
                        source=dict(study=source.prefix, task=key, forecast_sha256=digest(artifact)))
    return records


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen uncertainty study')
    content = (root / MATCHED_REPORT).read_bytes()
    if digest(content) != MATCHED_SHA:
        raise ValueError('exact archived matching report required')
    records = extract(root, json.loads(content))
    directory.mkdir(parents=True)
    inputs = {'prior': MATCHED_REPORT, 'plan': PLAN}
    for identity, record in records.items():
        path = directory / (identity + '.json')
        atomic(path, encoded(record))
        inputs[identity] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(cut, law) for cut in CUTS for law in LAWS], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 8:
            raise ValueError('all rolling cases must have a saved outcome')
        rows = []
        for identity in study.tasks:
            row = study.artifact(identity, 'matched-uncertainty.json')
            if (row != study.envelope(identity)['result'] or row['identity'] != identity
                    or row['scientific_decision'] != 'abstain'):
                raise ValueError('sealed diagnostic disagrees with saved result')
            rows.append(row)
        charges = sum(row[key] is not None for row in rows for key in ('same_120', 'full'))
        if charges != study.summary['bound_evaluations']:
            raise ValueError('every evaluated horizon must have its own charge')
        output = encoded(dict(rows=rows, recordings=1, scientific_decision='abstain',
            calibrated_coverage=False, manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, output)
    print(digest(output))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
