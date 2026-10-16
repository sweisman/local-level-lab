# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known answers qualify a separate candidate without changing archived evidence."""
import importlib
import importlib.util
import pytest

CONTROLS=('interior','boundary','redundant','scaled','nonlinear','gain_offset',
          'curved_boundary','exponential','curved_redundant','nonlinear27')


def candidate():
    name='lll.ilvis0_solver_timing'
    assert importlib.util.find_spec(name) is not None,'separate damped solver is missing'
    return importlib.import_module(name)


def meters(delta):
    import numpy as np
    return np.column_stack((delta,np.zeros((len(delta),2))))


@pytest.mark.parametrize('name',CONTROLS)
@pytest.mark.parametrize('index',range(4))
def test_known_objective_prediction_and_feasible_parameters(name,index):
    solver=candidate()
    import numpy as np
    from lll.ilvis0_boundary_controls import problem_for,starts
    problem,optimum,expected,unique=problem_for(name)
    fit=solver.fit_candidate(problem,'control',start=starts(len(optimum))[index],
                             maximum_evaluations=200,physical_step=meters)
    point=np.array(fit['normalized_parameters'])
    assert fit['converged'] and fit['stability_verified']
    assert fit['residual_sum_squares']==pytest.approx(expected,abs=1e-7,rel=0)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum))<=1e-4
    if unique: assert point==pytest.approx(optimum,abs=1e-5)
    assert np.all(abs(point)<=1)
    assert problem.calls==fit['evaluations']<=200
    assert fit['scientific_decision']=='abstain' and not fit['scientific_eligible']


def test_exhausted_nonstationary_fit_cannot_pass():
    solver=candidate()
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('exponential')
    fit=solver.fit_candidate(problem,'control',start=[-.8,-.8],maximum_evaluations=6,physical_step=meters)
    assert not fit['converged']
    assert problem.calls==fit['evaluations']<=6


@pytest.mark.parametrize('truth',[(.15,-.2),(.98,-.98),(1.,-1.)])
@pytest.mark.parametrize('start',[(0.,0.),(-.7,.6)])
def test_independent_raw_increment_motion_controls(kernels,truth,start):
    solver=candidate()
    import numpy as np
    from test_ilvis0_precision_solver import straight_problem
    problem=straight_problem(kernels,truth)
    fit=solver.fit_candidate(problem,'flat_still',start=np.array(start),maximum_evaluations=40)
    assert fit['converged']
    assert fit['normalized_parameters']==pytest.approx(truth,abs=2e-6)
    assert fit['residual_sum_squares']<1e-10
    assert fit['evaluations']<=40


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    candidate()
    from lll import ilvis0_precision as precision,ilvis0_exploratory as explore
    directory=tmp_path_factory.mktemp('trust-motion-controls')
    return explore.load_kernel(directory)[0],precision.load_tangent(directory)[0]


def test_damping_cannot_make_a_failed_physical_gate_pass(monkeypatch):
    solver=candidate()
    import numpy as np
    from lll import ilvis0_solver_position as position
    from lll.ilvis0_boundary_controls import problem_for
    original=position.verify_stability
    seen=[]
    def reject(*args):
        value=original(*args);seen.append(value)
        return dict(value,passed=False,reason='controlled physical gate failure')
    monkeypatch.setattr(position,'verify_stability',reject)
    problem,_,_,_=problem_for('interior')
    fit=solver.fit_candidate(problem,'control',start=np.zeros(2),maximum_evaluations=40,physical_step=meters)
    assert seen and not fit['converged'] and not fit['scientific_eligible']


@pytest.mark.parametrize('kind',['crossing','knot','cusp'])
@pytest.mark.parametrize('index',range(4))
def test_independent_piecewise_timing_objectives(kind,index):
    solver=candidate()
    import numpy as np
    from lll.ilvis0_solver_controls import ControlBounds
    from lll.ilvis0_boundary_controls import starts
    class Problem:
        calls=0;ends=np.array([.6,1.1,2.1]);gps_times=np.array([1.])
        bounds=ControlBounds(2)
        bounds.active=('offset','time_offset')
        bounds.limits={'time_offset':1.}
        def residual_tangent(self,u,model):
            self.calls+=1
            if kind=='cusp':
                return np.array([u[0]-.2,1+abs(u[1]-.1),1.]),np.diag([1.,-1. if u[1]<=.1 else 1.]).tolist()+[[0.,0.]],0
            target=.4 if kind=='crossing' else .1
            h=lambda t:t if t<=.1 else .1+3*(t-.1)
            slope=1. if u[1]<=.1 else 3.
            return np.array([u[0]+h(u[1])-(.2+h(target)),2*u[0]-h(u[1])-(.4-h(target)),1.]),np.array([[1.,slope],[2.,-slope],[0.,0.]]),0
    p=Problem();fit=solver.fit_candidate(p,'control',start=starts(2)[index],maximum_evaluations=200,physical_step=meters)
    assert fit['residual_sum_squares']==pytest.approx(2. if kind=='cusp' else 1.,abs=1e-7)
    assert bool(fit['converged'])==(kind!='cusp')
    assert p.calls==fit['evaluations']<=200
    assert max(abs(v) for v in fit['normalized_parameters'])<=1.


