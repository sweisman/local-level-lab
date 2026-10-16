# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from test_ilvis0_timing_worker import fixture


def module():
    import ilvis0_timing_worker_v2
    return ilvis0_timing_worker_v2


def test_two_failed_endpoints_only_and_24_call_ceiling():
    tasks=module().select_tasks(*fixture())
    assert len(tasks)==2
    assert all(t['identity'].startswith(module().PREFIX) for t in tasks)
    assert sum(t['maximum_native_evaluations'] for t in tasks)==24


def test_cannot_substitute_a_converged_fit():
    parent,summary,audit=fixture();summary['results'][module().PREFIX+'primary']['converged']=True
    with pytest.raises(ValueError):module().select_tasks(parent,summary,audit)
