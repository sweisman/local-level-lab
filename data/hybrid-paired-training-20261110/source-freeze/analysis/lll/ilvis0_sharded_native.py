# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged adapter for strict one-thread compatibility with sealed native controls.

Module import is standard-library only; numerical imports occur inside a guarded
worker. The original native kernel and mathematical enclosure stay unchanged.
"""
import ctypes
import gzip
import json
import subprocess


def plain(value):
    import numpy as np
    if isinstance(value,np.ndarray):return plain(value.tolist())
    if isinstance(value,np.generic):return plain(value.item())
    if isinstance(value,dict):return {key:plain(item) for key,item in value.items()}
    if isinstance(value,(tuple,list)):return [plain(item) for item in value]
    return value


def compare_native(actual,expected):
    import numpy as np
    for key in ('point','prediction','jacobian'):
        left=np.asarray(actual[key],dtype='<f8');right=np.asarray(expected[key],dtype='<f8')
        if left.shape!=right.shape or left.tobytes()!=right.tobytes():
            raise ValueError('native '+key+' differs bitwise from four-thread reference')
    if actual['warning']!=expected['warning']:raise ValueError('native warning differs from reference')


def compare_bound(actual,expected):
    def encoded(value):return json.dumps(plain(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if encoded(actual)!=encoded(expected):raise ValueError('complete factored bound differs from four-thread reference')


def read(path):
    with (gzip.open(path,'rt') if str(path).endswith('.gz') else path.open()) as handle:return json.load(handle)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_shape import load_tangent
    from lll import ilvis0_acceleration_native as candidate
    from lll.ilvis0_acceleration_control_case import evaluate_case
    specification=task['payload'];case=read(context.input_path());reference_outputs=read(context.input_path(specification['reference_key']))
    for compiler,version in reference_outputs['compilers'].items():
        if subprocess.check_output([compiler,'--version'],text=True).splitlines()[0]!=version:
            raise ValueError('native compiler differs from qualified reference')
    config=case['configuration'];config={k:np.ascontiguousarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v for k,v in config.items()}
    theta=np.ascontiguousarray(case['theta']);dv=np.ascontiguousarray(case['dv']);dt=np.ascontiguousarray(case['dt']);n=len(dt)
    if n!=specification['packets'] or config['model']!=specification['model'] or config['profile']!=specification['profile']:
        raise ValueError('native input/candidate identity mismatch')
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(exist_ok=True)
    kernel,kernel_id=load_tangent(directory);calls=0;bounds=0
    def native(point):
        nonlocal calls
        context.charge(native_calls=1,packet_visits=n);calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));warning=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([case['time_s']]),config['initial_c'],config['initial_v'],config['initial_r'],config['limits'],
            np.ascontiguousarray(point),config['model'],int(config['profile']),config['gravity'],config['radius'],out,jac,ctypes.byref(warning))
        if code:raise ValueError('native query outside support')
        record=plain(dict(point=point,prediction=out[0],jacobian=jac,warning=warning.value))
        context.save(f'native-{calls:02d}.json',record)
        compare_native(record,reference_outputs['native'][calls-1])
        return out[0],jac
    def bound(point,left,right):
        nonlocal bounds
        context.charge(bound_calls=1,bound_steps=n);bounds+=1
        reference=candidate.make_reference(config,theta,dv,dt,lower=left,upper=right,center=point)
        report=candidate.enclose(config,theta,dv,dt,time=case['time_s'],lower=left,upper=right,reference=reference)
        record=plain(dict(report.report(),reference=reference.report(),previous_reference=reference.reference.report()))
        context.save(f'bound-{bounds:02d}.json',record)
        compare_bound(record,reference_outputs['bounds'][bounds-1])
        return report,reference
    result=evaluate_case(specification,case,native=native,bound=bound)
    if calls!=len(reference_outputs['native']) or bounds!=len(reference_outputs['bounds']):raise ValueError('reference operation coverage changed')
    return plain(dict(result,native_evaluations=calls,bound_evaluations=bounds,reserved_bound_steps=bounds*n,kernel=kernel_id,
        bitwise_native_compatible=True,canonical_bound_compatible=True,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain'))
