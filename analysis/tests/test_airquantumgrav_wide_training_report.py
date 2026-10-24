# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_wide_training_report_rejects_open_study_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_wide_training_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_wide_training_render_keeps_qualification_distinct_from_aircraft_findings():
    from lll.airquantumgrav_wide_training_report import render
    report=dict(total=24,passed=24,returned=24,qualified=True,elapsed_s=60.,charged=dict(native_calls=24),
        maximum_prediction_horizontal_rms_m=.001,maximum_prediction_height_rms_m=.002,maximum_prediction_spatial_error_m=.003)
    text=render(report)
    assert 'generated' in text and 'not aircraft findings' in text
    assert 'stopping' in text and '800' in text and '400' in text
    assert 'protected' in text
