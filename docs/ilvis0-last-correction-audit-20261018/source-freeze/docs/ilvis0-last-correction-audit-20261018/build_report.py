# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only final-stretch correction diagnosis; no native calls or refits."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
GUIDE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data'/GUIDE.name
PARENT=ROOT/'docs/ilvis0-last-free-time-20261018'
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):durable_write(path,encoded(value),replace=True)


def solve(point,residual,jac,*,time_index,method):
    import numpy as np
    from scipy.optimize import lsq_linear
    from lll.ilvis0_affine_audit import step_metrics
    from lll.ilvis0_scaled_branch import scaled_lsq
    x,r,j=map(lambda v:np.asarray(v,float),(point,residual,jac))
    if (x.ndim!=1 or not len(x) or r.ndim!=1 or not len(r) or j.shape!=(len(r),len(x))
            or any(not np.all(np.isfinite(v)) for v in (x,r,j)) or np.any(abs(x)>1)
            or type(time_index) is not int or not 0<=time_index<len(x)
            or method not in ('original','scaled','fixed_time')):
        raise ValueError('finite compatible bounded local problem required')
    active=np.arange(len(x))
    if method=='fixed_time':active=np.delete(active,time_index)
    if not len(active):raise ValueError('nonempty free affine parameter set required')
    solver=scaled_lsq if method=='scaled' else lsq_linear
    fitted=solver(j[:,active],-r,bounds=((-1-x)[active],(1-x)[active]),method='bvls',tol=1e-10,max_iter=100)
    step=np.zeros(len(x));step[active]=fitted.x
    return dict(method=method,success=bool(fitted.success),iterations=int(fitted.nit),
        optimality=float(fitted.optimality),**step_metrics(x,r,j,step))


def spectrum(jac):
    import numpy as np
    j=np.asarray(jac,float)
    if j.ndim!=2 or not j.size or not np.all(np.isfinite(j)):raise ValueError('finite nonempty matrix required')
    singular=np.linalg.svd(j,compute_uv=False)
    cutoff=max(j.shape)*np.finfo(float).eps*singular[0]
    return dict(singular_values=singular.tolist(),rank=int(np.sum(singular>cutoff)),columns=j.shape[1],
        cutoff=float(cutoff),condition_number=float(singular[0]/singular[-1]) if singular[-1] else None,diagnostic_only=True)


