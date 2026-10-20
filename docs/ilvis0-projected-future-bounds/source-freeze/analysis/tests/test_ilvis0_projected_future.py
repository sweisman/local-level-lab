# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from types import SimpleNamespace
import numpy as np
from lll import ilvis0_sharded_prediction as original,ilvis0_projected_future as adapter
from lll.ilvis0_sharded_native import plain
import ilvis0_native_training_worker as generator


def test_unchanged_projected_box_reproduces_saved_prediction_without_native_calls(tmp_path,monkeypatch):
    import lll.ilvis0_control_shards as runner
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    spec=dict(identity='projection-control',kind='orientation-sector',model=0,profile=False,sector=4,packets=100,
        training_times=[.2,.25],future_time=.3,maximum_bound_seconds=30.)
    case=generator.case_inputs(spec);source=tmp_path/'case.json';source.write_text(json.dumps(plain(case)))
    (tmp_path/'shards/000').mkdir(parents=True);saved={}
    first=SimpleNamespace(root=tmp_path,shard=0,input_path=lambda:source,charge=lambda **kw:None,
        save=lambda name,value:saved.__setitem__(name,value))
    result=original.evaluate(dict(payload=spec),first)
    parameters=[dict(lower=a,upper=b) for a,b in zip(saved['future.json']['lower'],saved['future.json']['upper'])]
    bundle=dict(result=result,training=saved['training.json'],future=saved['future.json'],parameters=parameters,physical_truth=case['truth'])
    path=tmp_path/'saved.json';path.write_text(json.dumps(plain(bundle)));charges=[];outputs={}
    second=SimpleNamespace(root=tmp_path,shard=0,manifest={},input_path=lambda key=None:source if key=='case' else path,
        charge=lambda **kw:charges.append(kw),save=lambda name,value:outputs.__setitem__(name,value))
    answer=adapter.evaluate(dict(identity=spec['identity'],payload=dict(case_key='case',packets=100,maximum_bound_seconds=30.)),second)
    assert answer['passed'] and answer['native_evaluations']==0
    assert charges==[dict(bound_calls=1,bound_steps=100)]
    np.testing.assert_allclose(answer['new_width_m'],answer['previous_width_m'],rtol=0,atol=1e-10)
    assert outputs['future.json']['parameter_count']==42
