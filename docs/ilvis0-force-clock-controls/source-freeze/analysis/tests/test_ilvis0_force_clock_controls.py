# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from types import SimpleNamespace
from lll import ilvis0_force_clock_controls as control
from lll.ilvis0_sharded_native import plain
import ilvis0_native_training_worker as generator


def test_standalone_loader_and_short_adapter_reservations(tmp_path,monkeypatch):
    import lll.ilvis0_control_shards as runner
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    spec=importlib.util.spec_from_file_location('standalone_force_clock_control',control.__file__)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    source=tmp_path/'case.json';source.write_text(json.dumps(plain(generator.case_inputs(dict(model=0,profile=False,packets=1600)))))
    artifacts={};context=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda:source,
        save=lambda name,value:artifacts.__setitem__(name,value))
    result=adapter.evaluate(dict(identity='short-control',payload=dict(family='short',packets=16,nominal_time=.04,seed=611)),context)
    assert result['passed'] and result['exact_integral_checks']==72
    assert result['independent_histories']<=14 and len(result['augmented_design'][0])==51
    assert sum(name.startswith('history-') for name in artifacts)==result['independent_histories']
