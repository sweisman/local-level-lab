# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-error diagnosis using shared statistics and study lifecycle."""
import json
import math

from lll.airquantumgrav_diagnosis import environment
from lll.airquantumgrav_inventory import IMU_NAME
from lll.prediction_residuals import LAGS

SCOPE='saved ESA prediction error structure only; no fitting, propagation or original/protected reads'
PARENT='docs/esa-observed-wide-pilot'


def recipe():
    return dict(version='esa-error-structure-v1',workers=1,threads=1,maximum_wall_s=300.,
        maximum_saved_records=24,maximum_saved_error_epochs=28800,maximum_curves_bytes=32*1024*1024,
        receiver_epochs=1200,training_epochs=800,lags=list(LAGS),plots=True,
        native_calls=0,observed_starts=0,new_propagations=0,original_reads=0,protected_reads=0,retries=0)


def tasks():
    return [dict(identity='saved-error-structure',input_key='curves',payload=dict(recording='187'),
        native_kind='value',limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]


def work_limits(r):
    count=r['maximum_saved_records'];n=r['receiver_epochs'];cut=r['training_epochs']
    pairs=3*sum(max(0,m-lag) for m in (cut,n-cut,cut-1,n-cut-1) for lag in r['lags'])
    return dict(records=count,saved_error_epochs=r['maximum_saved_error_epochs'],statistics_sections=4*count,
        spectra=12*count,correlation_pairs=count*pairs,plotted_epochs=12*n)


def require_parent(report):
    try:
        valid=(report['verified'] is True and report['total']==24 and report['expected_primaries']==12
            and report['complete_predictions']==22 and report['numerically_converged']==22
            and not any(report[k] for k in ('original_reads','protected_reads','native_calls_during_audit'))
            and report['source']['source_references']['imu']['filename']==IMU_NAME)
    except (KeyError,TypeError):valid=False
    if not valid:raise ValueError('exact verified recording-187 development parent required')


def parent_report(root):
    from lll.airquantumgrav_diagnosis import closed_parent
    study,report=closed_parent(root,PARENT)
    try:require_parent(report)
    except Exception:study.close();raise
    return study,report


def validate_inputs(report,manifest_raw,completion,receipt,curves):
    from lll.studies.artifacts import digest,encoded
    require_parent(report)
    if (digest(manifest_raw)!=report['manifest_sha256'] or completion['manifest_sha256']!=report['manifest_sha256']
            or completion['summary_sha256']!=report['summary_sha256']
            or digest(encoded(report))!=receipt['artifacts']['artifacts/publication/verified-report.json']):
        raise ValueError('parent publication and completion binding differ')
    expected={row['identity'] for row in report['rows'] if row['complete']}
    if len(report['rows'])!=24 or len({v['identity'] for v in report['rows']})!=24 or len(expected)!=22 or set(curves)!=expected:
        raise ValueError('every completed curve and original missing outcome must be retained')
    reference=None;r=recipe()
    for identity,curve in curves.items():
        scores=curve['scores'];name='artifacts/'+identity+'/scores.json'
        if digest(encoded(scores))!=curve['source_sha256'] or receipt['artifacts'][name]!=curve['source_sha256']:
            raise ValueError('saved error curve differs from its parent artifact')
        times=scores['times_s']
        if (len(times)!=r['receiver_epochs'] or len(scores['errors_neu_m'])!=len(times)
                or (reference is not None and times!=reference)):
            raise ValueError('complete identical saved query epochs required')
        reference=times
    if len(report['primaries'])!=12:raise ValueError('all original primary choices required')
    for group in report['primaries']:
        row=group['primary']
        if row is not None and (row['identity'] not in curves or row['start']!=group['selected_training_start']
                or any(row[k]!=group[k] for k in ('model','profile','policy_id'))):
            raise ValueError('unchanged parent primary selection required')


def calculate(report,curves,r,*,reserve,save,save_bytes):
    from lll.prediction_residuals import summarize,error_growth_figure
    if r!=recipe():raise ValueError('unchanged descriptive recipe required')
    rows=report['rows'];n=r['receiver_epochs'];cut=r['training_epochs']
    selected={v['primary']['identity'] for v in report['primaries'] if v['primary'] is not None}
    reserve(records=len(curves),saved_error_epochs=len(curves)*n)
    per_pairs=work_limits(r)['correlation_pairs']//r['maximum_saved_records'];result=[];plot=[]
    for row in rows:
        identity=row['identity'];item={key:row[key] for key in ('identity','model','profile','policy_id','start','complete','passed')}
        item.update(selected_primary=identity in selected,parent_reason=row.get('reason'),statistics=None)
        if row['complete']:
            reserve(statistics_sections=4,spectra=12,correlation_pairs=per_pairs)
            curve=curves[identity];scores=curve['scores'];cost=row['last_training_cost']
            if type(cost) not in (int,float) or not math.isfinite(cost) or cost<0:raise ValueError('finite saved training cost required')
            item.update(statistics=summarize(scores['times_s'],scores['errors_neu_m'],training_epochs=cut),
                source_scores_sha256=curve['source_sha256'],weighted_training_rms=math.sqrt(cost/(3*cut)),
                weighted_training_rms_is_chisquare_test=False)
            if identity in selected:plot.append(dict(times_s=scores['times_s'],errors_neu_m=scores['errors_neu_m'],spec=item))
        result.append(item)
    save('statistics.json',result)
    if r['plots']:
        reserve(plotted_epochs=len(plot)*n)
        save_bytes('error-growth.png',error_growth_figure(plot,training_epochs=cut))
    return dict(passed=True,records=len(curves),missing_records=len(rows)-len(curves),saved_error_epochs=len(curves)*n,
        selected_primaries=len(selected),native_calls=0,observed_starts=0,new_propagations=0,
        original_reads=0,protected_reads=0,forecasts_changed=False,model_decisions_changed=False,
        error_law_calibrated=False,raw_receiver_or_imu_noise_estimated=False,scientific_decision='abstain')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/airquantumgrav_error_structure.py',
        'analysis/lll/airquantumgrav_error_structure_report.py',
        'analysis/tests/test_airquantumgrav_error_structure.py',
        'analysis/tests/test_airquantumgrav_error_structure_numeric.py',
        'analysis/tests/test_airquantumgrav_error_structure_report.py',
        'analysis/tests/test_prediction_residuals.py','docs/esa-error-structure/PLAN.md'])


