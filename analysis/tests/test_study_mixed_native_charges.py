# SPDX-License-Identifier: AGPL-3.0-or-later
"""Mixed operation accounting, using real journals and no numerical work."""
import pytest

from lll import ilvis0_control_shards as runner


def fixture(tmp_path,*,kind='mixed',accounting='sqlite-v1'):
    project=tmp_path/'project';project.mkdir();(project/'adapter.py').write_text('# fixture\n')
    (project/'case.json').write_text('{}\n')
    entry=project/'analysis/tests/ilvis0_control_shards.py';entry.parent.mkdir(parents=True);entry.write_text('# fixture\n')
    path=tmp_path/'study'
    task=dict(identity='case',input_key='case',native_kind=kind,payload={},
        limits=dict(native_calls=2,packet_visits=5,bound_calls=1,bound_steps=1))
    runner.prepare(path,project_root=project,tasks=[task],sources=['adapter.py','analysis/tests/ilvis0_control_shards.py'],
        inputs={'case':'case.json'},adapter='adapter.py',workers=1,threads=1,maximum_wall_s=60,
        environment=runner.runtime_environment(),accounting_format=accounting)
    return runner.TaskContext(path,0,'case')


@pytest.mark.parametrize('accounting',['receipts-v1','sqlite-v1'])
def test_mixed_native_calls_keep_each_actual_kind_and_one_combined_allowance(tmp_path,accounting):
    context=fixture(tmp_path,accounting=accounting)
    context.charge(native_kind='tangent',native_calls=1,packet_visits=3)
    context.charge(native_kind='value',native_calls=1,packet_visits=2)
    rows=context.journal.read('sweeps')
    assert [v['kind'] for v in rows]==['tangent','value']
    assert runner._counts(context.journal,context.task)==dict(native_calls=2,packet_visits=5,bound_calls=0,bound_steps=0)
    with pytest.raises(ValueError,match='allowance'):context.charge(native_kind='value',native_calls=1,packet_visits=0)
    assert len(context.journal.read('sweeps'))==2


@pytest.mark.parametrize('bad_kind',[None,'mixed','undeclared'])
def test_mixed_context_rejects_missing_or_invalid_operation_kind_before_charging(tmp_path,bad_kind):
    context=fixture(tmp_path)
    with pytest.raises(ValueError):context.charge(native_kind=bad_kind,native_calls=1,packet_visits=1)
    assert context.journal.read('sweeps')==[]


def test_fixed_native_kind_and_bound_reservations_cannot_be_reclassified(tmp_path):
    context=fixture(tmp_path,kind='tangent')
    with pytest.raises(ValueError):context.charge(native_kind='value',native_calls=1,packet_visits=1)
    with pytest.raises(ValueError):context.charge(native_kind='value',bound_calls=1,bound_steps=1)
    assert context.journal.read('sweeps')==[]
    context.charge(native_calls=1,packet_visits=1)
    assert context.journal.read('sweeps')[0]['kind']=='tangent'
