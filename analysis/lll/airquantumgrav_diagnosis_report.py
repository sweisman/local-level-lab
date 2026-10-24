# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read saved diagnosis artifacts only; never repeat a calculation or forecast."""
import json


def check_scope(result):
    if (not result['passed'] or result['settings']!=12 or not 0<=result['available_settings']<=12
            or any(result[key] for key in ('native_calls','observed_starts','new_propagations','original_reads',
                'protected_reads','forecasts_changed','causation_established'))
            or any(result['gravity_reference'][key] for key in ('gravity_measured','scale_is_forecast','scale_is_error_bound','causation_established'))):
        raise ValueError('read-only sensitivity diagnosis cannot create forecasts, measurements, bounds or causal conclusions')


def inspect(root,prefix='data/esa-development-diagnosis-20261023'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import encoded
    from lll.airquantumgrav_geographic_report import construction_counts
    study=ClosedStudy(root,prefix)
    try:
        if not study.summary['passed'] or len(study.tasks)!=1:raise ValueError('complete passing diagnosis required')
        identity=next(iter(study.tasks));envelope=study.envelope(identity);result=envelope['result'];check_scope(result)
        r=study.input('recipe');pilot=study.input('pilot-report');curves=study.input('curves',raw=True)
        cases=study.artifact(identity,'cases.json');context=study.artifact(identity,'recorded-context.json')
        sensitivity=study.artifact(identity,'start-sensitivity.json');cut=r['training_epochs']
        if (len(cases)!=12 or len(pilot['primaries'])!=12 or encoded(sensitivity)!=encoded(pilot['start_sensitivity'])
                or len(context['times_s'])!=r['receiver_epochs'] or not context['temperature_display_uses_recorded_samples']
                or encoded(context['gravity_reference'])!=encoded(result['gravity_reference'])
                or context['force_based_reference_mps2']!=result['force_based_initial_reference_mps2']
                or sum(case['available'] for case in cases)!=result['available_settings']):
            raise ValueError('unchanged parent sensitivity, context or diagnosis scope required')
        import gzip
        curves=json.loads(gzip.decompress(curves));visited=0
        for case,group in zip(cases,pilot['primaries'],strict=True):
            if (case['spec']!={key:group[key] for key in ('model','profile','policy_id')}
                    or case['available']!=(group['primary'] is not None)
                    or case['selected_training_start']!=group['selected_training_start']):
                raise ValueError('diagnosis must retain original primary choices and failures')
            if not case['available']:continue
            row=group['primary'];curve=curves[row['identity']]
            if (case['identity']!=row['identity'] or case['source_scores_sha256']!=curve['source_sha256']
                    or case['training']!=row['training'] or case['prediction']!=row['prediction']
                    or case['calibration']['normalized']!=row['normalized_parameters']
                    or case['calibration']['calibration_uniquely_identified']
                    or case['calibration']['force_reference_is_independent_gravity']
                    or case['forecasts_changed'] or case['blocks_are_independent_trials'] or case['epochs']!=r['receiver_epochs']):
                raise ValueError('saved forecast, calibration or interpretation changed')
            expected=0
            for block in case['blocks']:
                first,last=block['first_epoch'],block['last_epoch']
                if (first!=expected or last<first or block['epochs']!=last-first+1
                        or (block['section']=='training' and not last<cut)
                        or (block['section']=='prediction' and not first>=cut)
                        or block['section'] not in ('training','prediction')):
                    raise ValueError('blocks must partition epochs without crossing the training boundary')
                expected=last+1
            if expected!=r['receiver_epochs']:raise ValueError('diagnostic blocks omit original epochs')
            visited+=expected
        if visited!=result['processed_primary_error_epochs']:raise ValueError('processed epoch count differs')
        limits=dict(raw_points=r['maximum_raw_points'],receiver_epochs=r['receiver_epochs'],saved_records=r['maximum_saved_records'],
            saved_error_epochs=r['maximum_saved_error_epochs'],settings=r['maximum_settings'])
        counts=construction_counts(study.artifact(identity,'diagnosis-work.sqlite',raw=True),study.completion['manifest_sha256'],identity,limits)
        if (counts!=result['charged_work'] or any(study.summary['charged'].values())
                or result['raw_points']>limits['raw_points'] or result['receiver_epochs']!=limits['receiver_epochs']
                or result['available_saved_records']>limits['saved_records']):raise ValueError('finite read-only work differs')
        for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
        return dict(verified=True,result=result,cases=cases,context=context,parent_source=pilot['source'],
            parent_manifest_sha256=pilot['manifest_sha256'],start_sensitivity=sensitivity,elapsed_s=study.summary['elapsed_s'],
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            original_reads=0,native_calls=0,observed_starts=0,scientific_decision='abstain')
    finally:study.close()


def render(report):
    result=report['result'];reference=result['gravity_reference']
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe, zero field',flat_still='Tested disc')
    lines=['# Diagnosing later-position errors','',
        f"**{result['available_settings']}/12 settings have a qualified saved forecast available.** "
        'This diagnosis preserves every original prediction and accuracy label. It performs no new fit or propagation.','',
        'The reference gravity curve changes by '
        f"**{reference['range_mps2']:.6g} m/s²** over the recorded height range. "
        'Under the declared radial-field sensitivity, its largest later discrepancy from the earlier mean corresponds to a '
        f"constant-acceleration position scale of **{reference['constant_acceleration_position_scale_m']:.1f} m**.",
        'That scale is a diagnostic illustration. It is not a predicted error, confidence bound, measured gravity field '
        'or established explanation for the observed errors. The same reference applies to every candidate.','',
        '| Candidate | Removal | Working errors | Parameters near bounds | Fitted constant gravity | Later horizontal RMS | Later height RMS |',
        '|---|---|---|---:|---:|---:|---:|']
    for case in report['cases']:
        spec=case['spec'];fields=[labels[spec['model']],'Profiled' if spec['profile'] else 'Zero',
            'Short memory' if spec['policy_id']=='reported-short-v1' else 'Persistent']
        if case['available']:
            c=case['calibration'];p=case['prediction'];fields += [str(len(c['near_boundary'])),
                f"{c['fitted_constant_gravity_mps2']:.6f} m/s²",f"{p['horizontal_rms_m']:.6g} m",f"{p['vertical_rms_m']:.6g} m"]
        else:fields+=['Unavailable']*4
        lines.append('| '+' | '.join(fields)+' |')
    identity='saved-prediction-diagnosis'
    lines+=['', 'A parameter is counted near its bound at absolute normalized value ≥0.999.',
        'That descriptive threshold creates no acceptance gate. Fitted gravity includes',
        'the initializer’s force-based reference and its constant adjustment; the',
        'reference is not independent gravity during aircraft motion. Missing',
        'predictions retain their original failures and are not replaced.','',
        f'![Recorded height, ground speed and temperature](artifacts/{identity}/context.png)','',
        f'![Unchanged north, east and height errors](artifacts/{identity}/saved-errors.png)','',
        'The error plot uses a symmetric logarithmic vertical scale beyond ±1 m.',
        'Colors identify candidates; line styles and opacity distinguish the',
        'processing and working-error cases. The dotted line begins prediction.',
        'Sixty-second blocks are diagnostics, not independent observations.','',
        'These results help choose the next software qualification. Calibration,',
        'initialization, timing, gravity variation and other missing dynamics remain',
        'possible explanations. A revised physical model needs independent generated',
        'controls and a separate observed-data freeze, with the same accuracy limits.',
        'No new geometry, background-field, causal or calibrated detection claim follows.',
        'Seven confirmation groups and the NASA findings remain unchanged.','',
        '[Frozen diagnostic plan](PLAN.md) · [Observed pilot](../esa-development-pilot/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-development-diagnosis-20261023',output='docs/esa-development-diagnosis'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('diagnosis publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-development-diagnosis/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0,original_reads=0)
