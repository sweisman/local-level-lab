# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply a fixed descriptive accuracy screen to archived ESA forecasts."""

from contextlib import closing
import json
from pathlib import Path

from .esa_height_error_transfer import CUTS, DOCS, HORIZON, LAWS, extract
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-absolute-accuracy-v1-20261121'
SCOPE = 'Fixed absolute accuracy check on twelve saved ESA 187 windows'
PLAN = DOCS + 'ESA_ABSOLUTE_ACCURACY_PLAN.md'
RESULT = DOCS + 'esa-absolute-accuracy.json'
WINDOW_CLASSES = ('rolling', 'turn', 'steady')
SOURCES = (
    ('turn', 'esa-repeat-turn-forecast-v2', 'input-preflight', 'esa-repeat-turn-forecast-evidence',
     '6607441aa0ae1cf43ae263a39eb4240e552d447ffe7b4a5774995cd8fe96fd3e',
     'ae1fa59746e4f57cb539595afbde23d71899a7fdde73af438976c82daf3d988e'),
    ('steady', 'esa-straight-control-forecast-v1', 'bundle', 'esa-straight-control-evidence',
     '81785223db3c55f9723d921d5112223ac8c2367d872dc5aea12cd61779a8b7f8',
     'af3c50ac7841ad3ab91ee811ebe8e51e216a8e7e37673bfa2f228d0b9bf4b19c'),
)


def describe(times, errors):
    from .ilvis0_forecast_error_transfer import score
    from .ilvis0_prediction_observed import accuracy_screen

    if len(times) != HORIZON or len(errors) != HORIZON:
        raise ValueError('exactly 120 matched receiver errors required')
    metrics = score(times, errors)
    return dict(score=metrics, limits=accuracy_screen(metrics))


def task_for(identity):
    return dict(identity=identity, input_key=identity, payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=0))


def evaluate(task, context):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != task_for(identity):
        raise ValueError('exact accuracy audit task required')
    data = json.loads(context.input_path().read_bytes())
    kind = data['kind']
    if kind not in WINDOW_CLASSES or data['identity'] != identity or set(data['laws']) != set(LAWS):
        raise ValueError('one window and both inertial error laws required')
    outcomes = {}
    for law in LAWS:
        case = data['laws'][law]
        context.charge(bound_calls=1, bound_steps=0)
        if kind == 'rolling':
            errors = case['errors']
        else:
            observed = np.asarray(data['coordinates'], dtype=float)
            predicted = np.asarray(case['mean'], dtype=float)
            legacy = observed - predicted
            legacy[:, 1] = longitude_residual(legacy[:, 1])
            legacy *= physical_metric([case['anchor']])[0]
            rms = np.sqrt(np.mean(legacy**2, axis=0))
            if not np.allclose(rms, case['legacy_rms'], rtol=1e-12, atol=1e-10):
                raise ValueError('saved forecast and receiver positions do not reproduce the original RMS')
            errors = receiver_errors(predicted, observed).tolist()
        outcomes[law] = dict(describe(data['times'], errors), source=case['source'])
    result = dict(identity=identity, kind=kind, laws=outcomes, passed=True,
                  navigation_fits=0, scientific_decision='abstain')
    context.save('absolute-accuracy.json', result)
    return result


