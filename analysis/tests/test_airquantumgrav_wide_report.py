# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_wide_controls_report_rejects_open_study_before_audit(tmp_path):
    from lll.airquantumgrav_wide_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_wide_controls_report_does_not_claim_solver_or_observed_qualification():
    from lll.airquantumgrav_wide_report import render
    text=render(dict(total=48,returned=48,passed=48,qualified=True,elapsed_s=60.,
        charged=dict(native_calls=144),maximum_coarse_3d_m=.1,maximum_fine_3d_m=.03,maximum_value_disagreement_m=1e-5))
    assert 'not a solver qualification' in text.lower()
    assert 'No aircraft recording' in text and '27' in text
