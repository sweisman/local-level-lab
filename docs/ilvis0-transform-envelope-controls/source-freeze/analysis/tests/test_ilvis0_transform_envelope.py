# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import replace
import numpy as np
import pytest
from lll import ilvis0_transform_envelope as joint
from lll.ilvis0_transform_native import TransformReference,TransformEnclosure
from lll.ilvis0_common_force_transform import ForceTransform,ForceTransformCoefficients
from lll.ilvis0_shared_reference_terms import SharedCoefficients
from lll.ilvis0_reference_acceleration import AccelerationCoefficients
from test_ilvis0_acceleration_envelope import fixture as previous_fixture


def fixture(center=None):
    acceleration,epoch=previous_fixture(center);transform=ForceTransform(acceleration.reference)
    reference=TransformReference(acceleration,transform)
    def candidate(t,radius=0.):
        value,jac,old=epoch(t,radius);force=np.zeros((3,9));force[0,0]=1.
        metadata=dict(old.metadata,reference_binding=reference.binding,transform_reference=transform.report(),
            force_integrals=dict(source_id='a'*64),clock_transform=dict(matrix_binding=transform.binding,source_id='a'*64))
        return value,jac,TransformEnclosure(value,old.unshared_remainder,old.previous_coefficients,old.acceleration_coefficients,
            ForceTransformCoefficients(force,transform.binding),metadata)
    return reference,candidate


def train(reference,epoch):
    r=reference.parent;rows=[epoch(t) for t in (0.,1.)]
    return joint.training(times=[0.,1.],observations=np.zeros((2,3)),native_values=[x[0] for x in rows],
        native_jacobians=[x[1] for x in rows],reports=[x[2] for x in rows],reference=reference,
        physical_lower=r.lower,physical_upper=r.upper,coordinate_scale=np.ones(3),origin=np.zeros(3),
        noise_allowance=np.zeros((2,3)),arithmetic_allowance=0.)


def test_all_three_common_blocks_are_one_joint_unknown_across_epochs():
    reference,epoch=fixture();region=train(reference,epoch);value,jac,report=epoch(2.)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference)
    assert region.design.shape==(6,51) and region.center.shape==(51,)
    assert np.max(abs(np.r_[result['lower'],result['upper']]))<1e-12
    assert result['parameter_count']==51 and region.upper[50]==1.
    assert result['scientific_decision']=='abstain'


@pytest.mark.parametrize('field',['source','time','center','domain','old','acceleration','transform','force-source','clock-matrix','reference'])
def test_mismatched_native_or_any_common_source_is_rejected(field):
    reference,epoch=fixture();region=train(reference,epoch);value,jac,report=epoch(2.)
    if field=='old':report=replace(report,previous_coefficients=SharedCoefficients(report.previous_coefficients.matrix,'stale'))
    elif field=='acceleration':report=replace(report,acceleration_coefficients=AccelerationCoefficients(report.acceleration_coefficients.matrix,'stale'))
    elif field=='transform':report=replace(report,transform_coefficients=ForceTransformCoefficients(report.transform_coefficients.matrix,'stale'))
    else:
        changes={'source':dict(source_id='other'),'time':dict(time_s=1.9),'center':dict(normalized_center=[.1]*27),
            'domain':dict(bound_lower=[0.]*27),'force-source':dict(force_integrals=dict(source_id='b'*64)),
            'clock-matrix':dict(clock_transform=dict(matrix_binding='stale',source_id='a'*64)),
            'reference':dict(reference_binding='stale')}
        report=replace(report,metadata=dict(report.metadata,**changes[field]))
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference)


def test_contracted_domain_and_nonlinear_radius_stay_explicit():
    center=np.zeros(27);center[:2]=[.2,-.1];reference,epoch=fixture(center);region=train(reference,epoch)
    lo=region.lower.copy();hi=region.upper.copy();lo[0]=.5;hi[27]=-.5;hi[33]=0.;hi[42]=0.
    value,jac,report=epoch(2.,.01)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=reference,lower=lo,upper=hi)
    assert result['lower'][0]<=-.01 and result['upper'][0]>=.01
    assert result['upper'][0]-result['lower'][0]<.021
    with pytest.raises(ValueError):region.design[0,0]=9.
