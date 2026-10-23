# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from pathlib import Path
import pytest


def test_saved_cold_source_reuse_requires_all_numerical_dependencies(tmp_path):
    from lll.ilvis0_native_prefix_long import compatible_sources
    from lll.studies.artifacts import digest
    old=b"import math\nA=1\ndef enclose(x):\n return x+A\n"
    new=b"import math\nA=1\ndef enclose(x):\n from .ilvis0_native_prefix import _cold_enclose\n return _cold_enclose(x)\n"
    numeric='analysis/lll/physics.py';orchestration='analysis/lll/ilvis0_remainder_native.py'
    archive='analysis/lll/studies/artifacts.py'
    previous={numeric:digest(b'unchanged'),orchestration:digest(old),archive:digest(b'old storage')}
    current={numeric:digest(b'unchanged'),orchestration:digest(new),archive:digest(b'new storage')}
    result=compatible_sources(previous,current,old,new)
    assert result['original_cold_sha256']==digest(old)
    assert result['unchanged_numerical_dependencies']==[numeric]
    assert result['storage_only_changes']==[archive]
    for mutation in ({**current,numeric:digest(b'changed')},{k:v for k,v in current.items() if k!=numeric}):
        with pytest.raises(ValueError,match='numerical dependency'):
            compatible_sources(previous,mutation,old,new)
    changed=new.replace(b'A=1',b'A=2')
    with pytest.raises(ValueError,match='helpers'):
        compatible_sources(previous,{**current,orchestration:digest(changed)},old,changed)
    with pytest.raises(ValueError,match='source hash'):
        compatible_sources(previous,current,old+b' ',new)


def test_long_comparison_retains_deep_queries_and_finite_limits():
    from lll.ilvis0_native_prefix_long import recipe,limits
    r=recipe();a=limits()
    assert r['times_s']==[290.,438.] and r['packets']==96000
    assert r['identities']==6 and r['workers']==4 and r['threads']==1
    assert r['oracle_arithmetic_allowance_m']==1e-5
    assert a['packet_steps']==192000 and a['force_profile_packets']==192000
    assert a['reused_cold_reports']==1 and a['cold_bound_queries']==1
    assert r['maximum_cold_seconds']==7200. and r['maximum_batch_seconds']==14400.
    assert r['maximum_wall_s']==86400. and r['maximum_rss_bytes']==1536*1024**2


def test_long_adapter_freezes_the_cpp_sources_named_by_python():
    from lll.studies.dependencies import source_closure
    root=Path(__file__).resolve().parents[2]
    sources=source_closure(root,['analysis/lll/ilvis0_native_prefix_long.py',
        'analysis/lll/ilvis0_source_prefix_reference.cpp','analysis/lll/ilvis0_source_prefix_intervals.cpp'])
    for name in ('ilvis0_batched_bounds.cpp','ilvis0_compiled_bounds.cpp','ilvis0_tangent.cpp',
                 'ilvis0_source_stream.cpp','ilvis0_source_derivative_intervals.cpp','ilvis0_source_point_derivatives.cpp'):
        assert 'analysis/lll/'+name in sources


def test_saved_reference_checks_domain_clock_proof_and_complete_columns():
    from lll.ilvis0_native_prefix_long import validate_saved
    reference=dict(binding='ref',parent=dict(source_id='source',center=[0.]*27))
    proof=dict(input_binding='proof',source_id='source',region_binding='region')
    report=dict(time_s=438.,reference_binding='ref',source_id='source',lower=[-1.]*27,
        upper=[1.]*27,conditioning=proof,center=[0.]*3,normalized_center=[0.]*27,
        previous_coefficients=[[0.]*6]*3,acceleration_coefficients=[[0.]*9]*3,
        transform_coefficients=[[0.]*9]*3)
    value=dict(lower=[-1.]*27,upper=[1.]*27,center=[0.]*27,reference_report=reference,proof_report=proof)
    assert validate_saved(value,report,time=438.) is None
    for key,altered in [('time_s',290.),('source_id','other'),('lower',[-2.]*27),
                        ('conditioning',{**proof,'input_binding':'different'})]:
        bad=deepcopy(report);bad[key]=altered
        with pytest.raises(ValueError,match='saved cold'):
            validate_saved(value,bad,time=438.)