def history(row):
    steps=row['step_history']
    return dict(accepted=sum(bool(s['accepted']) for s in steps),rejected=sum(not s['accepted'] for s in steps),
        smallest_trial=min(steps,key=lambda s:s['normalized_step']) if steps else None,
        first_full_trial=next((s for s in steps if s.get('method')=='full_bounded'),None),
        budget_exhausted=row['evaluations']>=row['maximum_evaluations'],message=row['message'])


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed audit changed')
    s=load(OUTPUT/'summary.json')
    text='# Why the last free-timing fits failed\n\n'
    text+='The full trial passed both controls but failed all four target checks. '
    text+='Repeated target solutions agree closely; that alone does not establish local stability. '
    text+='This audit uses saved Jacobians, fit histories and receiver timing only: '
    text+='**zero native predictions, zero observed fits and zero original-recording reads**.\n\n'
    text+='| Processing case / start | Accepted / rejected steps | Full timing correction | Nearest clock transition | Full / fixed-time affine change |\n'
    text+='|---|---:|---:|---:|---:|\n'
    for r in s['targets']:
        h=r['history'];a=r['solves'];g=r['clock_geometry']
        text+=f"| {r['case_id']} / {r['start_role']} | {h['accepted']} / {h['rejected']} | {a['original']['time_step_s']:+.6g} s | {g['center_relocation_s']:+.6g} s | {a['original']['affine_cost_change']:+.6g} / {a['fixed_time']['affine_cost_change']:+.6g} |\n"
    text+='\nSigned affine changes compare each local correction with the feasible zero step. '
    text+='A negative value predicts a decrease in the linear approximation; it is not a fresh '
    text+='full-model result. The report retains the corrections, spectra, packet-state changes '
    text+='and the preceding native trial\'s actual increases. Fixing timing is diagnostic only.\n\n'
    text+='No fit label, physical bound or stopping limit changes. Findings remain '
    text+='**52 globe / 0 flat / 1 unresolved**.\n\n[Finite plan](PLAN.md) · '
    text+='[Full trial](../ilvis0-last-free-time-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).\n'
    (GUIDE/'README.md').write_text(text)
    names=['manifest.json','summary.json','completion.json']
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    names+=['README.md','PLAN.md']
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names},
        native_calls=0,observed_starts=0,original_reads=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from types import SimpleNamespace
    from lll import runtime,ilvis0_clock_brackets as clock
    from lll import ilvis0_solver_position as position
    from lll.ilvis0_solver_refinement import projected_stationarity
    sys.path.insert(0,str(ROOT/'analysis/tests'))
    import ilvis0_last_free_time_worker as worker
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart; use --render-only')
        executor=worker.build_executor();executor.prior.sealed(worker.OUTPUT,published=PARENT)
        m=load(PARENT/'manifest.json');summary=load(PARENT/'summary.json')
        runtime.check_environment(m['environment'])
        tasks={t['identity']:t for t in m['plan']['tasks']}
        rows=[r for r in summary['results'] if r['kind']=='target']
        executor.case_groups(rows)
        if (summary['state']!='complete' or len(summary['results'])!=6 or len(rows)!=4
                or any(r['status']!='complete' or r['converged'] for r in rows)
                or not all(r['converged'] for r in summary['results'] if r['kind']=='control')):
            raise ValueError('exact completed failed trial with passing controls required')
        inputs={str(PARENT/n):sha(PARENT/n) for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json')}
        for row in rows:
            name=row['linearization_file']
            if Path(name).name!=name or sha(PARENT/name)!=row['linearization_sha256']:raise ValueError('saved tangent changed')
            inputs[str(PARENT/name)]=row['linearization_sha256']
        sources=dict(m['sources'])
        for p in (Path(__file__).resolve(),GUIDE/'PLAN.md',ROOT/'analysis/tests/test_ilvis0_last_correction_audit.py',
                  ROOT/'analysis/lll/ilvis0_affine_audit.py',ROOT/'analysis/lll/ilvis0_scaled_branch.py',
                  ROOT/'analysis/lll/ilvis0_clock_brackets.py'):
            sources[str(p)]=sha(p)
        executor.prior.check_hashes(sources)
        write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,environment=m['environment'],
            maximum_batches=1,maximum_targets=4,maximum_affine_solves=12,maximum_svd=8,
            maximum_clock_queries=4120,numerical_threads=4,retries=0,native_calls=0,observed_starts=0,original_reads=0))
        executor.prior.snapshot(OUTPUT,sources)
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        reports=[];queries=0
        base=executor.prior.engine().base
        assumption=next(a for a in base.sensitivity.assumptions() if a.name=='h1_v3_tau60')
        for row in rows:
            with gzip.open(PARENT/row['linearization_file'],'rt') as stream:a=json.load(stream)
            names=a['active_parameters'];x=np.array(a['normalized_parameters']);r=np.array(a['residual']);j=np.array(a['jacobian'])
            task=tasks[row['identity']];ti=names.index('time_offset');scale=task['time_scale_s']
            if (a['normalized_parameters']!=row['normalized_parameters'] or names!=row['active_parameters']
                    or abs(float(r@r)-row['residual_sum_squares'])>1e-10*max(float(r@r),1.)):
                raise ValueError('saved endpoint layout or objective changed')
            count=task['task']['provenance']['native_packets'];times=np.array(a['times_s']);gps=np.array(a['gps'])
            geometry=clock.bracket(times,count,scale,x[ti],maximum_queries=1024);queries+=geometry['queries']
            ends=np.cumsum(np.full(count,.005));state=clock.indices(ends,times,scale,x[ti]);queries+=1
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
            conversion=SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(covariance))
            solves={}
            for method in ('original','scaled','fixed_time'):
                report=solve(x,r,j,time_index=ti,method=method);step=np.array(report['step'])
                delta=position.physical_residual_step(conversion,j@step)
                new_state=clock.indices(ends,times,scale,float(np.clip(x[ti]+step[ti],-1.,1.)));queries+=1
                report.update(time_step_s=float(step[ti]*scale),changed_receiver_packet_states=int(np.sum(new_state!=state)),
                    crossed_packet_boundaries=int(np.sum(abs(new_state-state))),
                    predicted_position_rms_neu_m=np.sqrt(np.mean(delta**2,axis=0)).tolist(),
                    largest_coordinates=[dict(parameter=names[i],normalized_step=float(step[i]))
                        for i in np.argsort(abs(step))[-6:][::-1]])
                solves[method]=report
            old_norm=row['full_stability']['normalized_parameter_step']
            if abs(solves['original']['normalized_step']-old_norm)>1e-10:raise ValueError('saved native correction not reproduced')
            reports.append(dict(identity=row['identity'],case_id=task['task']['case_id'],start_role=row['start_role'],
                normalized_parameters=x.tolist(),active_parameters=names,source_cost=float(r@r),
                stationarity=float(projected_stationarity(x,r,j)[0]),history=history(row),solves=solves,
                clock_geometry=geometry,full_spectrum=spectrum(j),non_timing_spectrum=spectrum(np.delete(j,ti,axis=1)),
                saved_native_stability=row['full_stability'],original_failed_gate_preserved=True))
        if queries>4120:raise ValueError('clock query allowance exceeded')
        executor.prior.check_hashes({**inputs,**sources})
        write(OUTPUT/'summary.json',dict(state='complete',targets=reports,affine_solves=12,singular_decompositions=8,
            clock_queries=queries,native_calls=0,observed_starts=0,original_reads=0,labels_changed=False))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(dict(state='complete',affine_solves=12,singular_decompositions=8,clock_queries=queries,native_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
