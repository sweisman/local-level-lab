# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_pilot_preparation') is not None,'finite preparation adapter missing'
    return importlib.import_module('lll.airquantumgrav_pilot_preparation')


def test_pilot_preparation_has_separate_finite_no_fit_allowance():
    r=library().recipe();tasks=library().tasks()
    assert len(tasks)==1 and all(v==0 for v in tasks[0]['limits'].values())
    assert r['workers']==r['threads']==1 and r['maximum_wall_s']==1200
    assert r['receiver_passes']==r['imu_passes']==1
    assert r['maximum_imu_records']==10000000 and r['maximum_receiver_records']==100000
    assert r['maximum_retained_points']==360100 and r['maximum_constructed_intervals']==360099
    assert r['working_error_descriptions']==2 and r['observed_starts']==r['native_calls']==r['protected_reads']==0


def test_pilot_preparation_requires_source_bound_qualification_before_writes(tmp_path):
    with pytest.raises(ValueError,match='qualification'):library().prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_pilot_preparation_rejects_changed_task_before_reading_any_source():
    from types import SimpleNamespace
    def forbidden(*args):raise AssertionError('input opened before frozen task checked')
    with pytest.raises(ValueError):library().evaluate(dict(identity='other'),SimpleNamespace(input_path=forbidden))
