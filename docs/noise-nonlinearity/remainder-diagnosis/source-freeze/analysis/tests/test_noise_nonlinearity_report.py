# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math
import pytest


def fixture():
    odd=[.2,.4,.6];even=.0001
    errors=[[[x+even for x in odd]],[[-x+even for x in odd]],
        [[.5*x+.25*even for x in odd]],[[-.5*x+.25*even for x in odd]]]
    a,b,c,d=[row[0] for row in errors]
    remainder=max(abs((x+y)/2) for x,y in zip(a,b))
    change=max(abs((u-v)-(x-y)/2) for x,y,u,v in zip(a,b,c,d))
    summary=dict(passed=True,maximum_even_remainder_m=remainder,
        maximum_half_amplitude_even_remainder_m=max(abs((u+v)/2) for u,v in zip(c,d)),
        maximum_half_response_change_m=change,maximum_even_remainder_fraction_of_limit=remainder/.01,
        maximum_half_response_change_fraction_of_limit=change/.01,
        absolute_limit_m=.001,relative_limit=.01,plus_rms_neu_m=[abs(x) for x in a],
        minus_rms_neu_m=[abs(x) for x in b],independent_realizations=1,
        finite_sample_check_only=True,global_remainder_bound_established=False,
        confidence_calibrated=False,scientific_decision='abstain')
    return errors,[[1.,1.,1.]],summary


def test_saved_nonlinearity_recomputes_matched_metrics_with_scalar_arithmetic():
    from lll.noise_nonlinearity_report import verify_curves
    errors,sigma,summary=fixture()
    row=verify_curves(errors,sigma,summary)
    assert row['passed'] and row['maximum_even_remainder_m']==pytest.approx(.0001)


@pytest.mark.parametrize('field',['passed','absolute_limit_m','relative_limit','independent_realizations',
    'confidence_calibrated','global_remainder_bound_established','maximum_even_remainder_m'])
def test_saved_nonlinearity_rejects_changed_result_or_interpretation(field):
    from lll.noise_nonlinearity_report import verify_curves
    errors,sigma,summary=fixture();summary[field]=not summary[field] if type(summary[field]) is bool else summary[field]+1
    with pytest.raises(ValueError):verify_curves(errors,sigma,summary)


def test_saved_nonlinearity_rejects_missing_or_nonfinite_curves():
    from lll.noise_nonlinearity_report import verify_curves
    errors,sigma,summary=fixture()
    with pytest.raises(ValueError):verify_curves(errors[:3],sigma,summary)
    errors[0][0][0]=math.nan
    with pytest.raises(ValueError):verify_curves(errors,sigma,summary)


def test_nonlinearity_audit_requires_closed_study_before_array_import(tmp_path):
    import sys
    from lll.noise_nonlinearity_report import inspect
    before='numpy' in sys.modules
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path,'data/missing')
    assert ('numpy' in sys.modules)==before


def test_nonlinearity_report_preserves_failed_settings_and_finite_scope():
    from lll.noise_nonlinearity_report import render
    r=dict(verified=True,total=4,complete=4,passed_settings=3,total_realizations=64,passed_realizations=63,
        rows=[dict(identity='point-1200',law='point',duration_s=1200,complete=True,passed=False,
            passed_realizations=15,realizations=16,maximum_even_remainder_m=.12,
            maximum_half_response_change_m=.02)])
    text=render(r)
    assert '3/4' in text and '15/16' in text and 'Failed' in text
    assert 'not' in text and 'confidence' in text and 'independent' in text


def test_nonlinearity_publication_requires_qualification_before_creating_files(tmp_path):
    from lll.noise_nonlinearity_report import publish
    with pytest.raises(ValueError):publish(tmp_path,'data/missing',qualification=None)
    assert not (tmp_path/'docs').exists()


def test_remainder_components_locate_failing_axis_and_quadratic_scaling():
    from lll.noise_nonlinearity_report import remainder_components
    errors,sigma,summary=fixture()
    for k,amplitude in enumerate((1.,-1.,.5,-.5)):
        errors[k][0][2]=amplitude*.6+amplitude**2*.02
    r=remainder_components(errors,sigma)
    assert r['axes']['up']['maximum_remainder_fraction_of_limit']==pytest.approx(2.)
    assert r['axes']['up']['worst_epoch_index']==0
    assert r['axes']['north']['maximum_remainder_fraction_of_limit']==pytest.approx(.01)
    assert max(v['maximum_quadratic_scaling_discrepancy_m'] for v in r['axes'].values())<1e-14
    assert r['parameter_uncertainty_included'] is False and r['labels_changed'] is False


def test_remainder_components_use_paired_moments_without_counting_signs_twice():
    from lll.noise_nonlinearity_report import remainder_components
    errors,sigma,summary=fixture();r=remainder_components(errors,sigma)
    expected=sum(((errors[0][0][j]**2+errors[1][0][j]**2)/2) for j in (0,1))
    assert r['paired_horizontal_mean_squared_error_m2']==pytest.approx(expected)
    assert r['predicted_horizontal_mean_squared_error_m2']==2.
    assert r['independent_realizations']==1
