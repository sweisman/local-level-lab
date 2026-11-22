# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the fixed accuracy screen on all saved starts in two NASA studies."""

from collections import Counter, defaultdict
from contextlib import closing
import json
import math
from pathlib import Path


ID = 'ilvis0-forecast-accuracy-margin-v1-20261120'
SCOPE = 'Fixed accuracy screen and shared receiver-error radii on 104 sealed NASA fits'
BASE = 'docs/prediction-group-transfer/'
PLAN = BASE+'ACCURACY_MARGIN_PLAN.md'
RESULT = BASE+'accuracy-margin.json'
ROOT_STEPS = 64
SCREENS = {'horizontal':(10.,50.), 'height':(30.,150.)}
COHORTS = {
    'transfer': (80, 30, 'remaining-verified-report.json', 'e95e20ebe21d61182166e6e140371b8e3397a1f97f32ac1519c46343a82b0d4f'),
    'methods': (24, 7, 'observed-method-v2-diagnosis.json', 'e4c67aa6467d55d442925e24d84417599dc0e4c4c97baa0c74baa91e898c36fc'),
}


def tasks():
    return [dict(identity=cohort, input_key=cohort, payload={}, limits=dict(native_calls=0,
                 packet_visits=0, bound_calls=count, bound_steps=count*2*ROOT_STEPS))
            for cohort, (count, *_) in COHORTS.items()]


def axis_margin(magnitudes, *, rms_limit, peak_limit):
    import numpy as np

    values = np.asarray(magnitudes, float)
    if (values.ndim != 1 or not len(values) or not np.isfinite(values).all() or np.any(values < 0.)
            or not 0. < rms_limit <= peak_limit < math.inf):
        raise ValueError('finite nonnegative forecast errors and ordered positive limits required')
    mean_square = float(np.mean(values**2))
    rms, peak = math.sqrt(mean_square), float(np.max(values))
    rms_passed, peak_passed = rms <= rms_limit, peak <= peak_limit
    edge = None
    if rms_passed and peak_passed:
        difference = max(0., (rms_limit-rms)*(rms_limit+rms))
        mean = float(np.mean(values))
        rms_edge = difference/(math.sqrt(mean**2+difference)+mean)
        edge = min((rms_edge, 'rms'), (peak_limit-peak, 'maximum'))
    left, right = 0., 0.
    if not rms_passed:
        right = peak
        for _ in range(ROOT_STEPS):
            mid = (left+right)/2.
            if float(np.mean(np.maximum(values-mid,0.)**2)) > rms_limit**2:
                left = mid
            else:
                right = mid
    peak_excess = max(0.,peak-peak_limit)
    return dict(rms=rms, peak=peak, rms_passed=rms_passed, peak_passed=peak_passed,
                boundary=edge, rescue_radius_m=[max(left,peak_excess), max(right,peak_excess)])


def margins(errors):
    import numpy as np

    rows = np.asarray(errors, float)
    if rows.ndim != 2 or rows.shape[1] != 3:
        raise ValueError('aligned north, east and height errors required')
    magnitudes = {'horizontal':np.hypot(rows[:,0],rows[:,1]), 'height':np.abs(rows[:,2])}
    axes = {key: axis_margin(magnitudes[key], rms_limit=rms, peak_limit=peak)
            for key, (rms,peak) in SCREENS.items()}
    failing = [f'{axis}_{label}_m' for axis, row in axes.items()
               for label, kind in (('rms','rms_passed'), ('maximum','peak_passed')) if not row[kind]]
    boundary, first = None, None
    if not failing:
        boundary, first = min((v['boundary'][0],f"{key}_{v['boundary'][1]}_m") for key,v in axes.items())
    lows, highs = zip(*(row['rescue_radius_m'] for row in axes.values()), strict=True)
    return dict(axes=axes, accuracy_screen_passed=not failing, failed_limits=failing,
                screen_boundary_radius_m=boundary, first_limit=first,
                joint_needed_m=[max(lows), math.hypot(*highs)])


