# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed raw and earlier-adjusted ESA paths on identical support."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .esa_absolute_accuracy import describe
from .esa_height_error_transfer import CUTS, DOCS, HORIZON, LAWS, PARENT, PARENT_MANIFEST, PARENT_SUMMARY
from .esa_training_warning import RAW_REPORT, RAW_SHA
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-matched-conditioning-v1-20261121'
SCOPE = 'Same-support raw and earlier-conditioned ESA 187 forecast comparison'
PLAN = DOCS + 'ESA_MATCHED_CONDITIONING_PLAN.md'
RESULT = DOCS + 'esa-matched-conditioning.json'
RECEIPTS = {
    200: ('ROLLING_ORIGIN_200_CONDITIONAL_RESULT.json', 'eca1861b603193e46d2947b5ba6d0b8b48c4aa636b0df69a758167a256666796'),
    400: ('ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json', '31ecc2f2ea657aa2be2b63f83656e5fda35decfcd17247145766771dea5294e6'),
    600: ('training-split-score.json', '4a6fa5aeea168b2fb2ad6a65047163dca450907138ca4f29a242509008f41974'),
    800: ('conditional-forecast-result.json', 'b25dbe7b787f5684c01438a751bd3199d229caece97baa94c8974b676d2ac11f'),
}


def matched_positions(raw, saved, cut, law):
    raw_path = raw['coordinates']
    later = raw_path[cut:]
    adjusted = saved['conditional_receiver_mean']
    if (raw['training_epochs'] != cut or saved['training_epochs'] != cut
            or raw['prediction_epochs'] != len(later) or saved['prediction_epochs'] != len(later)
            or raw['prediction_receiver_positions_used'] is not False
            or saved['later_receiver_values_used'] is not False or saved['optimization_performed'] is not False
            or saved['law'] != law or saved['times_s'] != raw['times_s']
            or len(raw['times_s']) != len(raw_path) or len(adjusted) != len(later) or len(later) < HORIZON
            or (saved['raw_coordinates'] != raw_path and saved['raw_coordinates'] != later)):
        raise ValueError('conditioner must bind the same earlier fit, instrument law and receiver clock')
    return later[:HORIZON], adjusted[:HORIZON]


def task_for(identity):
    return dict(identity=identity, input_key=identity, payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=0))


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    data = json.loads(context.input_path().read_bytes())
    if declared != task_for(identity) or context.manifest['scope'] != SCOPE or data['identity'] != identity:
        raise ValueError('exact saved conditioning comparison required')
    result = dict(identity=identity, cut=data['cut'], law=data['law'], raw=data['prior_raw'],
                  adjusted=None, reason=data.get('reason'), scientific_decision='abstain', passed=True)
    if result['reason'] is None:
        context.charge(bound_calls=1, bound_steps=0)
        errors = [receiver_errors(data[key], data['receiver']) for key in ('raw', 'adjusted')]
        raw, adjusted = [describe(data['times'], values) for values in errors]
        if raw['limits'] != data['prior_raw']['limits'] or any(not math.isclose(value,
                data['prior_raw']['score'][key], rel_tol=1e-12, abs_tol=1e-9) for key, value in raw['score'].items()):
            raise ValueError('the raw score must reproduce the earlier same-support audit')
        if 'saved_adjusted_errors' in data and not np.allclose(errors[1], data['saved_adjusted_errors'], rtol=0., atol=1e-8):
            raise ValueError('the adjusted forecast must reproduce the previous score receipt')
        result.update(raw=raw, adjusted=adjusted, source=data['source'])
    context.save('matched-conditioning.json', result)
    return result


