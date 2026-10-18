# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer controls for ULP-qualified sides, without archive observations."""
import numpy as np
import pytest

from test_ilvis0_boundary_adapter import Surface,physical,clock_oracle,motion_kernels


def candidate():
    from lll import ilvis0_representable_boundary
    return ilvis0_representable_boundary


class NarrowSurface(Surface):
    def __init__(self,kind='minimum'):
        from lll.ilvis0_boundary_adapter import transitions
        self.kind=kind;self.calls=[];self.count=1000;self.scale=.15
        ends=np.cumsum(np.full(self.count,.005));offset=-.3163
        self.times=ends[[199,399,599,799]]-offset*self.scale+np.arange(4)*4e-15
        self.truth=transitions(self.times,self.count,self.scale,offset)['knots'][2]


def check(surface,tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    point=np.array([0.,surface.truth+1e-7]);saved=surface.evaluate(point,fresh=True)[0];surface.calls.clear()
    ledger=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=26);ledger.start('endpoint')
    result=candidate().check_endpoint(ledger,'endpoint',lambda u,m:surface.evaluate(u,fresh=True),
        'sphere_still',point,saved,physical,time_index=1,geometry_at=None,
        times=surface.times,packet_count=surface.count,scale=surface.scale)
    assert result['evaluations']==len(surface.calls)==ledger.count('endpoint','diagnostic')<=26
    return result


def test_narrow_known_minimum_passes_without_relaxing_scientific_limits(tmp_path):
    from lll import ilvis0_clock_brackets as clock,ilvis0_boundary_stop as stopping
    surface=NarrowSurface();old=clock.bracket(surface.times,surface.count,surface.scale,surface.truth)
    assert not old['side_geometry_supported']
    result=check(surface,tmp_path)
    assert result['passed'] and result['boundary_check']['passed']
    assert result['normalized_parameters']==pytest.approx([0.,surface.truth],abs=0,rel=0)
    assert result['cumulative_from_source']['passed']
    for key in ('stationarity_tolerance','relative_cost_tolerance','position_rms_tolerance_m','position_max_tolerance_m'):
        assert result['boundary_check']['policy'][key]==stopping.POLICY[key]
    assert result['geometry']['representability']['passed']


def test_narrow_clock_states_match_independent_compiled_comparison(clock_oracle,record_property):
    surface=NarrowSurface();g=candidate().bracket(surface.times,surface.count,surface.scale,surface.truth)
    assert g['side_geometry_supported'] and g['queries']<=g['maximum_queries']==1024
    before=clock_oracle(surface.times,surface.count,surface.scale,np.nextafter(g['point'],-np.inf))
    at=clock_oracle(surface.times,surface.count,surface.scale,g['point'])
    assert not np.array_equal(before,at)
    for i,p in enumerate(g['side_points']):
        assert np.array_equal(clock_oracle(surface.times,surface.count,surface.scale,p),before if i<2 else at)
    record_property('compiled_clock_queries',6)


def test_broad_geometry_recovers_same_known_solution(tmp_path):
    surface=Surface();result=check(surface,tmp_path)
    assert result['passed'] and result['normalized_parameters']==pytest.approx([0.,surface.truth],abs=0,rel=0)


@pytest.mark.parametrize('kind',['maximum','discontinuous','unfinished_nuisance'])
def test_narrow_bad_solutions_keep_abstention(kind,tmp_path):
    assert not check(NarrowSurface(kind),tmp_path)['passed']


@pytest.mark.parametrize('offset',[1,4,8])
def test_collapsed_or_insufficient_ulp_branches_rejected(offset):
    t=-.3163;step=np.spacing(abs(t))
    assert not candidate().probe_geometry(t,t-offset*step,t+offset*step)['passed']


@pytest.mark.parametrize('values',[(np.nan,-1.,1.),(0.,0.,1.),(2.,-1.,3.),(.1,.2,.3)])
def test_invalid_partitions_rejected(values):
    with pytest.raises(ValueError):candidate().probe_geometry(*values)


def test_wrong_clock_state_cannot_qualify_geometry(monkeypatch):
    from lll import ilvis0_clock_brackets as clock
    surface=NarrowSurface();original=clock.indices
    # Supply correct states to the original bracketer, then corrupt one side.
    g=clock.bracket(surface.times,surface.count,surface.scale,surface.truth)
    bad=g['side_points'][0]
    def indices(ends,times,scale,point):
        result=original(ends,times,scale,point)
        if point==bad:result=result+1
        return result
    monkeypatch.setattr(clock,'indices',indices)
    assert not candidate().bracket(surface.times,surface.count,surface.scale,surface.truth)['side_geometry_supported']


def test_geometry_query_budget_includes_direct_clock_checks():
    surface=NarrowSurface()
    with pytest.raises((ValueError,RuntimeError)):
        candidate().bracket(surface.times,surface.count,surface.scale,surface.truth,maximum_queries=6)