@pytest.mark.parametrize('reuse_early,corrupt_early',[(False,False),(True,False),(True,True)])
def test_complete_comparison_reuses_only_final_report_and_checks_actual_batch(kernels,tmp_path,reuse_early,corrupt_early):
    import json
    import numpy as np
    from lll.studies.artifacts import encoded
    from native_prefix_reference import original
    from lll.ilvis0_native_prefix_controls import make_case
    from lll.ilvis0_native_prefix_long import compare
    from lll.ilvis0_shape import load_tangent
    original_module=original()[0]
    value=make_case(0,False,'conditioned',reserve=lambda **v:None)
    value['times']=[value['times'][0],value['times'][-1]]
    old=json.loads(encoded(original_module.enclose(value['configuration'],value['theta'],value['dv'],value['dt'],
        time=value['times'][-1],lower=value['lower'],upper=value['upper'],reference=value['reference'],
        conditioning=value['conditioning'],maximum_seconds=30.,**kernels[1]).report()))
    early=None
    if reuse_early:
        early=json.loads(encoded(original_module.enclose(value['configuration'],value['theta'],value['dv'],value['dt'],
            time=value['times'][0],lower=value['lower'],upper=value['upper'],reference=value['reference'],
            conditioning=value['conditioning'],maximum_seconds=30.,**kernels[1]).report()))
    if corrupt_early:early['unshared_remainder'][0]+=1.
    value['reference_report']=value['reference'].report();value['proof_report']=value['conditioning'].report()
    saved={};charges=[];counts={}
    # Use the actual immutable artifact writer. A dict.update surrogate would
    # conceal the repeated-filename failure discovered before the long batch.
    from lll.ilvis0_control_shards import TaskContext
    context=object.__new__(TaskContext)
    context.root=tmp_path;context.shard=0;context.task={'identity':'check'}
    context.manifest={'allocation':{'workers':1}}
    context.directory=tmp_path/'artifacts'/'check';context.artifacts={};context.finished=False
    def save(name,value):
        context.save(name,value);saved[name]=json.loads((context.directory/name).read_bytes())
    def reserve(**v):
        for k,n in v.items():counts[k]=counts.get(k,0)+n
    tangent=load_tangent(tmp_path)[0]
    def run():
        return compare(value,old,original=original_module,prefix_kernels=kernels[0],cold_kernels=kernels[1],
            tangent=tangent,reserve=reserve,charge=lambda **v:charges.append(v),
            save=save,maximum_cold_seconds=30.,maximum_batch_seconds=30.,
            maximum_packet_steps=48,maximum_rss_bytes=1536*1024**2,saved_early_report=early)
    if corrupt_early:
        with pytest.raises(ValueError,match='complete long report differs'):run()
        assert {'batched-00.json','batched-01.json','batch-work.json'}<=set(saved)
        assert saved['batched-01.json']==old
        return
    result=run()
    assert result['passed'] and result['complete_reports_equal']==2
    assert counts.get('cold_bound_queries',0)==int(not reuse_early)
    assert counts['reused_cold_reports']==1+int(reuse_early)
    assert counts['design_comparisons']==2 and result['design_columns_checked']==51
    assert sum(v.get('bound_calls',0) for v in charges)==2-int(reuse_early)
    assert sum(v.get('native_calls',0) for v in charges)==2
    assert result['long_history_qualified'] is False  # small software invocation only
    assert result['work']['prefix_packet_steps']+result['work']['tail_packet_steps']<=48
    assert saved['batched-01.json']==old
    assert result['maximum_native_center_error_m']<1e-5


from test_ilvis0_native_prefix import kernels  # noqa: E402,F401
