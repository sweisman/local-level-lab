# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_transform_native as old
from lll import ilvis0_conditioned_transform_native as candidate
from lll.ilvis0_acceleration_projection import project
from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
from lll.ilvis0_shape import load_tangent
from test_ilvis0_native_box_bounds import configuration
from test_ilvis0_regrouped_history import native


def case(model,profile,point=False):
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1))
    dv=np.c_[1e-5*np.sin(np.arange(n)),2e-5*np.cos(np.arange(n)),np.full(n,-.04905)]
    center=np.full(27,.1);outer_lo=np.full(27,-.2);outer_hi=np.full(27,.5)
    reference=old.make_reference(config,theta,dv,dt,lower=outer_lo,upper=outer_hi,center=center)
    lo=center.copy();hi=center.copy()
    if not point:lo[12:14]-=.1;hi[12:14]+=.1
    # Rotation, gain, clock and lever are fixed: all auxiliary remainders are
    # exactly zero in this affine-bias software control, not in aircraft data.
    lower=lo.tolist()+[0.]*24;upper=hi.tolist()+[0.]*24
    row=[0.]*51;row[12]=row[13]=1.
    region=dict(parameter_count=51,center=center.tolist()+[0.]*24,
        lower=lower,upper=upper,inequality_design=[row,[-v for v in row]],
        inequality_upper=[.205,-.195],binding=reference.binding,
        source_id=reference.parent.source_id,future_truth_used=False)
    bundle=dict(training=dict(region=region),reference=reference.report(),lower=lower,upper=upper)
    certificate=project(**bundle,reserve=lambda *_:None)
    conditioning=ConditionedAcceleration(bundle,certificate,reserve=lambda *_:None)
    return config,theta,dv,dt,center,lo,hi,reference,conditioning


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
@pytest.mark.parametrize('point',[False,True])
def test_conditioning_keeps_native_centres_columns_and_feasible_probe_containment(model,profile,point,tmp_path):
    config,theta,dv,dt,center,lo,hi,reference,conditioning=case(model,profile,point)
    kwargs=dict(time=.05,lower=lo,upper=hi,reference=reference)
    baseline=old.enclose(config,theta,dv,dt,**kwargs)
    report=candidate.enclose(config,theta,dv,dt,conditioning=conditioning,**kwargs)
    np.testing.assert_array_equal(report.center,baseline.center)
    np.testing.assert_array_equal(report.previous_coefficients.matrix,baseline.previous_coefficients.matrix)
    np.testing.assert_array_equal(report.acceleration_coefficients.matrix,baseline.acceleration_coefficients.matrix)
    np.testing.assert_array_equal(report.transform_coefficients.matrix,baseline.transform_coefficients.matrix)
    assert report.metadata['conditioning']['applies_only_to_training_region']
    assert report.metadata['retained_acceleration_remainder']==reference.acceleration.remainder
    assert report.metadata['conditioned_acceleration_change']<=reference.acceleration.change
    kernel=load_tangent(tmp_path)[0];value,jac=native(kernel,config,theta,dv,dt,.05,center)
    scale=np.array([6371000.,6371000.,1.]);assert np.max(abs(value-report.center)*scale)<1e-6
    design=report.design(jac,reference);assert design.shape==(3,51)
    probes=[center]
    if not point:
        for sign in (1,-1):
            probe=center.copy();probe[12]+=.08*sign;probe[13]-=.08*sign;probes.append(probe)
    for probe in probes:
        actual,_=native(kernel,config,theta,dv,dt,.05,probe)
        gamma=reference.normalized_values_at(probe)
        assert np.all(gamma==0.)
        error=abs((actual-value-design@np.r_[probe-center,gamma])*scale)
        assert np.all(error<=report.unshared_remainder*scale+1e-5)


def test_missing_condition_or_mismatched_physical_domain_is_rejected():
    config,theta,dv,dt,_,lo,hi,reference,conditioning=case(0,False)
    kwargs=dict(time=.05,lower=lo,upper=hi,reference=reference)
    with pytest.raises(ValueError,match='condition'):candidate.enclose(config,theta,dv,dt,conditioning=None,**kwargs)
    kwargs['lower']=lo.copy();kwargs['lower'][0]-=.01
    with pytest.raises(ValueError,match='domain'):candidate.enclose(config,theta,dv,dt,conditioning=conditioning,**kwargs)
