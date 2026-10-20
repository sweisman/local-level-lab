# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.stats import chi2,norm

from lll.ilvis0_bounded_prediction import known_scale,shared_scale_bound,Region,predict,union


def scale(value=.1,covariance_id='common'):
    return known_scale(value,source_id='declared-control',covariance_id=covariance_id)


def test_shared_scale_upper_uses_calibration_residual_degrees_of_freedom():
    result=shared_scale_bound([-1.,0.,1.],np.ones((3,1)),alpha=.01,
        source_id='shared-reference',covariance_id='common',remainder_radius=0.,design_is_fixed=True)
    assert result.upper == pytest.approx(np.sqrt(2./chi2.ppf(.01,2)))
    assert result.residual_degrees_of_freedom==2
    assert result.failure_probability==.01


def test_deterministic_remainder_widens_scale_bound_before_chi_square_inversion():
    result=shared_scale_bound([-1.,0.,1.],np.ones((3,1)),alpha=.01,
        source_id='shared-reference',covariance_id='common',remainder_radius=.5,design_is_fixed=True)
    assert result.upper == pytest.approx((np.sqrt(2.)+.5)/np.sqrt(chi2.ppf(.01,2)))


def test_no_residual_degrees_of_freedom_or_unknown_remainder_cannot_supply_scale():
    result=shared_scale_bound([1.,2.],np.eye(2),alpha=.01,source_id='reference',
        covariance_id='common',remainder_radius=0.,design_is_fixed=True)
    assert result.upper is None
    unknown=shared_scale_bound([1.,2.],np.ones((2,1)),alpha=.01,source_id='reference',
        covariance_id='common',remainder_radius=None,design_is_fixed=True)
    assert unknown.upper is None


def test_rank_deficient_reference_requires_bounds_on_discarded_response():
    x=np.column_stack((np.ones(3),np.ones(3)))
    result=shared_scale_bound([-1.,0.,1.],x,alpha=.01,source_id='reference',
        covariance_id='common',remainder_radius=0.,design_is_fixed=True)
    assert result.upper is None
    bounded=shared_scale_bound([-1.,0.,1.],x,alpha=.01,source_id='reference',covariance_id='common',
        remainder_radius=0.,coefficient_bounds=[[-1.,1.],[-1.,1.]],design_is_fixed=True)
    assert bounded.upper is not None


def test_identifiable_interval_matches_known_scalar_ellipsoid_and_box():
    region=Region(np.full(4,.5),np.ones((4,1)),[[0.,1.]],scale=scale(),
        covariance_id='common',remainder_radius=0.,alpha=.02,design_is_fixed=True)
    result=region.support([[1.]])
    half=.1*np.sqrt(chi2.ppf(.98,1))/2.
    np.testing.assert_allclose(result['lower'],[.5-half],atol=1e-14)
    np.testing.assert_allclose(result['upper'],[.5+half],atol=1e-14)


def test_unidentified_parameters_retain_box_range_and_all_columns():
    design=np.column_stack((np.ones(4),np.zeros(4)))
    region=Region(np.full(4,.5),design,[[0.,1.],[-2.,3.]],scale=scale(),covariance_id='common',
        remainder_radius=0.,alpha=.02)
    result=region.support([[0.,1.]])
    assert region.parameter_count==2 and region.rank==1
    np.testing.assert_allclose(result['lower'],[-2.],atol=1e-14)
    np.testing.assert_allclose(result['upper'],[3.],atol=1e-14)


def test_data_dependent_candidate_design_uses_full_noise_dimension():
    fixed=Region(np.ones(8),np.ones((8,1)),[[-2.,2.]],scale=scale(),covariance_id='common',
        remainder_radius=0.,alpha=.02,design_is_fixed=True)
    learned=Region(np.ones(8),np.ones((8,1)),[[-2.,2.]],scale=scale(),covariance_id='common',
        remainder_radius=0.,alpha=.02)
    assert fixed.noise_degrees_of_freedom==1
    assert learned.noise_degrees_of_freedom==8
    assert learned.radius>fixed.radius


def test_shared_scale_cannot_claim_fixed_reference_after_learning_its_design():
    result=shared_scale_bound([-1.,0.,1.],np.ones((3,1)),alpha=.01,
        source_id='reference',covariance_id='common',remainder_radius=0.)
    assert result.upper is None and result.reason=='data_dependent_scale_reference'


