# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded saved-Jacobian diagnosis, never an observed fit or native prediction."""
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
PARENT=ROOT/'docs/ilvis0-final-pair-boundary-v2-20261018'
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded


def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):durable_write(p,encoded(v),replace=True)


def solve_local(point,residual,jac,*,time_index,edges,side):
    import numpy as np
    from scipy.optimize import lsq_linear
    from lll.ilvis0_solver_refinement import POLICY
    x,r,j=np.asarray(point,float),np.asarray(residual,float),np.asarray(jac,float)
    if (x.ndim!=1 or r.ndim!=1 or not len(x) or not len(r) or j.shape!=(len(r),len(x))
            or any(not np.all(np.isfinite(v)) for v in (x,r,j)) or np.any(abs(x)>1)
            or type(time_index) is not int or not 0<=time_index<len(x)
            or len(edges)!=2 or not np.all(np.isfinite(edges))
            or not -1<=edges[0]<x[time_index]<edges[1]<=1 or side not in ('left','right','fixed')):
        raise ValueError('finite compatible bounded branch problem required')
    lower=-1-x;upper=1-x;active=np.arange(len(x))
    if side=='fixed':active=np.delete(active,time_index)
    elif side=='left':lower[time_index]=edges[0]-x[time_index];upper[time_index]=0.
    else:lower[time_index]=0.;upper[time_index]=edges[1]-x[time_index]
    if not len(active):raise ValueError('at least one active affine parameter required')
    fitted=lsq_linear(j[:,active],-r,bounds=(lower[active],upper[active]),method='bvls',
        tol=POLICY['stability_probe_linear_tolerance'],max_iter=POLICY['stability_probe_linear_maximum_iterations'])
    correction=np.zeros(len(x));correction[active]=fitted.x
    predicted=r.astype(np.longdouble)+j.astype(np.longdouble)@correction.astype(np.longdouble)
    old=r.astype(np.longdouble);source=float(old@old);cost=float(predicted@predicted)
    return dict(success=bool(fitted.success),status=int(fitted.status),iterations=int(fitted.nit),
        optimality=float(fitted.optimality),correction=correction.tolist(),source_cost=source,predicted_cost=cost,
        predicted_relative_cost_change=abs(cost-source)/max(cost,source,1.),maximum_normalized_step=float(max(abs(correction))))


def spectrum(jac):
    import numpy as np
    j=np.asarray(jac,float)
    if j.ndim!=2 or not j.size or not np.all(np.isfinite(j)):raise ValueError('finite nonempty matrix required')
    singular=np.linalg.svd(j,compute_uv=False);threshold=max(j.shape)*np.finfo(float).eps*singular[0]
    rank=int(np.sum(singular>threshold))
    return dict(singular_values=singular.tolist(),numerical_rank=rank,columns=j.shape[1],rank_cutoff=float(threshold),
        largest_to_smallest=None if singular[-1]==0 else float(singular[0]/singular[-1]),
        rank_is_diagnostic_only=True)


