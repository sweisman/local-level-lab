# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from lll import ilvis0_shared_norm_controls as control
from lll import ilvis0_control_shards as runner
from test_ilvis0_shared_reference_terms import config


def test_standalone_oracle_checks_all_seven_norms(tmp_path,monkeypatch):
    spec=importlib.util.spec_from_file_location('shared_norm_standalone_test',Path(control.__file__))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cfg=dict(config(),gravity=9.81);cfg={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in cfg.items()}
    path=tmp_path/'input.json';path.write_text(json.dumps(dict(configuration=cfg,dv=[[.001,-.002,-.04905]],dt=[.005])))
    saved={};monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    context=SimpleNamespace(input_path=lambda:path,root=tmp_path,manifest={},save=lambda n,v:saved.update({n:v}))
    result=module.evaluate(dict(identity='unit',payload=dict(family='full',seed=82,maximum_probes=64)),context)
    assert result['passed'] and result['vector_norm_checks']==448
    assert result['exact_inequalities']==11648 and 'reservation.json' in saved