@pytest.mark.parametrize('truth',[-.8,.8])
@pytest.mark.parametrize('start',[-.7,.7])
def test_native_motion_with_unknown_timing(kernels,truth,start):
    solver=candidate()
    import numpy as np
    from lll import ilvis0_shape as shape,ilvis0_estimator as estimator
    count=900;dt=np.full(count,.005);theta=np.zeros((count,3));dv=np.zeros_like(theta);dv[:,2]=-9.81*dt
    times=np.arange(.5,4.01,.5);radius=6371000.
    initial=dict(latitude_rad=.8,longitude_rad=.1,height_m=1000.,velocity_ned_mps=np.array([250.,0.,0.]),attitude_body_to_ned=np.eye(3))
    gps=np.column_stack((.8+250*(times+.15*truth)/radius,np.full(len(times),.1),np.full(len(times),1000.)))
    p=shape.TangentProblem(theta,dv,dt,times,gps,np.diag(np.tile([radius**-2,radius**-2,1.],len(times))),initial,
        estimator.Bounds({'time_offset':.15}),fit_earth_removal=False,kernel=kernels[0],tangent_kernel=kernels[1],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)
    fit=solver.fit_candidate(p,'flat_still',start=[start],maximum_evaluations=40)
    assert fit['converged'] and fit['evaluations']<=40
    assert fit['normalized_parameters'][0]==pytest.approx(truth,abs=2e-6)


def test_packet_interval_box_and_neighbor_anchors():
    candidate()
    from lll.ilvis0_solver_timing import interval_box
    import numpy as np
    from types import SimpleNamespace
    p=SimpleNamespace(ends=np.array([.005,.010,.015]),gps_times=np.array([.006,.011]),
                      bounds=SimpleNamespace(active=('other','time_offset'),limits={'time_offset':.001}))
    i,lo,hi=interval_box(p,np.array([0.,.2]))
    assert i==1
    assert lo==pytest.approx(-1.2)
    assert hi==pytest.approx(3.8)


def test_interval_step_improves_true_cost_after_crossing_step_fails():
    solver=candidate()
    import numpy as np
    from types import SimpleNamespace
    p=SimpleNamespace(ends=np.array([.6,1.1,2.1]),gps_times=np.array([1.]),
        bounds=SimpleNamespace(active=('other','time_offset'),limits={'time_offset':1.}))
    point=np.array([.2,.11]);history=[];calls=[]
    def evaluate(u):
        calls.append(u.copy())
        r=np.array([u[0]-.2,1+abs(u[1]-.1),1.])
        j=np.array([[1.,0.],[0.,-1. if u[1]<=.1 else 1.],[0.,0.]])
        return r,j,0
    r,j,_=evaluate(point);calls.clear()
    result=solver.refine_timing(p,point,r,j,evaluate,lambda:len(calls)<5,history,0)
    assert result is not None and result[3]==pytest.approx(2.,abs=1e-10)
    assert len(calls)<=5
    assert history[-1]['method']=='timing_interval' and history[-1]['accepted']


def test_interval_probes_cannot_spend_exhausted_allowance():
    solver=candidate()
    import numpy as np
    from types import SimpleNamespace
    p=SimpleNamespace(ends=np.array([.6,1.1,2.1]),gps_times=np.array([1.]),
        bounds=SimpleNamespace(active=('other','time_offset'),limits={'time_offset':1.}))
    def forbidden(*args):raise AssertionError('native call after finite limit')
    assert solver.refine_timing(p,np.array([.2,.11]),np.ones(3),np.array([[1.,0.],[0.,1.],[0.,0.]]),
                                forbidden,lambda:False,[],0) is None
