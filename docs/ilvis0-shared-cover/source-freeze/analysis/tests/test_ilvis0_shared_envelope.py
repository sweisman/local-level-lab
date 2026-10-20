# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import replace

import numpy as np
import pytest
from lll import ilvis0_shared_envelope as joint
from lll.ilvis0_shared_native import SharedEnclosure
from lll.ilvis0_shared_reference_terms import ReferenceErrors, SharedCoefficients
from test_ilvis0_shared_reference_terms import config


def fixture(center=None):
    c=np.zeros(27) if center is None else center
    reference=ReferenceErrors(config(),-np.ones(27),np.ones(27),c)
    def epoch(t, radius=0.):
        j=np.zeros((3,27));j[0,0]=1.;j[0,1]=t
        extra=np.zeros((3,6));extra[0,0]=1.
        value=j@c
        report=SharedEnclosure(value,np.full(3,radius),SharedCoefficients(extra,reference.binding),
            dict(source_id=reference.source_id,normalized_center=c.tolist(),time_s=t,
                 bound_lower=reference.lower.tolist(),bound_upper=reference.upper.tolist()))
        return value,j,report
    return reference,epoch


def train(reference, epoch, **kwargs):
    rows=[epoch(t) for t in (0.,1.)]
    return joint.training(times=[0.,1.],observations=np.zeros((2,3)),
        native_values=[r[0] for r in rows],native_jacobians=[r[1] for r in rows],reports=[r[2] for r in rows],
        reference=reference,physical_lower=reference.lower,physical_upper=reference.upper,
        coordinate_scale=np.ones(3),origin=np.zeros(3),noise_allowance=np.zeros((2,3)),arithmetic_allowance=0.,**kwargs)


def test_common_error_is_one_unknown_across_all_epochs():
    reference,epoch=fixture();region=train(reference,epoch)
    value,j,report=epoch(2.)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=reference)
    assert region.design.shape==(6,33) and region.center.shape==(33,)
    assert region.inequality_design.shape==(12,33)
    assert np.max(abs(np.r_[result['lower'],result['upper']]))<1e-12
    assert result['parameter_count']==33 and result['scientific_decision']=='abstain'
    # The p0 and common-error ambiguity is retained; only their sum is fixed.
    assert region.lower[0]==-1 and region.upper[27]==1


def test_nonzero_center_and_unshared_allowances_retain_feasible_points():
    c=np.zeros(27);c[:2]=[.2,-.1]
    reference,epoch=fixture(c);region=train(reference,epoch)
    value,j,report=epoch(2.,radius=.01)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=reference)
    assert result['lower'][0]<=-.01 and result['upper'][0]>=.01
    assert result['lower'][0]>-.011 and result['upper'][0]<.011


@pytest.mark.parametrize('field,bad',[
    ('source_id','another-recording'),('normalized_center',[.01]*27),
    ('time_s',1.9),('bound_lower',[0.]*27),('bound_upper',[0.]*27)])
def test_mismatched_native_report_is_rejected(field,bad):
    reference,epoch=fixture();region=train(reference,epoch)
    value,j,report=epoch(2.);report=replace(report,metadata=dict(report.metadata,**{field:bad}))
    with pytest.raises(ValueError):
        joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=reference)


def test_missing_shared_block_and_stale_reference_are_rejected():
    reference,epoch=fixture();region=train(reference,epoch)
    value,j,report=epoch(2.)
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=j[:,:26],report=report,reference=reference)
    other=ReferenceErrors(dict(config(),source_id='another-recording'),-np.ones(27),np.ones(27),np.zeros(27))
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=other)
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report.report(),reference=reference)


def test_contracted_domain_can_exclude_fixed_expansion_center():
    reference,epoch=fixture();region=train(reference,epoch)
    lo=region.lower.copy();hi=region.upper.copy();lo[0]=.5;hi[27]=-.5
    value,j,report=epoch(2.)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=reference,lower=lo,upper=hi)
    assert result['lower'][0]<=0<=result['upper'][0]
    assert result['upper'][0]-result['lower'][0]<1e-12
    hi[1]=2.
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=j,report=report,reference=reference,lower=lo,upper=hi)


def test_region_copies_inputs_and_keeps_zero_columns():
    reference,epoch=fixture();region=train(reference,epoch)
    assert np.count_nonzero(region.design[:,2:27])==0
    for array in (region.center,region.design,region.lower,region.upper,region.coordinate_scale,region.origin):
        assert not array.flags.writeable
    with pytest.raises(ValueError):region.design[0,0]=999.


def test_training_times_and_native_center_are_checked():
    reference,epoch=fixture()
    def wrong(t):
        value,j,report=epoch(t)
        return value+1.,j,report
    with pytest.raises(ValueError):train(reference,wrong)
    region=train(reference,epoch);value,j,report=epoch(1.)
    with pytest.raises(ValueError):joint.future(region,time=1.,native_value=value,native_jacobian=j,report=report,reference=reference)
