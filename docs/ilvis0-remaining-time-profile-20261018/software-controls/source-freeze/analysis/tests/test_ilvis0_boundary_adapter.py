# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known timing optima and explicit abstentions, without archive observations."""
import ctypes
from pathlib import Path
import subprocess
import numpy as np
import pytest


def candidate():
    from lll import ilvis0_boundary_adapter
    return ilvis0_boundary_adapter


def geometry():
    return np.array([1.,2.+1e-8,3.+2e-8,4.+3e-8]),1000,.15


@pytest.fixture(scope='module')
def clock_oracle(tmp_path_factory):
    binary=tmp_path_factory.mktemp('boundary-clock')/'clock.so'
    subprocess.run(['c++','-O2','-std=c++17','-shared','-fPIC',str(Path(__file__).with_name('ilvis0_clock_reference.cpp')),'-o',str(binary)],check=True,capture_output=True)
    fn=ctypes.CDLL(str(binary)).clock_indices
    fn.argtypes=[ctypes.c_size_t,ctypes.c_size_t,np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS'),ctypes.c_double,ctypes.c_double,np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')]
    fn.restype=ctypes.c_int
    def query(times,count,scale,u):
        result=np.empty(len(times),np.int64)
        assert fn(count,len(times),times,u,scale,result)==0
        return result
    return query


def test_every_cluster_transition_matches_compiled_packet_comparison(clock_oracle):
    times,count,scale=geometry()
    result=candidate().transitions(times,count,scale,0.)
    roots=result['knots']
    assert len(roots)==4 and np.all(np.diff(roots)>0)
    changes=np.zeros(4,np.int64)
    for root in roots:
        before=clock_oracle(times,count,scale,np.nextafter(root,-np.inf))
        after=clock_oracle(times,count,scale,root)
        assert np.sum(after-before)==1
        changes+=after-before
    assert changes.tolist()==[1,1,1,1]
    assert result['clock_queries']<=200000


def test_no_transition_and_no_merging_of_distinct_events():
    times,count,scale=geometry()
    assert candidate().transitions(times,count,scale,.001)['knots']==[]
    close=np.array([1.,2.+1e-12,3.+2e-12])
    assert len(candidate().transitions(close,count,scale,0.)['knots'])==3


def test_clock_enumeration_hard_limit():
    with pytest.raises(RuntimeError,match='budget'):
        candidate().transitions(*geometry(),0.,maximum_queries=2)


@pytest.mark.parametrize('point,width',[(np.nan,1e-6),(2.,1e-6),(0.,-.1),(0.,.006)])
def test_invalid_search_geometry_rejected(point,width):
    with pytest.raises(ValueError):candidate().transitions(*geometry(),point,window_s=width)


@pytest.mark.parametrize('gradients',[[-3,-2,-1,1,2],[-1,2,-3,2,1],[-1,-2,-3,-4,1]])
def test_discrete_search_preserves_bracket_without_monotonicity(gradients):
    knots=[-.6,-.2,.2,.6];calls=[]
    def derivative(u):
        i=np.searchsorted(knots,u,side='right');calls.append(i);return gradients[i]
    result=candidate().locate(knots,-.9,.9,derivative)
    root=result['point'];i=knots.index(root)
    assert result['passed'] and gradients[i]<0<gradients[i+1]
    assert len(calls)==result['evaluations']<=12


@pytest.mark.parametrize('gradient',[lambda u:1.,lambda u:-1.,lambda u:0.,lambda u:-u])
def test_no_minimum_bracket_must_abstain(gradient):
    r=candidate().locate([0.],-.5,.5,gradient)
    assert not r['passed'] and r['evaluations']==2


def test_search_exhaustion_is_not_a_result():
    result=candidate().locate(np.linspace(-.8,.8,64),-.9,.9,lambda u:-1 if u<.123 else 1,maximum_evaluations=2)
    assert not result['passed'] and result['reason']=='search_budget_exhausted'


def test_nonfinite_derivative_cannot_bracket():
    with pytest.raises(ValueError):candidate().locate([0.],-.5,.5,lambda u:np.nan)


def physical(delta):return np.column_stack((np.asarray(delta)*2,np.zeros((len(delta),2))))


class Surface:
    def __init__(self,kind='minimum'):
        self.kind=kind;self.calls=[]
        self.times,self.count,self.scale=geometry()
        roots=candidate().transitions(self.times,self.count,self.scale,0.)['knots']
        self.truth=roots[2]
    def evaluate(self,u,*,fresh=False):
        assert fresh and np.all(abs(u)<=1)
        self.calls.append(np.array(u).copy());x,t=u;d=t-self.truth
        sign=-1. if d<0 else 1.
        value=.001*abs(d);slope=.001*sign
        if self.kind=='maximum':value=-value;slope=-slope
        if self.kind=='discontinuous' and d>0:value+=.01
        target=.7 if self.kind=='unfinished_nuisance' else 0.
        return np.array([1.+value,.005*(x-target),40.]),np.array([[0.,slope],[.005,0.],[0.,0.]]),0


def diagnose(surface,**kwargs):
    r=candidate().diagnose([0.,0.],surface.evaluate,physical,time_index=1,
        times=surface.times,packet_count=surface.count,scale=surface.scale,**kwargs)
    assert r['evaluations']==len(surface.calls)<=26
    assert r['scientific_decision']=='abstain' and not r['scientific_eligible']
    return r


