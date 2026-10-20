# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the complete directional prediction comparison."""
import argparse
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read
from lll.ilvis0_saved_prediction_audit import endpoint

DATA=ROOT/'data/ilvis0-directional-prediction-20261020';PUBLIC=ROOT/'docs/ilvis0-directional-prediction'
OLD=ROOT/'docs/ilvis0-coupled-prediction';LATEST=ROOT/'docs/ilvis0-coupled-subdivision'
QUALIFIED=ROOT/'docs/ilvis0-directional-native-controls';BASE=ROOT/'docs/ilvis0-projected-future-bounds'
ADAPTER='analysis/lll/ilvis0_directional_prediction.py';PLAN='docs/ilvis0-directional-prediction/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_directional_interface.py','analysis/lll/ilvis0_training_remainder_audit.py',
    'analysis/tests/ilvis0_directional_prediction_worker.py','analysis/tests/test_ilvis0_directional_prediction.py',
    'analysis/tests/test_ilvis0_directional_prediction_summary.py',
    'analysis/tests/test_ilvis0_directional_interface.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/test_ilvis0_regrouped_history.py','analysis/tests/test_ilvis0_coupled_prediction.py',
    'analysis/tests/test_ilvis0_product_prediction.py','analysis/tests/test_ilvis0_transform_audit.py',
    'analysis/tests/saved_prediction_fixtures.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('complete directional prediction already frozen')
    sources=set(SOURCES)
    for directory in (OLD,LATEST,QUALIFIED,BASE):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('all prerequisite correctness checks required')
    for directory in (OLD,QUALIFIED):
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('qualified numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    latest_manifest=runner._load(LATEST/'manifest.json')
    if latest_manifest['inputs']['previous-comparison']['sha256']!=runner._sha(OLD/'comparison.json'):
        raise ValueError('inherited subdivision must descend from the same parent comparison')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');tasks=[];inputs={};frames={}
    for key,record in previous['inputs'].items():
        if key.startswith('case-'):
            path=OLD/record['path']
            if len(read(path)['dt'])!=1600:raise ValueError('original complete generated histories required')
            inputs[key]=str(path.relative_to(ROOT))
    limits=dict(setups=1,proofs=1,training_audits=36,contractions=1,proposals=6,supports=24,truth_audits=1)
    for old_task in previous['tasks']:
        identity=old_task['identity'];item=next(r for r in summary['results'] if r['identity']==identity)
        result=runner._load(OLD/item['artifact'])['result']
        if not result['passed'] or result['excluded']:raise ValueError('all 48 passing parents required')
        directory=OLD/'artifacts'/identity;training=runner._load(directory/'training.json');future=runner._load(directory/'future.json')
        if len(training['times_s'])!=6:raise ValueError('six original training epochs required')
        group=(result['task']['model'],result['task']['profile']);frame=(training['region']['origin'],training['region']['coordinate_scale'])
        if group in frames and frames[group]!=frame:raise ValueError('all sector unions must share the coordinate frame')
        frames[group]=frame;prior=read(OLD/previous['inputs'][old_task['input_key']]['path'])
        bundle=dict(result=result,training=training,future=future,product_cuts=prior['product_cuts'])
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=old_task['payload']['case_key'],
            packets=1600,maximum_bound_seconds=120.,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=7,bound_steps=22400)))
    if len(tasks)!=48 or len(frames)!=6:raise ValueError('all six groups and eight sectors required')
    inputs['baseline']=str((BASE/'case-unions.json').relative_to(ROOT))
    inputs['inherited']=str((LATEST/'comparison.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=2400,environment=runner.runtime_environment())


def comparison(manifest,rows):
    baseline=runner._load(DATA/manifest['inputs']['baseline']['path'])['cases']
    inherited=runner._load(DATA/manifest['inputs']['inherited']['path'])['cases'];cases=[]
    for model in range(3):
        for profile in (False,True):
            group=[r for r in rows if r.get('task',{}).get('model')==model and r.get('task',{}).get('profile')==profile]
            complete=(len(group)==8 and {r['task']['sector'] for r in group}==set(range(8))
                and all(r.get('passed',False) for r in group))
            kept=[r for r in group if r.get('passed') and not r['excluded']]
            known=[r for r in group if r.get('truth_in_sector')]
            complete=complete and bool(kept) and bool(known) and all(r['known_truth_retained'] for r in known)
            case=dict(model=model,profile=profile,complete=complete,twofold=False,fresh_twofold=False,
                completed_sectors=len(group),excluded_sectors=sum(r.get('excluded',False) for r in group))
            if complete:
                lo=[min(r['future_lower_m'][j] for r in kept) for j in range(3)]
                hi=[max(r['future_upper_m'][j] for r in kept) for j in range(3)]
                old=next(r for r in inherited if (r['model'],r['profile'])==(model,profile))
                original=next(r for r in baseline if (r['model'],r['profile'])==(model,profile))
                left=[max(a,b) for a,b in zip(lo,old['union_lower_m'])];right=[min(a,b) for a,b in zip(hi,old['union_upper_m'])]
                if any(a>b for a,b in zip(left,right)):raise ValueError('fresh/inherited complete predictions disagree')
                widths=[F(b)-F(a) for a,b in zip(left,right)];fresh=[F(b)-F(a) for a,b in zip(lo,hi)]
                case.update(fresh_lower_m=lo,fresh_upper_m=hi,fresh_width_m=[endpoint(v,True) for v in fresh],
                    union_lower_m=left,union_upper_m=right,union_width_m=[endpoint(v,True) for v in widths],
                    ratio_to_inherited=[float(w/F(v)) for w,v in zip(widths,old['union_width_m'])],
                    twofold=all(w<=F(v)/2 for w,v in zip(widths,original['union_width_m'])),
                    fresh_twofold=all(w<=F(v)/2 for w,v in zip(fresh,original['union_width_m'])))
            cases.append(case)
    return dict(cases=cases,all_cases_twofold=all(c['complete'] and c['twofold'] for c in cases),
        all_fresh_cases_twofold=all(c['complete'] and c['fresh_twofold'] for c in cases),
        native_evaluations=0,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']];comp=comparison(manifest,rows)
    accounts=[]
    for item,row in zip(summary['results'],rows,strict=True):
        if 'work' not in row:continue
        record=runner._load(DATA/item['artifact']);task=next(t for t in manifest['tasks'] if t['identity']==row['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid work reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('changed reservation journal')
        expected=limits|dict(proposals=0 if row['excluded'] else 6,supports=0 if row['excluded'] else 24)
        if counts!=expected or counts!=row['work'] or row['bound_evaluations']!=7:raise ValueError('complete work accounting failed')
        accounts.append(dict(identity=row['identity'],**counts))
    text=['# Complete directional prediction comparison','',f"{sum(r.get('passed',False) for r in rows)}/48 sector calculations passed.",'',
        'Every combined range meets the unchanged twofold target: '+('**yes**.' if comp['all_cases_twofold'] else '**no**.'),'',
        '| Candidate / removal | Complete | Fresh widths N / E / height (m) | Combined widths (m) | Combined target |',
        '|---|---|---:|---:|---|']
    for c in comp['cases']:
        label=('Globe with specified field','Globe with zero field','Flat disc')[c['model']]+(' / profiled' if c['profile'] else ' / zero')
        fresh=' / '.join(f'{v:.4f}' for v in c.get('fresh_width_m',[])) or 'unavailable'
        combined=' / '.join(f'{v:.4f}' for v in c.get('union_width_m',[])) or 'unavailable'
        text.append(f"| {label} | {'Yes' if c['complete'] else 'No'} | {fresh} | {combined} | {'Yes' if c['twofold'] else 'No'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Charged {summary['charged']['bound_calls']}/336 bounds "
        f"and {summary['charged']['bound_steps']}/1,075,200 packet-steps. The fresh range unions every surviving "
        'sector. The combined range intersects that union with the independently qualified 192-box union; '
        'both remain visible. Missing or failed sectors prevent qualification.','',
        'No new native predictions or original-aircraft reads ran. The same six generated 7.2-second '
        'histories, original physical bounds, observations, calibration references and 78 coordinates '
        'remain. All old constraints are preserved. This is a method-usefulness test, '
        'not calibrated observational coverage or a full-recording aircraft validation.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'comparison.json',comp);runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==48))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('comparison.json','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 sectors / 336 bounds / 288 LP / 1152 supports; four total threads.')
    elif args.package_only:publish();print('Published complete directional prediction comparison.')
    else:publication.check(DATA,PUBLIC);print('Verified complete directional prediction evidence.')


if __name__=='__main__':main()