def test_source_mismatch_and_native_errors_remain_charged(tmp_path):
    from lll.ilvis0_receipt_journal import Ledger
    surface=NarrowSurface();point=[0.,surface.truth];book=Ledger(tmp_path,'b'*64,['source','exception'],fit_limit=1,diagnostic_limit=26)
    book.start('source')
    with pytest.raises(ValueError,match='source'):
        candidate().check_endpoint(book,'source',lambda u,m:surface.evaluate(u,fresh=True),'sphere_still',point,
            np.array([100.,0.,40.]),physical,time_index=1,geometry_at=None,times=surface.times,packet_count=surface.count,scale=surface.scale)
    assert book.count('source','diagnostic')==1
    book.start('exception')
    def fail(u,m):raise RuntimeError('native failure')
    with pytest.raises(RuntimeError,match='native failure'):
        candidate().check_endpoint(book,'exception',fail,'sphere_still',point,np.array([1.,0.,40.]),physical,
            time_index=1,geometry_at=None,times=surface.times,packet_count=surface.count,scale=surface.scale)
    assert book.count('exception','diagnostic')==1


def test_nonfinite_native_values_rejected(tmp_path):
    surface=NarrowSurface();original=surface.evaluate
    def evaluate(u,*,fresh=False):
        r,j,n=original(u,fresh=fresh)
        if len(surface.calls)>1:j[0,1]=np.nan
        return r,j,n
    surface.evaluate=evaluate
    with pytest.raises(ValueError):check(surface,tmp_path)


def test_private_candidate_keeps_frozen_modules_and_tolerances_unchanged():
    from lll import ilvis0_boundary_adapter as adapter,ilvis0_boundary_stop as stopping
    before=(adapter.clock,adapter.stopping,dict(stopping.POLICY))
    helper=candidate().build_candidate()
    assert (adapter.clock,adapter.stopping,stopping.POLICY)==before
    assert helper.adapter.stopping is not stopping and helper.adapter is not adapter
    assert helper.adapter.stopping.POLICY['minimum_parameter_ulps']==8


@pytest.mark.parametrize('offset_s',[-3e-8,0.,3e-8])
def test_compiled_motion_controls_keep_known_observation_agreement(motion_kernels,offset_s,tmp_path,record_property):
    from lll import ilvis0_shape as shape,ilvis0_estimator as estimator,ilvis0_solver_position as position
    from lll.ilvis0_receipt_journal import Ledger
    surface=NarrowSurface();times=surface.times;count=surface.count;scale=surface.scale
    truth=surface.truth*scale+offset_s;radius=6371000.;speed=250.;latitude=.8;longitude=.1;height=1000.
    dt=np.full(count,.005);theta=np.zeros((count,3));dv=np.zeros_like(theta);dv[:,2]=-9.81*dt
    gps=np.column_stack((latitude+speed*(times+truth)/radius,np.full(len(times),longitude),np.full(len(times),height)))
    initial=dict(latitude_rad=latitude,longitude_rad=longitude,height_m=height,velocity_ned_mps=np.array([speed,0.,0.]),attitude_body_to_ned=np.eye(3))
    p=shape.TangentProblem(theta,dv,dt,times,gps,np.diag(np.tile([radius**-2,radius**-2,1.],len(times))),initial,
        estimator.Bounds(dict(time_offset=scale)),fit_earth_removal=False,kernel=motion_kernels[0],tangent_kernel=motion_kernels[1],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)
    point=np.array([truth/scale]);saved=p.residual_tangent(point,'flat_still')[0]
    book=Ledger(tmp_path,'c'*64,['native'],fit_limit=1,diagnostic_limit=26);book.start('native')
    result=candidate().check_endpoint(book,'native',p.residual_tangent,'flat_still',point,saved,
        lambda d:position.physical_residual_step(p,d),time_index=0,geometry_at=None,times=times,packet_count=count,scale=scale)
    record_property('native_evaluations',book.count('native','diagnostic')+1)
    assert book.count('native','diagnostic')<=26
    assert min(t['cost'] for t in result['evaluation_trace'])<1e-8
    if result['passed']:
        # A local boundary check is not an exact alignment estimator. Compare
        # independently known observations at its declared physical resolution.
        assert abs(result['normalized_parameters'][0]*scale-truth)*speed<=position.POLICY['position_rms_tolerance_m']
        discrepancy=position.physical_residual_step(p,result['center_native'][0])
        assert np.max(np.abs(discrepancy))<=position.POLICY['position_rms_tolerance_m']
        assert float(result['center_native'][0]@result['center_native'][0])<1e-8
    else:
        assert result['reason'] in ('smooth_zero_requires_separate_check','no_negative_to_positive_bracket',
            'boundary_check_unresolved','side_geometry_unsupported')
