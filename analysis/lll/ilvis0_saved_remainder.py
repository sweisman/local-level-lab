# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply a qualified remainder candidate without repeating saved training work.

The native integration engine, bridge and support builder remain shared.
Passing software checks does not establish aircraft uncertainty coverage.
"""
from copy import deepcopy
from fractions import Fraction as F
import json


def saved_inputs(root,parent,qualification):
    """Verify closed parent evidence and assemble inputs without packet copies."""
    from pathlib import Path
    from lll.studies.artifacts import ArchiveStore,digest
    from lll.ilvis0_saved_budget_audit import read_materials
    root=Path(root);store=ArchiveStore(root);catalog=store.catalog()
    def read(prefix,name,expected=None):
        raw=store._read(prefix+'/'+name,catalog)
        if expected is not None and digest(raw)!=expected:raise ValueError('saved dependency hash mismatch: '+name)
        return json.loads(raw),digest(raw)
    def closed(prefix):
        completion,_=read(prefix,'completion.json')
        manifest,sha=read(prefix,'manifest.json',completion['manifest_sha256'])
        summary,_=read(prefix,'summary.json',completion['summary_sha256'])
        return manifest,sha,summary
    qualified,qualified_sha,controls=closed(qualification)
    if not controls['passed'] or controls['completed']!=12 or len(controls['results'])!=12:
        raise ValueError('all twelve completed short controls required')
    coverage=set()
    for row in controls['results']:
        envelope,_=read(qualification,row['artifact'],row['artifact_sha256'])
        check=envelope['result']
        if not all(check.get(k) is True for k in ('passed','all_probes_contained','maps_preserved',
                                                  'remainders_nonwidening','force_remainder_reduced')):
            raise ValueError('failed short prerequisite')
        coverage.add((check['model'],check['profile'],check['scope']))
    if coverage!={(m,p,s) for m in range(3) for p in (False,True) for s in ('physical','conditioned')}:
        raise ValueError('complete short-control model, processing and proof coverage required')
    engine_names={name for name in qualified['sources'] if name.endswith(('.cpp','.hpp','.h'))}
    engine_names.update('analysis/lll/'+name for name in ('ilvis0_remainder_native.py',
        'ilvis0_remainder_interface.py','ilvis0_conditional_remainder.py','ilvis0_direct_native.py',
        'ilvis0_conditioned_acceleration.py','ilvis0_direct_interface.py'))
    if any(digest((root/name).read_bytes())!=qualified['sources'][name] for name in engine_names):
        raise ValueError('qualified native component changed; separate qualification required')
    manifest,manifest_sha,summary=closed(parent)
    if summary['completed']!=6 or len(summary['results'])!=6:
        raise ValueError('all six closed parent cases required')
    outcomes={row['identity']:row for row in summary['results']}
    tasks={task['identity']:task for task in manifest['tasks']};out=[]
    for material in read_materials(root,parent):
        identity=material['identity'];result=material['result'];item=outcomes[identity]
        envelope,_=read(parent,item['artifact'],item['artifact_sha256'])
        if not result['numerical_checks_passed'] or result['packets']!=recipe()['packets']:
            raise ValueError('complete numerically checked parent history required')
        artifacts={}
        def artifact(name):
            path='artifacts/'+identity+'/'+name
            value,sha=read(parent,path,envelope['artifacts'][path]);artifacts[name]=sha
            return value
        reference=artifact('reference.json');region=artifact('stage-02-region.json')
        proof_input=artifact('stage-02-conditioning-input.json')
        certificate=artifact('stage-02-certificate.json');future=artifact('future.json')
        nominal=artifact('native-11.json');truth=artifact('truth-audit.json')
        if (nominal['status']!=0 or nominal['time_s']!=recipe()['future_s']
                or nominal['point']!=region['center'][:27]
                or proof_input['training']['region']!=region or proof_input['reference']!=reference
                or material['certificate']['reference_binding']!=reference['binding']
                or future['shared_binding']!=reference['binding']
                or result['parameter_count']!=51 or len(region['inequality_design'])!=recipe()['training_rows']):
            raise ValueError('matching saved conditioning, native centre and complete training region required')
        saved=dict(parameter_count=51,reference=reference,bound=material['certificate'],envelope=future,
            lower=region['lower'],upper=region['upper'],fixed_center=region['center'][:27],
            nominal=nominal['prediction'],jacobian=nominal['jacobian'],time_s=nominal['time_s'])
        case_spec=manifest['inputs'][tasks[identity]['payload']['case_key']]
        provenance=dict(parent=parent,manifest_sha256=manifest_sha,result_sha256=item['artifact_sha256'],
            qualification=qualification,qualification_manifest_sha256=qualified_sha,
            artifact_sha256=artifacts,case_sha256=case_spec['sha256'])
        out.append(dict(material=dict(identity=identity,model=result['model'],profile=result['profile'],
            reference=reference,saved=saved,proof_input=proof_input,conditioning_certificate=certificate,
            prior_width_m=result['future_width_m'],provenance=provenance),
            truth=dict(truth,identity=identity,reference_binding=reference['binding']),
            case_name=parent+'/'+case_spec['path'],case_sha256=case_spec['sha256']))
    return out


def recipe():
    return dict(packets=96000,future_s=438.,training_rows=30,
        maximum_bound_seconds=7200.,width_target_m=[20.,20.,50.])


def limits():
    n=recipe()['packets']
    return dict(reference_setups=1,conditional_proofs=1,algebra_certificates=2,
        source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,
        source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n,
        matched_comparisons=1,lp_proposals=6,exact_supports=30,truth_audits=1)


def rebuild_prediction(region,saved,report,*,reserve,save):
    from lll.ilvis0_direct_interface import matched_bounds
    from lll.ilvis0_consistent_prediction import rebuild_future
    from lll.ilvis0_saved_prediction_audit import verify_joint_envelope
    if (region['parameter_count']!=51 or saved['parameter_count']!=51
            or saved['lower']!=region['lower'] or saved['upper']!=region['upper']
            or saved['fixed_center']!=region['center'][:27]
            or saved['time_s']!=report['time_s']
            or region['binding']!=report['reference_binding']
            or region['source_id']!=report['source_id'] or region['future_truth_used'] is not False):
        raise ValueError('unchanged complete saved domain, source and prediction time required')
    reserve(matched_comparisons=1)
    matched=matched_bounds(saved['bound'],report);save('matched-bound.json',matched)
    if not matched['passed']:raise ValueError('matched bound changed a shared map or widened a remainder')
    updated=deepcopy(saved);updated['bound']=report
    ordinals=[]
    def proposal(ordinal):
        if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six ordered future proposals required')
        # Two exact checks within propose, plus the retained old dual fallback.
        reserve(lp_proposals=1,exact_supports=3);ordinals.append(ordinal)
    updated['envelope']=rebuild_future(region,updated,updated['lower'],updated['upper'],reserve=proposal)
    save('future.json',updated)
    reserve(exact_supports=6)
    audit=verify_joint_envelope(region,updated);save('independent-audit.json',audit)
    return dict(future=updated,audit=audit,matched=matched)


def calculate(material,case,spec,*,reserve,charge,save,kernel_directory,source_directory,expected_sources):
    import time
    import numpy as np
    from lll.ilvis0_coupled_map import restore_static_reference
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_remainder_interface import bridge
    from lll import ilvis0_remainder_native as candidate
    n=spec['packets'];saved=material['saved'];bundle=material['proof_input'];region=bundle['training']['region']
    config=case['configuration']
    if (any(len(case[k])!=n for k in ('theta','dv','dt'))
            or config['model']!=spec['model'] or config['profile']!=spec['profile']
            or len(region['inequality_design'])!=spec['training_rows']
            or saved['time_s']!=spec['future_s'] or saved['reference']!=bundle['reference']
            or saved['fixed_center']!=region['center'][:27]
            or bundle['lower']!=region['lower'] or bundle['upper']!=region['upper']):
        raise ValueError('complete saved history, candidate, training region and fixed future required')
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    lo=np.asarray(region['lower'][:27]);hi=np.asarray(region['upper'][:27])
    reserve(reference_setups=1)
    ref=restore_static_reference(config,dv[0],float(dt[0]),lower=lo,upper=hi,
        center=saved['fixed_center'],expected_report=saved['reference'])
    reserve(conditional_proofs=1)
    proof=ConditionedAcceleration(bundle,material['conditioning_certificate'],
        reserve=lambda number:reserve(exact_supports=number))
    save('conditioning.json',proof.report())
    kernel_directory.mkdir(parents=True,exist_ok=True)
    arithmetic=configure_backend(kernel_directory,source_directory=source_directory)
    source,sm=load_stream(kernel_directory,source_directory=source_directory)
    derivative,dm=load_kernel(kernel_directory,source_directory=source_directory)
    point,pm=load_point(kernel_directory,source_directory=source_directory)
    compilation=dict(arithmetic=arithmetic,source=sm,derivative=dm,point=pm)
    for metadata in compilation.values():
        if metadata['compiler']!=spec['compiler'] or any(expected_sources.get('analysis/lll/'+name)!=sha
                for name,sha in metadata['sources'].items()):
            raise ValueError('compiler or bound source differs from the frozen environment')
    save('compilation.json',compilation)
    reserve(algebra_certificates=1,source_setups=1,source_steps=n,source_body_bounds=n,
        source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,
        source_point_steps=n,source_direct_steps=n)
    charge(bound_calls=1,bound_steps=9*n)
    started=time.monotonic()
    raw=candidate.enclose(config,theta,dv,dt,time=spec['future_s'],lower=lo,upper=hi,
        reference=ref,conditioning=proof,source_kernel=source,derivative_kernel=derivative,
        point_kernel=point,maximum_seconds=spec['maximum_bound_seconds'])
    save('raw-bound.json',dict(report=raw.report(),elapsed_s=time.monotonic()-started))
    if any(raw.metadata[k]>n for k in ('source_reference_steps','source_derivative_steps',
                                      'source_direct_steps','rounded_source_prefixes')):
        raise ValueError('actual source work exceeds its frozen full-history reservation')
    reserve(algebra_certificates=1)
    report=bridge(raw,ref,proof,saved['nominal'],region['coordinate_scale']).report()
    conditional=report['conditional_acceleration_remainder']
    if conditional['remainder_upper']>conditional['original_remainder']:
        raise ValueError('candidate widened the declared operational remainder')
    save('future-bound.json',report)
    result=rebuild_prediction(region,saved,report,reserve=reserve,save=save)
    return dict(result,conditional_remainder=conditional)


def evaluate(task,context):
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_sharded_native import read,plain
    spec=task['payload'];material=read(context.input_path());identity=task['identity']
    if ({k:spec.get(k) for k in recipe()}!=recipe() or spec.get('limits')!=limits()
            or material['identity']!=identity or material['model']!=spec['model']
            or material['profile']!=spec['profile']):
        raise ValueError('fixed complete-history recipe, candidate and finite allowance required')
    path=context.directory/'allowance.sqlite'
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),limits={identity:limits()})
    journal.start(identity)
    def reserve(**values):
        _check_continue(context.root,context.manifest)
        for key,number in values.items():journal.reserve(identity,key,number)
    def save(name,value):context.save(name,plain(value))
    try:
        case=read(context.input_path(spec['case_key']))
        result=calculate(material,case,spec,reserve=reserve,charge=context.charge,save=save,
            kernel_directory=context.root/'shards'/f'{getattr(context,"shard",0):03d}'/'kernels',
            source_directory=context.root/'source-freeze/analysis/lll',expected_sources=context.manifest.get('sources',{}))
        reserve(truth_audits=1)
        truth=read(context.input_path(spec['truth_key']))  # Open only after the prediction was saved.
        if (truth['identity']!=identity or truth['reference_binding']!=material['reference']['binding']
                or truth['known_truth_retained'] is not True or F(truth['maximum_exact_training_slack'])>0
                or len(truth['future_truth_m'])!=3):
            raise ValueError('unchanged saved training witness and three-axis future truth required')
        env=result['future']['envelope']
        contained=all(F(a)<=F(v)<=F(b) for a,v,b in zip(env['lower'],truth['future_truth_m'],env['upper'],strict=True))
        save('truth-audit.json',dict(truth,future_truth_contained=contained,evaluated_after_prediction=True))
        counts={key:journal.count(identity,key) for key in limits()}
        if counts!=limits():raise ValueError('complete declared work accounting required')
        save('accounting.json',counts)
        widths=result['audit']['width_m'];useful=all(F(a)<=F(b) for a,b in zip(widths,spec['width_target_m'],strict=True))
        return dict(identity=identity,passed=bool(contained and useful),numerical_checks_passed=contained,
            useful=useful,model=spec['model'],profile=spec['profile'],future_width_m=widths,
            previous_width_m=material['prior_width_m'],width_target_m=spec['width_target_m'],
            conditional_remainder=result['conditional_remainder'],work=counts,known_truth_retained=True,
            future_truth_contained=contained,future_observations_used=False,parameter_count=51,
            physical_parameter_count=27,native_evaluations=0,bound_evaluations=1,optimizer_starts=0,
            original_reads=0,observational_coverage_qualified=False,scientific_decision='abstain')
    finally:
        journal.verify();context.note_file(path)
