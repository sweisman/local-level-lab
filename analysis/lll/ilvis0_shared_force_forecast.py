# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score saved matched IMU forecasts on the force-only GPS witness."""

from contextlib import ExitStack, closing
import json
from pathlib import Path


ID = 'ilvis0-shared-force-forecast-v1-20261120'
SCOPE = 'Apply the sealed force-only receiver correction to six unchanged IMU forecasts'
PLAN = 'docs/ilvis0-measurement-contribution/SHARED_FORCE_FORECAST_PLAN.md'
RESULT = 'docs/ilvis0-measurement-contribution/shared-force-forecast.json'
FORCE_RECEIPT_SHA = 'c76abc3a90e3731f6cd1a4cbec5fce58af747572845ef7c06d4f4d635cb2a3b1'
FORECAST_RECEIPT_SHA = '2a010e456688f320728c9fc8a2ad76b73478c2a0af012a6fd1af1b4776bd196c'
RECORDERS = ('imu8','imu21')


def tasks():
    return [dict(identity=imu, input_key=imu, payload={},
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=2, bound_steps=0))
            for imu in RECORDERS]


def aligned_correction(saved, correction, scoring):
    import numpy as np

    cut = saved['cut']
    times = saved['times']
    coordinates = np.asarray(saved['coordinates'], float)
    delta = np.asarray(correction['correction_m'], float)
    if (type(cut) is not int or not 0 < cut < len(times) or correction['times_s'] != times
            or correction['axes'] != ['north','east','up'] or delta.shape != (len(times), 3)
            or coordinates.shape != delta.shape or not np.isfinite(delta).all()
            or times[cut:] != scoring['query_times_s']
            or not np.array_equal(coordinates[cut:], scoring['coordinates']['onboard'])):
        raise ValueError('force and forecast must use the same receiver coordinates and epochs')
    return delta[cut:]


def scores(first, second, correction):
    import numpy as np

    f, s, delta = (np.asarray(v, float) for v in (first, second, correction))
    if (f.ndim != 2 or f.shape[1] != 3 or not len(f) or s.shape != f.shape or delta.shape != f.shape
            or any(not np.isfinite(v).all() for v in (f, s, delta))):
        raise ValueError('aligned three-axis forecasts and one common receiver correction required')
    output = {}
    for name, axes in (('horizontal', slice(0,2)), ('height', slice(2,3))):
        x, y, d = f[:, axes], s[:, axes], delta[:, axes]
        before = [float(np.mean(np.sum(v*v, axis=1))) for v in (x, y)]
        after = [float(np.mean(np.sum((v-d)**2, axis=1))) for v in (x, y)]
        raw_gap, corrected_gap = before[1]-before[0], after[1]-after[0]
        inner_product = float(-2.*np.mean(np.sum(d*(y-x), axis=1)))
        scale = max(*before, *after, 1.)
        if abs(corrected_gap-raw_gap-inner_product) > 1e-11*scale:
            raise ValueError('shared correction failed the paired score identity')
        output[name] = dict(before_rms_m=np.sqrt(before).tolist(), after_rms_m=np.sqrt(after).tolist(),
                            before_gap_m2=raw_gap, after_gap_m2=corrected_gap, gap_change_m2=inner_product)
    return output


def evaluate(task, context):
    import numpy as np
    from .ilvis0_matched_forecast_receiver import HORIZONS, MODELS, PAIRS

    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact fixed-forecast scoring tasks required')
    material = json.loads(context.input_path().read_bytes())
    time = np.asarray(material['elapsed_s'], float)
    change = np.asarray(material['correction_m'], float)
    trajectories = material['forecasts_neu_m']
    if (time.ndim != 1 or not len(time) or not np.isfinite(time).all()
            or np.any(np.diff(time) <= 0.) or set(trajectories) != set(MODELS)
            or change.shape != (len(time),3) or material['recorder'] != task['identity']):
        raise ValueError('unchanged paired forecast timelines required')
    if task['identity'] == 'imu21' and np.any(change):
        raise ValueError('original IMU21 correction must be exactly zero')
    for _ in range(2):
        context.charge(bound_calls=1, bound_steps=0)
    rows = []
    for horizon in HORIZONS:
        n = len(time) if horizon is None else int(np.searchsorted(time, horizon, side='right'))
        if n < 2 or (horizon is not None and time[-1] < horizon):
            raise ValueError('complete declared receiver horizon required')
        pairs = {name: scores(trajectories[first][:n], trajectories[second][:n], change[:n])
                 for name, first, second in PAIRS}
        rows.append(dict(horizon_s=horizon, epochs=n, pairs=pairs))
    record = dict(recorder=task['identity'], segment_id=material['segment_id'], rows=rows,
        largest_horizontal_correction_m=float(np.max(np.linalg.norm(change[:,:2], axis=1))),
        largest_height_correction_m=float(np.max(np.abs(change[:,2]))), missing_forecast='flat_still',
        fit_starts=0, new_propagations=0, scientific_decision='abstain')
    context.save('corrected-scores.json', record)
    return dict(record, passed=True)