def test_adaptive_direction_cannot_use_fixed_rank_noise_shortcut():
    # An adversarial design aligns its only column with the observed noise.
    # The true coefficient remains zero; the full-noise radius protects it.
    noise=np.ones(20);design=(noise/np.linalg.norm(noise))[:,None]
    correct=Region(noise,design,[[0.,10.]],scale=scale(1.),covariance_id='common',
        remainder_radius=0.,alpha=.02)
    incorrect=Region(noise,design,[[0.,10.]],scale=scale(1.),covariance_id='common',
        remainder_radius=0.,alpha=.02,design_is_fixed=True)
    assert correct.support([[1.]])['lower'][0]<=0.
    assert incorrect.support([[1.]])['lower'][0]>0.


def test_zero_rank_is_a_box_not_a_zero_uncertainty_result():
    region=Region(np.ones(4),np.zeros((4,2)),[[-1.,1.],[-2.,2.]],scale=scale(),
        covariance_id='common',remainder_radius=0.,alpha=.02)
    result=region.support([[1.,1.]])
    assert region.rank==0
    np.testing.assert_allclose(result['lower'],[-3.])
    np.testing.assert_allclose(result['upper'],[3.])


def test_weak_discarded_design_response_is_added_to_remainder():
    x=np.column_stack((np.ones(4),1e-12*np.arange(4)))
    region=Region(np.ones(4),x,[[-2.,2.],[-100.,100.]],scale=scale(),covariance_id='common',
        remainder_radius=0.,alpha=.02,rank_tolerance=1e-8)
    assert region.rank==1 and region.discarded_response_bound>1e-10
    assert region.parameter_count==2


def test_exact_outside_box_mean_produces_empty_outer_support():
    region=Region(np.full(4,2.),np.ones((4,1)),[[0.,1.]],scale=scale(0.),
        covariance_id='common',remainder_radius=0.,alpha=.02)
    result=region.support([[1.]])
    assert result['empty']


def test_unknown_remainder_or_scale_keeps_prediction_unsupported():
    region=Region(np.ones(4),np.ones((4,1)),[[0.,1.]],scale=scale(),covariance_id='common',
        remainder_radius=None,alpha=.02)
    assert not region.support([[1.]])['supported']


def test_different_candidate_covariance_cannot_reuse_shared_scale_silently():
    with pytest.raises(ValueError):
        Region(np.ones(4),np.ones((4,1)),[[0.,1.]],scale=scale(),covariance_id='different',
            remainder_radius=0.,alpha=.02)


def make_prediction(covariance_id='common',remainder=.2):
    region=Region(np.zeros(4),np.ones((4,1)),[[0.,0.]],scale=scale(.3,covariance_id),
        covariance_id=covariance_id,remainder_radius=remainder,alpha=.02)
    return predict(region,[0.,0.],[[1.],[1.]],conditional_variance=[1.,4.],
        training_response_norm=[.5,2.],future_remainder_bounds=[.1,.2],
        alpha=.03,prediction_ids=('north','up'))


def test_prediction_includes_parameter_remainder_scale_and_simultaneous_future_noise():
    result=make_prediction()
    noise=.3*norm.isf(.03/4)*np.array([1.,2.])
    deterministic=np.array([.1,.2])+np.array([.5,2.])*.2
    np.testing.assert_allclose(result['lower'],-noise-deterministic,atol=1e-14)
    np.testing.assert_allclose(result['upper'],noise+deterministic,atol=1e-14)
    assert result['nominal_failure_probability_bound']==.05
    assert not result['observational_coverage_calibrated']
    assert result['scientific_decision']=='abstain'


def test_finite_covariance_union_keeps_all_alternatives_and_common_source():
    a=make_prediction('a');b=make_prediction('b',remainder=.5)
    result=union({'a':a,'b':b})
    np.testing.assert_allclose(result['lower'],np.minimum(a['lower'],b['lower']))
    np.testing.assert_allclose(result['upper'],np.maximum(a['upper'],b['upper']))
    assert result['covariance_ids']==['a','b']
    assert not result['outside_declared_family_coverage_established']


def test_unsupported_covariance_alternative_cannot_be_dropped_from_union():
    a=make_prediction('a')
    result=union({'a':a,'b':dict(supported=False,reason='unsupported model error')})
    assert not result['supported']


def test_union_requires_matching_prediction_coordinates_and_shared_calibration_source():
    a=make_prediction('a');b=make_prediction('b');b['prediction_ids']=('east','up')
    with pytest.raises(ValueError):union({'a':a,'b':b})
    b=make_prediction('b');b['scale_source_id']='different-source'
    with pytest.raises(ValueError):union({'a':a,'b':b})


@pytest.mark.parametrize('bounds',[[[1.,0.]],[[0.,np.inf]],[[0.,1.],[0.,1.]]])
def test_invalid_parameter_bounds_rejected(bounds):
    with pytest.raises(ValueError):Region(np.ones(4),np.ones((4,1)),bounds,scale=scale(),
        covariance_id='common',remainder_radius=0.,alpha=.02)
