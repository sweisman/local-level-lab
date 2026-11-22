"""The versioned pilot changes recovery provenance, not scientific tasks."""

from lll import ilvis0_observed_method_pilot as original
from lll import ilvis0_observed_method_pilot_v2 as revised
import pytest


def test_v2_reuses_preselected_recordings_and_scientific_tasks():
    assert revised.tasks is original.tasks
    assert revised.SCOPE==original.SCOPE
    assert revised.PREFLIGHT_SCOPE==original.PREFLIGHT_SCOPE
    assert revised.ID!=original.ID
    assert revised.PREFLIGHT_ID!=original.PREFLIGHT_ID


def test_v2_requires_new_recovery_qualification_and_generated_gate(tmp_path,monkeypatch):
    assert revised.RECOVERY!=original.RECOVERY
    assert revised.REQUEST!=original.REQUEST
    assert revised.PLAN!=original.PLAN
    monkeypatch.setattr('lll.ilvis0_long_independent_solver_report.build',
                        lambda root:{'passed':False})
    with pytest.raises(ValueError,match='long independent generated gate'):
        revised.prepare(tmp_path,preflight=True)
