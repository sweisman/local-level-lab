# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small adapter check: charge before work and preserve all prediction evidence."""
import json
from types import SimpleNamespace
import numpy as np
from lll.ilvis0_sharded_native import plain
from lll import ilvis0_transform_prediction as adapter
import ilvis0_native_training_worker as generator


def test_charged_adapter_retains_training_future_and_all_columns(tmp_path):
    specification=dict(identity='adapter',kind='orientation-sector',model=0,profile=False,sector=4,packets=100,
        training_times=[.2,.25],future_time=.3,maximum_bound_seconds=30.)
    case=generator.case_inputs(specification);source=tmp_path/'input.json';source.write_text(json.dumps(plain(case)))
    (tmp_path/'shards/000').mkdir(parents=True);charges=[];saved={}
    def save(name,value):
        assert charges
        if name=='native-03.json':assert 'training.json' in saved and 'future.json' in saved
        saved[name]=value
    context=SimpleNamespace(root=tmp_path,shard=0,input_path=lambda:source,
        charge=lambda **value:charges.append(value),save=save)
    result=adapter.evaluate(dict(payload=specification),context)
    assert result['passed'] and result['scientific_decision']=='abstain'
    assert result['native_evaluations']==3 and result['bound_evaluations']==4
    assert sum(c.get('packet_visits',0) for c in charges)==300
    assert sum(c.get('bound_steps',0) for c in charges)==800
    assert np.shape(saved['training.json']['region']['design'])[1]==51
    assert saved['future.json']['parameter_count']==51