def released_windows(root):
    from .esa_repeat_turn_release import receiver_positions
    from .esa_repeat_turn_scoring import VERSION

    records, windows, inputs = {}, {}, {}
    receiver_metadata = None
    for kind, study_id, input_key, folder, release_sha, score_sha in SOURCES:
        prefix = 'data/' + study_id
        paths = [DOCS + folder + '/' + file for file in ('receiver-release.json', 'receiver-scores.json')]
        raw = [(root / path).read_bytes() for path in paths]
        if [digest(value) for value in raw] != [release_sha, score_sha]:
            raise ValueError('exact previous forecast release and scoring receipts required')
        receipt, scores = map(json.loads, raw)
        if (scores['release_sha256'] != release_sha or scores['protected_reads']
                or len(receipt['primary']) != 8 or receipt['recovery_sha256'] is not None):
            raise ValueError('exact original eight released forecasts required')
        if receiver_metadata is not None and receiver_metadata != receipt['receiver_metadata']:
            raise ValueError('turn and steady receiver metadata differ')
        receiver_metadata = receipt['receiver_metadata']
        inputs.update({kind + '-release': paths[0], kind + '-previous-scores': paths[1]})
        with closing(ClosedStudy(root, prefix)) as study:
            if (study.completion['manifest_sha256'] != receipt['manifest_sha256']
                    or receipt['closures'] != {prefix: digest(encoded(study.completion))}):
                raise ValueError('saved closed study does not match the release')
            local = {w['window']['first_index']: w for w in study.input(input_key)['windows']}
            if len(local) != 4 or set(local) & set(windows):
                raise ValueError('four distinct windows required for each flight phase')
            windows.update(local)
            for case in receipt['primary']:
                identity, index, law, sha = (case[k] for k in ('identity', 'first_index', 'law', 'forecast_sha256'))
                prior = scores['scores'][identity]
                outcome = receipt['outcomes'][identity]
                raw_forecast = study.artifact(identity, 'sealed-receiver-forecast.json', raw=True)
                forecast = json.loads(raw_forecast)
                release_window = local[index]
                if (case['state'] != 'sealed' or outcome['study'] != prefix or not outcome['passed']
                        or outcome['result_sha256'] != study.envelope(identity)['result_sha256']
                        or sha != digest(raw_forecast) or sha != prior['forecast_sha256']
                        or forecast['policy'] != VERSION or forecast['law'] != law or prior['law'] != law
                        or prior['receiver_used_for_training'] is not False
                        or forecast['training_sha256'] != release_window['training_receiver_sha256']
                        or forecast['times_s'] != release_window['query_times_s'][-HORIZON:]):
                    raise ValueError('archived chosen forecast or scoring support differs')
                key = f'{kind}-{index}'
                window = records.setdefault(key, dict(identity=key, kind=kind, index=index,
                                                        times=forecast['times_s'], laws={}))
                if law in window['laws'] or window['times'] != forecast['times_s']:
                    raise ValueError('both distinct laws require identical receiver support')
                window['laws'][law] = dict(mean=forecast['mean_geodetic'], anchor=forecast['anchor_geodetic'],
                    legacy_rms=prior['physical_rms_neu_m'], source=dict(identity=identity, study=prefix, forecast_sha256=sha))
    if len(records) != 8 or any(set(case['laws']) != set(LAWS) for case in records.values()):
        raise ValueError('all sixteen selected forecasts are required')
    observations = receiver_positions(root, windows, expected_metadata=receiver_metadata)
    for window in records.values():
        times, coordinates = observations[window['index']]
        if times != window['times']:
            raise ValueError('scoring clock differs from the saved primary forecasts')
        window['coordinates'] = coordinates
    return records, inputs


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen accuracy audit')
    cuts = extract(root)
    records, inputs = released_windows(root)
    for cut in CUTS:
        key = f'rolling-{cut}'
        times = cuts[cut, LAWS[0]]['times']
        laws = {law: dict(errors=cuts[cut, law]['errors'], source=cuts[cut, law]['forecast']) for law in LAWS}
        if any(cuts[cut, law]['times'] != times for law in LAWS):
            raise ValueError('both rolling forecast laws must share scoring support')
        records[key] = dict(identity=key, kind='rolling', index=cut, times=times, laws=laws)
    directory.mkdir(parents=True)
    inputs['plan'] = PLAN
    identities = sorted(records)
    for identity in identities:
        path = directory / (identity + '.json')
        atomic(path, encoded(records[identity]))
        inputs[identity] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(identity) for identity in identities], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 12 or study.summary['bound_evaluations'] != 24:
            raise ValueError('complete charged audit required')
        rows = []
        for identity in study.tasks:
            row = study.artifact(identity, 'absolute-accuracy.json')
            if (row != study.envelope(identity)['result'] or identity != row['identity']
                    or row['scientific_decision'] != 'abstain' or row['navigation_fits']):
                raise ValueError('sealed absolute accuracy result is inconsistent')
            rows.append(row)
        by_kind = {}
        for kind in WINDOW_CLASSES:
            group = [row for row in rows if row['kind'] == kind]
            if len(group) != 4:
                raise ValueError('four windows per class required')
            by_kind[kind] = dict(windows=4, passing_both_laws=sum(all(case['limits']['passed']
                for case in row['laws'].values()) for row in group))
        result = encoded(dict(rows=rows, by_kind=by_kind, source_recordings=1, navigation_fits=0,
            scientific_decision='abstain', calibrated_coverage=False,
            manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
