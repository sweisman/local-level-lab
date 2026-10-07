# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guard the expensive diagnostic's freeze and deadline without running its envelope."""
import hashlib
from pathlib import Path
import signal

import pytest
import check_observed_pair_envelope as check


def fixture_plan(monkeypatch):
    monkeypatch.setattr(check.baseline, 'implementation_hash', lambda: 'science-fixture')
    monkeypatch.setattr(check, 'numerical_environment_hash', lambda: 'environment-fixture')
    return dict(implementation_hash='science-fixture', numerical_environment_hash='environment-fixture',
        helper_sha256=hashlib.sha256(Path(check.__file__).read_bytes()).hexdigest(),
        input_sha256={}, wall_seconds_cap=1., trajectory_input={}, schedule_minutes=[],
        crab_model='wind_tas', comparison=check.PAIR, limitations=['fixture only'])


def test_changed_environment_refused_before_work(monkeypatch):
    plan = fixture_plan(monkeypatch)
    plan['numerical_environment_hash'] = 'different-environment'
    with pytest.raises(ValueError, match='numerical environment changed'):
        check.execute(plan)


def test_expired_budget_cannot_claim_envelope_pass(monkeypatch):
    plan = fixture_plan(monkeypatch)
    monkeypatch.setattr(check.baseline, 'realize', lambda *args, **kwargs: {})
    monkeypatch.setattr(check.baseline, 'geometry_problem', lambda *args, **kwargs: None)
    def timed_out(problem):
        raise TimeoutError('fixture deadline')
    monkeypatch.setattr(check, 'envelope_information', timed_out)
    result = check.execute(plan)
    assert result['state'] == 'wall_time_cap_reached_no_envelope_claim'
    assert 'report' not in result and 'criterion' not in result
    assert result['additional_flight_attempts'] == 0
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0.


def test_oversized_budget_refused(monkeypatch):
    plan = fixture_plan(monkeypatch)
    plan['wall_seconds_cap'] = 121
    with pytest.raises(ValueError, match='time cap'):
        check.execute(plan)
