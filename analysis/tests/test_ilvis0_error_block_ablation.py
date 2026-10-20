# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from types import SimpleNamespace
import pytest
from lll import ilvis0_error_block_ablation as diagnostic
from test_ilvis0_transform_audit import fixture


def context(tmp_path,monkeypatch,block='acceleration_remainder'):
    from lll import ilvis0_control_shards
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *_:None)
    result,training,future=fixture()
    bundle=json.loads(json.dumps(dict(result=result,training=training,future=future,anchor=[0.]*51)))
    future=bundle['future'];future['bound']['acceleration_coefficients'][0][6]=1.
    cert=future['envelope']['certificates'][0];cert['upper']='1';cert['negated_lower']='1'
    future['envelope']['lower'][0]=-1.15625;future['envelope']['upper'][0]=1.15625
    bundle['result']['future_lower_m']=future['envelope']['lower'];bundle['result']['future_upper_m']=future['envelope']['upper']
    path=tmp_path/'case.json';path.write_text(json.dumps(bundle));saved={}
    ctx=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda:path,
        save=lambda name,value:saved.update({name:value}))
    task=dict(identity='fixture-fixed-'+block,payload=dict(source_identity='fixture',block=block,maximum_proposals=6))
    return task,ctx,saved


def test_fixing_remainder_recovers_known_conditional_width_and_stays_oracle_labeled(tmp_path,monkeypatch):
    task,ctx,saved=context(tmp_path,monkeypatch)
    row=diagnostic.evaluate(task,ctx)
    assert row['passed'] and row['parameter_count']==51 and row['exact_supports_checked']==6
    assert row['conditional_width_m'][0]==.3125 and row['source_width_m'][0]==2.3125
    assert row['oracle_assisted'] and row['prediction_method_qualified'] is False
    assert saved['future.json']['lower'][39:42]==[0.,0.,0.]
    assert len(saved['future.json']['lower'])==51 and row['lp_proposals_reserved']==6


def test_fixing_unrelated_matrix_block_correctly_leaves_width_unchanged(tmp_path,monkeypatch):
    task,ctx,_=context(tmp_path,monkeypatch,block='force_matrix')
    row=diagnostic.evaluate(task,ctx)
    assert row['passed'] and row['conditional_width_m']==row['source_width_m']


def test_invalid_anchor_and_unknown_block_are_rejected(tmp_path,monkeypatch):
    task,ctx,_=context(tmp_path,monkeypatch)
    path=ctx.input_path();bundle=json.loads(path.read_text());bundle['anchor'][39]=2.
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError,match='anchor'):diagnostic.evaluate(task,ctx)
    task['payload']['block']='unknown'
    with pytest.raises(ValueError):diagnostic.evaluate(task,ctx)
