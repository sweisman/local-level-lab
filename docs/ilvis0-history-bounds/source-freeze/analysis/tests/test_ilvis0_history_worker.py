# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def module():
    import ilvis0_history_worker
    return ilvis0_history_worker


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    worker=module();directory=tmp_path_factory.mktemp('history-kernels')
    worker.base.compile_kernels(directory)
    return worker.Kernel(directory)


def test_finite_history_scope_preserves_full_parameter_region():
    w=module()
    assert len(w.TASKS)==54
    assert w.LIMITS['maximum_c_calls']==918
    assert w.LIMITS['maximum_tangent_calls']==54
    assert w.LIMITS['maximum_reference_calls']==2376
    assert w.LIMITS['maximum_probes']==864
    assert w.LIMITS['original_reads']==w.LIMITS['optimizer_starts']==0
    assert {t['packets'] for t in w.TASKS}=={3,9,33}


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('timing',['interior','boundary','multiple'])
def test_generated_history_agrees_with_both_kernels_and_global_bounds(kernel,model,timing):
    w=module();task=dict(next(t for t in w.TASKS if t['model']==model and t['timing']==timing and t['packets']==3 and t['profile']))
    task['probes']=4
    result=w.evaluate(task,kernel)
    assert result['passed'],result
    assert result['columns']==27
    assert result['calls']==dict(c=5,tangent=1,reference=32)
    assert (result['native_boundary_warning']>0)==(timing=='boundary')
    assert result['boundary_crossings']>0 if timing!='interior' else result['boundary_crossings']==0


def test_history_reference_timing_column_uses_native_one_sided_branch(kernel):
    w=module();task=next(t for t in w.TASKS if t['timing']=='boundary')
    case=w.case_inputs(task);point=case['center'].astype(complex);point[25]+=1e-25j
    reference=w.reference(case,point)['observation'].imag/1e-25
    _,jac,warning=kernel.tangent(case,case['center'])
    assert warning==1
    np.testing.assert_allclose(reference*case['metre_scale'],jac[:,25]*case['metre_scale'],atol=2e-5,rtol=1e-10)


def test_calls_deadline_and_restart_guards(tmp_path,monkeypatch):
    w=module();calls=w.base.Calls(1,1,1)
    calls.tick('c')
    with pytest.raises(ValueError):calls.tick('c')
    with pytest.raises(w.base.AllowanceExhausted):w.base.check_time(0.)
    monkeypatch.setattr(w,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='restart'):w.run()
