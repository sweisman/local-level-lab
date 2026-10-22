# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-Jacobian diagnostic; no native integration or aircraft fitting."""
import argparse
from fractions import Fraction as F
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
DATA=ROOT/'data/ilvis0-linear-leverage-20261021'
PARENT=ROOT/'data/ilvis0-long-staged-feasibility-v2-20261021'
PUBLIC=ROOT/'docs/ilvis0-linear-leverage'
SOURCE='docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'
PLAN='docs/ilvis0-linear-leverage/PLAN.md'


def probe(design,objective,sign,allowance,reserve):
    """Produce a feasible inner witness, not an asserted exact LP optimum."""
    import numpy as np
    import warnings
    from scipy.optimize import linprog,OptimizeWarning
    a=np.asarray(design,float);c=np.asarray(objective,float)
    if (a.ndim!=2 or c.ndim!=1 or not 1<=len(c)<=27 or a.shape[1]!=len(c) or not len(a)
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(c)) or sign not in (-1,1)
            or not math.isfinite(allowance) or allowance<=0):
        raise ValueError('finite complete affine design and positive allowance required')
    reserve()
    # SciPy forwards this HiGHS option; retain its explicit one-thread cap.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',message="Unrecognized options detected:.*'threads': 1",category=OptimizeWarning)
        result=linprog(-sign*c,A_ub=np.r_[a,-a],b_ub=np.full(2*len(a),allowance),
            bounds=[(-1.,1.)]*len(c),method='highs',options=dict(time_limit=5.,threads=1))
    if not result.success or result.x is None:
        raise ValueError('finite affine proposal failed: '+str(result.message))
    point=list(map(F,map(float,result.x)));rows=[list(map(F,row)) for row in a.tolist()]
    # Verify the primal witness exactly. A single common contraction repairs
    # any represented feasibility error; it never enlarges the training set.
    contraction=max([F(1),*map(abs,point),*(abs(sum((v*x for v,x in zip(row,point,strict=True)),F(0)))/F(allowance) for row in rows)])
    point=[v/contraction for v in point]
    change=[sum((v*x for v,x in zip(row,point,strict=True)),F(0)) for row in rows]
    if any(abs(x)>1 for x in point) or any(abs(v)>F(allowance) for v in change):
        raise ValueError('exact affine witness is not feasible')
    future=sum((F(float(v))*x for v,x in zip(c,point,strict=True)),F(0))
    return dict(feasible=True,point=list(map(str,point)),training_change_m=list(map(str,change)),
        future_change_m=str(future),proposal_status=int(result.status),contraction=str(contraction),
        exact_optimum_claimed=False)


def evaluate(task,context):
    from lll.ilvis0_control_shards import _check_continue
    spec=task['payload'];case=runner._load(context.input_path());calls=0;axes=[]
    if spec['maximum_proposals']!=6 or len(case['training'])!=15 or any(len(r)!=27 for r in case['training']):
        raise ValueError('fixed five-epoch full-physical diagnostic required')
    def reserve():
        nonlocal calls
        _check_continue(context.root,context.manifest)
        if calls>=6:raise ValueError('six proposal allowance exhausted')
        calls+=1;context.save(f'proposal-reservation-{calls:02d}.json',dict(proposals=calls,maximum=6))
    for axis,row in enumerate(case['future']):
        if len(row)!=27:raise ValueError('all physical future columns required')
        negative=probe(case['training'],row,-1,1.,reserve)
        positive=probe(case['training'],row,1,1.,reserve)
        width=F(positive['future_change_m'])-F(negative['future_change_m'])
        if width<0:raise ValueError('affine witness order reversed')
        record=dict(axis=axis,negative=negative,positive=positive,feasible_spread_m=str(width),
            exceeds_target=width>F(case['targets'][axis]))
        axes.append(record);context.save(f'axis-{axis}.json',record)
    return dict(identity=task['identity'],passed=calls==6,model=0,profile=spec['profile'],
        proposals=calls,physical_parameter_count=27,training_epochs=5,training_allowance_m=1.,
        affine_feasible_spread_m=[float(F(a['feasible_spread_m'])) for a in axes],
        exceeds_target=[a['exceeds_target'] for a in axes],targets_m=case['targets'],
        original_reads=0,native_evaluations=0,optimizer_starts=0,
        approximation_and_shared_errors_omitted=True,nonlinear_feasibility_established=False,
        exact_optima_claimed=False,observational_coverage_qualified=False,scientific_decision='abstain')


