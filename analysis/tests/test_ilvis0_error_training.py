# SPDX-License-Identifier: AGPL-3.0-or-later
"""Catch wrong REML degrees of freedom, missing beta uncertainty and data leakage."""
import numpy as np
import pytest


def api():
    from lll import ilvis0_error_training as training
    from lll.ilvis0_error_model import Spec
    return training,Spec


def axis_design(epochs):return np.tile(np.eye(3),(epochs,1))


def test_gls_parameters_and_covariance_have_independent_white_noise_answers():
    m,S=api();fit=m.fit([0.,1.],[2.,4.,6.,4.,6.,8.],axis_design(2),S(np.eye(3)))
    np.testing.assert_allclose(fit.beta,[3.,5.,7.])
    np.testing.assert_allclose(fit.beta_covariance,.5*np.eye(3))
    assert fit.quadratic==pytest.approx(6.)
    assert fit.reml==pytest.approx(.5*(3*np.log(2*np.pi)+3*np.log(2)+6))


def test_prediction_includes_parameter_uncertainty_without_training_future_errors():
    m,S=api();fit=m.fit([0.,1.],[2.,4.,6.,4.,6.,8.],axis_design(2),S(np.eye(3)))
    out=m.predict(fit,[2.],np.eye(3))
    np.testing.assert_allclose(out['mean'],[3.,5.,7.])
    np.testing.assert_allclose(out['known_parameter_covariance'],np.eye(3))
    np.testing.assert_allclose(out['parameter_covariance_contribution'],.5*np.eye(3))
    np.testing.assert_allclose(out['covariance'],1.5*np.eye(3))
    assert out['parameter_uncertainty_included']
    assert not out['covariance_parameter_uncertainty_included']


def test_cross_boundary_correlation_changes_the_parameter_uncertainty_term():
    m,S=api();spec=S(np.eye(3),offset=np.eye(3))
    fit=m.fit([0.,1.],[2.,4.,6.,2.,4.,6.],axis_design(2),spec)
    out=m.predict(fit,[2.],np.eye(3))
    np.testing.assert_allclose(out['mean'],[2.,4.,6.])
    np.testing.assert_allclose(out['known_parameter_covariance'],(4/3)*np.eye(3))
    # (I - 2/3 I) (1.5 I) (I - 2/3 I)' = I/6, not naive 1.5 I.
    np.testing.assert_allclose(out['parameter_covariance_contribution'],np.eye(3)/6)
    np.testing.assert_allclose(out['covariance'],1.5*np.eye(3))


def test_exact_gaussian_moments_check_linear_prediction_uncertainty():
    m,S=api();spec=S(np.eye(3));truth=np.array([3.,-2.,1.]);errors=[]
    # Independent known white generator: 18 cubature points in nine dimensions.
    points=3*np.concatenate((np.eye(9),-np.eye(9)))
    for p in points:
        fit=m.fit([0.,1.],axis_design(2)@truth+p[:6],axis_design(2),spec)
        out=m.predict(fit,[2.],np.eye(3))
        errors.append(truth+p[6:]-out['mean'])
    errors=np.array(errors)
    np.testing.assert_allclose(errors.mean(axis=0),np.zeros(3),atol=1e-14)
    np.testing.assert_allclose(errors.T@errors/18,1.5*np.eye(3),atol=1e-14)
    np.testing.assert_allclose(out['covariance'],1.5*np.eye(3))


def test_reml_uses_training_sample_count_and_mean_degrees_of_freedom():
    m,S=api();candidates=(('small',S(np.eye(3))),('large',S(4*np.eye(3))))
    values=np.array([-1.,1.,-1.,1.,-1.,1.]);x=np.ones((6,1))
    out=m.select([0.,1.],values,x,candidates)
    assert out['selected_id']=='small' and out['selection_unique']
    expected=.5*(5*np.log(2*np.pi)+np.log(6)+6.)
    assert out['scores'][0]['reml']==pytest.approx(expected)
    large=.5*(5*np.log(2*np.pi)+5*np.log(4)+np.log(6)+1.5)
    assert out['scores'][1]['reml']==pytest.approx(large)
    assert m.select([0.,1.],3*values,x,candidates)['selected_id']=='large'


def test_covariance_ties_are_explicit_and_order_is_deterministic():
    m,S=api();s=S(np.eye(3));out=m.select([0.,1.],np.arange(6.),np.ones((6,1)),(('a',s),('b',s)))
    assert out['selected_id']=='a' and not out['selection_unique']
    assert out['score_margin']==pytest.approx(0.)


def test_covariance_sensitivity_returns_all_predictions_and_no_pseudo_interval():
    m,S=api();choices=(('one',S(np.eye(3))),('four',S(4*np.eye(3))))
    selection=m.select([0.,1.],[2.,4.,6.,4.,6.,8.],axis_design(2),choices)
    predictions=m.predict_choices(selection,[2.],np.eye(3))
    assert set(predictions)=={'one','four'}
    np.testing.assert_allclose(predictions['one']['covariance'],1.5*np.eye(3))
    np.testing.assert_allclose(predictions['four']['covariance'],6*np.eye(3))
    assert all(not p['covariance_parameter_uncertainty_included'] for p in predictions.values())


