# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only diagnosis of position allowances; no integration or model fitting."""
import json
import math
from lll.studies.artifacts import ArchiveStore,digest


def budget_row(material):
    result=material['result'];certificate=material['certificate']
    vectors=[certificate[k] for k in ('position_unshared_remainder',
        'lever_unshared_remainder','unshared_remainder')]
    vectors.append(result['future_width_m'])
    if any(len(v)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in v) for v in vectors):
        raise ValueError('finite nonnegative three-axis allowances required')
    position,lever,total,width=vectors
    if any(abs(p+l-t)>1e-10*max(1,t) for p,l,t in zip(position,lever,total)):
        raise ValueError('saved position/lever components do not reconstruct total')
    if type(result['profile']) is not bool or type(result['useful']) is not bool or type(result['numerical_checks_passed']) is not bool:
        raise ValueError('explicit original outcomes required')
    return dict(identity=material['identity'],model=result['model'],profile=result['profile'],
        time_s=certificate['time_s'],prior_useful=result['useful'],
        prior_numerical_checks_passed=result['numerical_checks_passed'],future_width_m=width,
        position_share=[p/t if t else 0.0 for p,t in zip(position,total)],
        position_unshared_remainder=position,lever_unshared_remainder=lever,
        total_unshared_remainder=total,result_sha256=material['result_sha256'],
        bound_sha256=material['bound_sha256'],new_prediction_bound=False)


