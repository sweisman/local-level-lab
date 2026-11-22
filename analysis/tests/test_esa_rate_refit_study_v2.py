"""Technical smoke qualification must not relabel nonconverged fits."""
import pytest


def test_v2_smoke_accepts_matched_reference_status_only():
    from lll.esa_rate_refit_study_v2 import smoke_gate

    assert smoke_gate(False, False, True, 'linear_points')
    assert smoke_gate(False, False, True, 'left_hold')
    assert not smoke_gate(False, False, False, 'right_hold')
    assert not smoke_gate(False, True, True, 'linear_points')
    assert not smoke_gate(False, False, False, 'linear_points')
    assert not smoke_gate(True, False, True, 'linear_points')


def test_v2_observed_gate_still_requires_convergence():
    from lll.esa_rate_refit_study_v2 import observed_gate

    assert observed_gate(True, True, 'linear_points')
    assert observed_gate(True, None, 'left_hold')
    assert not observed_gate(False, True, 'linear_points')
    assert not observed_gate(True, False, 'linear_points')


def test_v2_preparation_requires_source_qualification(tmp_path):
    from lll.esa_rate_refit_study_v2 import prepare

    with pytest.raises(ValueError, match='qualification required'):
        prepare(tmp_path, smoke=False)
