# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved descriptive statistics; never fit or propagate aircraft data."""
import json


def verify_statistics(parent,curves,statistics,result):
    import math
    from lll.prediction_residuals import summarize
    from lll.studies.artifacts import encoded
    selected={v['primary']['identity'] for v in parent['primaries'] if v['primary'] is not None}
    if len(statistics)!=len(parent['rows']):raise ValueError('all parent labels and missing outcomes required')
    keys=('identity','model','profile','policy_id','start','complete','passed')
    for original,saved in zip(parent['rows'],statistics,strict=True):
        if (any(saved[k]!=original[k] for k in keys) or saved['parent_reason']!=original.get('reason')
                or saved['selected_primary']!=(original['identity'] in selected)):
            raise ValueError('parent labels, failures or training-only choices changed')
        if not original['complete']:
            if saved['statistics'] is not None:raise ValueError('missing curve cannot acquire statistics')
            continue
        curve=curves[original['identity']];scores=curve['scores']
        expected=summarize(scores['times_s'],scores['errors_neu_m'],training_epochs=800)
        if (encoded(saved['statistics'])!=encoded(expected) or saved['source_scores_sha256']!=curve['source_sha256']
                or saved['weighted_training_rms']!=math.sqrt(original['last_training_cost']/2400)
                or saved['weighted_training_rms_is_chisquare_test'] is not False):
            raise ValueError('saved descriptive statistics differ from unchanged parent curves')
    n=len(curves)
    if (result['passed'] is not True or result['records']!=n or result['missing_records']!=len(statistics)-n
            or result['saved_error_epochs']!=1200*n or result['selected_primaries']!=len(selected)
            or any(result[k] for k in ('native_calls','observed_starts','new_propagations','original_reads','protected_reads',
                'forecasts_changed','model_decisions_changed','error_law_calibrated','raw_receiver_or_imu_noise_estimated'))
            or result['scientific_decision']!='abstain'):
        raise ValueError('descriptive statistics scope or interpretation changed')


def inspect(root,prefix='data/esa-error-structure-20261024'):
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix)  # Reject unfinished studies before numerical imports.
    try:
        import gzip
        import io
        from lll.airquantumgrav_error_structure import recipe,tasks,work_limits,validate_inputs,environment,SCOPE
        from lll.airquantumgrav_geographic_report import construction_counts
        from lll.studies.source_binding import verify
        from lll.studies.artifacts import digest,encoded
        r=study.input('recipe');expected=tasks()[0];identity=expected['identity']
        if (not study.summary['passed'] or r!=recipe() or study.manifest['scope']!=SCOPE
                or set(study.tasks)!={identity}
                or {k:v for k,v in study.tasks[identity].items() if k not in ('index','shard')}!=expected
                or study.manifest['allocation']['workers']!=1 or study.manifest['allocation']['threads']!=1
                or study.input('qualification-environment')!=environment()):
            raise ValueError('complete unchanged finite saved-error scope required')
        verify(root,declared=study.input('qualification-request')['sources'],manifest=study.manifest['sources'])
        parent=study.input('parent-report');raw=study.input('curves',raw=True)
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw=stream.read(r['maximum_curves_bytes']+1)
        if len(raw)>r['maximum_curves_bytes']:raise ValueError('saved curves exceed byte allowance')
        curves=json.loads(raw)
        validate_inputs(parent,study.input('parent-manifest',raw=True),study.input('parent-completion'),
            study.input('parent-receipt'),curves)
        envelope=study.envelope(identity);result=envelope['result'];statistics=study.artifact(identity,'statistics.json')
        verify_statistics(parent,curves,statistics,result)
        counts=construction_counts(study.artifact(identity,'statistics-work.sqlite',raw=True),
            study.completion['manifest_sha256'],identity,work_limits(r),complete=False)
        n=len(curves);expected_counts=dict(records=n,saved_error_epochs=n*1200,statistics_sections=4*n,
            spectra=12*n,correlation_pairs=34698*n,plotted_epochs=result['selected_primaries']*1200)
        if counts!=expected_counts or counts!=result['charged_work'] or any(study.summary['charged'].values()):
            raise ValueError('charged saved-data work differs')
        for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
        return dict(verified=True,result=result,statistics=statistics,elapsed_s=study.summary['elapsed_s'],
            parent_manifest_sha256=parent['manifest_sha256'],parent_report_sha256=digest(encoded(parent)),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,protected_reads=0,native_calls=0,observed_starts=0,scientific_decision='abstain')
    finally:study.close()