def read_materials(root,prefix):
    """Verify the closed-study hash chain before consuming its six saved cases."""
    store=ArchiveStore(root);catalog=store.catalog()
    def read(name,expected=None):
        raw=store._read(prefix+'/'+name,catalog)
        if expected is not None and digest(raw)!=expected:raise ValueError('saved evidence hash mismatch: '+name)
        return json.loads(raw),digest(raw)
    completion,_=read('completion.json')
    _,manifest_sha=read('manifest.json',completion['manifest_sha256'])
    summary,_=read('summary.json',completion['summary_sha256'])
    if summary['passed'] or summary['completed']!=6 or len(summary['results'])!=6:
        raise ValueError('expected the frozen six-case unsuccessful feasibility study')
    materials=[]
    for case in summary['results']:
        envelope,sha=read(case['artifact'],case['artifact_sha256'])
        result=envelope['result'];identity=case['identity']
        if (envelope['manifest_sha256']!=manifest_sha or envelope['identity']!=identity
                or result['identity']!=identity or digest((json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode())!=envelope['result_sha256']
                or result['original_reads']!=0 or result['optimizer_starts']!=0):
            raise ValueError('saved case identity, result hash or scope mismatch')
        name='artifacts/'+identity+'/future-bound.json'
        certificate,bound_sha=read(name,envelope['artifacts'][name])
        materials.append(dict(identity=identity,result=result,certificate=certificate,
            result_sha256=sha,bound_sha256=bound_sha,manifest_sha256=manifest_sha))
    if {(m['result']['model'],m['result']['profile']) for m in materials}!={(i,p) for i in range(3) for p in (False,True)}:
        raise ValueError('all three models and both processing cases required')
    return materials


def static_materials(root,prefix):
    """Extract only static inputs after verifying their complete parent chain."""
    materials=read_materials(root,prefix);store=ArchiveStore(root);catalog=store.catalog()
    def read(name,expected=None):
        raw=store._read(prefix+'/'+name,catalog)
        if expected is not None and digest(raw)!=expected:raise ValueError('saved evidence hash mismatch: '+name)
        return json.loads(raw),digest(raw)
    completion,_=read('completion.json')
    manifest,manifest_sha=read('manifest.json',completion['manifest_sha256'])
    summary,_=read('summary.json',completion['summary_sha256'])
    outcomes={r['identity']:r for r in summary['results']}
    tasks={t['identity']:t for t in manifest['tasks']};out=[]
    for material in materials:
        identity=material['identity'];item=outcomes[identity]
        envelope,_=read(item['artifact'],material['result_sha256'])
        def artifact(name):
            path='artifacts/'+identity+'/'+name
            return read(path,envelope['artifacts'][path])
        region,region_sha=artifact('stage-02-region.json')
        reference,reference_sha=artifact('reference.json')
        case_spec=manifest['inputs'][tasks[identity]['payload']['case_key']]
        case,case_sha=read(case_spec['path'],case_spec['sha256']);configuration=case['configuration']
        acceleration_change=material['certificate']['conditioned_acceleration_change']
        if (configuration['model']!=material['result']['model']
                or configuration['profile']!=material['result']['profile']
                or reference['binding']!=region['binding']
                or reference['binding']!=material['certificate']['reference_binding']
                or reference['parent']['source_id']!=region['source_id']
                or not case['dv'] or not case['dt'] or len(case['dv'][0])!=3
                or not math.isfinite(case['dt'][0]) or case['dt'][0]<=0
                or not math.isfinite(acceleration_change) or acceleration_change<0
                or any(not math.isfinite(v) for v in case['dv'][0])):
            raise ValueError('matching saved reference, physical candidate and finite start required')
        out.append(dict(identity=identity,configuration={k:configuration[k]
                for k in ('initial_r','limits','model','profile','gravity')},
            first_delta_v=case['dv'][0],first_dt=case['dt'][0],reference_report=reference,
            lower=material['certificate']['lower'],upper=material['certificate']['upper'],
            center=material['certificate']['normalized_center'],training_region=region,
            prior_acceleration_change=acceleration_change,
            provenance=dict(parent=prefix,manifest_sha256=manifest_sha,case_sha256=case_sha,
                reference_sha256=reference_sha,training_region_sha256=region_sha,
                result_sha256=material['result_sha256'])))
    return out


def evaluate(task,context):
    if task.get('payload',{}).get('analysis')=='width_budget':
        return width_budget_evaluate(task,context)
    if task.get('payload',{}).get('analysis')=='static_reference':
        return static_reference_evaluate(task,context)
    if task.get('payload',{}).get('analysis')=='coordinate_projection':
        return calibration_evaluate(task,context)
    material=json.loads(context.input_path().read_text())
    row=budget_row(material);context.save('budget-row.json',row)
    return dict(passed=True,scientific_decision='abstain',identity=task['identity'],
        scope='saved allowance arithmetic only',prior_study_qualified=False,
        observational_coverage_qualified=False,optimizer_starts=0,original_reads=0,
        row=row)


def width_budget(material):
    """Decompose preserved widths in metres, without new supports or bounds.

    Input hashes must be verified by the caller. Exact arithmetic here checks
    the width identity, not the physical or numerical validity of its terms.
    """
    from fractions import Fraction as F
    from lll.ilvis0_saved_prediction_audit import endpoint
    region=material['training_region'];future=material['future'];bound=material['certificate']
    if (region['parameter_count']!=51 or future['parameter_count']!=51
            or region['binding']!=future['shared_binding'] or region['binding']!=bound['reference_binding']
            or region['source_id']!=future['source_id'] or region['source_id']!=bound['source_id']
            or region['future_truth_used'] is not False or future['future_truth_used'] is not False):
        raise ValueError('unchanged complete training-only source and future envelope required')
    arrays=[region['coordinate_scale'],future['lower'],future['upper'],future['certificates'],
        bound['position_unshared_remainder'],bound['lever_unshared_remainder'],bound['unshared_remainder'],
        material['result']['future_width_m']]
    if any(len(v)!=3 for v in arrays):raise ValueError('all three original axes required')
    arithmetic=F(region['arithmetic_allowance']);axes=[]
    if arithmetic<0:raise ValueError('nonnegative arithmetic allowance required')
    for i in range(3):
        scale=F(region['coordinate_scale'][i]);left=F(future['lower'][i]);right=F(future['upper'][i])
        if (scale<=0 or right<left
                or endpoint(right-left,True)!=material['result']['future_width_m'][i]):
            raise ValueError('positive coordinate scales and preserved widths required')
        cert=future['certificates'][i];affine=F(cert['upper'])+F(cert['negated_lower'])
        position=2*scale*F(bound['position_unshared_remainder'][i])
        lever=2*scale*F(bound['lever_unshared_remainder'][i])
        unshared=2*scale*F(bound['unshared_remainder'][i]);width=right-left
        allowance_rounding=unshared-position-lever
        endpoint_rounding=width-affine-unshared-2*arithmetic
        reported=F(material['result']['future_width_m'][i])
        terms=dict(affine=affine,position=position,lever=lever,unshared=unshared,
            arithmetic=2*arithmetic,allowance_rounding=allowance_rounding,endpoint_rounding=endpoint_rounding,
            reported_rounding=reported-width)
        if any(v<0 for v in terms.values()):raise ValueError('saved components do not reconstruct the width')
        axes.append(dict(axis=i,width_m=float(reported),coordinate_scale=float(scale),
            **{k+'_width_m':float(v) for k,v in terms.items()},
            exact_width=str(width),exact_components={k:str(v) for k,v in terms.items()},
            unshared_fraction=float(unshared/width) if width else None,
            position_fraction=float(position/width) if width else None))
    return dict(passed=True,identity=material['identity'],model=material['result']['model'],
        profile=material['result']['profile'],axes=axes,width_axes_checked=3,
        new_prediction_bound=False,native_evaluations=0,bound_evaluations=0,
        optimizer_starts=0,original_reads=0,prior_study_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def width_budget_evaluate(task,context):
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    if task.get('payload')!=dict(analysis='width_budget',maximum_width_axes=3):
        raise ValueError('three separately frozen arithmetic width checks required')
    material=json.loads(context.input_path().read_text());identity=task['identity']
    if material['identity']!=identity:raise ValueError('saved width identity mismatch')
    path=context.directory/'allowance.sqlite'
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:dict(width_axes=3)})
    journal.start(identity);_check_continue(context.root,context.manifest)
    journal.reserve(identity,'width_axes',3)
    try:
        report=width_budget(material);context.save('width-budget.json',report);return report
    finally:
        journal.verify();context.note_file(path)


