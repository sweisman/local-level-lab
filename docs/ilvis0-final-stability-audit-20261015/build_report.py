# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two saved-tangent systems, four affine solves, zero native calls or refits."""
import argparse
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data/ilvis0-final-stability-audit-20261015'
PARENT=ROOT/'docs/ilvis0-trust-trial-20261015'
PREFIX='fd7b81e48a4122b149c4925b::bias1_profiled_removal::sphere_still::'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path): return json.loads(path.read_text())


def render(summary):
    text='# Saved-tangent audit of the last matched-trial target\n\n'
    text+='Both the primary and repeat stopped before their evaluation caps. Their saved endpoints '
    text+='pass stationarity but fail fresh objective and axis-RMS position checks. This audit uses '
    text+='their preserved residuals and Jacobians only: **zero native predictions and zero archival fit starts**. '
    text+='An affine correction is a local numerical diagnostic; it cannot resolve the flight comparison.\n\n'
    text+='The zero correction is feasible and leaves the objective unchanged. A successful local solver '
    text+='must therefore be checked against that baseline. Column scaling changes numerical coordinates, '
    text+='with bounds transformed consistently; it does not change the affine problem.\n\n'
    text+='| Endpoint | Local solve | Success | Feasible | Signed affine objective change | Step norm |\n'
    text+='|---|---|---|---|---:|---:|\n'
    for row in summary['results']:
        for method in row['audit']['methods']:
            text+=f"| {row['role']} | {method['method']} | {method['success']} | {method['feasible']} | {method['affine_cost_change']:+.9g} | {method['normalized_step']:.6g} |\n"
    text+='\nFull singular spectra, diagnostic ranks, column norms and correction vectors are retained '
    text+='in the [audit data](diagnosis.json). Reported ranks are descriptive; no scientific rank cutoff changes. '
    text+='Predicted affine improvement needs a separately bounded full-model check before it can inform '
    text+='a revised stopping or step policy. The original unresolved labels and all earlier failures remain unchanged.\n'
    (HERE/'README.md').write_text(text)
    for name in ('manifest.json','diagnosis.json','completion.json'):
        shutil.copyfile(OUTPUT/name,HERE/name)
    shutil.copytree(OUTPUT/'source-freeze',HERE/'source-freeze',dirs_exist_ok=True)
    receipt=dict(artifacts={n:sha(HERE/n) for n in ('README.md','manifest.json','diagnosis.json','completion.json')},
                 observed_fit_starts=0,native_predictions=0)
    (HERE/'evidence-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.render_only or (OUTPUT/'completion.json').exists():
            complete=load(OUTPUT/'completion.json')
            if complete['diagnosis_sha256']!=sha(OUTPUT/'diagnosis.json'): raise ValueError('completed audit mismatch')
            render(load(OUTPUT/'diagnosis.json'));return
        if (OUTPUT/'start.json').exists(): raise ValueError('interrupted audit remains charged; no retry')
        sys.path.insert(0,str(ROOT/'analysis'))
        from lll.compute_budget import environment
        import os
        os.environ.update(environment(workers=1,threads=4,reserved=0))
        from lll import ilvis0_affine_audit as audit,runtime
        import numpy as np
        receipt=load(PARENT/'evidence-receipt.json')
        if any(sha(PARENT/n)!=h for n,h in receipt['artifacts'].items()): raise ValueError('parent publication mismatch')
        saved=load(PARENT/'summary.json')['results'];inputs={str(PARENT/n):sha(PARENT/n) for n in ('summary.json','manifest.json','completion.json','evidence-receipt.json')}
        for role in ('primary','repeat'):
            fit=saved[PREFIX+role];name=fit['linearization_file']
            if Path(name).name!=name or sha(PARENT/name)!=fit['linearization_sha256']: raise ValueError('saved tangent mismatch')
            inputs[str(PARENT/name)]=fit['linearization_sha256']
        sources={str(p):sha(p) for p in (Path(__file__).resolve(),Path(audit.__file__).resolve(),ROOT/'analysis/tests/test_ilvis0_affine_audit.py')}
        manifest=dict(version=audit.VERSION,inputs=inputs,sources=sources,environment=runtime.numerical_environment(),
                      systems=2,maximum_affine_solves=4,observed_fit_starts=0,native_predictions=0,retries=0,numerical_threads=4)
        (OUTPUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        freeze=OUTPUT/'source-freeze';freeze.mkdir()
        for p in sources: shutil.copyfile(p,freeze/Path(p).name)
        (OUTPUT/'start.json').write_text(json.dumps(dict(manifest_sha256=sha(OUTPUT/'manifest.json')))+'\n')
        results=[]
        for role in ('primary','repeat'):
            fit=saved[PREFIX+role];linear=json.loads(gzip.decompress((PARENT/fit['linearization_file']).read_bytes()))
            point=np.array(linear['normalized_parameters']);residual=np.array(linear['residual']);jac=np.array(linear['jacobian'])
            if not np.array_equal(point,np.array(fit['normalized_parameters'])): raise ValueError('saved endpoint mismatch')
            result=audit.assess(point,residual,jac)
            if abs(result['zero_step_cost']-fit['residual_sum_squares'])>1e-10*max(fit['residual_sum_squares'],1.):
                raise ValueError('saved residual objective mismatch')
            result['largest_correction_coordinates']={m['method']:[dict(parameter=linear['active_parameters'][i],step=m['step'][i])
                for i in sorted(range(len(point)),key=lambda i:abs(m['step'][i]),reverse=True)[:6]] for m in result['methods']}
            results.append(dict(role=role,identity=PREFIX+role,saved_stability_probe=fit['stability_probe'],audit=result))
        summary=dict(state='complete',results=results,observed_fit_starts=0,native_predictions=0,affine_solves=4,original_labels_changed=False)
        (OUTPUT/'diagnosis.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
        (OUTPUT/'completion.json').write_text(json.dumps(dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),diagnosis_sha256=sha(OUTPUT/'diagnosis.json')),indent=2)+'\n')
        render(summary)
        print(json.dumps([dict(role=r['role'],methods=[{k:m[k] for k in ('method','success','affine_cost_change','normalized_step')} for m in r['audit']['methods']]) for r in results]))


if __name__=='__main__': main()
