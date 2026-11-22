# SPDX-License-Identifier: AGPL-3.0-or-later
"""Match raw and training-adjusted ESA forecasts on frozen receiver positions."""

from contextlib import closing
import json
from pathlib import Path

from .esa_absolute_accuracy import DOCS, HORIZON, ID as PARENT, LAWS, RESULT as PRIOR, describe
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-raw-accuracy-v1-20261121'
SCOPE = 'All-raw absolute accuracy on the same twelve ESA 187 windows'
PLAN = DOCS + 'ESA_RAW_ACCURACY_PLAN.md'
RESULT = DOCS + 'esa-raw-accuracy.json'
PRIOR_SHA = '78eb740381ac6f868fc2629bf442b6bc2cbd9eee16c944d0953ee0b96f24b145'


def raw_positions(forecast, later_times):
    cut = forecast['training_epochs']
    if (forecast['prediction_receiver_positions_used'] is not False
            or forecast['continuous_propagation_without_gps_reset'] is not True):
        raise ValueError('archived raw forecast without later positions required')
    if (cut != 400 or forecast['prediction_epochs'] != HORIZON or len(later_times) != HORIZON
            or len(forecast['coordinates']) != cut + HORIZON or len(forecast['times_s']) != cut + HORIZON
            or forecast['times_s'][cut:] != later_times):
        raise ValueError('full raw path must share the original scoring clock')
    return forecast['coordinates'][cut:]


def task_for(identity):
    return dict(identity=identity, input_key=identity, payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=0))


def evaluate(task, context):
    from .airquantumgrav_scoring import receiver_errors

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    case = json.loads(context.input_path().read_bytes())
    if (declared != task_for(identity) or context.manifest['scope'] != SCOPE
            or case['identity'] != identity or case['kind'] not in ('turn', 'steady')
            or set(case['laws']) != set(LAWS)):
        raise ValueError('exact turn or steady window and both laws required')
    laws = {}
    for law in LAWS:
        source = case['laws'][law]
        context.charge(bound_calls=1, bound_steps=0)
        errors = receiver_errors(source['raw_positions'], case['coordinates'])
        laws[law] = dict(raw=describe(case['times'], errors), adjusted=source['adjusted'],
                         raw_forecast_sha256=source['raw_forecast_sha256'])
    result = dict(identity=identity, kind=case['kind'], laws=laws, passed=True,
                  navigation_fits=0, scientific_decision='abstain')
    context.save('raw-accuracy.json', result)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen raw accuracy study')
    prior = (root / PRIOR).read_bytes()
    if digest(prior) != PRIOR_SHA:
        raise ValueError('require the exact completed earlier accuracy audit')
    prior = json.loads(prior)
    records = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent:
        if any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256')):
            raise ValueError('prior report must agree with the closed study')
        for kind in ('turn', 'steady'):
            rows = [row for row in prior['rows'] if row['kind'] == kind]
            if len(rows) != 4:
                raise ValueError('all four windows must be present')
            references = {case['source']['study'] for row in rows for case in row['laws'].values()}
            if len(references) != 1:
                raise ValueError('one sealed original per window class required')
            with closing(ClosedStudy(root, references.pop(), store=parent.store)) as original:
                for row in rows:
                    identity = row['identity']
                    if row != parent.artifact(identity, 'absolute-accuracy.json'):
                        raise ValueError('prior report must reproduce its saved score')
                    data = parent.input(identity)
                    laws = {}
                    for law in LAWS:
                        case = row['laws'][law]
                        source = case['source']
                        raw = original.artifact(source['identity'], 'forecast.json', raw=True)
                        laws[law] = dict(raw_positions=raw_positions(json.loads(raw), data['times']),
                                         adjusted=case, raw_forecast_sha256=digest(raw))
                    records[identity] = dict(identity=identity, kind=kind, times=data['times'],
                                             coordinates=data['coordinates'], laws=laws)
    directory.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    identities = sorted(records)
    for identity in identities:
        path = directory / (identity + '.json')
        atomic(path, encoded(records[identity]))
        inputs[identity] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    result = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(identity) for identity in identities], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(result['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 8 or study.summary['bound_evaluations'] != 16:
            raise ValueError('all eight planned raw forecast comparisons must complete')
        rolling = [row for row in study.input('prior')['rows'] if row['kind'] == 'rolling']
        rows = []
        for identity in study.tasks:
            row = study.artifact(identity, 'raw-accuracy.json')
            if (row != study.envelope(identity)['result'] or row['identity'] != identity
                    or row['navigation_fits'] or row['scientific_decision'] != 'abstain'):
                raise ValueError('sealed raw forecast comparison differs')
            rows.append(row)
        result = encoded(dict(rolling=rolling, turn_and_steady=rows, source_recordings=1,
            navigation_fits=0, manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'], scientific_decision='abstain'))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
