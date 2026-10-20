# SPDX-License-Identifier: AGPL-3.0-or-later
import time

import numpy as np
import pytest

import ilvis0_geographic_worker as worker


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    path=tmp_path_factory.mktemp('geographic-bound-kernels');worker.compile_kernels(path)
    return worker.Kernel(path)


def test_finite_scope_covers_27_columns_and_no_archive_work():
    assert len(worker.TASKS)==72 and sum(t['probes'] for t in worker.TASKS)==4608
    assert worker.LIMITS['maximum_c_calls']==4680 and worker.LIMITS['maximum_tangent_calls']==72
    assert worker.LIMITS['maximum_reference_calls']==6624
    assert worker.LIMITS['original_reads']==worker.LIMITS['optimizer_starts']==0


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
@pytest.mark.parametrize('timing',['fixed','interior'])
def test_full_native_value_derivative_and_bound_agree(kernel,model,timing):
    task=dict(next(t for t in worker.TASKS if t['model']==model and t['timing']==timing
        and t['removal_center']=='upper' and t['width']=='broad'))
    task['probes']=4;result=worker.evaluate(task,kernel)
    assert result['passed'] and result['parameter_columns']==27
    assert result['c_calls']==5 and result['tangent_calls']==1 and result['reference_calls']==32


def test_native_parameter_timing_column_is_preserved_when_fixed(kernel):
    task=next(t for t in worker.TASKS if t['timing']=='fixed');case=worker.case_inputs(task)
    out,jac,warning=kernel.tangent(case,case['center'])
    assert jac.shape==(3,27) and np.all(jac[:,25]==0.) and warning==1


def test_reference_has_continuous_longitude_and_shared_packet_fraction():
    case=worker.case_inputs(next(t for t in worker.TASKS if t['timing']=='interior'))
    value=worker.reference(case,np.ones(27))
    assert value['inputs']['period']<=case['packet_dt']
    assert np.isclose(value['inputs']['period']/case['packet_dt'],.7)


def test_allowances_and_restart_protection(tmp_path,monkeypatch):
    book=worker.Calls(1,1,1);book.tick('c');book.tick('tangent');book.tick('reference')
    with pytest.raises(ValueError):book.tick('c')
    monkeypatch.setattr(worker,'DATA',tmp_path);(tmp_path/'start.json').write_text('{}')
    with pytest.raises(ValueError,match='cannot restart'):worker.run()
    with pytest.raises(worker.AllowanceExhausted):worker.check_time(time.monotonic()-1.)
