# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from lll import ilvis0_column_orientation_prediction as candidate


def test_saved_support_uses_added_constraint_without_future_truth():
    lo=[-1.]*51;hi=[1.]*51;zero=[0.]*51;one=zero.copy();one[0]=1.
    region=dict(lower=lo,upper=hi,center=zero,coordinate_scale=[1.]*3,origin=[0.]*3,
        arithmetic_allowance=0.,inequality_design=[zero,one],inequality_upper=[0.,.25])
    bound=dict(previous_coefficients=[[0.]*6]*3,acceleration_coefficients=[[0.]*9]*3,
        transform_coefficients=[[0.]*9]*3,unshared_remainder=[0.]*3)
    cert=dict(upper_multipliers=[0.],lower_multipliers=[0.])
    saved=dict(nominal=[0.]*3,jacobian=[[1.]+[0.]*26,[0.]*27,[0.]*27],bound=bound,
        envelope=dict(certificates=[cert]*3,lower=[-1.,0.,0.],upper=[1.,0.,0.]))
    reservations=[]
    result=candidate.rebuild_future(region,saved,lo,hi,reserve=reservations.append)
    assert reservations==list(range(1,7))
    assert result['lower']==[-1.,0.,0.] and result['upper']==[.25,0.,0.]


def test_standalone_entry_does_not_need_a_package_relative_import():
    spec=importlib.util.spec_from_file_location('consistent_prediction_standalone',Path(candidate.__file__))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate)


def test_sealed_generated_case_reuses_evidence_without_native_calls(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_sharded_native import read
    root=Path(__file__).resolve().parents[2];old=root/'docs/ilvis0-orientation-gain-prediction'
    manifest=read(old/'manifest.json');task=manifest['tasks'][0]
    summary=read(old/'summary.json');result=next(r for r in summary['results'] if r['identity']==task['identity'])
    identity=task['identity'];bundle=dict(result=read(old/result['artifact'])['result'],
        training=read(old/'artifacts'/identity/'training.json'),future=read(old/'artifacts'/identity/'future.json'))
    path=tmp_path/'bundle.json';path.write_text(json.dumps(bundle));saved={}
    case_key=task['payload']['case_key']
    case=old/manifest['inputs'][case_key]['path']
    monkeypatch.setattr(runner,'_check_continue',lambda *args:None)
    context=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda key=None:case if key else path,
        save=lambda name,value:saved.update({name:value}))
    result=candidate.evaluate(dict(identity=identity,payload=dict(case_key=case_key,maximum_proposals=6)),context)
    assert result['passed'] and result['native_evaluations']==0
    assert result['exact_supports_checked']==6 and 'independent-audit.json' in saved
