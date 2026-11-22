# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit training-only warnings against sealed raw predictions on ESA 187."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .esa_height_error_transfer import DOCS, LAWS, PARENT, PARENT_MANIFEST, PARENT_SUMMARY
from .esa_raw_accuracy import ID as RAW_ID, RESULT as RAW_REPORT
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-training-warning-v1-20261121'
SCOPE = 'Earlier-only accuracy warnings across twelve ESA 187 windows'
PLAN = DOCS + 'ESA_TRAINING_WARNING_PLAN.md'
RESULT = DOCS + 'esa-training-warning.json'
RAW_SHA = 'ae6bf27a654eb998c79b47d13fbbe1ec3ebe7fa0c1077a868a862ea0139ca0de'


def training_input(forecast, observations):
    cut = forecast['training_epochs']
    times = observations['times_s']
    observed = observations['coordinates']
    if (type(cut) is not int or cut < 2 or len(times) != cut or len(observed) != cut
            or len(forecast['times_s']) <= cut or len(forecast['coordinates']) != len(forecast['times_s'])
            or forecast['prediction_receiver_positions_used'] is not False
            or any(not math.isclose(a, b, rel_tol=0., abs_tol=1e-8)
                   for a, b in zip(times, forecast['times_s'][:cut], strict=True))):
        raise ValueError('exact earlier observations must align with the training clock')
    return dict(times_s=times, observed=observed, predicted=forecast['coordinates'][:cut])


def contingency(pairs):
    names = {(False, False): 'pass_without_warning', (True, False): 'pass_with_warning',
             (False, True): 'failure_without_warning', (True, True): 'failure_with_warning'}
    counts = dict.fromkeys(names.values(), 0)
    counts['unavailable'] = 0
    for warning, failure in pairs:
        counts[names.get((warning, failure), 'unavailable')] += 1
    return counts


def task_for(identity):
    return dict(identity=identity, input_key=identity, payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=0))


def evaluate(task, context):
    from .airquantumgrav_scoring import receiver_errors
    from .ilvis0_forecast_error_transfer import score
    from .ilvis0_prediction_observed import accuracy_screen

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    earlier = json.loads(context.input_path().read_bytes())
    if (declared != task_for(identity) or context.manifest['scope'] != SCOPE
            or earlier['identity'] != identity or set(earlier['laws']) != set(LAWS)):
        raise ValueError('exact earlier-only warning task required')
    laws = {}
    for law in LAWS:
        data = earlier['laws'][law]
        if data is None:
            laws[law] = None
            continue
        context.charge(bound_calls=1, bound_steps=0)
        errors = receiver_errors(data['predicted'], data['observed'])
        metrics = score(data['times_s'], errors)
        limits = accuracy_screen(metrics)
        laws[law] = dict(warning=not limits['passed'], score=metrics, limits=limits,
                         training_reports=len(errors), source=data['source'])
    result = dict(identity=identity, laws=laws, later_scores_used=False,
                  scientific_decision='abstain', passed=True)
    context.save('training-warning.json', result)
    return result


def original_training(study):
    if (study.completion['manifest_sha256'], study.completion['summary_sha256']) != (PARENT_MANIFEST, PARENT_SUMMARY):
        raise ValueError('exact archived 800-report parent required')
    binding = study.input('saved-input-binding')
    rows = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(rows) != 800 or binding['training_epochs'] != 800:
        raise ValueError('complete earlier receiver record required')
    return dict(times_s=[row['time_s'] - binding['time_origin_s'] for row in rows],
        coordinates=[[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]
                     for row in rows])


def case_sources(prior):
    rows = {row['identity']: {law: row['laws'][law]['source'] for law in LAWS} for row in prior['rolling']}
    rows.update({row['identity']: {law: dict(row['laws'][law]['adjusted']['source'],
        raw_forecast_sha256=row['laws'][law]['raw_forecast_sha256']) for law in LAWS}
        for row in prior['turn_and_steady']})
    if len(rows) != 12:
        raise ValueError('all twelve original forecast identities required')
    return rows


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen warning audit')
    saved = (root / RAW_REPORT).read_bytes()
    if digest(saved) != RAW_SHA:
        raise ValueError('exact raw accuracy report required')
    prior = json.loads(saved)
    selections = case_sources(prior)
    records = {identity: dict(identity=identity, laws={}) for identity in selections}
    prefixes = sorted({case['study'] for laws in selections.values() for case in laws.values()})
    with closing(ClosedStudy(root, 'data/' + RAW_ID)) as raw:
        if any(prior[key] != raw.completion[key] for key in ('manifest_sha256', 'summary_sha256')):
            raise ValueError('raw accuracy report must match its sealed completion')
        for prefix in prefixes:
            with closing(ClosedStudy(root, prefix, store=raw.store)) as original:
                for identity, laws in selections.items():
                    for law, source in laws.items():
                        if source['study'] != prefix:
                            continue
                        if prefix == PARENT:
                            archive = original.input('saved-' + law + '-forecast', raw=True)
                            observations = original_training(original)
                        else:
                            key = source.get('identity', law)
                            archive = original.artifact(key, 'forecast.json', raw=True)
                            observations = original.artifact(key, 'training-observations.json')
                        sha = digest(archive)
                        if (source.get('raw_forecast_sha256', sha) != sha
                                or any(source.get(key, original.completion[key]) != original.completion[key]
                                       for key in ('manifest_sha256', 'summary_sha256'))):
                            raise ValueError('earlier fitted path must match selected later forecast')
                        records[identity]['laws'][law] = dict(training_input(json.loads(archive), observations),
                            source=dict(source, raw_forecast_sha256=sha))
    if any(set(row['laws']) != set(LAWS) for row in records.values()):
        raise ValueError('all chosen earlier fits must be represented')
    directory.mkdir(parents=True)
    inputs = {'plan': PLAN, 'later-outcomes': RAW_REPORT}
    for identity, material in records.items():
        path = directory / (identity + '.json')
        atomic(path, encoded(material))
        inputs[identity] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(identity) for identity in selections], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 12:
            raise ValueError('all twelve warning records must be sealed before comparison')
        warnings = {}
        for identity in study.tasks:
            row = study.artifact(identity, 'training-warning.json')
            if (row != study.envelope(identity)['result'] or row['identity'] != identity
                    or row['later_scores_used'] or row['scientific_decision'] != 'abstain'):
                raise ValueError('sealed training-only result differs')
            warnings[identity] = row['laws']
        if study.summary['bound_evaluations'] != sum(case is not None for laws in warnings.values() for case in laws.values()):
            raise ValueError('each evaluated warning must have its own charge')
        actual = study.input('later-outcomes')
        later = {row['identity']: {law: row['laws'][law]['limits']['passed'] for law in LAWS}
                 for row in actual['rolling']}
        later.update({row['identity']: {law: row['laws'][law]['raw']['limits']['passed'] for law in LAWS}
                      for row in actual['turn_and_steady']})
        if set(later) != set(warnings):
            raise ValueError('warning and later outcome identities differ')
        rows = {identity: {law: dict(earlier=cases[law], later_passed=later[identity][law]) for law in LAWS}
                for identity, cases in warnings.items()}
        counts = {law: contingency([(cases[law]['earlier']['warning'] if cases[law]['earlier'] else None,
            not cases[law]['later_passed'] if cases[law]['later_passed'] is not None else None)
            for cases in rows.values()]) for law in LAWS}
        result = encoded(dict(rows=rows, counts_by_law=counts, source_recordings=1, scientific_decision='abstain',
            manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
