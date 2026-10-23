# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from copy import deepcopy
import numpy as np
import pytest
from lll import ilvis0_coupled_map as coupled
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_common_force_transform import ForceTransform
from lll.ilvis0_transform_native import TransformReference
from lll.ilvis0_interval_calibration import couple
from test_ilvis0_shared_reference_terms import config


def reference(*,fixed=False):
    center=np.full(27,.1);lower=center.copy() if fixed else -np.ones(27)
    upper=center.copy() if fixed else np.ones(27)
    r=ReferenceErrors(config(),lower,upper,center)
    return TransformReference(AccelerationTerms(r,[.001,-.002,-.04905],.005,9.81),ForceTransform(r))


def test_complete_source_map_values_are_inside_independent_oracle_bounds():
    ref=reference();model=coupled.StaticMap(ref,expected_report=ref.report())
    lower=np.full(27,-.4);upper=np.full(27,.6);bounds=model.bound(lower,upper)
    assert len(bounds)==24 and all(len(v.derivative)==27 for v in bounds)
    for point in (lower,upper,np.linspace(-.3,.5,27)):
        oracle=ref.normalized_values_at(point)
        assert all(b.value.lo<=v<=b.value.hi for b,v in zip(bounds,oracle))
    assert model.report()['reference_binding']==ref.binding
    assert model.report()['whole_program_roundoff_qualified'] is False


def test_velocity_clock_derivatives_agree_with_exact_bilinear_formula():
    ref=reference();model=coupled.StaticMap(ref,expected_report=ref.report())
    point=np.full(27,.3);values=model.bound(point,point)
    r=ref.parent
    expected=F(float(r.limits[3]))*F(float(r.limits[25]))*(F(.3)-F(.1))/F(float(r.caps[0]))
    for column in (3,25):assert values[0].derivative[column].lo<=expected<=values[0].derivative[column].hi
    assert all(v.lo==v.hi==0. for j,v in enumerate(values[0].derivative) if j not in (3,25))


def test_point_bounds_are_narrow_and_preserve_source_zero_conventions():
    ref=reference();model=coupled.StaticMap(ref,expected_report=ref.report());point=np.full(27,.17)
    values=model.bound(point,point);expected=ref.normalized_values_at(point)
    assert max(v.value.hi-v.value.lo for v in values)<1e-4
    assert all(b.value.lo<=v<=b.value.hi for b,v in zip(values,expected))
    at_origin=model.bound(ref.parent.center,ref.parent.center)
    assert all(v.value.lo<=0.<=v.value.hi for v in at_origin)
    fixed=reference(fixed=True);fixed_map=coupled.StaticMap(fixed,expected_report=fixed.report())
    assert all(v.value.lo==v.value.hi==0. for v in fixed_map.bound(fixed.parent.center,fixed.parent.center))


def test_coupled_rows_keep_all_coordinates_and_known_feasible_generated_points():
    ref=reference();model=coupled.StaticMap(ref,expected_report=ref.report())
    lo=np.full(27,-.15);hi=np.full(27,.25);center=(lo+hi)/2
    cuts=couple(model.bound(lo,hi),model.bound(center,center),lo,hi,center)
    assert cuts['parameter_count']==51 and len(cuts['design'])==48
    for point in (lo,hi,center):
        x=list(map(F,point))+list(map(F,ref.normalized_values_at(point)))
        assert all(sum((F(a)*v for a,v in zip(row,x)),F(0))<=F(bound)
            for row,bound in zip(cuts['design'],cuts['upper']))


def test_changed_source_invalid_box_and_negative_numerical_allowance_are_rejected():
    ref=reference();report=deepcopy(ref.report());report['parent']['binding']='different'
    with pytest.raises(ValueError):coupled.StaticMap(ref,expected_report=report)
    with pytest.raises(ValueError):coupled.StaticMap(ref,expected_report=ref.report(),numerical_allowance=-1.)
    model=coupled.StaticMap(ref,expected_report=ref.report())
    with pytest.raises(ValueError):model.bound(np.full(27,-1.1),np.ones(27))
    with pytest.raises(ValueError):model.bound(np.zeros(26),np.ones(26))


def test_bound_source_and_normalization_cannot_be_changed_after_construction():
    from dataclasses import FrozenInstanceError
    ref=reference();model=coupled.StaticMap(ref,expected_report=ref.report())
    with pytest.raises(FrozenInstanceError):model.reference=reference(fixed=True)
    with pytest.raises(ValueError):model.caps[0]=1.
    with pytest.raises(ValueError):model.rotation_jacobian[0][0,0]=1.


def test_static_reference_restores_from_verified_start_without_reading_history(monkeypatch):
    from lll import ilvis0_shared_native
    monkeypatch.setattr(ilvis0_shared_native,'_data',lambda *a:pytest.fail('no trajectory history read'))
    ref=reference()
    restored=coupled.restore_static_reference(dict(config(),gravity=9.81),ref.acceleration.raw_delta_v,ref.acceleration.period,
        lower=ref.parent.lower,upper=ref.parent.upper,center=ref.parent.center,expected_report=ref.report())
    assert restored.report()==ref.report()
    assert np.array_equal(restored.normalized_values_at(np.full(27,.17)),
        ref.normalized_values_at(np.full(27,.17)))


@pytest.mark.parametrize('changed',['force','period','rotation','report'])
def test_static_reference_rejects_changed_source_start_or_reference(changed):
    ref=reference();configuration=dict(config(),gravity=9.81);raw=ref.acceleration.raw_delta_v.copy()
    period=ref.acceleration.period;report=deepcopy(ref.report())
    if changed=='force':raw[0]+=.001
    elif changed=='period':period*=2
    elif changed=='rotation':configuration['initial_r']=[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]
    else:report['transform']['caps'][0]*=2
    with pytest.raises(ValueError):coupled.restore_static_reference(configuration,raw,period,
        lower=ref.parent.lower,upper=ref.parent.upper,center=ref.parent.center,expected_report=report)
