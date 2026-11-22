# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test transfer of a fixed earlier forecast-error trend to a later cut."""

from collections import defaultdict
from contextlib import closing
import json
import math
from pathlib import Path
from statistics import median


ID = 'ilvis0-forecast-error-transfer-v1-20261120'
SCOPE = 'Earlier-only forecast-error correction across the twenty original NASA groups'
BASE = 'docs/prediction-group-transfer/'
PLAN = BASE+'ERROR_TRANSFER_PLAN.md'
RESULT = BASE+'error-transfer.json'
PARENT = BASE+'remaining-verified-report.json'
PARENT_SHA = 'e95e20ebe21d61182166e6e140371b8e3397a1f97f32ac1519c46343a82b0d4f'
ORIGINS = ('inner','outer')


def choose_start(rows):
    from .ilvis0_rolling_origin_report import select_primary

    if (sorted(row['start'] for row in rows) != [0,1] or any(
            not isinstance(row['training_cost'], (int,float)) or not math.isfinite(row['training_cost'])
            or row['training_cost'] < 0. or type(row['passed']) is not bool for row in rows)):
        raise ValueError('both originals with finite earlier training costs required')
    selected = select_primary(rows)
    return selected if selected is not None else min(rows, key=lambda row:(row['training_cost'],row['start']))


def predict_error(earlier_times, earlier_errors, later_times, *, height_only=False):
    import numpy as np

    earlier, errors, later = (np.asarray(v, float) for v in (earlier_times,earlier_errors,later_times))
    if (earlier.ndim != 1 or len(earlier) < 2 or errors.shape != (len(earlier),3)
            or later.ndim != 1 or not len(later) or earlier[0] <= 0. or later[0] <= 0.
            or np.any(np.diff(earlier) <= 0.) or np.any(np.diff(later) <= 0.)
            or any(not np.isfinite(v).all() for v in (earlier,errors,later))):
        raise ValueError('positive increasing elapsed times and finite position errors required')
    center = earlier.mean()
    t = earlier-center
    rate = (t @ errors)/(t @ t)
    offset = errors.mean(axis=0)-rate*center
    if height_only:
        rate[:2] = 0.
        offset[:2] = 0.
    return offset+later[:,None]*rate, dict(offset_m=offset.tolist(), rate_mps=rate.tolist())


def score(times, errors):
    from .receiver_only_forecast_report import replay

    rows = [dict(epoch=i, time_s=float(t), north_error_m=float(n), east_error_m=float(e), up_error_m=float(u))
            for i,(t,(n,e,u)) in enumerate(zip(times,errors,strict=True))]
    result = replay(rows)
    result['vertical_rms_m'] = result.pop('up_rms_m')
    return result


def task_for(segment):
    return dict(identity=segment, input_key=segment+'-earlier', payload={},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=0))


def evaluate(task, context):
    return evaluate_pair(task, context, scope=SCOPE)


def evaluate_pair(task, context, *, scope, height_only=False):
    import numpy as np
    from .ilvis0_remaining_gps_report import physical

    segment = task['identity']
    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if context.manifest['scope'] != scope or declared != task_for(segment):
        raise ValueError('exact one-cut transfer task required')
    earlier = json.loads(context.input_path().read_bytes())
    if (earlier['segment_id'] != segment or earlier['last_earlier_position_s'] >= earlier['first_later_position_s']
            or 'later_errors' in earlier or len(earlier['earlier_times']) != len(earlier['later_times'])):
        raise ValueError('separate chronologically ordered equal-horizon positions required')
    context.charge(bound_calls=1, bound_steps=0)
    predicted, fit = predict_error(earlier['earlier_times'],earlier['earlier_errors'],earlier['later_times'],
                                   height_only=height_only)
    context.save('earlier-only-error-model.json',dict(fit, segment_id=segment,
        expected_later_error_m=predicted.tolist(), later_errors_used=False))
    late = json.loads(context.input_path(segment+'-scoring').read_bytes())
    actual = np.asarray(late['later_errors'], float)
    if late['segment_id'] != segment or actual.shape != predicted.shape:
        raise ValueError('exact saved later forecast errors required')
    times = earlier['later_times']
    before, corrected = score(times,actual), score(times,actual-predicted)
    if height_only and any(before[key] != corrected[key] for key in
                           ('north_rms_m','east_rms_m','horizontal_rms_m','maximum_horizontal_m')):
        raise ValueError('height-only correction changed a horizontal error')
    for key in ('horizontal_rms_m','vertical_rms_m','maximum_horizontal_m','maximum_absolute_up_m'):
        if not math.isclose(before[key],late['original_scores'][key],rel_tol=1e-12,abs_tol=1e-10):
            raise ValueError('original later forecast metric differs')
    record = dict(segment_id=segment, inner_identity=earlier['inner_identity'], outer_identity=late['outer_identity'],
        inner_stop=earlier['inner_stop'], outer_stop=late['outer_stop'], both_stopped=earlier['inner_stop'] and late['outer_stop'],
        earlier_only_error_model=fit, before=before, corrected=corrected,
        original_physical_pass=physical(before), corrected_physical_pass=physical(corrected),
        navigation_fits=0, scientific_decision='abstain')
    context.save('score-transfer.json',record)
    return dict(record,passed=True)


