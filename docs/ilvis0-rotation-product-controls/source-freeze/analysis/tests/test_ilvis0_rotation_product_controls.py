# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from types import SimpleNamespace
import numpy as np
import pytest
from lll import ilvis0_rotation_product_controls as controls
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_common_force_transform import ForceTransform
from test_ilvis0_native_box_bounds import configuration


def fixture(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *_:None)
    cfg=configuration();center=np.full(27,.1);lo=-np.ones(27);hi=np.ones(27)
    ref=ReferenceErrors(cfg,lo,hi,center,source_id='source-fixture')
    result=dict(identity='source-fixture',passed=True,
        cuts=dict(transform_binding=ForceTransform(ref).binding),
        probes=[dict(point=center.tolist(),common_error=[0.]*24) for _ in range(64)])
    cfg={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in cfg.items()}
    bundle=dict(result=result,case=dict(configuration=cfg))
    path=tmp_path/'bundle.json';path.write_text(json.dumps(bundle));saved={}
    ctx=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda:path,
        save=lambda name,value:saved.update({name:value}))
    task=dict(identity='new-controls',payload=dict(family='full',maximum_probes=64,maximum_planes=129))
    return task,ctx,saved


def test_new_constraints_reuse_physical_probes_without_oracle_reruns(tmp_path,monkeypatch):
    task,context,saved=fixture(tmp_path,monkeypatch)
    from lll import ilvis0_shared_norm_controls
    monkeypatch.setattr(ilvis0_shared_norm_controls,'evaluate',lambda *_:pytest.fail('do not rerun completed controls'))
    row=controls.evaluate(task,context)
    assert row['passed'] and row['parameter_count']==78 and row['original_parameter_count']==51
    assert row['physical_probes_reused']==64 and row['exact_inequalities']==8256
    assert row['original_reads']==row['native_evaluations']==row['new_physical_oracle_evaluations']==0
    assert saved['reservation.json']['exact_inequalities']==8256


def test_mismatched_source_and_extra_probes_cannot_qualify(tmp_path,monkeypatch):
    task,context,_=fixture(tmp_path,monkeypatch);path=context.input_path();bundle=json.loads(path.read_text())
    bundle['result']['cuts']['transform_binding']='other';path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError,match='source'):controls.evaluate(task,context)
    bundle['result']['probes'].append(bundle['result']['probes'][0]);path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError):controls.evaluate(task,context)
