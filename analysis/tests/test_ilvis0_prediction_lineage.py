# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata contracts only: no numerical imports, trajectories or fits."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import pytest


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def fixture():
    times=list(map(float,range(2,291)));future=list(map(float,range(292,439)))
    source=dict(source_id='source',reference_binding='reference',normalized_center=[0.]*27,
        lower=[-1.]*27,upper=[1.]*27)
    region=dict(parameter_count=51,center=[0.]*51,lower=[-1.]*51,upper=[1.]*51,
        coordinate_scale=[1.,1.,1.],arithmetic_allowance=0.,design=[[0.]*51 for _ in range(3*len(times))])
    training=dict(region=region,times_s=times,observations=[[0.,0.,0.] for _ in times],
        nominal=[[0.,0.,0.] for _ in times],source_binding=source)
    physical=dict(version='ilvis0-physical-directional-acceleration-v1',uses_training_data=False,
        applies_only_to_physical_domain=True,reference_binding='reference',source_id='source',
        lower=source['lower'],upper=source['upper'])
    reports=[dict(source,time_s=t,center=[0.,0.,0.],unshared_remainder=[0.,0.,0.],conditioning=physical) for t in times]
    # Arbitrary fixed metadata rows test identity wiring. They do not stand in
    # for the separately qualified numerical Legendre construction.
    weights=[]
    for j in range(12):
        row=[0.]*(3*len(times));row[j]=1.;weights.append(row)
    expr=dict(nominal=training['nominal'],observations=training['observations'],design=region['design'],
        unshared_remainders=[r['unshared_remainder'] for r in reports],arithmetic_allowance=0.,
        lower=region['lower'],upper=region['upper'],center=region['center'])
    binding=dict(source=source,times_s=times,coordinate_scale=[1.,1.,1.],expression_sha256=identity(expr),
        weights=weights,expression_columns=51,physical_parameter_count=27,enclosure_parameter_count=51)
    rows=dict(binding=binding,projected_training_id=identity(binding),parameter_count=51,
        physical_parameter_count=27,original_expression_columns=51,new_rows=24,
        observation_allowance_m=[2.]*12,design=[[0.]*51 for _ in range(24)],upper=[2.]*24,
        future_observations_used=False)
    law=dict(times_s=times+future,clock_interval_s=['-1','1'],origin_s='0')
    covariance=identity(law)
    projection=dict(version='ilvis0-fixed-linear-variance-v1',covariance_id=covariance,
        weights=[[str(F(v)) for v in row]+['0']*(3*len(future)) for row in weights])
    ids=[f'training:legendre-{j}:{axis}' for j in range(4) for axis in ('north','east','up')]
    ids += [f'future:{t}:{axis}' for t in future for axis in ('north','east','up')]
    family=dict(summary_projection_id=identity(projection),future_times_s=future,covariance_id=covariance,row_ids=ids)
    errors=dict(law=law,covariance_id=covariance,summary_projection_id=identity(projection),
        family_projection_id=identity(family),scalar_family_count=453,training_epochs=289,
        summary_rows=12,future_epochs=147,future_observations_used=False,
        allowances=dict(supported=True,coordinate_count=453,covariance_id=covariance,
            projection_id=identity(family),row_ids=ids,radius_m=[2.]*453))
    new_region=dict(region,binding='reference',source_id='source',future_truth_used=False,
        inequality_design=rows['design'],inequality_upper=rows['upper'])
    bundle=dict(training={'region':new_region},reference={'binding':'reference','parent':{'source_id':'source'}},
        lower=region['lower'],upper=region['upper'])
    return training,reports,rows,errors,bundle


def test_physical_roots_and_matching_training_origins_form_an_acyclic_chain():
    from lll.ilvis0_prediction_lineage import register
    args=fixture();origin=register(*args)
    assert origin.input_binding==identity(args[-1]) and not origin.parents
    assert not origin.report()['prediction_method_qualified']
    training,reports,rows,errors,bundle=deepcopy(args)
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            input_binding=origin.input_binding,source_id='source',reference_binding='reference')
    bundle['training']['region']['inequality_design']=list(map(list,origin.design))+rows['design']
    bundle['training']['region']['inequality_upper']=list(origin.upper_bounds)+rows['upper']
    second=register(training,reports,rows,errors,bundle,origins=[origin])
    assert second.parents==(origin.input_binding,)
    with pytest.raises(ValueError,match='circular'):
        register(*args,origins=[origin])


