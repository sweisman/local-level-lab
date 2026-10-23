# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditioning-interface checks; supplied reports are not native enclosures."""
from copy import deepcopy
import pytest


def test_center_transfer_preserves_raw_report_and_bounds_the_exact_translation():
    import math
    from fractions import Fraction as F
    from lll.ilvis0_dense_training import transfer_center
    from lll.studies.artifacts import encoded,digest
    raw=dict(center=[-.8,1.,10000.],unshared_remainder=[2e-9,3e-9,.2],
        source_id='unchanged',reference_binding='same',conditioning={'physical':True})
    before=deepcopy(raw);center=[math.nextafter(raw['center'][i],math.inf) for i in range(3)]
    result=transfer_center(raw,center,coordinate_scale=[6371000.,2692500.,1.],maximum_center_error_m=1e-5)
    assert raw==before and result['center']==center
    assert result['center_transfer']['original_report_sha256']==digest(encoded(raw))
    for i in range(3):
        radius=F(raw['unshared_remainder'][i])+abs(F(raw['center'][i])-F(center[i]))
        assert F(result['unshared_remainder'][i])>=radius
        for sign in (-1,1):
            endpoint=F(raw['center'][i])+sign*F(raw['unshared_remainder'][i])
            assert abs(endpoint-F(center[i]))<=F(result['unshared_remainder'][i])
    assert result['source_id']==raw['source_id'] and result['conditioning']==raw['conditioning']
    with pytest.raises(ValueError,match='already'):
        transfer_center(result,center,coordinate_scale=[6371000.,2692500.,1.],maximum_center_error_m=1e-5)


@pytest.mark.parametrize('change',['too_far','nonfinite','negative_radius','scale','tolerance'])
def test_center_transfer_rejects_unsupported_or_excessive_changes(change):
    from lll.ilvis0_dense_training import transfer_center
    raw=dict(center=[0.,0.,0.],unshared_remainder=[0.,0.,0.]);target=[0.,0.,0.];scale=[1.,1.,1.];tol=1e-5
    if change=='too_far':target[0]=1.
    elif change=='nonfinite':target[1]=float('nan')
    elif change=='negative_radius':raw['unshared_remainder'][2]=-1.
    elif change=='scale':scale[0]=0.
    else:tol=-1.
    with pytest.raises(ValueError):transfer_center(raw,target,coordinate_scale=scale,maximum_center_error_m=tol)


def test_dense_builder_rejects_old_constraints_before_doing_row_arithmetic():
    from test_ilvis0_prediction_lineage import fixture
    from lll.ilvis0_dense_training import build
    training,reports,rows,errors,old_bundle=fixture()
    training['region']['inequality_design']=rows['design']
    training['region']['inequality_upper']=rows['upper']
    with pytest.raises(ValueError,match='typed parent'):
        build(training,reports,reference=old_bundle['reference'],errors=errors)


def test_dense_builder_rejects_unknown_old_conditioning_without_relabeling_it():
    from test_ilvis0_prediction_lineage import fixture
    from lll.ilvis0_dense_training import build
    training,reports,rows,errors,old_bundle=fixture()
    reports[0]['conditioning'].update(version='ilvis0-verified-training-acceleration-v1',input_binding='old-one-metre')
    with pytest.raises(ValueError,match='unknown training'):
        build(training,reports,reference=old_bundle['reference'],errors=errors)


@pytest.fixture(scope='module')
def dense_case():
    from test_ilvis0_declared_training_rows import fixture
    from lll.ilvis0_summary_error_controls import calculate,recipe
    training,reports=fixture();template=deepcopy(training);bounds=deepcopy(reports)
    times=list(map(float,range(2,291)));n=len(times);training['times_s']=times
    for name in ('nominal','observations','jacobian'):
        training[name]=[deepcopy(template[name][i%2]) for i in range(n)]
    region=training['region'];region['parameter_count']=51;region['center']=region['center'][:51]
    region.update(lower=[-2.]*51,upper=[2.]*51)
    region['design']=[deepcopy(template['region']['design'][3*(i%2)+j]) for i in range(n) for j in range(3)]
    source=dict(source_id='artificial-expression',reference_binding='fixed-frame',
        normalized_center=region['center'][:27],lower=[-2.]*27,upper=[2.]*27)
    training['source_binding']=source;reports=[]
    for i,t in enumerate(times):
        r=deepcopy(bounds[i%2]);r.update(deepcopy(source));r['time_s']=t
        r['conditioning']=dict(version='ilvis0-physical-directional-acceleration-v1',uses_training_data=False,
            applies_only_to_physical_domain=True,source_id=source['source_id'],reference_binding=source['reference_binding'],
            lower=source['lower'],upper=source['upper'])
        reports.append(r)
    errors=calculate(recipe()['times_s'],correlation_s=10,gyro_psd=1e-12)
    reference=dict(binding=source['reference_binding'],parent=dict(source_id=source['source_id']))
    return training,reports,reference,errors


def test_dense_builder_connects_actual_error_family_rows_and_typed_origin(dense_case):
    from lll.ilvis0_dense_training import build
    from lll.ilvis0_prediction_lineage import register
    training,reports,reference,errors=deepcopy(dense_case)
    before=deepcopy(training)
    first=build(training,reports,reference=reference,errors=errors)
    assert training==before
    assert len(first['rows']['design'])==24 and all(len(r)==51 for r in first['rows']['design'])
    assert first['rows']['observation_allowance_m']==errors['allowances']['radius_m'][:12]
    assert first['bundle']['training']['error_family_id']==first['origin'].family_id
    assert first['bundle']['training']['error_premise_id']==first['origin'].error_premise_id
    assert not first['origin'].report()['prediction_method_qualified']
    assert register(training,reports,first['rows'],errors,first['bundle'])==first['origin']
    origin=first['origin']
    for report in reports:
        report['conditioning']=dict(version='ilvis0-verified-training-acceleration-v1',
            source_id=training['source_binding']['source_id'],reference_binding=reference['binding'],
            input_binding=origin.input_binding)
    training['region']['inequality_design']=list(map(list,origin.design))
    training['region']['inequality_upper']=list(origin.upper_bounds)
    second=build(training,reports,reference=reference,errors=errors,origins=[origin])
    assert second['origin'].parents==(origin.input_binding,)
    problem=second['bundle']['training']['region']
    assert len(problem['inequality_design'])==48
    assert problem['inequality_design'][:24]==list(map(list,origin.design))
    assert problem['inequality_upper'][:24]==list(origin.upper_bounds)


def test_dense_builder_rejects_mutated_family_or_inherited_inequalities(dense_case):
    from lll.ilvis0_dense_training import build
    training,reports,reference,errors=deepcopy(dense_case)
    errors['allowances']['projection_id']='different'
    with pytest.raises(ValueError,match='identity'):
        build(training,reports,reference=reference,errors=errors)
