# SPDX-License-Identifier: AGPL-3.0-or-later
"""GPS-only forecast control on the sealed twenty-group NASA transfer study."""

from contextlib import closing
import gzip
from io import BytesIO
import json
from pathlib import Path


ID = 'ilvis0-remaining-gps-baseline-v2-20261120'
ORIGINAL = 'ilvis0-remaining-gps-baseline-v1-20261120'
ORIGINAL_SHA = '9cf8af0e8eee6ce1ac1c1340a26d19cd7ce602bbcc507da2b00205284bbfdae0'
PLAN = 'docs/prediction-group-transfer/REMAINING_GPS_BASELINE_V2_PLAN.md'
SCOPE = 'Forty GPS-only forecasts on unchanged retrospective NASA receiver epochs'
PARENT_REPORT = 'docs/prediction-group-transfer/remaining-verified-report.json'
PARENT_REPORT_SHA = 'e95e20ebe21d61182166e6e140371b8e3397a1f97f32ac1519c46343a82b0d4f'
ORIGINS = ('inner', 'outer')


def receiver_header(raw):
    """Read the sorted frozen receiver header without decoding IMU rows."""
    with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:
        prefix = stream.read(2**17)
    header, separator, _ = prefix.partition(b',"values":[')
    if not separator:
        raise ValueError('expected leading frozen receiver metadata within 128 KiB')
    data = json.loads(header+b'}')
    if set(data) != {'layout', 'segment_id', 'times'}:
        raise ValueError('exact archived receiver metadata required')
    return data


def evaluate(task, context):
    import numpy as np

    from .receiver_only_forecast import RADIUS_M, _wrap
    from .receiver_only_forecast_report import replay
    from .receiver_only_geodesic import forecast_geodesic

    training = json.loads(context.input_path().read_bytes())
    segment, origin = task['payload']['segment_id'], task['payload']['origin']
    if (set(training) != {'segment_id', 'group_id', 'origin', 'training_times', 'training_gps', 'future_times'}
            or (training['segment_id'], training['origin']) != (segment, origin)
            or task['identity'] != f'{segment}-{origin}' or origin not in ORIGINS):
        raise ValueError('exact separated earlier receiver input required')
    context.charge(bound_calls=1, bound_steps=0)
    forecast = forecast_geodesic(training['training_times'], training['training_gps'], training['future_times'])
    positions = forecast['coordinates']
    times = training['future_times']
    context.save('forecast.json', dict(coordinates=positions.tolist(), times=times, later_positions_used=False))
    scoring = json.loads(context.input_path(task['identity']+'-scoring').read_bytes())
    observed = np.asarray(scoring['prediction_gps'], dtype=float)
    if scoring['segment_id'] != segment or observed.shape != positions.shape or not np.all(np.isfinite(observed)):
        raise ValueError('complete separate scoring positions required')
    scale = RADIUS_M + observed[:, 2]
    errors = np.column_stack(((positions[:, 0]-observed[:, 0])*scale,
        _wrap(positions[:, 1]-observed[:, 1])*scale*np.cos(observed[:, 0]), positions[:, 2]-observed[:, 2]))
    epochs = [dict(epoch=i, time_s=float(time), north_error_m=float(north), east_error_m=float(east), up_error_m=float(up))
              for i, (time, (north, east, up)) in enumerate(zip(times, errors, strict=True))]
    context.save('epochs.json', epochs)
    return dict(passed=True, segment_id=segment, group_id=training['group_id'], origin=origin,
                horizon=len(times), gps=replay(epochs), imu=scoring['imu'], imu_samples_used=0,
                scientific_decision='abstain')


def prepare(root):
    from .ilvis0_remaining_prediction_report import STUDY, verify_closed
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing twenty-group GPS forecast freeze')
    parent = (root/PARENT_REPORT).read_bytes()
    if digest(parent) != PARENT_REPORT_SHA:
        raise ValueError('exact previously verified score ledger required')
    report = json.loads(parent)
    material = {'plan': PLAN, 'parent-report': PARENT_REPORT}
    packets = {}
    tasks = []
    with closing(ClosedStudy(root, STUDY)) as study:
        verify_closed(study)
        layouts = study.input('layouts')
        comparison = {row['segment_id']: row for row in report['rows']}
        if (report['summary_sha256'] != study.completion['summary_sha256'] or len(layouts) != 20
                or len({record['group_id'] for record in layouts}) != 20
                or set(comparison) != {record['segment_id'] for record in layouts}):
            raise ValueError('unchanged twenty group identities and scoring ledger required')
        for layout in layouts:
            segment = layout['segment_id']
            key = segment+'-common'
            common = receiver_header(study.input(key, raw=True))
            study.cache.pop(study.prefix+'/'+study.manifest['inputs'][key]['path'])
            times = common['times']
            if common['layout'] != layout or common['segment_id'] != segment or len(times) != layout['receiver_epochs']:
                raise ValueError('unchanged common receiver time base required')
            for origin in ORIGINS:
                identity = f'{segment}-{origin}'
                earlier = study.input(identity+'-training')
                scoring = study.input(identity+'-scoring')
                cut, horizon = earlier['cut_epoch'], earlier['horizon_epochs']
                query = times[cut:cut+horizon]
                if (earlier['segment_id'] != segment or scoring['segment_id'] != segment
                        or len(earlier['training_gps']) != cut or len(scoring['prediction_gps']) != horizon
                        or len(query) != horizon):
                    raise ValueError('unchanged paired receiver splits required')
                start = comparison[segment][origin+'_identity']
                imu = None
                if start:
                    if not study.rows[start]['passed'] or not start.startswith(identity+'-'):
                        raise ValueError('archived IMU selection differs')
                    score = study.artifact(start, 'scores.json')['prediction']
                    forecast = study.artifact(start, 'forecast.json')
                    if forecast['times'][cut:] != query or forecast['prediction_receiver_positions_used']:
                        raise ValueError('original inertial forecast must use the same later timestamps')
                    imu = dict(identity=start, scores=score)
                packets[identity+'-training'] = encoded(dict(segment_id=segment, group_id=layout['group_id'],
                    origin=origin, training_times=times[:cut], training_gps=earlier['training_gps'], future_times=query))
                packets[identity+'-scoring'] = encoded(dict(scoring, imu=imu))
                tasks.append(dict(identity=identity, input_key=identity+'-training',
                    payload=dict(segment_id=segment, origin=origin),
                    limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=0)))
    with closing(ClosedStudy(root, 'data/'+ORIGINAL)) as original:
        zero = dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)
        original_tasks = [{k: v for k, v in task.items() if k not in ('shard', 'index')}
                          for task in original.tasks.values()]
        if (original.completion['manifest_sha256'] != ORIGINAL_SHA or original.completion['state'] != 'terminal'
                or original.summary['charged'] != zero or original.summary['completed'] != 40
                or original_tasks != tasks or original.input('parent-report', raw=True) != parent
                or any(original.input(key, raw=True) != raw for key, raw in packets.items())):
            raise ValueError('exact original zero-work technical failure and input bytes required')
        for identity in original.rows:
            error = original.envelope(identity)['result']
            if (error['passed'] or error.get('error_type') != 'ValueError'
                    or error.get('reason') != 'one complete finite operation reservation required'):
                raise ValueError('technical correction applies only to the original accounting failure')
    base.mkdir(parents=True)
    for key, raw in packets.items():
        path = base/(key+'.json')
        atomic(path, raw)
        material[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=material, tasks=tasks, workers=1, threads=1,
                       maximum_wall_s=120., sources=source_closure(root, [adapter, PLAN]))
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
