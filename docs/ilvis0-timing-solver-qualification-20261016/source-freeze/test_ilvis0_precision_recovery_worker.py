# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

import ilvis0_precision_recovery_worker as worker
from lll.ilvis0_sweep_journal import Ledger
from test_ilvis0_precision_solver import kernels,straight_problem


def test_per_role_budget_is_enforced_before_another_native_call(tmp_path,kernels):
    base=straight_problem(kernels,(.15,-.2))
    problem=worker.ChargedProblem.__new__(worker.ChargedProblem)
    problem.__dict__.update(base.__dict__)
    problem.book=Ledger(tmp_path,'a'*64,['known'],fit_limit=200,diagnostic_limit=2)
    problem.book.start('known');problem.identity='known';problem.phase='fit';problem.maximum_evaluations=1
    problem.residual_tangent(np.zeros(2),'flat_still')
    with pytest.raises(worker.base.estimator.EvaluationLimit):
        problem.residual_tangent(np.zeros(2),'flat_still')
    assert problem.book.count('known','fit')==1
    problem.phase='diagnostic';problem.predict(np.zeros(2),'flat_still')
    assert problem.book.count('known','diagnostic')==1


def test_control_disagreement_with_saved_cost_blocks_qualification():
    plan=dict(tasks=[dict(identity='control',role='control',reference=dict(residual_sum_squares=1.))],
              control_cost_relative_tolerance=1e-6,control_track_rms_tolerance_m=.01)
    fit=dict(converged=True,residual_sum_squares=1.01,reference_track_change_rms_neu_m=[0.,0.,0.])
    value=worker.qualify(plan,dict(control=fit))
    assert not value['controls_passed']
    assert not value['qualified']


def test_atomic_artifact_has_no_partial_publication(tmp_path):
    path=tmp_path/'saved.json.gz';worker.atomic_bytes(path,b'first')
    worker.atomic_bytes(path,b'second')
    assert path.read_bytes()==b'second'
    assert not path.with_suffix(path.suffix+'.tmp').exists()