def test_adapter_finds_correct_cluster_knot_and_preserves_all_nuisances():
    s=Surface();r=diagnose(s)
    assert r['passed'] and r['normalized_parameters']==pytest.approx([0.,s.truth],abs=0,rel=0)
    assert r['relocation']['passed'] and abs(r['relocation_s'])<=1e-6
    assert r['boundary_check']['passed']
    assert all(p[0]==0. for p in s.calls[:r['search']['evaluations']+2])


@pytest.mark.parametrize('kind',['maximum','discontinuous','unfinished_nuisance'])
def test_adapter_cannot_promote_bad_endpoint(kind):
    assert not diagnose(Surface(kind))['passed']


def test_large_prediction_change_on_relocation_is_rejected():
    s=Surface()
    r=candidate().diagnose([0.,0.],s.evaluate,lambda d:physical(d)*1e15,time_index=1,
        times=s.times,packet_count=s.count,scale=s.scale)
    assert not r['passed'] and r['reason']=='relocation_not_stable'


def test_budget_cannot_be_changed_after_search_configuration():
    s=Surface()
    with pytest.raises(ValueError):diagnose(s,maximum_evaluations=27)
    assert not s.calls


def test_original_repeat_failure_is_not_hidden():
    s=Surface();original=s.evaluate
    def evaluate(u,*,fresh=False):
        r,j,m=original(u,fresh=fresh)
        if len(s.calls)==2:r[0]+=.1
        return r,j,m
    result=candidate().diagnose([0.,0.],evaluate,physical,time_index=1,
        times=s.times,packet_count=s.count,scale=s.scale)
    assert not result['passed'] and result['reason']=='original_not_repeatable' and len(s.calls)==2


@pytest.fixture(scope='module')
def motion_kernels(tmp_path_factory):
    from lll import ilvis0_precision as precision,ilvis0_exploratory as explore
    path=tmp_path_factory.mktemp('boundary-adapter-motion')
    return explore.load_kernel(path)[0],precision.load_tangent(path)[0]


@pytest.mark.parametrize('offset_s',[-3e-8,0.,3e-8])
def test_native_increment_integrator_recovers_analytic_straight_track(motion_kernels,offset_s,record_property):
    from lll import ilvis0_shape as shape,ilvis0_estimator as estimator,ilvis0_solver_position as position
    count=1000;times=np.array([1.,2.,3.,4.]);scale=.15
    dt=np.full(count,.005);theta=np.zeros((count,3));dv=np.zeros_like(theta);dv[:,2]=-9.81*dt
    radius=6371000.;latitude=.8;longitude=.1;height=1000.;speed=250.
    # Closed-form receiver trajectory: no predictions generated by either kernel.
    gps=np.column_stack((latitude+speed*(times+offset_s)/radius,np.full(len(times),longitude),np.full(len(times),height)))
    initial=dict(latitude_rad=latitude,longitude_rad=longitude,height_m=height,
        velocity_ned_mps=np.array([speed,0.,0.]),attitude_body_to_ned=np.eye(3))
    p=shape.TangentProblem(theta,dv,dt,times,gps,np.diag(np.tile([radius**-2,radius**-2,1.],len(times))),initial,
        estimator.Bounds({'time_offset':scale}),fit_earth_removal=False,kernel=motion_kernels[0],tangent_kernel=motion_kernels[1],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)
    calls=[]
    def evaluate(u,*,fresh=False):
        assert fresh;calls.append(np.array(u).copy())
        return p.residual_tangent(u,'flat_still')
    result=candidate().diagnose([0.],evaluate,lambda d:position.physical_residual_step(p,d),
        time_index=0,times=times,packet_count=count,scale=scale)
    record_property('native_evaluations',len(calls))
    record_property('adapter_outcome',result['reason'])
    assert result['evaluations']==len(calls)<=26
    # A smooth optimum may lie between transitions: this is a boundary check,
    # so it must not mistake a neighboring packet event for a qualified minimum.
    if result['passed']:
        assert result['normalized_parameters'][0]*scale==pytest.approx(offset_s,abs=1e-9)
        assert result['boundary_check']['passed']
    else:
        assert result['reason'] in ('smooth_zero_requires_separate_check','no_negative_to_positive_bracket',
            'boundary_check_unresolved','side_geometry_unsupported')
    assert min(t['cost'] for t in result['evaluation_trace'])<1e-8


def test_absent_transition_uses_no_native_predictions():
    s=Surface();s.times+=.001
    result=diagnose(s)
    assert not result['passed'] and result['reason']=='no_transition_in_window'
    assert result['evaluations']==0


def test_more_than_12_search_calls_is_not_allowed():
    with pytest.raises(ValueError):candidate().locate([0.],-.5,.5,lambda u:u,maximum_evaluations=13)


def test_timing_search_exhaustion_preserves_total_native_allowance():
    # More than 2**10 plateaus require more than twelve derivative calls.
    roots=np.linspace(-.8,.8,4096);calls=[]
    def derivative(u):calls.append(u);return -1. if u<.123456 else 1.
    result=candidate().locate(roots,-.9,.9,derivative)
    assert not result['passed'] and len(calls)==12


def test_transition_clock_budget_and_native_budget_are_separate():
    s=Surface();s.times=np.array([np.nan,2.])
    with pytest.raises(ValueError):diagnose(s)
    assert not s.calls
