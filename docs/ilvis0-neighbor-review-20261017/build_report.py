# SPDX-License-Identifier: AGPL-3.0-or-later
"""One saved-pair comparison; publication never runs a native prediction."""
import argparse
import copy
import fcntl
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data'/HERE.name
FOLLOWUP=ROOT/'docs/ilvis0-boundary-followup-20261016'
PREVIOUS=ROOT/'docs/ilvis0-boundary-review-20261016'
SID='bb8061a43b4f14b6262ceda1'
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_boundary_publication as policy


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    from lll.ilvis0_receipt_journal import durable_write,encoded
    durable_write(path,encoded(value),replace=True)


def sealed(directory,artifact,key):
    c=load(directory/'completion.json')
    if c['state']!='complete' or c['manifest_sha256']!=sha(directory/'manifest.json') or c[key]!=sha(directory/artifact):
        raise ValueError('sealed source required')
    for name,h in load(directory/'evidence-receipt.json')['artifacts'].items():
        if Path(name).name!=name or sha(directory/name)!=h:raise ValueError('source publication mismatch')


def render():
    for name in ('manifest.json','review.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    r=load(HERE/'review.json');d=r['dispositions'][SID];p=r['pairs'][0]
    text='# Completed adjacent-boundary comparison\n\n'
    text+=f"**Shape result: {d['shape_preference']}.** All six primary fits passed: {d['all_primaries_passed']}. "
    text+=f"Both controls passed: {d['controls_passed']}. Required repeat agreement passed: {p['passed']}.\n\n"
    text+='The completed trial used 44 native calls; this review performed no additional fits or predictions. '
    text+='The same two-sided check now explicitly covers the reached neighboring timing boundary. '
    text+='Earlier stopping failures, measurements, physical bounds, clock and receiver weights are preserved.\n\n'
    text+='| Repeat check | Measured difference | Required limit |\n|---|---:|---:|\n'
    text+=f"| Relative cost | {p['relative_cost_difference']:.6g} | 10⁻⁶ |\n"
    for axis,value in zip(('North','East','Up'),p['track_rms_neu_m']):
        text+=f'| {axis} track RMS | {value:.6g} m | 0.01 m |\n'
    text+='\n| Processing case | Globe with field cost | Zero-field globe cost | Flat-disc cost |\n|---|---:|---:|---:|\n'
    for case in r['comparisons'][0]['cases']:
        costs={f['model']:f['residual_sum_squares'] for f in case['fits']}
        text+=f"| {case['case_id']} | {costs['sphere_rotating']:.6f} | {costs['sphere_still']:.6f} | {costs['flat_still']:.6f} |\n"
    text+='\nThese are numerical model preferences and repeatability checks, not calibrated significance '
    text+='or instrument-accuracy estimates. Background-field preference follows the shape comparison; '
    text+='the field’s cause and solar-versus-sidereal rate are not determined.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [Full stretch table](../ilvis0-current-findings-20261015/STRETCHES.md) · '
    text+='[Underlying trial](../ilvis0-boundary-followup-20261016/RESULTS.md).\n'
    (HERE/'README.md').write_text(text)
    names=['manifest.json','review.json','completion.json','README.md']
    names.extend(p.name for p in HERE.glob('evidence-*') if p.name!='evidence-receipt.json' and p.is_file())
    write(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in names},observed_starts=0,native_predictions=0))