def prepare():
    from lll.ilvis0_training_remainder_audit import scaled_design
    if DATA.exists():raise ValueError('linear leverage diagnostic already frozen')
    manifest=runner.verify(PARENT);inputs={};tasks=[]
    for task in manifest['tasks'][:2]:
        runner._validate_own_results(PARENT,manifest,task['shard'])
        identity=task['identity'];envelope=runner._load(PARENT/'shards'/f"{task['shard']:03d}"/'results'/(identity+'.json'))
        records={};hashes={}
        for name in ('stage-02-region.json','future-bound.json','native-11.json'):
            path=PARENT/'artifacts'/identity/name;relative=str(path.relative_to(PARENT));digest=runner._sha(path)
            if envelope['artifacts'][relative]!=digest:raise ValueError('sealed diagnostic input changed')
            records[name]=runner._load(path);hashes[relative]=digest
        region=records['stage-02-region.json'];native=records['native-11.json']
        if region['times_s']!=[2.,10.,30.,180.,290.] or native['time_s']!=438. or native['point']!=[0.]*27:
            raise ValueError('fixed first pair, five training epochs and unchanged expansion required')
        rows=scaled_design(native['jacobian'],records['future-bound.json'],task['payload']['coordinate_scale'])
        case=dict(training=[r[:27] for r in region['design']],future=[r[:27] for r in rows],
            targets=[20.,20.,50.],source_sha256=hashes,scope='optimistic affine geometry diagnostic')
        p=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(p,case);key=identity;inputs[key]=str(p.relative_to(ROOT))
        tasks.append(dict(identity='linear-leverage-'+str(int(task['payload']['profile'])),input_key=key,
            payload=dict(profile=task['payload']['profile'],maximum_proposals=6),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    sources={SOURCE,PLAN,'analysis/tests/test_ilvis0_linear_leverage.py'}
    sources.update(name for name in manifest['sources'] if name.startswith('analysis/lll/'))
    sources.update(('analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=SOURCE,
        workers=1,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    from lll import ilvis0_control_publication as publication
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[]
    if runner._sha(Path(__file__))!=manifest['sources'][SOURCE]:raise ValueError('saved audit source changed')
    for item in summary['results']:
        row=runner._load(DATA/item['artifact'])['result'];rows.append(row)
    lines=['# Does five-epoch training constrain the linear prediction?','',
        'This saved-data diagnostic isolates training leverage from the large nonlinear '
        'approximation bounds. It uses all 27 physical derivative columns at the original '
        'expansion, with ±1 m training changes at five epochs. It omits shared and nonlinear '
        'errors. It is not a replacement prediction interval or an aircraft result.','',
        '| Processing | Feasible north spread | East spread | Height spread |',
        '|---|---:|---:|---:|']
    for row in rows:
        if row.get('passed'):
            if row['proposals']!=6 or row['physical_parameter_count']!=27:raise ValueError('incomplete affine diagnostic')
            lines.append('| '+('Profiled removal' if row['profile'] else 'Zero removal')+' | '+
                ' | '.join(f'{v:,.3f} m' for v in row['affine_feasible_spread_m'])+' |')
        else:lines.append('| Failed diagnostic | Unavailable | Unavailable | Unavailable |')
    lines+=['','The spreads come from two exactly verified feasible points per axis, not an '
        'assertion that the LP found an exact optimum. Each point stays inside the original '
        'physical box and the affine training-change limits. Nonlinear feasibility is not '
        'established; a large affine spread is a geometry warning, not proof that the full '
        'prediction target is impossible. A small spread would not bound the entire family.','',
        'No new integration, aircraft fitting or active-shard merge is performed. '
        'The running study, its targets and all earlier outcomes remain unchanged.','',
        '[Fixed diagnostic scope](PLAN.md) · [Long-record first pair](../ilvis0-long-staged-feasibility-v2/FIRST_PAIR.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(lines),plan=PLAN)


def main():
    p=argparse.ArgumentParser(description=__doc__);group=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only'):group.add_argument('--'+name,action='store_true')
    p.add_argument('--reserved-threads',type=int);args=p.parse_args()
    if args.prepare:prepare();print('Frozen two saved-geometry diagnostics / 12 LP proposals / zero native calls.')
    elif args.run:
        if args.reserved_threads is None:p.error('explicit reserved allocation required')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print(result['state'])
    else:publish();print('Rendered saved affine-leverage diagnosis; no proposals.')


if __name__=='__main__':main()
