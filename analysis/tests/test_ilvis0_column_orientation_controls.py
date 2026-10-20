# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from test_ilvis0_shared_reference_terms import config


def test_standalone_orientation_gain_adapter_uses_independent_oracle(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *_:None)
    source=Path(__file__).parents[1]/'lll/ilvis0_column_orientation_controls.py'
    spec=importlib.util.spec_from_file_location('standalone_orientation_gain',source)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    case=tmp_path/'case.json'
    case.write_text(json.dumps(dict(configuration=dict(config(),gravity=9.81),dv=[[.001,-.002,-.04905]],dt=[.005]),
        default=lambda value:value.tolist()))
    saved={}
    context=SimpleNamespace(input_path=lambda *_:case,save=lambda name,value:saved.setdefault(name,value),
        root=tmp_path,manifest={})
    task=dict(identity='independent-rotation-gain',payload=dict(family='full',seed=19,maximum_probes=64))
    row=adapter.evaluate(task,context)
    assert row['passed'] and row['probe_points']==64 and row['exact_inequalities']==4992
    assert row['maximum_oracle_difference']<3e-10
    assert row['native_evaluations']==0
    assert np.asarray(row['cuts']['design']).shape==(78,51)
