# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer and rejection controls for the supplied-bound 51-column API."""
from dataclasses import replace
import sys


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll import ilvis0_transform_envelope as joint
    from lll.ilvis0_transform_native import TransformReference,TransformEnclosure
    from lll.ilvis0_shared_reference_terms import ReferenceErrors,SharedCoefficients
    from lll.ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients
    from lll.ilvis0_common_force_transform import ForceTransform,ForceTransformCoefficients
    from lll.ilvis0_control_shards import _check_continue
    spec=task['payload'];config=read(context.input_path());axis=spec.get('axis',0);center=np.zeros(27)
    if spec.get('center'):center[:2]=[.125,-.25]
    parent=ReferenceErrors(config,-np.ones(27),np.ones(27),center,source_id='known-'+task['identity'])
    acceleration=AccelerationTerms(parent,[0.,0.,-.04905],.005,9.81);matrix=ForceTransform(parent)
    reference=TransformReference(acceleration,matrix);noise=.001 if spec.get('noise') else 0.;radius=.002
    def epoch(t,r):
        jac=np.zeros((3,27));jac[axis,0]=1.;jac[axis,1]=t
        old=np.zeros((3,6));added=np.zeros((3,9));force=np.zeros((3,9))
        if spec['kind']!='force-only':old[axis,0]=1.;added[axis,0]=1.
        force[axis,3*axis+spec.get('column',0)]=1.;value=jac@center
        metadata=dict(source_id=parent.source_id,time_s=t,normalized_center=center.tolist(),
            bound_lower=parent.lower.tolist(),bound_upper=parent.upper.tolist(),reference_binding=reference.binding,
            transform_reference=matrix.report(),force_integrals=dict(source_id='a'*64),
            clock_transform=dict(matrix_binding=matrix.binding,source_id='a'*64))
        return value,jac,TransformEnclosure(value,np.full(3,r),SharedCoefficients(old,parent.binding),
            AccelerationCoefficients(added,acceleration.binding),ForceTransformCoefficients(force,matrix.binding),metadata)
    epochs=[epoch(t,0.) for t in (0.,1.)]
    def training(reports):
        return joint.training(times=[0.,1.],observations=np.zeros((2,3)),native_values=[x[0] for x in epochs],
            native_jacobians=[x[1] for x in epochs],reports=reports,reference=reference,
            physical_lower=parent.lower,physical_upper=parent.upper,coordinate_scale=np.ones(3),origin=np.zeros(3),
            noise_allowance=np.full((2,3),noise),arithmetic_allowance=0.)
    region=training([x[2] for x in epochs]);value,jac,report=epoch(2.,radius)
    negative=spec['kind']=='rejection';maximum=0 if negative else 6
    context.save('reservation.json',dict(maximum_lp_proposals=maximum,maximum_exact_certificates=2*maximum))
    calls=0;certificates=0
    if sys.getprofile() is not None:raise ValueError('existing profiler must not be replaced')
    propose_code=joint.support.propose.__code__;certificate_code=joint.support.upper.__code__
    def observer(frame,event,arg):
        nonlocal calls,certificates
        if event!='call':return
        if frame.f_code==propose_code:
            _check_continue(context.root,context.manifest)
            if calls>=maximum:raise RuntimeError('unreserved LP attempt in joint control')
            calls+=1;context.save(f'proposal-{calls:02d}.json',dict(ordinal=calls,maximum_seconds=1))
        elif frame.f_code==certificate_code:
            if certificates>=2*maximum:raise RuntimeError('unreserved exact support certificate')
            certificates+=1;context.save(f'certificate-{certificates:02d}.json',dict(ordinal=certificates))
    def future(**extra):return joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference,**extra)
    rejected=False;result=None
    try:
        sys.setprofile(observer)
        if negative:
            field=spec['field']
            if field=='old-binding':report=replace(report,previous_coefficients=SharedCoefficients(report.previous_coefficients.matrix,'stale'))
            elif field=='acc-binding':report=replace(report,acceleration_coefficients=AccelerationCoefficients(report.acceleration_coefficients.matrix,'stale'))
            elif field=='force-binding':report=replace(report,transform_coefficients=ForceTransformCoefficients(report.transform_coefficients.matrix,'stale'))
            elif field not in ('training-force-source','future-observation'):
                changes={'source':dict(source_id='other'),'time':dict(time_s=1.9),'center':dict(normalized_center=[.1]*27),
                    'lower':dict(bound_lower=[0.]*27),'upper':dict(bound_upper=[0.]*27),
                    'force-source':dict(force_integrals=dict(source_id='b'*64)),
                    'clock-source':dict(clock_transform=dict(source_id='b'*64,matrix_binding=matrix.binding)),
                    'clock-matrix':dict(clock_transform=dict(source_id='a'*64,matrix_binding='stale')),
                    'matrix-binding':dict(transform_reference=dict(binding='stale')),'reference-binding':dict(reference_binding='stale')}
                report=replace(report,metadata=dict(report.metadata,**changes[field]))
            try:
                if field=='training-force-source':
                    second=epochs[1][2];bad=replace(second,metadata=dict(second.metadata,force_integrals=dict(source_id='b'*64),
                        clock_transform=dict(source_id='b'*64,matrix_binding=matrix.binding)))
                    training([epochs[0][2],bad])
                elif field=='future-observation':future(observations=np.zeros(3))
                else:future()
            except (ValueError,TypeError):rejected=True
        else:result=future()
    finally:sys.setprofile(None)
    if negative:
        return dict(identity=task['identity'],passed=rejected and calls==0 and certificates==0,rejected=rejected,
            parameter_count=51,lp_proposals=calls,exact_certificates=certificates,original_reads=0,native_evaluations=0,scientific_decision='abstain')
    expected=np.full(3,radius);expected[axis]+=3*noise
    selected=42+3*axis+spec.get('column',0)
    passed=(np.all(result['lower']<=-expected) and np.all(result['upper']>=expected)
        and np.max(abs(result['upper']-expected))<1e-12 and np.max(abs(result['lower']+expected))<1e-12
        and region.design.shape==(6,51) and np.count_nonzero(region.design[:,2:27])==0
        and np.count_nonzero(region.design[:,selected])==2 and calls==6 and certificates==12)
    return plain(dict(identity=task['identity'],passed=bool(passed),expected_radius=expected,region=region.report(),future=result,
        selected_force_column=selected,parameter_count=51,lp_proposals=calls,exact_certificates=certificates,
        original_reads=0,native_evaluations=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain'))
