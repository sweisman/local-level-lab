# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np


def module():
    from lll import ilvis0_projected_trust_qualification as q
    return q


def rows():
    return [dict(identity='a',model='sphere_rotating',clock='nominal',axes=['height'],start=start,
        fit=dict(converged=True,residual_sum_squares=1e-12,normalized_parameters=[sign]),
        prediction_error_m=np.zeros((3,3)).tolist(),maximum_retained_error_m=0.,truth_cost=1e-10)
        for start,sign in [('zero',-.9),('opposed',.9)]]


def test_nuisance_differences_do_not_replace_retained_prediction_agreement():
    q=module();values=rows();check=q.compare_pair(*values)
    assert check['passed']
    values[1]['prediction_error_m'][1][2]=.02
    assert not q.compare_pair(*values)['passed']


def test_incomplete_or_wrong_pair_cannot_pass_on_cost_alone():
    q=module();values=rows();values[1]['fit']['converged']=False
    assert not q.compare_pair(*values)['passed']
    values=rows();values[1]['axes']=['latitude','longitude']
    assert not q.compare_pair(*values)['passed']


def test_exact_scope_contains_every_model_clock_axes_start_once():
    tasks=module().tasks()
    assert len(tasks)==len({r['identity'] for r in tasks})==24
    assert len({(r['model'],r['clock'],tuple(r['axes'])) for r in tasks})==12
