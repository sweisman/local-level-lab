# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit candidate qualification matrix, not routine CI; no archive data.

Run through ilvis0_projected_controls_worker.py. A failed numerical candidate is
preserved as a failed qualification, not converted into a routine CI regression.
"""
import json
import numpy as np
import pytest
from scipy.linalg import solve_triangular

from lll import ilvis0_estimator as estimator
from lll import ilvis0_exploratory as explore
from lll import ilvis0_geographic_controls as geographic
from lll import ilvis0_precision as precision
from lll import ilvis0_shape as shape


def api():
    from lll import ilvis0_projected_fitting as projected
    return projected


@pytest.fixture(scope='module')
def native(tmp_path_factory,record_testsuite_property):
    path=tmp_path_factory.mktemp('projected-fitting-native')
    kernel,base_meta=explore.load_kernel(path)
    tangent,tangent_meta=precision.load_tangent(path)
    record_testsuite_property('native',json.dumps(dict(value=base_meta,tangent=tangent_meta)))
    return kernel,tangent


@pytest.fixture(scope='module')
def budget(record_testsuite_property):
    value=api().ControlBudget(maximum_native_sweeps=2400,maximum_starts=24)
    yield value
    record_testsuite_property('budget',json.dumps(dict(starts=value.starts,native_sweeps=value.native_sweeps)))


class Counted:
    def __init__(self,base,budget):
        self.base=base;self.bounds=base.bounds;self.cholesky=base.cholesky;self.gps=base.gps
        self.budget=budget

    def residual_tangent(self,point,model):
        self.budget.charge_native()
        return self.base.residual_tangent(point,model)

    def predict(self,point,model):
        self.budget.charge_native()
        return self.base.predict(point,model)


class Affine:
    def __init__(self):
        self.bounds=estimator.Bounds({'position_x':1.,'position_z':1.})
        self.gps=np.zeros((3,3));self.cholesky=np.eye(9);self.calls=0
        self.jac=np.tile([[1.,0.],[0.,0.],[0.,1.]],(3,1))
        self.target=np.tile([2.,0.,.4],3)

    def residual_tangent(self,point,model):
        self.bounds.decode(point);self.calls+=1
        return self.jac@point-self.target,self.jac.copy(),0

    def predict(self,point,model):
        return (self.jac@point).reshape(-1,3)


def test_missing_axis_remains_an_explicit_null_direction_and_bound_optimum():
    p=api().ProjectedProblem(Affine(),('latitude','longitude'))
    fit=api().fit_control(p,'flat_still',start=[0.,-.7],maximum_evaluations=12)
    assert fit['converged'] and fit['numerical_rank']==1
    assert fit['active_parameters']==['position_x','position_z']
    assert fit['normalized_parameters'][0]==pytest.approx(1.,abs=1e-7)
    assert fit['normalized_parameters'][1]==pytest.approx(-.7)
    assert fit['residual_sum_squares']==pytest.approx(3.)
    assert not fit['nuisance_fully_observable']
    assert fit['scientific_decision']=='abstain'
    assert fit['evaluations']==p.full_problem.calls


@pytest.mark.parametrize('axes',[(),('height','height'),('bad',)])
def test_invalid_coordinate_subsets_are_rejected(axes):
    with pytest.raises(ValueError):api().ProjectedProblem(Affine(),axes)


def test_inconsistent_covariance_layout_is_rejected():
    base=Affine();base.cholesky=np.eye(6)
    with pytest.raises(ValueError):api().ProjectedProblem(base,('height',))


def test_exhausted_fit_keeps_its_failure_and_never_exceeds_cap():
    class Curved(Affine):
        def residual_tangent(self,point,model):
            self.bounds.decode(point);self.calls+=1
            x,y=point
            value=np.exp(4*x)
            return np.tile([value-np.exp(3.2),y-.4,0.],3),np.tile([[4*value,0.],[0.,1.],[0.,0.]],(3,1)),0
    base=Curved();p=api().ProjectedProblem(base,('latitude','longitude'))
    fit=api().fit_control(p,'flat_still',start=[-.8,-.8],maximum_evaluations=6)
    assert fit['evaluations']==base.calls<=6
    assert not fit['converged'] and fit['termination']=='budget'


@pytest.mark.parametrize('bad',[0,5,81,True])
def test_control_requires_a_finite_small_evaluation_allowance(bad):
    with pytest.raises(ValueError):api().fit_control(
        api().ProjectedProblem(Affine(),('height',)), 'flat_still',start=[0.,0.],maximum_evaluations=bad)


def test_budget_rejects_the_next_call_before_spending_it():
    b=api().ControlBudget(maximum_native_sweeps=1,maximum_starts=1)
    b.charge_native();b.charge_start()
    with pytest.raises(estimator.EvaluationLimit):b.charge_native()
    with pytest.raises(estimator.EvaluationLimit):b.charge_start()
    assert b.native_sweeps==b.starts==1


def test_stability_conversion_restores_only_retained_physical_coordinates():
    from lll.ilvis0_solver_position import physical_metric
    base=Affine();base.gps[:,0]=.7
    base.cholesky=np.eye(9);base.cholesky[1,0]=.6;base.cholesky[4,0]=.3
    p=api().ProjectedProblem(base,('latitude','longitude'))
    delta=np.arange(6)/10
    lower=np.linalg.cholesky((base.cholesky@base.cholesky.T)[np.ix_(p.projection.indices,p.projection.indices)])
    expected=np.zeros((3,3));expected[:,:2]=(lower@delta).reshape(3,2)
    assert p.physical_step(delta)==pytest.approx(expected*physical_metric(base.gps))
    assert np.all(p.physical_step(delta)[:,2]==0)
    assert p.report()['unscored_coordinates_checked'] is False
    assert np.array_equal(p.predict([0.,.5],'flat_still'),base.predict([0.,.5],'flat_still'))


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('profile',[False,True])
def test_all_columns_match_direct_selected_native_derivatives(model,profile,native,budget):
    f=geographic.fixture(model,'nominal')
    sigma=np.tile(.01/f['metric'],len(f['gps']))
    base=shape.TangentProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],
        np.diag(sigma*sigma),f['initial'],estimator.Bounds(shape.instrument_limits(1.)),
        fit_earth_removal=profile,kernel=native[0],tangent_kernel=native[1],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
    counted=Counted(base,budget);p=api().ProjectedProblem(counted,('latitude','longitude'))
    point=np.full(len(base.bounds.active),.02)
    if profile:point[-1]=-.3
    before=budget.native_sweeps
    residual,jac,_=p.residual_tangent(point,model)
    selected=p.projection.indices
    covariance=base.cholesky@base.cholesky.T
    lower=np.linalg.cholesky(covariance[np.ix_(selected,selected)])
    direct=solve_triangular(lower,(counted.predict(point,model)-base.gps).ravel()[selected],lower=True)
    # AD and value-only kernels differ in floating-point accumulation. Compare
    # their predictions in metres, as in the established native tangent checks,
    # rather than requiring sub-nanometre agreement in whitened coordinates.
    metric=np.tile(f['metric'],len(f['gps']))[selected]
    assert np.max(abs((lower@(residual-direct))*metric))<3e-7
    assert jac.shape==(2*len(base.gps),26+int(profile))
    for column in range(len(point)):
        step=np.eye(len(point))[column]*1e-4
        delta=(counted.predict(point+step,model)-counted.predict(point-step,model)).ravel()[selected]/2e-4
        fd=solve_triangular(lower,delta,lower=True)
        assert np.allclose(fd,jac[:,column],atol=.005,rtol=3e-4),base.bounds.active[column]
    assert budget.native_sweeps-before<=56


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('clock',['nominal','variable'])
@pytest.mark.parametrize('axes',[('latitude','longitude'),('height',)])
@pytest.mark.parametrize('start_id',['zero','opposed'])
def test_independent_motion_refits_retained_coordinates(model,clock,axes,start_id,native,budget,record_property):
    f=geographic.fixture(model,clock);base=geographic.problem(f,*native)
    counted=Counted(base,budget);p=api().ProjectedProblem(counted,axes)
    truth=geographic.truth_point(f,base)
    start=np.zeros(len(truth)) if start_id=='zero' else -.8*np.sign(truth)
    budget.charge_start();before=budget.native_sweeps
    fit=api().fit_control(p,model,start=start,maximum_evaluations=80)
    point=np.array(fit['normalized_parameters'])
    reference=counted.predict(truth,model);prediction=counted.predict(point,model)
    selected=p.projection.indices
    lower=np.linalg.cholesky((base.cholesky@base.cholesky.T)[np.ix_(selected,selected)])
    r=solve_triangular(lower,(reference-base.gps).ravel()[selected],lower=True)
    physical=(prediction-base.gps)*f['metric']
    retained=[('latitude','longitude','height').index(a) for a in axes]
    maximum=float(np.max(abs(physical[:,retained])))
    record_property('control',json.dumps(dict(model=model,clock=clock,axes=axes,start=start_id,
        fit=fit,maximum_retained_error_m=maximum,maximum_all_axis_error_m=float(np.max(abs(physical))),
        truth_objective=float(r@r),native_sweeps=budget.native_sweeps-before)))
    assert fit['converged']
    assert maximum<.002
    assert fit['residual_sum_squares']<=float(r@r)+.01
    assert fit['evaluations']+2==budget.native_sweeps-before<=82
    assert fit['active_parameters']==list(base.bounds.active)
    assert fit['scientific_decision']=='abstain'


def test_complete_budget_is_bounded(budget,record_property):
    record_property('budget',json.dumps(dict(starts=budget.starts,native_sweeps=budget.native_sweeps)))
    assert budget.starts==24
    assert 0<budget.native_sweeps<=2400
