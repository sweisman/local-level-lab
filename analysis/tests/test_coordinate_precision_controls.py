# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite lifecycle guards and honest reporting of precision failures."""
from types import SimpleNamespace

import pytest


def test_matrix_has_six_cases_three_settings_and_original_caps():
    from lll.coordinate_precision_controls import tasks
    rows=tasks()
    assert len(rows)==18 and len({r['identity'] for r in rows})==18
    assert sum(r['limits']['native_calls'] for r in rows)==144
    assert sum(r['limits']['packet_visits'] for r in rows)==18720
    assert all(r['limits']['bound_calls']==r['limits']['bound_steps']==0 for r in rows)


def test_unknown_identity_and_scope_fail_before_native_work(tmp_path):
    from lll.coordinate_precision_controls import fixture,evaluate
    with pytest.raises(ValueError,match='identity'):fixture('extra')
    with pytest.raises(ValueError,match='scope'):
        evaluate({},SimpleNamespace(root=tmp_path,manifest={'scope':'unapproved'}))


def test_denied_evaluation_charge_prevents_native_execution():
    from lll.coordinate_precision_controls import calculate
    def deny(**v):raise RuntimeError('allowance exhausted')
    def forbidden(*a,**k):raise AssertionError('uncharged call')
    with pytest.raises(RuntimeError,match='allowance exhausted'):
        calculate('north-large',kernel=forbidden,reserve=deny)


def test_summary_does_not_relabel_a_failed_precision_comparison():
    from lll.coordinate_precision_controls import summarize
    row=summarize(dict(identity='north-large',mode='baseline',precision_passed=False,
        analytic_relative_error=1e-9,difference_relative_errors=[.1,.2,1.],evaluations=7,columns=26))
    assert row['precision_passed'] is False and row['maximum_difference_relative_error']==1.