def evaluate(task, context):
    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact archived forecast accuracy task required')
    material = json.loads(context.input_path().read_bytes())
    count, stopped, *_ = COHORTS[task['identity']]
    rows = material['records']
    if (len(rows) != count or len({r['identity'] for r in rows}) != count
            or sum(r['numerical_stop'] for r in rows) != stopped):
        raise ValueError('original cohort and stopping labels required')
    results = []
    for source in rows:
        meta = {key:source[key] for key in ('identity','segment_id','origin','start','solver','numerical_stop','archived_scores_sha256')}
        if source['errors_neu_m'] is None:
            results.append(dict(meta, screen=None))
            continue
        context.charge(bound_calls=1, bound_steps=2*ROOT_STEPS)
        screen = margins(source['errors_neu_m'])
        for name, fields in (('horizontal', ('horizontal_rms_m','maximum_horizontal_m')),
                             ('height', ('vertical_rms_m','maximum_absolute_up_m'))):
            for key, actual in zip(fields, (screen['axes'][name]['rms'],screen['axes'][name]['peak']), strict=True):
                if not math.isclose(source['score'][key], actual, rel_tol=1e-12, abs_tol=1e-10):
                    raise ValueError('reconstructed original forecast score differs')
        results.append(dict(meta, screen=screen))
    record = dict(cohort=task['identity'], rows=results, source_manifest=material['source_manifest'],
                  source_summary=material['source_summary'], refits=0, new_propagations=0, scientific_decision='abstain')
    context.save('accuracy-screens.json', record)
    return dict(passed=True, scored=sum(v['screen'] is not None for v in results), cutoff_preserved=True,
                scientific_decision='abstain')


def prepare(root):
    from .ilvis0_saved_prediction import summarize
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing accuracy audit freeze')
    inputs, staged = {'plan':PLAN}, {}
    for cohort, (total, stopped, filename, expected) in COHORTS.items():
        name = BASE+filename
        raw = (root/name).read_bytes()
        if digest(raw) != expected:
            raise ValueError('unchanged verified parent receipt required')
        inputs[cohort+'-receipt'] = name
        report = json.loads(raw)
        with closing(ClosedStudy(root, report['study'])) as study:
            if (len(study.tasks) != total or len(study.rows) != total or any(
                    study.completion[key] != report[key] for key in ('manifest_sha256','summary_sha256'))):
                raise ValueError('complete original forecast cohort required')
            rows = []
            for identity, task in study.tasks.items():
                envelope = study.envelope(identity)
                original, spec = envelope['result'], task['payload']
                numerical = study.rows[identity]['passed'] if cohort == 'transfer' else original['converged']
                if type(numerical) is not bool or original.get('converged') != numerical:
                    raise ValueError('original stopping label differs')
                score_path = f'artifacts/{identity}/scores.json'
                score, errors = None, None
                if score_path in envelope['artifacts']:
                    epochs = study.artifact(identity, 'epochs.json')
                    score = study.artifact(identity, 'scores.json')
                    forecast = study.artifact(identity, 'forecast.json')
                    cut, horizon = forecast['training_epochs'],forecast['prediction_epochs']
                    if (forecast['prediction_receiver_positions_used']
                            or not forecast['continuous_propagation_without_gps_reset']
                            or summarize(epochs, training_epochs=cut, prediction_epochs=horizon) != score
                            or score['prediction'] != original['prediction']):
                        raise ValueError('unchanged held-out forecast scores required')
                    errors = [[v[f'{axis}_direct_error_m'] for axis in ('north','east','up')] for v in epochs[cut:]]
                rows.append(dict(identity=identity, segment_id=spec['segment_id'], origin=spec['origin'],
                    solver=spec.get('solver','original'), start=spec['start'], numerical_stop=numerical,
                    archived_scores_sha256=envelope['artifacts'].get(score_path),
                    score=score['prediction'] if score else None, errors_neu_m=errors))
            if sum(row['numerical_stop'] for row in rows) != stopped:
                raise ValueError('original number of stopping outcomes differs')
            staged[cohort] = encoded(dict(records=rows, source_manifest=report['manifest_sha256'],
                                         source_summary=report['summary_sha256']))
    base.mkdir(parents=True)
    for key, raw in staged.items():
        path = base/(key+'.json')
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    source = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=source, sources=source_closure(root, [source, PLAN]),
        tasks=tasks(), inputs=inputs, workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


