# SPDX-License-Identifier: AGPL-3.0-or-later
"""Long bound operations must be visible without treating them as native calls."""
import importlib.util
from pathlib import Path
from lll import ilvis0_control_shards as runner
from test_ilvis0_control_shards import fixture


def test_status_separates_native_and_bound_reservations(tmp_path):
    output,_,_=fixture(tmp_path);context=runner.TaskContext(output,0,'task-0')
    context.charge(native_calls=1,packet_visits=3);context.charge(bound_calls=1,bound_steps=3)
    path=Path(__file__).resolve().parents[1]/'status.py'
    spec=importlib.util.spec_from_file_location('bound_status_test',path);status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)
    result=status.inspect_study(output)
    assert result['native_calls']==1
    assert result['bound_calls']==1 and result['bound_limit']==4
    assert '1/4 charged bounds' in status.render(dict(result,name='fixture'))