def extract(root, prior):
    from .esa_conditional_forecast_report import TASK

    records = {}
    rolling = {row['identity']: row['laws'] for row in prior['rolling']}
    with closing(ClosedStudy(root, PARENT)) as parent:
        if (parent.completion['manifest_sha256'], parent.completion['summary_sha256']) != (PARENT_MANIFEST, PARENT_SUMMARY):
            raise ValueError('exact archived receiver parent required')
        binding = parent.input('saved-input-binding')
        rows = json.loads(gzip.decompress(parent.input('scoring', raw=True)))
        for cut in CUTS:
            name, sha = RECEIPTS[cut]
            receipt_bytes = (root / DOCS / name).read_bytes()
            if digest(receipt_bytes) != sha:
                raise ValueError('exact original conditioning score receipt required')
            receipt = json.loads(receipt_bytes)
            observations = rows[cut:cut + HORIZON]
            times = [row['time_s'] - binding['time_origin_s'] for row in observations]
            receiver = [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]
                        for row in observations]
            for law in LAWS:
                identity = f'{cut}-{law}'
                records[identity] = dict(identity=identity, cut=cut, law=law, times=times, receiver=receiver,
                    prior_raw=rolling[f'rolling-{cut}'][law])
            if cut == 800:
                with closing(ClosedStudy(root, receipt['study'], store=parent.store)) as condition:
                    raw = parent.input('saved-increment-forecast')
                    saved = condition.artifact(TASK, 'conditional-forecast.json')
                    if (condition.completion['manifest_sha256'] != receipt['manifest_sha256']
                            or condition.completion['summary_sha256'] != receipt['summary_sha256']
                            or receipt['later_receiver_values_used_for_forecast'] is not False
                            or condition.input('weighted-forecast')['coordinates'] != raw['coordinates']):
                        raise ValueError('original 800-report adjusted path must bind the archived increment fit')
                    saved.setdefault('law', 'increment')
                    if any(abs(a - b) > 1e-8 for a, b in zip(raw['times_s'][cut:cut + HORIZON], times, strict=True)):
                        raise ValueError('later receiver and sealed forecast clocks differ')
                    pair = matched_positions(raw, saved, cut, 'increment')
                    records['800-increment'].update(raw=pair[0], adjusted=pair[1], source=condition.prefix)
                    records['800-point']['reason'] = 'No matched sealed earlier-conditioned point-law path'
            else:
                if receipt['parent_manifest_sha256'] != PARENT_MANIFEST:
                    raise ValueError('conditioned score must use the same receiver history')
                with closing(ClosedStudy(root, receipt['fit_study'], store=parent.store)) as fit, closing(
                        ClosedStudy(root, receipt['conditioning_study'], store=parent.store)) as condition:
                    for prefix, study in (('fit', fit), ('conditioning', condition)):
                        if any(receipt[f'{prefix}_{key}'] != study.completion[key]
                               for key in ('manifest_sha256', 'summary_sha256')):
                            raise ValueError('conditioning source seal differs from its score receipt')
                    for law in LAWS:
                        data = records[f'{cut}-{law}']
                        original = data['prior_raw']['source']
                        if original['study'] != fit.prefix or original['manifest_sha256'] != fit.completion['manifest_sha256']:
                            raise ValueError('raw accuracy audit must use the same selected fit')
                        raw = fit.artifact(law, 'forecast.json')
                        saved = condition.artifact(law, 'conditional-forecast.json')
                        outcome = condition.envelope(law)['result']
                        if (outcome['passed'] is not True or outcome['optimization_performed'] is not False
                                or outcome['later_receiver_values_used'] is not False):
                            raise ValueError('sealed conditioning task must have passed with earlier data alone')
                        saved.setdefault('optimization_performed', outcome['optimization_performed'])
                        if any(abs(a - b) > 1e-8 for a, b in zip(raw['times_s'][cut:cut + HORIZON], times, strict=True)):
                            raise ValueError('later receiver and sealed forecast clocks differ')
                        positions = matched_positions(raw, saved, cut, law)
                        archived_score = (receipt['scored_laws'][law]['conditional_neu_errors_m'][:HORIZON]
                            if cut == 600 else receipt['laws'][law]['score']['conditional']['neu_errors_m'])
                        data.update(raw=positions[0], adjusted=positions[1], saved_adjusted_errors=archived_score,
                                    source=condition.prefix)
    return records


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen conditioning study')
    source = (root / RAW_REPORT).read_bytes()
    if digest(source) != RAW_SHA:
        raise ValueError('exact completed raw audit required')
    records = extract(root, json.loads(source))
    directory.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': RAW_REPORT, **{f'receipt-{cut}': DOCS + binding[0]
                                                   for cut, binding in RECEIPTS.items()}}
    for identity, record in records.items():
        path = directory / (identity + '.json')
        atomic(path, encoded(record))
        inputs[identity] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(identity) for identity in records], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 8:
            raise ValueError('all eight rolling identities must be sealed')
        rows = []
        for identity in study.tasks:
            row = study.artifact(identity, 'matched-conditioning.json')
            if (row != study.envelope(identity)['result'] or row['identity'] != identity
                    or row['scientific_decision'] != 'abstain'):
                raise ValueError('sealed comparison disagrees with saved result')
            rows.append(row)
        if study.summary['bound_evaluations'] != sum(row['adjusted'] is not None for row in rows):
            raise ValueError('every comparison must have its own charge')
        result = encoded(dict(rolling=rows, turn_and_steady=study.input('prior')['turn_and_steady'],
            recordings=1, navigation_fits=0, scientific_decision='abstain',
            manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