def extract_pairs(study, rows):
    from .ilvis0_saved_prediction import summarize
    from .studies.artifacts import encoded

    staged = {}
    cases = defaultdict(list)
    for identity, task in study.tasks.items():
        spec = task['payload']
        if spec['clock'] != 'header_elapsed' or spec['profile']:
            continue
        result = study.envelope(identity)['result']
        cases[spec['segment_id'],spec['origin']].append(dict(identity=identity,start=spec['start'],
            training_cost=result['training_cost'],passed=study.rows[identity]['passed']))
    segments = {row['segment_id']:row for row in rows}
    if len(segments) != len(rows) or set(cases) != {(s,o) for s in segments for o in ORIGINS}:
        raise ValueError('all original groups and both header-clock cuts required')
    for segment, original in segments.items():
        pair = {}
        for origin in ORIGINS:
            case = choose_start(cases[segment,origin])
            identity = case['identity']
            if (identity if case['passed'] else None) != original[origin+'_identity']:
                raise ValueError('selection no longer reproduces original passing identities')
            epochs = study.artifact(identity,'epochs.json')
            path = study.artifact(identity,'forecast.json')
            archive = study.artifact(identity,'scores.json')
            cut, n = path['training_epochs'],path['prediction_epochs']
            if (path['prediction_receiver_positions_used'] is not False
                    or not path['continuous_propagation_without_gps_reset']
                    or summarize(epochs, training_epochs=cut, prediction_epochs=n) != archive):
                raise ValueError('exact original held-out scores required')
            times = [row['time_s'] for row in epochs[cut:]]
            start = epochs[cut-1]['time_s']
            pair[origin] = dict(case, times=times, elapsed=[t-start for t in times],
                errors=[[row[axis+'_direct_error_m'] for axis in ('north','east','up')] for row in epochs[cut:]],
                scores=archive['prediction'])
        early, late = (pair[key] for key in ORIGINS)
        staged[segment+'-earlier'] = encoded(dict(segment_id=segment, inner_identity=early['identity'],
            inner_stop=early['passed'], earlier_times=early['elapsed'],earlier_errors=early['errors'],
            later_times=late['elapsed'], last_earlier_position_s=early['times'][-1], first_later_position_s=late['times'][0]))
        staged[segment+'-scoring'] = encoded(dict(segment_id=segment, outer_identity=late['identity'],
            outer_stop=late['passed'], later_errors=late['errors'],original_scores=late['scores']))
    return staged, tuple(segments)


def prepare(root):
    from .ilvis0_remaining_prediction_report import verify_closed
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing archived error transfer freeze')
    raw = (root/PARENT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('exact twenty-group parent report required')
    report = json.loads(raw)
    with closing(ClosedStudy(root,report['study'])) as study:
        verify_closed(study)
        if study.completion['summary_sha256'] != report['summary_sha256']:
            raise ValueError('archived transfer completion changed')
        if len(report['rows']) != 20:
            raise ValueError('exact twenty-group source report required')
        staged, segments = extract_pairs(study, report['rows'])
    base.mkdir(parents=True)
    inputs = {'plan':PLAN, 'parent_report':PARENT}
    for key, material in staged.items():
        path = base/(key+'.json')
        atomic(path,material)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(s) for s in segments], sources=source_closure(root,[adapter,PLAN]),
        workers=1, threads=1, maximum_wall_s=90.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def summarize(rows):
    metrics = ('horizontal_rms_m','vertical_rms_m')
    return dict(groups=len(rows), raw_screen_passes=sum(row['original_physical_pass'] for row in rows),
        adjusted_screen_passes=sum(row['corrected_physical_pass'] for row in rows),
        rms={key:dict(improved=sum(row['corrected'][key] < row['before'][key] for row in rows),
                      median_raw=median(row['before'][key] for row in rows),
                      median_adjusted=median(row['corrected'][key] for row in rows),
                      median_change=median(row['corrected'][key]-row['before'][key] for row in rows)) for key in metrics})


def collect(root):
    collect_study(root, name=ID, output=RESULT, count=20, paired_count=5)


def collect_study(root, *, name, output, count, paired_count, height_only=False):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root,'data/'+name)) as study:
        if not study.summary['passed'] or study.summary['completed'] != count or study.summary['bound_evaluations'] != count:
            raise ValueError('complete charged error transfer tests required')
        rows = []
        for segment in study.tasks:
            row = study.artifact(segment,'score-transfer.json')
            model = study.artifact(segment,'earlier-only-error-model.json')
            if (model['later_errors_used'] or row['navigation_fits'] or row['scientific_decision'] != 'abstain'
                    or study.envelope(segment)['result'] != dict(row,passed=True)
                    or row['segment_id'] != segment or model['segment_id'] != segment):
                raise ValueError('archived preceding model and later score must agree')
            if height_only and any(n or e for n,e,_ in model['expected_later_error_m']):
                raise ValueError('sealed height-only correction changed horizontal positions')
            rows.append(row)
        matched = [row for row in rows if row['both_stopped']]
        if len(matched) != paired_count:
            raise ValueError('original twice-stopped group count differs')
        raw = encoded(dict(rows=rows, all_diagnostic=summarize(rows), both_original_stops=summarize(matched),
                           manifest_sha256=study.completion['manifest_sha256'],scientific_decision='abstain'))
    _write_equal(root/output,raw)
    print(digest(raw))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','collect'))
    args = parser.parse_args()
    {'prepare':prepare,'collect':collect}[args.action](Path.cwd())