def calibration_row(material,*,reserve):
    from lll.ilvis0_affine_support import project_coordinates
    row=budget_row(material);region=material['training_region'];bound=material['certificate']
    if (region.get('parameter_count')!=51 or region.get('physical_parameter_count')!=27
            or region.get('future_truth_used') is not False
            or region.get('source_id')!=bound.get('source_id')
            or region.get('binding')!=bound.get('reference_binding')
            or any(len(region.get(key,[]))!=51 for key in ('lower','upper','center'))):
        raise ValueError('complete source-bound training-only 51-column region required')
    row['projection']=project_coordinates(region['lower'],region['upper'],region['inequality_design'],
        region['inequality_upper'],axes=list(range(27)),reserve=reserve)
    row['new_prediction_bound']=False
    return row


def calibration_evaluate(task,context):
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    expected=dict(analysis='coordinate_projection',maximum_proposals=54,maximum_supports=162)
    if task.get('payload')!=expected:raise ValueError('fixed coordinate-projection allowance required')
    material=json.loads(context.input_path().read_text());identity=task['identity']
    if material['identity']!=identity:raise ValueError('saved calibration identity mismatch')
    path=context.directory/'allowance.sqlite'
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:dict(lp_proposals=54,exact_supports=162)})
    journal.start(identity)
    def reserve(proposals,supports):
        _check_continue(context.root,context.manifest)
        journal.reserve(identity,'lp_proposals',proposals)
        journal.reserve(identity,'exact_supports',supports)
    row=calibration_row(material,reserve=reserve)
    if journal.count(identity,'lp_proposals')!=54 or journal.count(identity,'exact_supports')!=162:
        raise ValueError('complete coordinate reservation sequence required')
    journal.verify();context.note_file(path);context.save('coordinate-projection.json',row)
    return dict(passed=True,scientific_decision='abstain',identity=identity,
        prior_study_qualified=False,observational_coverage_qualified=False,
        optimizer_starts=0,original_reads=0,native_evaluations=0,
        lp_proposals_reserved=54,exact_supports_reserved=162,row=row)


def static_reference_evaluate(task,context):
    from lll.studies.journal import Journal
    from lll.ilvis0_coupled_map import restore_static_reference
    if task.get('payload')!=dict(analysis='static_reference',maximum_restorations=1):
        raise ValueError('one separately frozen reference restoration required')
    material=json.loads(context.input_path().read_text());identity=task['identity']
    if material['identity']!=identity:raise ValueError('saved static identity mismatch')
    path=context.directory/'allowance.sqlite'
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:dict(reference_restorations=1)})
    journal.start(identity);journal.reserve(identity,'reference_restorations')
    ref=restore_static_reference(material['configuration'],material['first_delta_v'],material['first_dt'],
        lower=material['lower'],upper=material['upper'],center=material['center'],
        expected_report=material['reference_report'])
    journal.verify();context.note_file(path)
    report=dict(reference_unchanged=True,reference_binding=ref.binding,
        reference_sha256=digest((json.dumps(ref.report(),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()),
        provenance=material['provenance'],trajectory_history_loaded=False)
    context.save('reference-check.json',report)
    return dict(passed=True,scientific_decision='abstain',identity=identity,
        reference_binding=ref.binding,reference_restorations=1,native_evaluations=0,
        original_reads=0,optimizer_starts=0,observational_coverage_qualified=False)
