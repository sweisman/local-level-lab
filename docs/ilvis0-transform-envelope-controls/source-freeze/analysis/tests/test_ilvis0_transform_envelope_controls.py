# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
import sys
from types import SimpleNamespace
from lll import ilvis0_transform_envelope_controls as controls


def test_standalone_adapter_profiles_exact_support_and_rejection(tmp_path,monkeypatch):
    import lll.ilvis0_control_shards as runner
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    path=tmp_path/'fixture.json';path.write_text(json.dumps(dict(initial_r=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],
        limits=[1.]*18+[.15]*3+[1.]*6)))
    spec=importlib.util.spec_from_file_location('standalone_joint_control',controls.__file__)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    for payload in (dict(kind='force-only',axis=2,column=1),dict(kind='rejection',field='force-source'),dict(kind='rejection',field='future-observation')):
        saved={};context=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda:path,save=lambda name,value:saved.__setitem__(name,value))
        result=adapter.evaluate(dict(identity='fixture',payload=payload),context)
        assert result['passed'] and sys.getprofile() is None
        assert result['lp_proposals']==sum(name.startswith('proposal-') for name in saved)
        assert result['exact_certificates']==sum(name.startswith('certificate-') for name in saved)
        if payload['kind']=='force-only':assert result['selected_force_column']==49 and result['lp_proposals']==6
        else:assert result['lp_proposals']==0
