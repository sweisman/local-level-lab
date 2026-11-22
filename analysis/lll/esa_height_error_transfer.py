# SPDX-License-Identifier: AGPL-3.0-or-later
"""Height-only error transfer across saved chronological cuts of ESA 187."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path
from statistics import median

from .ilvis0_forecast_error_transfer import predict_error, score
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-height-error-transfer-v1-20261120'
SCOPE = 'Earlier-only height error transfer along ESA development flight 187'
DOCS = 'docs/prediction-observed-development/'
PLAN = DOCS + 'ESA_HEIGHT_ERROR_TRANSFER_PLAN.md'
RESULT = DOCS + 'esa-height-error-transfer.json'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
PARENT_MANIFEST = '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
PARENT_SUMMARY = '1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d'
SOURCE = 'esa-99f1530c3eda4318'
REPORTS = {
    200: ('ROLLING_ORIGIN_200_RAW_RESULT.json', 'ba314eb44f8d78d8b29167681f77fd14e3b3d1f9b30c8a5332578b6240454d62'),
    400: ('ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json', '31ecc2f2ea657aa2be2b63f83656e5fda35decfcd17247145766771dea5294e6'),
    600: ('training-split-score.json', '4a6fa5aeea168b2fb2ad6a65047163dca450907138ca4f29a242509008f41974'),
}
LAWS = ('increment', 'point')
CUTS = (200, 400, 600, 800)
HORIZON = 120


def task_for(identity):
    return dict(identity=identity, input_key=identity + '-earlier', payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=0))


def evaluate(task, context):
    import numpy as np

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared != task_for(identity) or context.manifest['scope'] != SCOPE:
        raise ValueError('exact ESA diagnostic task required')
    earlier = json.loads(context.input_path().read_bytes())
    if (earlier['identity'] != identity or 'later_errors' in earlier
            or earlier['last_earlier_time'] >= earlier['first_later_time']
            or len(earlier['elapsed']) != HORIZON or len(earlier['later_elapsed']) != HORIZON):
        raise ValueError('separate chronological forecast periods with 120 receiver reports required')
    context.charge(bound_calls=1, bound_steps=0)
    times = earlier['later_elapsed']
    correction, coefficient = predict_error(earlier['elapsed'], earlier['errors'], times,
                                             height_only=True)
    context.save('earlier-only-error-model.json', dict(identity=identity, **coefficient,
                 expected_later_error_m=correction.tolist(), later_errors_used=False))
    later = json.loads(context.input_path(identity + '-scoring').read_bytes())
    measured = np.asarray(later['errors'], float)
    if later['identity'] != identity or measured.shape != correction.shape or not np.isfinite(measured).all():
        raise ValueError('matching finite later scoring input required')
    adjusted = measured - correction
    if not np.array_equal(measured[:, :2], adjusted[:, :2]):
        raise ValueError('height correction changed horizontal scores')
    outcome = dict(identity=identity, earlier_forecast=earlier.get('forecast'),
                   later_forecast=later.get('forecast'), receiver_reports=HORIZON,
                   raw=score(times, measured), corrected=score(times, adjusted),
                   navigation_fits=0, scientific_decision='abstain', passed=True)
    context.save('height-transfer-score.json', outcome)
    return outcome


def saved_cut(forecast, cut, times, receiver):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    count = len(forecast['times_s'])
    stop = cut + HORIZON
    if (forecast['training_epochs'] != cut or forecast['prediction_epochs'] != count - cut
            or count < stop or count > len(times)
            or forecast['prediction_receiver_positions_used'] is not False
            or forecast['continuous_propagation_without_gps_reset'] is not True
            or not np.allclose(forecast['times_s'], times[:count], rtol=0., atol=1e-8)):
        raise ValueError('saved forecast must align with receiver sequence and use only earlier positions')
    support = forecast['times_s'][cut:stop]
    origin = forecast['times_s'][cut - 1]
    errors = receiver_errors(forecast['coordinates'][cut:stop], receiver[cut:stop])
    return dict(times=support, elapsed=[time - origin for time in support], errors=errors.tolist())


def extract(root):
    import numpy as np

    cuts = {}
    with closing(ClosedStudy(root, PARENT)) as source:
        binding = source.input('saved-input-binding')
        if (source.completion['manifest_sha256'] != PARENT_MANIFEST
                or source.completion['summary_sha256'] != PARENT_SUMMARY or binding['source_id'] != SOURCE
                or source.input('recipe')['model'] != 'sphere_rotating'):
            raise ValueError('exact closed ESA development parent required')
        rows = json.loads(gzip.decompress(source.input('scoring', raw=True)))
        times = [row['time_s'] - binding['time_origin_s'] for row in rows]
        receiver = [[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']),
                     row['height_m']] for row in rows]
        for law in LAWS:
            fit = source.input('saved-' + law + '-fit')
            cut = saved_cut(source.input('saved-' + law + '-forecast'), 800, times, receiver)
            cuts[800, law] = dict(cut, forecast=dict(study=PARENT, law=law,
                manifest_sha256=PARENT_MANIFEST, summary_sha256=PARENT_SUMMARY, cut=800,
                passed=bool(fit['converged'] and fit['stopping_rule_verified'] and fit['stability_verified'])))
    for cut, (filename, sha) in REPORTS.items():
        data = (root / DOCS / filename).read_bytes()
        if digest(data) != sha:
            raise ValueError('exact saved raw-score source required')
        report = json.loads(data)
        with closing(ClosedStudy(root, report['fit_study'])) as study:
            parent = study.input('parent_identity')
            if (parent['source_id'] != SOURCE or parent['manifest_sha256'] != PARENT_MANIFEST
                    or parent['summary_sha256'] != PARENT_SUMMARY
                    or study.completion['manifest_sha256'] != report['fit_manifest_sha256']
                    or study.completion['summary_sha256'] != report['fit_summary_sha256']
                    or study.input('recipe')['model'] != 'sphere_rotating'):
                raise ValueError('exact earlier development forecast and scoring receipt required')
            for law in LAWS:
                forecast = saved_cut(study.artifact(law, 'forecast.json'), cut, times, receiver)
                if cut == 200:
                    prior = report['scored_laws'][law]['raw_score']['neu_errors_m']
                elif cut == 400:
                    prior = report['laws'][law]['score']['raw']['neu_errors_m']
                else:
                    prior = report['scored_laws'][law]['raw_neu_errors_m'][:HORIZON]
                if not np.allclose(forecast['errors'], prior, rtol=0., atol=1e-8):
                    raise ValueError('receiver errors differ from archived raw forecast scores')
                cuts[cut, law] = dict(forecast, forecast=dict(study=report['fit_study'], law=law,
                    manifest_sha256=report['fit_manifest_sha256'], summary_sha256=report['fit_summary_sha256'],
                    cut=cut, passed=study.rows[law]['passed']))
    return cuts


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('use the existing frozen transfer study')
    cuts = extract(root)
    directory.mkdir(parents=True)
    tasks = []
    inputs = {'plan': PLAN, **{f'cut-{cut}-score-receipt': DOCS + file for cut, (file, _) in REPORTS.items()}}
    for first, second in zip(CUTS[:-1], CUTS[1:], strict=True):
        for law in LAWS:
            identity = f'{first}-to-{second}-{law}'
            early, late = cuts[first, law], cuts[second, law]
            materials = {'earlier': dict(identity=identity, elapsed=early['elapsed'],
                later_elapsed=late['elapsed'], last_earlier_time=early['times'][-1],
                first_later_time=late['times'][0], errors=early['errors'], forecast=early['forecast']),
                'scoring': dict(identity=identity, errors=late['errors'], forecast=late['forecast'])}
            for name, value in materials.items():
                key = identity + '-' + name
                path = directory / (key + '.json')
                atomic(path, encoded(value))
                inputs[key] = path.relative_to(root).as_posix()
            tasks.append(task_for(identity))
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    result = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=tasks, sources=source_closure(root, [adapter, PLAN]), workers=1, threads=1,
        maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=result['limits']), sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 6 or study.summary['bound_evaluations'] != 6:
            raise ValueError('all six charged transfers must complete')
        rows = []
        for identity in study.tasks:
            row = study.artifact(identity, 'height-transfer-score.json')
            prior = study.artifact(identity, 'earlier-only-error-model.json')
            if (row != study.envelope(identity)['result'] or row['scientific_decision'] != 'abstain'
                    or row['navigation_fits'] or prior['later_errors_used']
                    or any(n or e for n, e, _ in prior['expected_later_error_m'])):
                raise ValueError('saved score must bind the preceding height-only correction')
            rows.append(row)
        raw_values = [row['raw']['vertical_rms_m'] for row in rows]
        corrected_values = [row['corrected']['vertical_rms_m'] for row in rows]
        output = encoded(dict(rows=rows, source_id=SOURCE, recordings=1,
            improved=sum(new < old for old, new in zip(raw_values, corrected_values, strict=True)),
            raw_median_height_rms_m=median(raw_values), corrected_median_height_rms_m=median(corrected_values),
            manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256'],
            scientific_decision='abstain'))
    _write_equal(root / RESULT, output)
    print(digest(output))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    action = parser.parse_args().action
    {'prepare': prepare, 'collect': collect}[action](Path.cwd())