def test_old_one_metre_conditioning_is_not_authorized_by_new_noise_labels():
    from lll.ilvis0_prediction_lineage import register
    training,reports,rows,errors,bundle=fixture()
    reports[0]['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
        input_binding='old-one-metre-proof',source_id='source',reference_binding='reference')
    with pytest.raises(ValueError,match='unknown training premise'):
        register(training,reports,rows,errors,bundle)


@pytest.mark.parametrize('change',('radius','weights','observations','inequalities','future','frame'))
def test_incompatible_training_and_error_artifacts_are_rejected(change):
    from lll.ilvis0_prediction_lineage import register
    training,reports,rows,errors,bundle=fixture()
    if change=='radius':rows['observation_allowance_m'][0]=1.
    if change=='weights':rows['binding']['weights'][0][0]=.5;rows['projected_training_id']=identity(rows['binding'])
    if change=='observations':training['observations'][0][0]=1.
    if change=='inequalities':bundle['training']['region']['inequality_upper']=[1.]*24
    if change=='future':training['times_s'][-1]=292.
    if change=='frame':reports[0]['reference_binding']='other'
    with pytest.raises(ValueError):register(training,reports,rows,errors,bundle)


def test_a_valid_origin_cannot_be_transferred_to_a_different_error_family():
    from lll.ilvis0_prediction_lineage import register
    args=fixture();origin=register(*args)
    training,reports,rows,errors,bundle=deepcopy(args)
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            input_binding=origin.input_binding,source_id='source',reference_binding='reference')
    errors['law']['declared_case']='different supplied law'
    covariance=identity(errors['law']);errors['covariance_id']=covariance
    projection=dict(version='ilvis0-fixed-linear-variance-v1',covariance_id=covariance,
        weights=[[str(F(v)) for v in row]+['0']*(3*147) for row in rows['binding']['weights']])
    errors['summary_projection_id']=identity(projection)
    family=dict(summary_projection_id=identity(projection),future_times_s=list(map(float,range(292,439))),
        covariance_id=covariance,row_ids=errors['allowances']['row_ids'])
    errors['family_projection_id']=identity(family)
    errors['allowances'].update(covariance_id=covariance,projection_id=identity(family))
    bundle['training']['region']['inequality_design']=list(map(list,origin.design))+rows['design']
    bundle['training']['region']['inequality_upper']=list(origin.upper_bounds)+rows['upper']
    with pytest.raises(ValueError,match='different error family'):
        register(training,reports,rows,errors,bundle,origins=[origin])


def test_conditioned_parent_constraints_cannot_be_dropped():
    from lll.ilvis0_prediction_lineage import register
    args=fixture();origin=register(*args)
    training,reports,rows,errors,bundle=deepcopy(args)
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            input_binding=origin.input_binding,source_id='source',reference_binding='reference')
    bundle['training']['region']['note']='new stage without inherited constraints'
    with pytest.raises(ValueError,match='parent constraints'):
        register(training,reports,rows,errors,bundle,origins=[origin])


def test_same_covariance_does_not_authorize_a_different_error_allowance():
    from lll.ilvis0_prediction_lineage import register
    args=fixture();origin=register(*args)
    training,reports,rows,errors,bundle=deepcopy(args)
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            input_binding=origin.input_binding,source_id='source',reference_binding='reference')
    errors['allowances']['radius_m']=[4.]*453
    errors['allowances']['critical']=10
    rows['observation_allowance_m']=[4.]*12;rows['upper']=[4.]*24
    bundle['training']['region']['inequality_design']=list(map(list,origin.design))+rows['design']
    bundle['training']['region']['inequality_upper']=list(origin.upper_bounds)+rows['upper']
    with pytest.raises(ValueError,match='different error'):
        register(training,reports,rows,errors,bundle,origins=[origin])


def test_parent_auxiliary_domain_and_observation_identity_are_preserved():
    from lll.ilvis0_prediction_lineage import register
    args=fixture();args[-1]['lower']=list(args[-1]['lower']);args[-1]['upper']=list(args[-1]['upper'])
    args[-1]['lower'][45]=-.5;args[-1]['upper'][45]=.5
    origin=register(*args)
    training,reports,rows,errors,bundle=deepcopy(args)
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            input_binding=origin.input_binding,source_id='source',reference_binding='reference')
    bundle['training']['region']['note']='new stage'
    with pytest.raises(ValueError,match='parent proof domain'):
        register(training,reports,rows,errors,bundle,origins=[origin])
    training['observations'][0][0]=1.
    with pytest.raises(ValueError,match='observations changed'):
        register(training,reports,rows,errors,bundle,origins=[origin])