def render():
    c=load(OUTPUT/'completion.json')
    if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
        raise ValueError('completed audit changed')
    summary=load(OUTPUT/'summary.json')
    text='# Saved linear-system comparison of the failed corrections\n\n'
    text+='Both completed targets pass their endpoint side-gradient checks and agree closely with each other, '
    text+='but fail the fresh right-side correction. This audit compares bounded affine solves at their saved '
    text+='center Jacobians. It makes **zero native predictions and zero archival fits**.\n\n'
    text+='| Source | Saved right step, max normalized | Replayed left / right / fixed-time step | Center Jacobian rank |\n|---|---:|---:|---:|\n'
    for r in summary['targets']:
        sizes=' / '.join(f"{r['solves'][s]['maximum_normalized_step']:.6g}" for s in ('left','right','fixed'))
        text+=f"| {r['source_role']} | {r['saved_right_maximum_step']:.6g} | {sizes} | {r['full_spectrum']['numerical_rank']}/{len(r['active_parameters'])} |\n"
    text+='\nThe full numerical report preserves every correction, predicted cost, solver status and singular value. '
    text+='Fixing time here removes only the timing column for an affine diagnostic; it does not qualify a free-time fit '
    text+='or justify accepting the original endpoint. Small singular directions and parameter bounds remain explicit.\n\n'
    text+='A center Jacobian is not the complete record of both side Jacobians used by the failed test. '
    text+='Comparing it with a saved side correction can expose a discrepancy, but cannot establish whether that '
    text+='discrepancy comes from the side tangent, the bounded linear solve or nonlinear propagation. '
    text+='The next native diagnostic should preserve those side arrays and corrected-point arrays directly, '
    text+='under its own finite allowance, before choosing a replacement numerical method.\n\n'
    text+='No stopping tolerance, model, physical bound or published disposition changes. Findings remain '
    text+='**51 globe / 0 flat / 2 unresolved**.\n\n[Finite plan](PLAN.md) · '
    text+='[Source results](../ilvis0-final-pair-boundary-v2-20261018/RESULTS.md) · [Next steps](../NEXT_STEPS.md).\n'
    (GUIDE/'README.md').write_text(text)
    for n in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/n,GUIDE/n)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in
        ('manifest.json','summary.json','completion.json','README.md')},native_calls=0,observed_starts=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from lll import runtime
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart; use --render-only')
        inputs={};receipt=load(PARENT/'evidence-receipt.json')
        def verify(path,h):
            if sha(path)!=h:raise ValueError('saved source changed')
            inputs[str(path.relative_to(ROOT))]=h
        verify(PARENT/'evidence-receipt.json',sha(PARENT/'evidence-receipt.json'))
        for n in ('manifest.json','summary.json','completion.json'):verify(PARENT/n,receipt['artifacts'][n])
        completion=load(PARENT/'completion.json')
        if completion['summary_sha256']!=sha(PARENT/'summary.json') or completion['manifest_sha256']!=sha(PARENT/'manifest.json'):
            raise ValueError('source completion changed')
        targets=[r for r in load(PARENT/'summary.json')['results'] if r['kind']=='target']
        if len(targets)!=2 or any(r['status']!='complete' or r['passed'] for r in targets):
            raise ValueError('exact two completed failed endpoints required')
        for row in targets:
            name=row['linearization_file']
            if Path(name).name!=name or receipt['artifacts'][name]!=row['linearization_sha256']:
                raise ValueError('unsealed saved center')
            verify(PARENT/name,row['linearization_sha256'])
        sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),GUIDE/'PLAN.md',
            ROOT/'analysis/tests/test_ilvis0_correction_audit.py',ROOT/'analysis/lll/ilvis0_solver_refinement.py')}
        write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,environment=runtime.numerical_environment(),
            maximum_batches=1,maximum_targets=2,maximum_affine_solves=6,maximum_svd=4,maximum_iterations_per_solve=100,
            numerical_threads=4,native_calls=0,observed_starts=0,original_reads=0))
        freeze=OUTPUT/'source-freeze';freeze.mkdir()
        for p in sources:
            destination=freeze/p;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,destination)
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        reports=[]
        for row in targets:
            with gzip.open(PARENT/row['linearization_file'],'rt') as stream:saved=json.load(stream)
            names=saved['active_parameters'];x=np.array(saved['normalized_parameters']);r=np.array(saved['residual']);j=np.array(saved['jacobian'])
            check=row['boundary_check'];index=names.index('time_offset');edges=check['neighbor_edges']
            if x.tolist()!=row['normalized_parameters'] or x[index]!=check['knot']:raise ValueError('saved knot layout changed')
            solves={side:solve_local(x,r,j,time_index=index,edges=edges,side=side) for side in ('left','right','fixed')}
            branches={b['side']:b for b in check['branches']};delta=np.array(branches['right']['correction'])
            predicted=r.astype(np.longdouble)+j.astype(np.longdouble)@delta.astype(np.longdouble)
            report=dict(identity=row['identity'],source_role=row['source_role'],active_parameters=names,solves=solves,
                full_spectrum=spectrum(j),non_timing_spectrum=spectrum(np.delete(j,index,axis=1)),
                saved_right_maximum_step=float(max(abs(delta))),saved_right_fresh_stationarity=branches['right']['fresh_stationarity'],
                saved_right_native_relative_cost_change=branches['right']['relative_cost_change'],
                saved_right_center_tangent_cost=float(predicted@predicted),
                right_replay_step_difference_norm=float(np.linalg.norm(delta-np.array(solves['right']['correction']))),
                original_failed_gate_preserved=True)
            reports.append(report)
        for p,h in {**inputs,**sources}.items():
            if sha(ROOT/p)!=h:raise ValueError('audit dependency changed')
        write(OUTPUT/'summary.json',dict(state='complete',targets=reports,affine_solves=6,singular_decompositions=4,
            native_calls=0,observed_starts=0,original_reads=0,labels_changed=False))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(dict(state='complete',affine_solves=6,singular_decompositions=4,native_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
