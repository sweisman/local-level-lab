# SPDX-License-Identifier: AGPL-3.0-or-later
"""Portable adapter fixtures with fresh references and analytic future bounds.

The input packets remain sealed. Numerical references are constructed in the
test environment rather than claiming bitwise replay of another host's result.
Zero affine prediction rows qualify plumbing, not inertial physics or coverage.
"""
import hashlib
import json
from types import SimpleNamespace


def generated_context(old,tmp_path,monkeypatch):
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from test_ilvis0_transform_audit import fixture
    manifest=read(old/'manifest.json');task=manifest['tasks'][0]
    case_key=task['payload'].get('case_key',task['input_key'])
    record=manifest['inputs'][case_key];case_path=old/record['path']
    if hashlib.sha256(case_path.read_bytes()).hexdigest()!=record['sha256']:
        raise ValueError('sealed test input changed')
    case=read(case_path);sector_id=int(task['identity'].rsplit('-',1)[1]);box=sector(sector_id)
    ref=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    result,training,future=fixture();region=training['region'];report=ref.report()
    lower=box['lower'].tolist()+[-1.]*24;upper=box['upper'].tolist()+[1.]*24
    region.update(binding=ref.binding,source_id=ref.parent.source_id,lower=lower,upper=upper,
        center=box['center'].tolist()+[0.]*24)
    future.update(reference=report,lower=lower,upper=upper,fixed_center=box['center'].tolist())
    bound=future['bound']
    bound.update(reference_binding=ref.binding,shared_binding=report['parent']['binding'],
        acceleration_binding=report['acceleration']['binding'],transform_binding=report['transform']['binding'],
        transform_reference=report['transform'],source_id=ref.parent.source_id)
    bound['clock_transform']['matrix_binding']=report['transform']['binding']
    future['envelope'].update(shared_binding=ref.binding,source_id=ref.parent.source_id)
    identity=task['identity'];result.update(identity=identity,truth_in_sector=False,
        known_shared_error=[0.]*24,contraction=dict(lower=lower,upper=upper),
        task=dict(model=case['configuration']['model'],profile=case['configuration']['profile'],sector=sector_id))
    bundle=dict(result=result,training=training,future=future)
    path=tmp_path/'bundle.json';path.write_text(json.dumps(bundle));saved={}
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    context=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda key=None:case_path if key else path,
        save=lambda name,value:saved.update({name:value}))
    payload=dict(case_key=case_key,maximum_proposals=6)
    return dict(identity=identity,payload=payload),context,saved
