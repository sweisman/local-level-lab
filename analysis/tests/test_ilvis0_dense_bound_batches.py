# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from copy import deepcopy
from pathlib import Path
import pytest


def test_dense_batch_adapter_uses_the_actual_frozen_loader():
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_dense_bound_batches.py'
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate)
    assert module.recipe()['times_s']==list(map(float,range(2,291)))
    limits=module.auxiliary_limits()
    assert limits['force_profile_packets']==289*96000
    assert limits['packet_steps']==96000+289*512


def record():
    from lll.ilvis0_training_density import recipe
    count=len(recipe()['dense_s'])+1
    return dict(case_sha256='case',compiler='compiler',environment={'same':True},
        native_source_sha256='kernel',times_s=recipe()['dense_s']+[438.],point=[0.]*27,
        native=dict(status=0,counter=count,classification=dict(counter_verified=True,
            expected_counter=count,query_count=count,derivative_smoothness_qualified=False),
            prediction=[[0.,0.,0.] for _ in range(count)],
            jacobian=[[[0.]*27 for _ in range(3)] for _ in range(count)]))


def test_dense_batch_saved_native_selection_keeps_the_original_batch_metadata():
    from lll.ilvis0_dense_bound_batches import selected_native
    value=record();before=deepcopy(value)
    result=selected_native(value,case_sha256='case',compiler='compiler',environment={'same':True},native_source_sha256='kernel')
    assert value==before and len(result['prediction'])==289 and len(result['jacobian'])==289
    assert result['indices']==list(range(289)) and result['original_query_count']==293
    assert result['original_counter']==293 and result['subset_counter_reinterpreted'] is False


@pytest.mark.parametrize('change',['case','point','times','compiler','environment','kernel','counter','nonfinite','jacobian'])
def test_dense_batch_rejects_changed_saved_reference(change):
    from lll.ilvis0_dense_bound_batches import selected_native
    value=record()
    if change=='case':value['case_sha256']='other'
    elif change=='point':value['point'][0]=.1
    elif change=='times':value['times_s'][0]=1.
    elif change=='compiler':value['compiler']='other'
    elif change=='environment':value['environment']={}
    elif change=='kernel':value['native_source_sha256']='other'
    elif change=='counter':value['native']['classification']['expected_counter']=0
    elif change=='nonfinite':value['native']['prediction'][0][0]=float('nan')
    else:value['native']['jacobian'][0][0].pop()
    with pytest.raises(ValueError):selected_native(value,case_sha256='case',compiler='compiler',environment={'same':True},native_source_sha256='kernel')


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_real_small_batch_keeps_raw_stream_and_all_columns(tmp_path,monkeypatch,model,profile):
    import json
    import shutil
    import subprocess
    import numpy as np
    from lll import ilvis0_dense_bound_batches as module
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_native_prefix_controls import make_case
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import native_batch
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.studies.dependencies import source_closure
    from lll.studies.series import read_reports
    value=make_case(model,profile,'physical',reserve=lambda **v:None)
    c=value['configuration'];n=len(value['dt']);periods=np.full(n,.005)
    c={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in c.items()}
    case=dict(configuration=c,theta=value['theta'].tolist(),dv=value['dv'].tolist(),dt=periods.tolist())
    r=dict(module.recipe(),packets=n,times_s=[.01,.03,.05],clock_limit_s=c['limits'][25],maximum_batch_s=120.)
    monkeypatch.setattr(module,'recipe',lambda:r)
    conf={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in c.items()}
    kernel=load_tangent(tmp_path/'native')[0]
    native=native_batch(kernel,conf,value['theta'],value['dv'],periods,r['times_s'],lambda *v:None)
    selected={k:v.tolist() for k,v in native.items() if k in ('prediction','jacobian')}
    monkeypatch.setattr(module,'selected_native',lambda *a,**k:selected)
    monkeypatch.setattr(runner,'_check_continue',lambda *a:None)
    root=Path(__file__).resolve().parents[2];study=tmp_path/'study';source=study/'source-freeze'
    hashes={}
    for name in source_closure(root,['analysis/lll/ilvis0_dense_bound_batches.py',*module.NATIVE_SOURCES]):
        if Path(name).suffix not in ('.cpp','.h','.hpp'):continue
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
        hashes[name]=digest(target.read_bytes())
    atomic(study/'manifest.json',encoded({'test':'short real arithmetic'}))
    context=object.__new__(runner.TaskContext);context.root=study;context.shard=0;context.finished=False
    context.directory=study/'artifacts'/'test';context.directory.mkdir(parents=True);context.artifacts={}
    context.task={'identity':'test'};context.manifest=dict(sources=hashes,environment={},allocation={'workers':1})
    inputs=study/'inputs';inputs.mkdir();atomic(inputs/'case.json',encoded(case))
    atomic(inputs/'native.json',encoded(dict(coordinate_scale=[6371000.,6371000.*abs(np.cos(c['initial_c'][0])),1.])))
    context.input_path=lambda key=None:inputs/('case.json' if key is None else 'native.json')
    charges=[];context.charge=lambda **v:charges.append(v)
    task=dict(identity='test',payload=dict(recipe=r,auxiliary_limits=module.auxiliary_limits(),
        case_sha256=digest(encoded(case)),compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],
        model=model,profile=profile,native_key='native'))
    outcome=module.evaluate(task,context)
    binding=json.loads((context.directory/'series-binding.json').read_bytes())
    reports=read_reports(context.directory/'training-bounds.jsonl',binding=binding['binding'],
        maximum_records=3,maximum_record_bytes=r['maximum_record_bytes'])
    assert outcome['passed'] and outcome['training_epochs']==3 and outcome['expression_columns']==51
    assert [v['time_s'] for v in reports]==r['times_s']
    assert len(json.loads((context.directory/'columns.json').read_bytes())['design'])==9
    assert charges==[dict(bound_calls=1,bound_steps=9*module.auxiliary_limits()['packet_steps'])]
    assert 'artifacts/test/training-bounds.jsonl' in context.artifacts
