# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import inspect


def test_cached_recovery_cannot_call_a_cold_solver_or_point_oracle():
    from lll.ilvis0_native_prefix_recovery import recover
    signature=inspect.signature(recover)
    assert {'original','tangent','cold_kernels'}.isdisjoint(signature.parameters)
    assert {'original_reports','native_records','prefix_kernels'}<=set(signature.parameters)


def test_cached_recovery_checks_json_roundtrips_against_actual_native_values(kernels,tmp_path):
    import ctypes
    import json
    import numpy as np
    from native_prefix_reference import original
    from lll.ilvis0_native_prefix_controls import make_case
    from lll.ilvis0_native_prefix_recovery import recover
    from lll.ilvis0_shape import load_tangent
    from lll.studies.artifacts import encoded
    from lll.ilvis0_control_shards import TaskContext
    value=make_case(0,False,'conditioned',reserve=lambda **v:None)
    value['times']=[value['times'][0],value['times'][-1]];c=value['configuration']
    old=original()[0];reports=[];native=[];tangent=load_tangent(tmp_path)[0]
    for t in value['times']:
        reports.append(json.loads(encoded(old.enclose(c,value['theta'],value['dv'],value['dt'],time=t,
            lower=value['lower'],upper=value['upper'],reference=value['reference'],
            conditioning=value['conditioning'],maximum_seconds=30.,**kernels[1]).report())))
        position=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        status=tangent(len(value['dt']),np.ascontiguousarray(value['theta']),np.ascontiguousarray(value['dv']),
            np.ascontiguousarray(value['dt']),1,np.array([t]),c['initial_c'],c['initial_v'],c['initial_r'],
            c['limits'],np.ascontiguousarray(value['center']),c['model'],int(c['profile']),c['gravity'],c['radius'],
            position,jac,ctypes.byref(flag))
        native.append(dict(time_s=t,point=value['center'].tolist(),status=int(status),warning=flag.value,
            prediction=position[0].tolist(),jacobian=jac.tolist()))
    context=object.__new__(TaskContext);context.root=tmp_path;context.shard=0
    context.task={'identity':'cached-only'};context.manifest={'allocation':{'workers':1}}
    context.directory=tmp_path/'artifacts'/'cached-only';context.artifacts={};context.finished=False
    counts={};charges=[]
    def reserve(**v):
        for k,n in v.items():counts[k]=counts.get(k,0)+n
    out=recover(value,original_reports=reports,native_records=native,prefix_kernels=kernels[0],
        reserve=reserve,charge=lambda **v:charges.append(v),save=context.save,
        maximum_seconds=30.,maximum_packet_steps=48,maximum_rss_bytes=1536*1024**2)
    assert out['passed'] and out['report_comparisons']==2 and out['design_columns_checked']==51
    assert out['native_calls']==0 and out['original_cold_calls']==0
    assert charges==[dict(bound_calls=1,bound_steps=432)]
    assert (context.directory/'batched-00.json').exists() and (context.directory/'batched-01.json').exists()
    assert counts['packet_steps']<=48


from test_ilvis0_native_prefix import kernels  # noqa: E402,F401
