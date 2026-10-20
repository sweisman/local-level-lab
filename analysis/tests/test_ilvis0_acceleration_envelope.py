# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import replace

import numpy as np
import pytest
from lll import ilvis0_acceleration_envelope as joint
from lll.ilvis0_acceleration_native import AccelerationEnclosure
from lll.ilvis0_reference_acceleration import AccelerationTerms,AccelerationCoefficients
from lll.ilvis0_shared_reference_terms import SharedCoefficients
from test_ilvis0_shared_envelope import fixture as previous_fixture


def fixture(center=None):
    previous,epoch=previous_fixture(center)
    terms=AccelerationTerms(previous,[0.,0.,-.04905],.005,9.81)
    def candidate(t,radius=0.):
        value,jac,old=epoch(t,radius);extra=np.zeros((3,9));extra[0,0]=1.
        return value,jac,AccelerationEnclosure(value,old.unshared_remainder,old.coefficients,
            AccelerationCoefficients(extra,terms.binding),old.metadata)
    return terms,candidate


def train(terms,epoch):
    r=terms.reference;rows=[epoch(t) for t in (0.,1.)]
    return joint.training(times=[0.,1.],observations=np.zeros((2,3)),native_values=[x[0] for x in rows],
        native_jacobians=[x[1] for x in rows],reports=[x[2] for x in rows],reference=terms,
        physical_lower=r.lower,physical_upper=r.upper,coordinate_scale=np.ones(3),origin=np.zeros(3),
        noise_allowance=np.zeros((2,3)),arithmetic_allowance=0.)


def test_both_common_blocks_are_joint_unknowns_at_all_epochs():
    terms,epoch=fixture();region=train(terms,epoch);value,jac,report=epoch(2.)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=terms)
    assert region.design.shape==(6,42) and region.center.shape==(42,)
    assert np.max(abs(np.r_[result['lower'],result['upper']]))<1e-12
    assert result['scientific_decision']=='abstain' and result['parameter_count']==42
    assert region.lower[27]==-1 and region.upper[33]==1


@pytest.mark.parametrize('field', ['source','time','center','domain','old-block','new-block'])
def test_mismatched_native_or_either_common_block_is_rejected(field):
    terms,epoch=fixture();region=train(terms,epoch);value,jac,report=epoch(2.)
    if field=='old-block':report=replace(report,previous_coefficients=SharedCoefficients(report.previous_coefficients.matrix,'stale'))
    elif field=='new-block':report=replace(report,acceleration_coefficients=AccelerationCoefficients(report.acceleration_coefficients.matrix,'stale'))
    else:
        key,bad={'source':('source_id','other'),'time':('time_s',1.9),'center':('normalized_center',[.1]*27),
            'domain':('bound_lower',[0.]*27)}[field]
        report=replace(report,metadata=dict(report.metadata,**{key:bad}))
    with pytest.raises(ValueError):joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=terms)


def test_nonzero_center_remainder_and_contracted_domain():
    c=np.zeros(27);c[:2]=[.2,-.1];terms,epoch=fixture(c);region=train(terms,epoch)
    lo=region.lower.copy();hi=region.upper.copy();lo[0]=.5;hi[27]=-.5;hi[33]=0.
    value,jac,report=epoch(2.,.01)
    result=joint.future(region,time=2.,native_value=value,native_jacobian=jac,report=report,reference=terms,lower=lo,upper=hi)
    assert result['lower'][0]<=-.01 and result['upper'][0]>=.01
    assert result['upper'][0]-result['lower'][0]<.021
    assert not region.design.flags.writeable and not region.origin.flags.writeable
    with pytest.raises(ValueError):region.design[0,0]=9.
