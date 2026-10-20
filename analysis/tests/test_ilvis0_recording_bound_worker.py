# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def module():
    import ilvis0_recording_bound_worker
    return ilvis0_recording_bound_worker


def test_recording_scope_is_finite_and_does_not_use_archive_inputs():
    w=module()
    assert len(w.TASKS)==6
    assert w.CHECKPOINTS==(100,1000,10000,48000)
    assert w.LIMITS['maximum_bound_steps']==288000
    assert w.LIMITS['maximum_c_calls']==96
    assert w.LIMITS['maximum_tangent_calls']==24
    assert w.LIMITS['optimizer_starts']==w.LIMITS['original_reads']==0


def test_case_is_full_region_and_narrow_box_is_explicit_sensitivity():
    w=module();broad=w.case_inputs(w.TASKS[0]);narrow=w.case_inputs(w.TASKS[1])
    assert broad['raw_theta'].shape==(48000,3)
    assert np.all(broad['durations']==.005)
    assert broad['limits'].shape==(27,)
    assert narrow['limits'][2]<broad['limits'][2]
    assert broad['limits'][25]==narrow['limits'][25]==0.
    assert broad['limits'][26]==narrow['limits'][26]==1.


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    w=module();directory=tmp_path_factory.mktemp('recording-bound-kernels')
    w.history.base.compile_kernels(directory)
    return w.history.Kernel(directory)


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
def test_short_stream_retains_shared_calibration_and_matches_native(kernel,model):
    w=module();task=dict(next(t for t in w.TASKS if t['model']==model and t['box']=='broad'))
    case=w.case_inputs(task);result=w.evaluate(task,kernel,checkpoints=(2,5),case=case)
    assert result['checks_passed'],result
    assert result['supported_through_s']==.025
    assert result['executed_bound_steps']==5
    assert len(result['checkpoints'])==2
    assert result['calls']==dict(c=8,tangent=2)
    assert result['native_rounding_certificate'] is False


def test_unsupported_box_is_an_outcome_not_a_retry(kernel):
    w=module();task=w.TASKS[0];case=w.case_inputs(task)
    case['limits'][6:9]=1e12
    result=w.evaluate(task,kernel,checkpoints=(2,),case=case)
    assert result['support_status']=='unsupported'
    assert result['executed_bound_steps']==0
    assert result['calls']==dict(c=0,tangent=0)


def test_completed_charged_worker_cannot_restart(tmp_path,monkeypatch):
    w=module();monkeypatch.setattr(w,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='restart'):w.run()