def required_tests():
    return ['test_error_structure_standalone_definition_has_finite_zero_native_scope',
        'test_error_structure_requires_qualification_before_parent_or_inputs',
        'test_error_structure_rejects_unguarded_environment_before_parent',
        'test_error_structure_rejects_open_parent_before_numerical_imports',
        'test_error_structure_requires_exact_verified_development_parent',
        'test_error_structure_preparation_keeps_study_identity_separate_from_curve_identity',
        'test_saved_error_structure_preserves_parent_outcomes_choices_and_exact_work',
        'test_error_structure_report_rejects_open_before_numerical_imports',
        'test_error_structure_render_separates_error_dependence_from_noise_or_confidence',
        'test_error_structure_report_rejects_changed_labels_before_statistics',
        'test_constant_error_has_no_invented_correlation_or_spectral_variance',
        'test_ramp_covariance_and_actual_time_differences_have_known_values',
        'test_alternating_series_has_known_negative_lag_and_nyquist_variance',
        'test_sinusoid_has_analytically_known_low_frequency_energy',
        'test_irregular_cadence_is_retained_but_not_interpolated_for_a_spectrum',
        'test_later_errors_do_not_change_training_statistics_or_source_arrays']


def prepare(root,*,qualification,identity='esa-error-structure-20261024'):
    if qualification is None:raise ValueError('source-bound saved-error qualification required')
    import gzip
    import re
    from pathlib import Path
    from lll.compute_budget import environment as threads
    from lll.studies.artifacts import atomic,encoded,safe_path
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    r=recipe();env=environment()
    if env['numerical_environment']!=threads(workers=1,threads=1):raise ValueError('declared thread environment required')
    if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}',identity):raise ValueError('safe fresh identity required')
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh saved-error scope required')
    sources=qualification_sources(root);request,tests=checked(root,qualification,sources=sources,environment=env,
        required_tests=required_tests(),minimum_tests=25)
    parent,report=parent_report(root)
    try:
        curves={}
        receipt=parent.read('evidence-receipt.json');manifest=parent.read('manifest.json',parent.completion['manifest_sha256'],raw=True)
        for row in report['rows']:
            if not row['complete']:continue
            curve_identity=row['identity'];name='artifacts/'+curve_identity+'/scores.json'
            curves[curve_identity]=dict(scores=parent.artifact(curve_identity,'scores.json'),
                source_sha256=parent.envelope(curve_identity)['artifacts'][name])
        validate_inputs(report,manifest,parent.completion,receipt,curves)
        raw=encoded(curves)
        if len(raw)>r['maximum_curves_bytes']:raise ValueError('saved error input exceeds its byte allowance')
        materials={'parent-report':encoded(report),'parent-manifest':manifest,'parent-completion':encoded(parent.completion),
            'parent-receipt':encoded(receipt),'curves':gzip.compress(raw,mtime=0),'recipe':encoded(r),
            'qualification-request':request,'qualification-report':tests,'qualification-environment':encoded(env)}
    finally:parent.close()
    base.mkdir(parents=True);inputs={}
    for i,(key,raw) in enumerate(materials.items()):
        path=base/f'input-{i:03d}';atomic(path,raw);inputs[key]=str(path.relative_to(root))
    value=dict(id=identity,scope=SCOPE,adapter='analysis/lll/airquantumgrav_error_structure.py',sources=sources,inputs=inputs,
        tasks=tasks(),workers=1,threads=1,maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json',encoded(value));manifest=Definition.from_dict(value,root).prepare(root)
    return dict(path='data/'+identity,allocation=manifest['allocation'],native_calls=0,observed_starts=0)


def load_curves(path):
    import gzip
    with gzip.open(path,'rb') as stream:raw=stream.read(recipe()['maximum_curves_bytes']+1)
    if len(raw)>recipe()['maximum_curves_bytes']:raise ValueError('saved curves exceed finite byte allowance')
    return json.loads(raw)


def evaluate(task,context):
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    if {k:v for k,v in task.items() if k not in ('index','shard')}!=tasks()[0]:raise ValueError('one unchanged saved-error task required')
    load=lambda key:json.loads(context.input_path(key).read_bytes());r=recipe()
    if load('recipe')!=r or context.manifest['scope']!=SCOPE or load('qualification-environment')!=environment():
        raise ValueError('unchanged qualified saved-data scope and environment required')
    report=load('parent-report');curves=load_curves(context.input_path('curves'))
    validate_inputs(report,context.input_path('parent-manifest').read_bytes(),load('parent-completion'),load('parent-receipt'),curves)
    limits=work_limits(r);journal=Journal(context.directory/'statistics-work.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:limits});journal.start(task['identity'])
    try:
        def reserve(**work):
            _check_continue(context.root,context.manifest)
            for key,value in work.items():journal.reserve(task['identity'],key,value)
        result=calculate(report,curves,r,reserve=reserve,save=context.save,save_bytes=context.save_bytes)
        journal.verify();result['charged_work']={key:journal.count(task['identity'],key) for key in limits}
        return result
    finally:context.note_file(journal.path)