def summarize_cohort(rows):
    counts = Counter()
    cuts = defaultdict(list)
    for row in rows:
        screen = row['screen']
        status = 'missing' if screen is None else 'pass' if screen['accuracy_screen_passed'] else 'fail'
        counts[f"{'stop' if row['numerical_stop'] else 'nonstop'}_{status}"] += 1
        cuts[(row['segment_id'],row['origin'])].append(status)
    agreement = Counter('missing' if 'missing' in group else 'all_pass' if set(group)=={'pass'} else
                        'all_fail' if set(group)=={'fail'} else 'mixed' for group in cuts.values())
    return dict(fit_counts=dict(counts), cut_counts=dict(agreement))


def verify_saved_pass(source, result):
    """Check an archived passing margin by evaluating its saved boundary."""
    import numpy as np

    screen = result['screen']
    rows = np.asarray(source['errors_neu_m'], float)
    if not screen['accuracy_screen_passed'] or screen['failed_limits'] or screen['joint_needed_m'] != [0.,0.]:
        raise ValueError('report-only recovery requires the sealed passing margins')
    radius = screen['screen_boundary_radius_m']
    if not math.isfinite(radius) or radius < 0.:
        raise ValueError('finite nonnegative saved passing radius required')
    ratios = {}
    for axis, values, fields in (
            ('horizontal', np.hypot(rows[:,0],rows[:,1]), ('horizontal_rms_m','maximum_horizontal_m')),
            ('height', np.abs(rows[:,2]), ('vertical_rms_m','maximum_absolute_up_m'))):
        rms, peak = SCREENS[axis]
        archived = source['score']
        current = screen['axes'][axis]
        if (not current['rms_passed'] or not current['peak_passed'] or current['rescue_radius_m'] != [0.,0.]
                or not math.isclose(current['rms'], archived[fields[0]], rel_tol=1e-12, abs_tol=1e-10)
                or not math.isclose(current['peak'], archived[fields[1]], rel_tol=1e-12, abs_tol=1e-10)
                or archived[fields[0]] > rms or archived[fields[1]] > peak):
            raise ValueError('saved accuracy pass must match original score and cutoff')
        moved = values+radius
        ratios[axis+'_rms_m'] = float(np.linalg.norm(moved)/math.sqrt(len(values))/rms)
        ratios[axis+'_maximum_m'] = float(np.max(moved)/peak)
    if (max(ratios.values()) > 1.+1e-10
            or not math.isclose(ratios[screen['first_limit']],1.,rel_tol=1e-10)):
        raise ValueError('saved adversarial radius does not reach its first screen')


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (study.completion['manifest_sha256'] != '5662158e3818ae987291383ef110272e759868a6e208d7ef98722414b7c1bde0'
                or study.completion['state'] != 'terminal' or set(study.rows) != set(COHORTS)):
            raise ValueError('exact archived result-envelope failure required')
        results = []
        for cohort, (total, stopped, *_) in COHORTS.items():
            envelope = study.envelope(cohort)
            error = envelope['result']
            if (envelope['charged']['bound_calls'] != total or error.get('error_type') != 'ValueError'
                    or error.get('reason') != 'one explicit software result and continued scientific abstention required'):
                raise ValueError('original complete accounting and known envelope rejection required')
            material = study.input(cohort)
            record = study.artifact(cohort,'accuracy-screens.json')
            if (record['cohort'] != cohort or record['scientific_decision'] != 'abstain' or record['refits']
                    or record['new_propagations'] or len(record['rows']) != total
                    or sum(r['numerical_stop'] for r in record['rows']) != stopped
                    or any(record[k] != material[k] for k in ('source_manifest','source_summary'))):
                raise ValueError('sealed result rows differ from their study scope')
            for source, result in zip(material['records'],record['rows'],strict=True):
                if any(source[k] != result[k] for k in result if k != 'screen'):
                    raise ValueError('original identity, score hash or stopping label changed')
                verify_saved_pass(source,result)
            results.append(dict(record, **summarize_cohort(record['rows'])))
        data = encoded(dict(results=results, manifest_sha256=study.completion['manifest_sha256'],
            worker_state='terminal', result_envelopes_rejected=2, report_verified=True, scientific_decision='abstain'))
    _write_equal(root/RESULT,data)
    print(digest(data))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare','collect'))
    args = parser.parse_args()
    {'prepare':prepare, 'collect':collect}[args.action](Path.cwd())
