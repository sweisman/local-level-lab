# SPDX-License-Identifier: AGPL-3.0-or-later
"""Declared study purpose survives the real freeze and authorization hash."""
import pytest

from lll.studies.runtime import Definition


def definition(root):
    for name in ('analysis/lll/adapter.py','analysis/tests/ilvis0_control_shards.py',
        'analysis/lll/ilvis0_control_shards.py','analysis/lll/ilvis0_receipt_journal.py',
        'analysis/lll/compute_budget.py','analysis/lll/__init__.py'):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# metadata fixture\n')
    (root/'fixture.json').write_text('{}')
    return dict(id='purpose-check',adapter='analysis/lll/adapter.py',sources=['analysis/lll/adapter.py'],
        inputs={'fixture':'fixture.json'},tasks=[dict(identity='check',input_key='fixture',
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))],
        workers=1,threads=1,maximum_wall_s=60)


def test_explicit_receiver_inventory_scope_is_frozen_and_authorized(tmp_path):
    from lll.ilvis0_control_shards import verify
    value=definition(tmp_path);value['scope']='receiver-only development inventory; no IMU or model fitting'
    manifest=Definition.from_dict(value,tmp_path).prepare(tmp_path)
    assert manifest['scope']==value['scope']
    assert verify(tmp_path/'data/purpose-check')['scope']==value['scope']


def test_legacy_default_scope_remains_generated_software_controls(tmp_path):
    value=definition(tmp_path)
    manifest=Definition.from_dict(value,tmp_path).prepare(tmp_path)
    assert manifest['scope']=='generated software controls only'


@pytest.mark.parametrize('scope',['','  ',None,123])
def test_invalid_explicit_scope_is_rejected_before_freezing(tmp_path,scope):
    value=definition(tmp_path);value['scope']=scope
    with pytest.raises(ValueError,match='scope'):Definition.from_dict(value,tmp_path)
    assert not (tmp_path/'data').exists()