def csv_bytes(report):
    import csv
    import io
    from lll.prediction_residuals import LAGS
    header=['identity','model','profile','policy_id','start','selected_primary','section','series','axis','units',
        'epochs','mean','rms','std','absolute_p95','source_scores_sha256']
    header += ['acf_'+str(lag) for lag in LAGS]+['variance_period_gt60s','variance_period_10to60s','variance_period_lt10s']
    output=io.StringIO();writer=csv.writer(output);writer.writerow(header)
    for row in report['statistics']:
        if not row['complete']:continue
        for name in ('training','prediction'):
            original=row['statistics'][name]
            for series,section in (('position',original),('first_difference',original['first_differences'])):
                for axis in section['axes']:
                    d=axis['distribution'];bands=axis['spectrum'].get('bands',{})
                    writer.writerow([row[k] for k in ('identity','model','profile','policy_id','start','selected_primary')]
                        +[name,series,axis['axis'],section['units'],section['epochs'],d['mean'],d['rms'],d['centered_rms'],d['absolute_p95'],row['source_scores_sha256']]
                        +[v['value'] for v in axis['autocorrelation']]
                        +[bands.get(k) for k in ('longer_than_60_s','10_to_60_s','shorter_than_10_s')])
    return output.getvalue().encode()


def render(report):
    result=report['result'];labels=dict(sphere_rotating='Globe + specified field',sphere_still='Globe + zero field',flat_still='Tested disc')
    lines=['# What the saved prediction errors show','',
        f"**{result['records']} saved error curves examined.** The two deadline-limited starts remain unavailable.",
        'No new fit or aircraft propagation is performed. Every prediction, model choice and accuracy label is unchanged.','',
        'These settings reuse one development recording. They are not independent flights.',
        'The plots show how errors grow during training and later prediction. The dotted line begins prediction.','',
        '| Candidate | Removal | Working errors | Weighted training RMS | Later N/E/up lag-one correlation |',
        '|---|---|---|---:|---|']
    for row in report['statistics']:
        if not row['selected_primary']:continue
        values=[axis['autocorrelation'][0]['value'] for axis in row['statistics']['prediction']['axes']]
        corr=' / '.join('undefined' if v is None else f'{v:.3f}' for v in values)
        lines.append('| '+' | '.join([labels[row['model']],'Profiled' if row['profile'] else 'Zero',
            'Short memory' if row['policy_id']=='reported-short-v1' else 'Persistent',f"{row['weighted_training_rms']:.4g}",corr])+' |')
    lines+=['', '![Unchanged horizontal and height prediction errors](artifacts/saved-error-structure/error-growth.png)','',
        'A correlation near one means nearby errors move together. It is not raw receiver noise: aircraft reconstruction,',
        'instrument calibration, receiver errors and model mismatch all contribute. Large slow trends can produce high',
        'correlation. First differences describe changes between adjacent saved errors, using their actual time intervals;',
        'they do not separate those causes.','',
        'Training and prediction are summarized separately. Centred Fourier variance describes fast and slow fluctuations',
        'only when the original sampling is uniform; no interpolation is used. Sixty-second blocks are descriptive,',
        'not independent trials. Constant signals have undefined correlations.','',
        'These are not calibrated confidence statements. Weighted training RMS describes an already fitted objective;',
        'it is not a chi-squared test, an instrument accuracy measurement or a complete prediction-error law.',
        'All 22 completed starts are retained in the statistics; the table and plot use the parent’s training-only choices.',
        'Seven confirmation groups remain protected, and the 53-stretch findings remain unchanged.','',
        '[Axis statistics CSV](axis-statistics.csv) · [Diagnostic plan](PLAN.md) ·',
        '[Parent prediction comparison](../esa-observed-wide-pilot/INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-error-structure-20261024',output='docs/esa-error-structure'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('diagnostic publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-error-structure/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('artifacts/publication/verified-report.json',encoded(report)),
            ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),('axis-statistics.csv',csv_bytes(report))]:
        atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0,original_reads=0)
