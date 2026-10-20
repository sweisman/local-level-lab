# SPDX-License-Identifier: AGPL-3.0-or-later
import time

import numpy as np
import pytest

import ilvis0_local_step_worker as worker


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    directory=tmp_path_factory.mktemp('local-bound-kernel');worker.compile_kernel(directory)
    return worker.Kernel(directory/'local-bound-kernel.so')


def test_scope_has_finite_generated_native_and_reference_counts():
    assert len(worker.TASKS)==30
    assert sum(t['probes'] for t in worker.TASKS)==1920
    assert worker.LIMITS['maximum_software_native_calls']==1950
    assert worker.LIMITS['maximum_reference_calls']==3870
    assert worker.LIMITS['original_reads']==worker.LIMITS['optimizer_starts']==0


@pytest.mark.parametrize('kind',['narrow','broad','zero'])
def test_compiled_kernel_reference_and_global_local_bound(kernel,kind):
    task=next(dict(t) for t in worker.TASKS if (t.get('zero_center') if kind=='zero' else t['width']==kind and not t.get('zero_center')))
    task['probes']=4
    result=worker.evaluate(task,kernel)
    assert result['passed'] and result['probe_count']==4
    assert result['software_native_calls']==5 and result['reference_calls']==9


def test_complex_directional_derivative_has_independent_known_answer():
    task=next(t for t in worker.TASKS if t['model']=='flat_still' and t.get('zero_center') and not t['profile'])
    case=worker.case_inputs(task);z=np.zeros(24,dtype=complex);z[3:6]=1e-25j
    value=worker.reference(case,z)
    np.testing.assert_allclose(value['velocity'].imag/1e-25,case['widths'][3:6],atol=1e-12)


@pytest.mark.parametrize('model',['sphere_still','flat_still'])
def test_profiled_broad_case_preserves_candidate_physics(kernel,model):
    task=dict(next(t for t in worker.TASKS if t['model']==model and t['profile'] and t['width']=='broad'))
    task['probes']=4
    assert worker.evaluate(task,kernel)['passed']


def test_complex_tangent_matches_separate_symmetric_difference():
    task=next(t for t in worker.TASKS if t['model']=='flat_still' and t['profile'] and t['width']=='broad')
    case=worker.case_inputs(task);direction=np.random.default_rng(55).uniform(-.2,.2,24)
    derivative=worker.reference(case,1e-25j*direction)
    plus=worker.reference(case,1e-4*direction);minus=worker.reference(case,-1e-4*direction)
    for key in ('attitude','velocity','local_displacement'):
        np.testing.assert_allclose(derivative[key].imag/1e-25,(plus[key]-minus[key])/2e-4,rtol=3e-6,atol=3e-8)


def test_reference_limits_are_checked_before_calls():
    book=worker.Calls(1,1);book.tick('native');book.tick('reference')
    with pytest.raises(ValueError):book.tick('native')
    assert book.counts=={'native':1,'reference':1}


def test_interrupted_allowance_is_not_resumable(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()


def test_deadline_is_cooperative():
    with pytest.raises(worker.AllowanceExhausted):worker.check_time(time.monotonic()-1.)
