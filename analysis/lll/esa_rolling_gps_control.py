# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare archived inertial forecasts with fixed GPS-only extrapolations."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .esa_height_error_transfer import CUTS, DOCS, HORIZON, LAWS, PARENT, PARENT_MANIFEST, PARENT_SUMMARY, extract
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-rolling-gps-control-v1-20261121'
SCOPE = 'Matched earlier-only GPS extrapolation on ESA development recording 187'
PLAN = DOCS + 'ESA_ROLLING_GPS_CONTROL_PLAN.md'
RESULT = DOCS + 'esa-rolling-gps-control.json'
PRIOR = DOCS + 'ROLLING_ORIGIN_400_TURN_CONTROL.json'
PRIOR_SHA = '850515f476ff56c56d88f69f7fef1df737657f6ecaeb478456756612be58344a'
NEW_CUTS = (200, 600, 800)
RULES = ('fixed', 'turn')


def task_for(cut):
    return dict(identity=str(cut), input_key=f'{cut}-earlier', payload={'cut': cut},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=0))


def evaluate(task, context):
    from .esa_rolling_origin_400_score import score_raw
    from .receiver_only_constant_turn import forecast_constant_turn
    from .receiver_only_velocity import forecast_velocity

    cut = task['payload']['cut']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if cut not in NEW_CUTS or declared != task_for(cut) or context.manifest['scope'] != SCOPE:
        raise ValueError('exact new GPS-only comparison required')
    earlier = json.loads(context.input_path().read_bytes())
    times, velocities = earlier['training_times'], earlier['training_velocity']
    future, coordinate = earlier['future_times'], earlier['last_coordinate']
    if earlier['cut'] != cut or len(times) != 60 or len(velocities) != 60 or len(future) != HORIZON:
        raise ValueError('exact earlier and forecast support required')
    context.charge(bound_calls=1, bound_steps=0)
    fixed = forecast_velocity(times[-1], coordinate, velocities[-1], future)
    context.charge(bound_calls=1, bound_steps=0)
    turn = forecast_constant_turn(times, velocities, coordinate, future)
    predictions = dict(fixed=fixed, turn=turn)
    for name, prediction in predictions.items():
        if prediction['imu_samples_used'] or prediction['later_positions_used']:
            raise ValueError('receiver-only forecast must use earlier data alone')
        context.save(name + '-forecast.json', dict(cut=cut, future_times=future,
                     coordinates=prediction['coordinates'].tolist(), later_positions_used=False))
    scoring = json.loads(context.input_path(f'{cut}-scoring').read_bytes())
    if scoring['cut'] != cut or scoring['times'] != future:
        raise ValueError('later receiver positions must match the forecast clock')
    result = {name: score_raw(prediction['coordinates'], scoring['coordinates'])
              for name, prediction in predictions.items()}
    result.update(cut=cut, navigation_fits=0, scientific_decision='abstain', passed=True)
    context.save('gps-scores.json', result)
    return result


def prepare(root):
    from .airquantumgrav_geographic_report import error_metrics
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen GPS-only comparison')
    cuts = extract(root)
    prior_raw = (root / PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('400-report GPS-only control hash differs')
    prior = json.loads(prior_raw)
    if (prior['fit_manifest_sha256'] != cuts[400, 'increment']['forecast']['manifest_sha256']
            or prior['parent_manifest_sha256'] != PARENT_MANIFEST
            or prior['earlier_receiver_reports'] != 400 or prior['later_receiver_reports'] != HORIZON
            or not prior['no_imu_samples'] or prior['later_positions_used_for_forecast']):
        raise ValueError('400-report GPS-only control does not match the frozen split')
    with closing(ClosedStudy(root, PARENT)) as source:
        if (source.completion['manifest_sha256'] != PARENT_MANIFEST
                or source.completion['summary_sha256'] != PARENT_SUMMARY):
            raise ValueError('receiver archive no longer matches the development parent')
        origin = source.input('saved-input-binding')['time_origin_s']
        rows = json.loads(gzip.decompress(source.input('scoring', raw=True)))

    def coordinate(row):
        return [math.radians(row['latitude_deg']), math.radians(row['longitude_deg']), row['height_m']]

    def times(rows):
        return [row['time_s'] - origin for row in rows]

    artifacts = {'imu-scores': {str(cut): {
        law: dict(source=cuts[cut, law]['forecast'], metrics=error_metrics(cuts[cut, law]['errors']))
        for law in LAWS} for cut in CUTS}}
    for cut in NEW_CUTS:
        training, withheld = rows[cut - 60:cut], rows[cut:cut + HORIZON]
        future = times(withheld)
        if any(len(cuts[cut, law]['times']) != HORIZON or any(abs(a - b) > 1e-8
               for a, b in zip(future, cuts[cut, law]['times'], strict=True)) for law in LAWS):
            raise ValueError('GPS-only and inertial forecasts require the same receiver clock')
        artifacts[f'{cut}-earlier'] = dict(cut=cut, training_times=times(training), future_times=future,
            last_coordinate=coordinate(training[-1]),
            training_velocity=[[row[f'{axis}_mps'] for axis in ('north', 'east', 'up')] for row in training])
        artifacts[f'{cut}-scoring'] = dict(cut=cut, times=future, coordinates=[coordinate(row) for row in withheld])

    directory.mkdir(parents=True)
    inputs = {'plan': PLAN, 'saved-400-control': PRIOR}
    for key, value in artifacts.items():
        path = directory / (key + '.json')
        atomic(path, encoded(value))
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(cut) for cut in NEW_CUTS], sources=source_closure(root, [adapter, PLAN]),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if (not study.summary['passed'] or study.summary['completed'] != len(NEW_CUTS)
                or study.summary['bound_evaluations'] != 2 * len(NEW_CUTS)):
            raise ValueError('complete charged comparison required')
        prior = study.input('saved-400-control')
        imu = study.input('imu-scores')
        rows = []
        for cut in CUTS:
            if cut == 400:
                baseline = dict(fixed=prior['fixed_velocity_score'], turn=prior['constant_turn_score'])
            else:
                key = str(cut)
                baseline = study.artifact(key, 'gps-scores.json')
                if (baseline != study.envelope(key)['result'] or baseline['cut'] != cut
                        or baseline['scientific_decision'] != 'abstain' or baseline['navigation_fits']
                        or any(study.artifact(key, name + '-forecast.json')['later_positions_used']
                               for name in RULES)):
                    raise ValueError('saved forecast boundary or score is inconsistent')
            rows.append(dict(cut=cut, gps={name: baseline[name]['metrics'] for name in RULES},
                inertial=imu[str(cut)], reused_gps_scores=cut == 400))
        result = encoded(dict(rows=rows, source_recordings=1, withheld_positions_per_cut=HORIZON,
            navigation_fits=0, scientific_decision='abstain', prior_400_sha256=PRIOR_SHA,
            manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