def build():
    from lll.compute_budget import environment
    os.environ.update(environment(workers=1,threads=4,reserved=0))
    import numpy as np
    from types import SimpleNamespace
    from lll import ilvis0_gps_sensitivity as sensitivity,ilvis0_solver_position as position
    from lll import ilvis0_exploratory as explore,ilvis0_shape as shape,runtime
    sealed(FOLLOWUP,'summary.json','summary_sha256');sealed(PREVIOUS,'review.json','review_sha256')
    summary=load(FOLLOWUP/'summary.json');manifest=load(FOLLOWUP/'manifest.json')
    old=load(PREVIOUS/'review.json');old_manifest=load(PREVIOUS/'manifest.json')
    tasks={t['identity']:t for t in manifest['plan']['tasks']}
    if summary['state']!='complete' or len(tasks)!=4 or len(summary['results'])!=4 or summary['native_evaluations']!=44:
        raise ValueError('complete four-identity trial required')
    inputs={};native={};attempts=[];controls=[]
    def preserve(path):
        name='evidence-'+hashlib.sha256(str(path.relative_to(ROOT)).encode()).hexdigest()[:12]+'-'+path.name
        shutil.copyfile(path,HERE/name);inputs[str((HERE/name).relative_to(ROOT))]=sha(HERE/name)
    for directory,artifact in ((FOLLOWUP,'summary.json'),(PREVIOUS,'review.json')):
        for name in ('manifest.json',artifact,'completion.json','evidence-receipt.json'):preserve(directory/name)
    comparison=copy.deepcopy(next(r for r in old['comparisons'] if r['segment_id']==SID))
    fits={f'{SID}::{case["case_id"]}::{f["model"]}::primary':f for case in comparison['cases'] for f in case['fits']}
    target=f'{SID}::bias1_unsubtracted::sphere_still::primary'
    if len(fits)!=6 or any(not f['converged'] for k,f in fits.items() if k!=target):
        raise ValueError('five passing companions required')
    for key,fit in fits.items():
        if key==target:continue
        name,digest=fit['linearization_file'],fit['linearization_sha256']
        matches=[ROOT/n for n,h in old_manifest['inputs'].items() if Path(n).name.endswith(name) and h==digest]
        if not matches or any(sha(p)!=digest for p in matches):raise ValueError('verified companion artifact missing')
        preserve(sorted(matches)[0])
    for r in summary['results']:
        item=tasks[r['identity']];identity=r['source_identity'];reference=item['fit']
        path=FOLLOWUP/r['linearization_file']
        if sha(path)!=r['linearization_sha256']:raise ValueError('native artifact mismatch')
        preserve(path)
        with gzip.open(path,'rt') as stream:local=json.load(stream)
        if local['normalized_parameters']!=r['normalized_parameters'] or local['active_parameters']!=reference['active_parameters']:
            raise ValueError('saved parameter layout mismatch')
        cost=float(np.array(local['residual'])@np.array(local['residual']))
        if abs(cost-r['residual_sum_squares'])/max(cost,1.)>1e-12:raise ValueError('saved cost mismatch')
        if item['kind']=='neighbor' and (not r['checks'][-1]['passed'] or len(r['checks'])>3):
            raise ValueError('full final boundary check required')
        bounds=explore.ConditionalBounds(shape.instrument_limits(1.),fit_earth_removal='profiled_removal' in reference['case_id'])
        if list(bounds.active)!=reference['active_parameters']:raise ValueError('physical parameter order changed')
        fit=dict(model=reference['model'],case_id=reference['case_id'],role=reference['role'],
            converged=bool(r['passed'] and r['status']=='complete'),residual_sum_squares=cost,
            parameters=bounds.decode(r['normalized_parameters']),normalized_parameters=r['normalized_parameters'],
            active_parameters=reference['active_parameters'],active_bounds=[n for n,u in zip(bounds.active,r['normalized_parameters']) if abs(u)>=.999],
            message=r['reason'],evaluations=r['native_evaluations'],maximum_evaluations=item['maximum_evaluations'],
            numerical_check='checked_adjacent_boundary' if item['kind']=='neighbor' else 'unchanged_smooth_control',
            scientific_decision='abstain',scientific_eligible=False)
        fits[identity]=fit;native[identity]=local
        parts=identity.split('::')
        attempts.append(dict(identity=r['identity'],source_identity=identity,segment_id=parts[0],case_id=parts[1],model=parts[2],role=parts[3],
            passed=fit['converged'],status=r['status'],display_reason=r['reason'],fit=fit,
            operation='adjacent_boundary_continuation' if item['kind']=='neighbor' else 'saved_control_check'))
        if item['kind']=='control':controls.append(dict(identity=identity,passed=fit['converged']))
    repeat=target.rsplit('::',1)[0]+'::repeat';a,b=fits[target],fits[repeat];x,y=native[target],native[repeat]
    if x['times_s']!=y['times_s'] or x['gps']!=y['gps']:raise ValueError('common receiver epochs required')
    times=np.array(x['times_s']);gps=np.array(x['gps']);blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
    assumption=next(a for a in sensitivity.assumptions() if a.name=='h1_v3_tau60')
    covariance=sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)
    delta=position.physical_residual_step(SimpleNamespace(gps=gps,cholesky=np.linalg.cholesky(covariance)),
                                        np.array(y['residual'])-np.array(x['residual']))
    rms=np.sqrt(np.mean(delta**2,axis=0));relative=abs(a['residual_sum_squares']-b['residual_sum_squares'])/max(a['residual_sum_squares'],b['residual_sum_squares'],1.)
    pair=dict(identity=repeat,primary_passed=a['converged'],repeat_passed=b['converged'],relative_cost_difference=relative,track_rms_neu_m=rms.tolist(),
        passed=bool(a['converged'] and b['converged'] and relative<=policy.PAIR_COST_TOLERANCE and max(rms)<=policy.PAIR_TRACK_RMS_TOLERANCE_M))
    for case in comparison['cases']:
        case['fits']=[fits[f'{SID}::{case["case_id"]}::{m}::primary'] for m in sorted(policy.MODELS)]
    review=dict(version=policy.VERSION,target_segment_ids=[SID],comparisons=[comparison],controls=controls,pairs=[pair],required_repeat_identities=[repeat],
        attempts=attempts,observed_starts=0,native_predictions=0,original_files_read=0)
    review['dispositions']=policy.classify(review,{SID:'unresolved'})
    sources={str(Path(n).relative_to(ROOT)):h for n,h in manifest['sources'].items()}
    sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    sources[str(Path(policy.__file__).relative_to(ROOT))]=sha(Path(policy.__file__))
    for name,h in sources.items():
        if sha(ROOT/name)!=h:raise ValueError('frozen review source changed')
    write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,maximum_batches=1,maximum_saved_pair_comparisons=1,
        numerical_threads=4,environment=runtime.numerical_environment(),native_predictions=0,observed_starts=0))
    write(OUTPUT/'review.json',review)
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),review_sha256=sha(OUTPUT/'review.json')))
    render();print(json.dumps(dict(disposition=review['dispositions'][SID],pair=pair)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            c=load(OUTPUT/'completion.json')
            if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['review_sha256']!=sha(OUTPUT/'review.json'):raise ValueError('completed review changed')
            render();return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged review cannot restart')
        write(OUTPUT/'start.json',dict(maximum_batches=1,maximum_saved_pair_comparisons=1,native_predictions=0))
        build()


if __name__=='__main__':main()