def prepare(root):
    import numpy as np
    from . import ilvis0_matched_forecast_receiver as forecast
    from .ilvis0_shared_force_witness_report import RESULT as FORCE_RECEIPT
    from .ilvis0_shared_force_witness_study import ID as FORCE, ORIGINAL
    from .ilvis0_solver_position import physical_metric
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing shared correction scoring freeze')
    force_raw = (root/FORCE_RECEIPT).read_bytes()
    forecast_raw = (root/forecast.PARENT_RECEIPT).read_bytes()
    if digest(force_raw) != FORCE_RECEIPT_SHA or digest(forecast_raw) != FORECAST_RECEIPT_SHA:
        raise ValueError('exact recorded force and forecast receipts required')
    forced = json.loads(force_raw)
    staged = {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, 'data/'+forecast.parent.ID)))
        parent_receipt = json.loads(forecast_raw)
        if any(parent_receipt[key] != value for key, value in parent.completion.items()):
            raise ValueError('sealed IMU forecast parent changed')
        recordings = {f"imu{item['imu_type']}":item for item in parent.input('input_receipt')['recordings']}
        if set(recordings) != set(RECORDERS):
            raise ValueError('both original recorder identities required')
        for recorder, runtime in (('imu8', FORCE), ('imu21', ORIGINAL)):
            with closing(ClosedStudy(root, 'data/'+runtime, store=parent.store)) as force:
                if force.completion['manifest_sha256'] != forced['manifests'][recorder] or not force.rows[recorder]['passed']:
                    raise ValueError('sealed receiver witness changed')
                saved = force.input(recorder)
                correction = force.artifact(recorder, 'receiver-error.json')
            source = recordings[recorder]
            segment, cut = source['segment_id'], source['training_epochs']
            times = parent.input(segment+'-queries')['query_times_s']
            scoring = parent.input(segment+'-scoring')
            if (saved['segment_id'] != segment or saved['cut'] != cut or saved['times'] != times
                    or len(times)-cut != source['scoring_epochs']):
                raise ValueError('exact original recorder and split required')
            corrected = aligned_correction(saved, correction, scoring)
            reference = np.asarray(scoring['coordinates']['onboard'], float)
            metric = physical_metric(reference)
            models = {}
            for model in forecast.MODELS:
                identity = f'{segment}-{model}'
                recorded = parent.envelope(identity)['result']
                path = parent.artifact(identity, 'forecast.json')
                if (not recorded['passed'] or not recorded['converged'] or path['later_positions_used']
                        or path['training_epochs'] != cut or path['query_times_s'] != times):
                    raise ValueError('original scoring forecast changed')
                models[model] = forecast._local(path['coordinates'][cut:], reference, metric).tolist()
            missing = parent.rows.get(segment+'-flat_still')
            if missing is not None and missing['passed']:
                raise ValueError('unexpected zero-field disc forecast')
            staged[recorder] = encoded(dict(recorder=recorder, segment_id=segment,
                elapsed_s=(np.asarray(times[cut:])-times[cut-1]).tolist(), correction_m=corrected.tolist(),
                forecasts_neu_m=models, source_manifests=[parent.completion['manifest_sha256'], forced['manifests'][recorder]]))
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'force_receipt': FORCE_RECEIPT, 'forecast_receipt': forecast.PARENT_RECEIPT}
    for key, payload in staged.items():
        path = base/(key+'.json')
        atomic(path, payload)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter, scope=SCOPE, tasks=tasks(), inputs=inputs,
        workers=1, threads=1, maximum_wall_s=90., sources=source_closure(root, [adapter, PLAN])), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or set(study.rows) != set(RECORDERS) or study.summary['bound_evaluations'] != 4:
            raise ValueError('both sealed fixed-forecast score records required')
        rows = [study.artifact(imu, 'corrected-scores.json') for imu in RECORDERS]
        for row, recorder in zip(rows, RECORDERS, strict=True):
            if (dict(row, passed=True) != study.envelope(recorder)['result'] or len(row['rows']) != 4
                    or row['fit_starts'] or row['new_propagations']):
                raise ValueError('fixed-forecast artifact changes a sealed result')
        raw = encoded(dict(rows=rows, manifest_sha256=study.completion['manifest_sha256'], scientific_decision='abstain'))
    _write_equal(root/RESULT, raw)
    print(digest(raw))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','collect'))
    args = parser.parse_args()
    {'prepare':prepare, 'collect':collect}[args.action](Path.cwd())