def test_future_design_cannot_change_training_covariance_selection_or_parameters():
    m,S=api();selection=m.select([0.,1.],np.arange(6.),np.ones((6,1)),
        (('a',S(np.eye(3))),('b',S(4*np.eye(3)))))
    original=selection['fit'].beta.copy();scores=[r['reml'] for r in selection['scores']]
    m.predict_choices(selection,[2.],np.ones((3,1)))
    m.predict_choices(selection,[100.],10*np.ones((3,1)))
    np.testing.assert_array_equal(selection['fit'].beta,original)
    assert [r['reml'] for r in selection['scores']]==scores


def test_fixed_drift_anchor_survives_estimation_and_prediction():
    m,S=api();spec=S(np.eye(3),drift=4*np.eye(3),drift_origin_s=0.,drift_span_s=10.)
    fit=m.fit([0.],[2.,2.,2.],np.ones((3,1)),spec)
    out=m.predict(fit,[5.],np.ones((3,1)))
    np.testing.assert_allclose(out['known_parameter_covariance'],2*np.eye(3))
    np.testing.assert_allclose(out['covariance'],2*np.eye(3)+np.ones((3,3))/3)


def test_correlated_error_cubature_checks_parameter_error_cancellation():
    m,S=api();spec=S(np.eye(3),offset=np.eye(3));errors=[]
    points=np.sqrt(12)*np.concatenate((np.eye(12),-np.eye(12)))
    for p in points:
        # Nine white errors plus a three-axis common offset, generated separately.
        offset=p[9:];y=np.tile(offset,2)+p[:6]
        fitted=m.fit([0.,1.],y,axis_design(2),spec)
        predicted=m.predict(fitted,[2.],np.eye(3))
        errors.append(offset+p[6:9]-predicted['mean'])
    errors=np.array(errors)
    np.testing.assert_allclose(errors.T@errors/24,1.5*np.eye(3),atol=1e-14)
    np.testing.assert_allclose(predicted['covariance'],1.5*np.eye(3))


def test_parameter_units_do_not_change_predictions_or_covariance():
    m,S=api();x=axis_design(2);values=np.arange(6.);spec=S(np.eye(3))
    original=m.fit([0.,1.],values,x,spec)
    units=np.array([1e9,1e-9,2.]);changed=m.fit([0.,1.],values,x*units,spec)
    a=m.predict(original,[2.],np.eye(3));b=m.predict(changed,[2.],np.eye(3)*units)
    np.testing.assert_allclose(a['mean'],b['mean'])
    np.testing.assert_allclose(a['covariance'],b['covariance'])


def test_irregular_times_recover_a_linear_trend_and_its_prediction_covariance():
    m,S=api();t=np.repeat([0.,1.,4.],3);x=np.column_stack((np.ones(9),t))
    fitted=m.fit([0.,1.,4.],2+3*t,x,S(np.eye(3)))
    np.testing.assert_allclose(fitted.beta,[2.,3.])
    np.testing.assert_allclose(fitted.beta_covariance,np.array([[51.,-15.],[-15.,9.]])/234)
    out=m.predict(fitted,[6.],np.tile([1.,6.],(3,1)))
    np.testing.assert_allclose(out['mean'],[20.,20.,20.])
    np.testing.assert_allclose(out['covariance'],np.eye(3)+(5/6)*np.ones((3,3)))


@pytest.mark.parametrize('case',['rank_deficient','no_residual_dof','nonfinite_design',
    'bad_design_rows','nonfinite_values','bad_values','invalid_times'])
def test_invalid_or_unidentifiable_training_fits_fail(case):
    m,S=api();times=[0.,1.];y=np.arange(6.);x=np.ones((6,1))
    if case=='rank_deficient':x=np.ones((6,2))
    if case=='no_residual_dof':x=np.eye(6)
    if case=='nonfinite_design':x[0,0]=np.nan
    if case=='bad_design_rows':x=x[:-1]
    if case=='nonfinite_values':y[0]=np.nan
    if case=='bad_values':y=y[:-1]
    if case=='invalid_times':times=[1.,0.]
    with pytest.raises(ValueError):m.fit(times,y,x,S(np.eye(3)))


@pytest.mark.parametrize('case',['empty','duplicate_id','invalid_id'])
def test_invalid_candidate_sets_do_not_select_silently(case):
    m,S=api();s=S(np.eye(3));choices={'empty':(), 'duplicate_id':(('a',s),('a',s)),
        'invalid_id':(('',s),)}[case]
    with pytest.raises(ValueError):m.select([0.,1.],np.arange(6.),np.ones((6,1)),choices)


@pytest.mark.parametrize('case',['past','wrong_columns','wrong_rows','nonfinite'])
def test_invalid_prediction_inputs_fail(case):
    m,S=api();fit=m.fit([0.,1.],np.arange(6.),axis_design(2),S(np.eye(3)))
    times=[2.];x=np.eye(3)
    if case=='past':times=[.5]
    if case=='wrong_columns':x=np.ones((3,1))
    if case=='wrong_rows':x=x[:2]
    if case=='nonfinite':x[0,0]=np.nan
    with pytest.raises(ValueError):m.predict(fit,times,x)
