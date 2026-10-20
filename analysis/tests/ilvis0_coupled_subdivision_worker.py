# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a complete closed-box subdivision comparison."""
import argparse
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_physical_partition import split,audit
from lll.ilvis0_sharded_native import read
from lll.ilvis0_saved_prediction_audit import endpoint

DATA=ROOT/'data/ilvis0-coupled-subdivision-20261020';PUBLIC=ROOT/'docs/ilvis0-coupled-subdivision'
OLD=ROOT/'docs/ilvis0-coupled-prediction';PROJECTED=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_coupled_subdivision.py';PLAN='docs/ilvis0-coupled-subdivision/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_physical_partition.py',
    'analysis/tests/ilvis0_coupled_subdivision_worker.py','analysis/tests/test_ilvis0_coupled_subdivision.py',
    'analysis/tests/test_ilvis0_physical_partition.py','analysis/tests/saved_prediction_fixtures.py',
    'analysis/tests/test_ilvis0_transform_audit.py','analysis/tests/test_ilvis0_coupled_export_audit.py',
    'analysis/tests/test_ilvis0_coupled_prediction.py','analysis/tests/test_ilvis0_product_prediction.py',
    'analysis/tests/test_ilvis0_rotation_products.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('physical subdivision comparison already frozen')
    for directory in (OLD,PROJECTED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('parent correctness failed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');sources=set(SOURCES)
    if previous['environment']!=runner.runtime_environment():raise ValueError('qualified environment changed')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};parents=[]
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):inputs[key]=str((OLD/record['path']).relative_to(ROOT))
    limits=dict(partition_audits=1,setups=1,intervals=2,coupling_audits=1,
        contractions=1,proposals=6,supports=24,truth_audits=1)
    for task in previous['tasks']:
        identity=task['identity'];item=next(r for r in summary['results'] if r['identity']==identity)
        old=runner._load(OLD/item['artifact'])['result']
        if not old['passed'] or old['excluded']:raise ValueError('all 48 retained parents required')
        future=runner._load(OLD/'artifacts'/identity/'future.json')
        partition=split(future['lower'][:27],future['upper'][:27],axes=(0,1))
        audited=audit(partition,future['lower'][:27],future['upper'][:27],axes=(0,1))
        previous_input=read(OLD/previous['inputs'][identity]['path'])
        bundle=dict(result=old,future=future,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            product_cuts=previous_input['product_cuts'],partition=partition)
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        parents.append(dict(identity=identity,model=old['task']['model'],profile=old['task']['profile'],
            sector=old['task']['sector'],children=audited['children']))
        for child in partition['children']:
            tasks.append(dict(identity=identity+f"-xy-{child['index']}",input_key=identity,
                payload=dict(parent_identity=identity,case_key=task['payload']['case_key'],child_index=child['index'],
                    parent_children=audited['children'],limits=limits),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(parents)!=48 or not 48<=len(tasks)<=192:raise ValueError('complete finite parent/child cover required')
    definition=PUBLIC/'cover.json';runner._write(definition,dict(parents=parents,identities=len(tasks),maximum_identities=192,
        axes=[0,1],known_truth_used=False))
    inputs['cover']=str(definition.relative_to(ROOT));inputs['baseline']=str((PROJECTED/'case-unions.json').relative_to(ROOT))
    inputs['previous-comparison']=str((OLD/'comparison.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=960,environment=runner.runtime_environment())


def accounting(manifest,summary):
    accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        if not row.get('passed'):continue
        task=next(t for t in manifest['tasks'] if t['identity']==row['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):
                raise ValueError('invalid subdivision work reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('reservation changed')
        expected=limits|dict(proposals=0 if row['excluded'] else 6,supports=0 if row['excluded'] else 24)
        if counts!=expected or counts!=row['work'] or row['coupling_rows_checked']!=48:
            raise ValueError('subdivision accounting disagrees with complete work')
        accounts.append(dict(identity=row['identity'],**counts))
    return accounts


def comparisons(manifest,rows):
    cover=runner._load(DATA/manifest['inputs']['cover']['path']);parents=cover['parents']
    baseline=runner._load(DATA/manifest['inputs']['baseline']['path'])['cases']
    previous=runner._load(DATA/manifest['inputs']['previous-comparison']['path'])['cases'];cases=[]
    for model in range(3):
        for profile in (False,True):
            group=[p for p in parents if (p['model'],p['profile'])==(model,profile)]
            if len(group)!=8 or {p['sector'] for p in group}!=set(range(8)):raise ValueError('all eight parent sectors required')
            expected={p['identity']+f'-xy-{j}' for p in group for j in range(p['children'])}
            selected=[r for r in rows if r.get('identity') in expected]
            kept=[r for r in selected if r.get('passed') and not r['excluded']]
            containing=[r for r in selected if r.get('truth_in_child')]
            complete=(len(selected)==len(expected) and all(r.get('passed',False) for r in selected)
                and bool(kept) and bool(containing) and all(r['known_truth_retained'] for r in containing))
            case=dict(model=model,profile=profile,complete=complete,expected_cells=len(expected),
                completed_cells=len(selected),excluded_cells=sum(r.get('excluded',False) for r in selected),
                truth_containing_cells=len(containing),twofold=False)
            if complete:
                lo=[min(r['future_lower_m'][j] for r in kept) for j in range(3)]
                hi=[max(r['future_upper_m'][j] for r in kept) for j in range(3)]
                width=[F(b)-F(a) for a,b in zip(lo,hi)]
                original=next(b for b in baseline if (b['model'],b['profile'])==(model,profile))
                before=next(b for b in previous if (b['model'],b['profile'])==(model,profile))
                case.update(union_lower_m=lo,union_upper_m=hi,union_width_m=[endpoint(v,True) for v in width],
                    ratio_to_previous=[float(v/F(b)) for v,b in zip(width,before['union_width_m'])],
                    ratio_to_original=[float(v/F(b)) for v,b in zip(width,original['union_width_m'])],
                    twofold=all(v<=F(b)/2 for v,b in zip(width,original['union_width_m'])))
            cases.append(case)
    return dict(cases=cases,all_cases_twofold=all(c['complete'] and c['twofold'] for c in cases),
        original_parent_count=48,registered_child_count=cover['identities'],new_native_evaluations=0,
        observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);accounts=accounting(manifest,summary)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']];comparison=comparisons(manifest,rows)
    n=len(manifest['tasks']);labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Prediction ranges over smaller calibration boxes','',
        f"{sum(r.get('passed',False) for r in rows)}/{n} registered child calculations passed.",'',
        'All groups meet the unchanged twofold width target: '
        f"**{'yes' if comparison['all_cases_twofold'] else 'no'}**.",'',
        '| Candidate / removal | Complete | Width N / E / height (m) | Fraction of parent width | Twofold target |',
        '|---|---|---:|---:|---|']
    for case in comparison['cases']:
        label=labels[case['model']]+(' / profiled' if case['profile'] else ' / zero')
        width=' / '.join(f'{v:.4f}' for v in case.get('union_width_m',[])) or 'unavailable'
        ratio=' / '.join(f'{v:.4f}' for v in case.get('ratio_to_previous',[])) or 'unavailable'
        text.append(f"| {label} | {'Yes' if case['complete'] else 'No'} | {width} | {ratio} | {'Yes' if case['twofold'] else 'No'} |")
    totals={k:sum(r[k] for r in accounts) for k in ('partition_audits','setups','intervals','coupling_audits',
        'contractions','proposals','supports','truth_audits')}
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Published ranges union every surviving "
        'child and all eight original yaw sectors. Shared-boundary children are retained; '
        'they do not create independent observations. All original radii, expressions, '
        'parent constraints and 78 coordinates remain.','',
        f"Reconciled {totals['partition_audits']}/192 cover audits, {totals['setups']}/192 setups, "
        f"{totals['intervals']}/384 interval maps, {totals['coupling_audits']}/192 coupling audits, "
        f"{totals['contractions']}/192 contractions, {totals['proposals']}/1,152 LP proposals, "
        f"{totals['supports']}/4,608 exact support checks and {totals['truth_audits']}/192 truth audits.",'',
        'This is a generated 7.2-second method comparison. No native prediction or '
        'propagation bound was recomputed, no original-aircraft file was read and no '
        'observed model was fitted. Full-flight usefulness and observational coverage '
        'remain separate gates.','',
        '[Frozen scope](PLAN.md) · [Parent comparison](../ilvis0-coupled-prediction/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'comparison.json',comparison)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==n,totals=totals,
        maximum_identities=192,new_numerical_evaluations=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('comparison.json','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen complete physical subdivision; at most 192 children / 1152 LP / 4608 supports; zero native work.')
    elif args.package_only:publish();print('Published complete physical subdivision.')
    else:publication.check(DATA,PUBLIC);print('Verified subdivision evidence.')

if __name__=='__main__':main()
