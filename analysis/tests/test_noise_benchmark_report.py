# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import math
import sys
import pytest


def summary():
    return dict(training_epochs=6,prediction_epochs=3,marginal_variance_neu_m2=[[1.,4.,9.]]*3,
        horizontal_expected_squared_rms_m2=5.,vertical_expected_squared_rms_m2=9.,
        sqrt_expected_horizontal_squared_rms_m=math.sqrt(5),sqrt_expected_vertical_squared_rms_m=3.,
        endpoint_standard_deviation_neu_m=[1.,2.,3.],known_calibration_benchmark=True,
        is_expected_realized_rms=False,calibration_uncertainty_included=False,
        confidence_calibrated=False,nonlinear_coverage_established=False,scientific_decision='abstain',
        accuracy_limits={'horizontal_rms_m':10.,'vertical_rms_m':30.},
        descriptive_second_moment_exceeds_screen={'horizontal':False,'vertical':False})


def test_saved_noise_summary_is_recomputed_without_numerical_imports():
    from lll.noise_benchmark_report import verify_summary
    before='numpy' in sys.modules;s=summary();original=copy.deepcopy(s)
    verify_summary(s,training_epochs=6,prediction_epochs=3)
    assert s==original and ('numpy' in sys.modules)==before


@pytest.mark.parametrize('field,value',[
    ('horizontal_expected_squared_rms_m2',4.),('endpoint_standard_deviation_neu_m',[1.,2.,4.]),
    ('is_expected_realized_rms',True),('confidence_calibrated',True),
    ('marginal_variance_neu_m2',[[1.,-1.,9.]]*3),('prediction_epochs',4)])
def test_saved_noise_summary_rejects_changed_values_or_interpretation(field,value):
    from lll.noise_benchmark_report import verify_summary
    s=summary();s[field]=value
    with pytest.raises(ValueError):verify_summary(s,training_epochs=6,prediction_epochs=3)


def test_noise_report_requires_closed_study_before_any_numerical_import(tmp_path):
    from lll.noise_benchmark_report import inspect
    before='numpy' in sys.modules
    with pytest.raises((ValueError,FileNotFoundError)):inspect(tmp_path,'data/unfinished')
    assert ('numpy' in sys.modules)==before


def test_noise_report_render_preserves_missing_cases_and_distinguishes_expected_scale():
    from lll.noise_benchmark_report import render
    report=dict(verified=True,total=4,complete=3,rows=[
        dict(identity='increment-120',complete=True,law='increment',duration_s=120.,
            horizontal_scale_m=2.,vertical_scale_m=.2),
        dict(identity='point-120',complete=False,law='point',duration_s=120.,reason='No sealed summary')],
        native_calls_attempted=100,elapsed_s=10.)
    text=render(report)
    assert 'Unavailable' in text and 'expected' in text and 'calibration' in text
    assert 'does not qualify' in text and 'unchanged' in text


def test_noise_report_publication_requires_qualification_before_creating_files(tmp_path):
    from lll.noise_benchmark_report import publish
    with pytest.raises(ValueError):publish(tmp_path,'data/missing',qualification=None)
    assert not (tmp_path/'docs').exists()
