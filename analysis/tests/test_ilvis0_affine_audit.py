# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import importlib.util


def audit():
    name='lll.ilvis0_affine_audit'
    assert importlib.util.find_spec(name), 'saved-tangent audit is missing'
    return importlib.import_module(name)


def test_zero_step_is_feasible_and_increasing_step_is_visible():
    import numpy as np
    module=audit();point=np.array([0.]);residual=np.array([1.]);jac=np.array([[2.]])
    zero=module.step_metrics(point,residual,jac,np.zeros(1))
    worse=module.step_metrics(point,residual,jac,np.ones(1))
    assert zero['feasible'] and zero['affine_cost_change']==0
    assert worse['feasible'] and worse['affine_cost_change']>0 and not worse['improves_on_zero']


def test_affine_audit_keeps_stationary_and_weak_directions_distinct():
    import numpy as np
    result=audit().assess(np.array([0.,0.]),np.array([1.,1.,1.]),np.array([[1e6,0.],[0.,1e-6],[0.,0.]]))
    assert len(result['methods'])==2
    assert result['condition_number']>=1e11
    assert all(m['feasible'] for m in result['methods'])
    assert result['zero_step_cost']>min(m['affine_cost'] for m in result['methods'])
