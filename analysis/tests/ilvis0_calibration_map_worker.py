# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the six-case generated calibration-map diagnosis."""
import argparse
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_calibration_map_diagnostic import reconcile

DATA=ROOT/'data/ilvis0-calibration-map-diagnostic-20261020'
PUBLIC=ROOT/'docs/ilvis0-calibration-map-diagnostic'
OLD=ROOT/'docs/ilvis0-product-prediction';QUALIFIED=ROOT/'docs/ilvis0-feasible-witness-controls'
ADAPTER='analysis/lll/ilvis0_calibration_map_diagnostic.py'
PLAN='docs/ilvis0-calibration-map-diagnostic/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/ilvis0_calibration_map_worker.py',
    'analysis/tests/test_ilvis0_calibration_map_diagnostic.py','analysis/tests/saved_prediction_fixtures.py',
    'analysis/tests/test_ilvis0_transform_audit.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py','analysis/lll/ilvis0_control_publication.py']


def prepare():
    if DATA.exists():raise ValueError('calibration-map diagnostic already frozen')
    sources=set(SOURCES)
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=runner.runtime_environment():
            raise ValueError('passing prerequisite and unchanged environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified mathematical source changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json')
    tasks=[];inputs={};groups=set()
    for task in previous['tasks']:
        identity=task['identity'];record=next(r for r in summary['results'] if r['identity']==identity)
        old=runner._load(OLD/record['artifact'])['result']
        if not old['truth_in_sector']:continue
        group=(old['task']['model'],old['task']['profile'])
        if group in groups or not old['passed'] or old['excluded']:raise ValueError('unique passing known sector required')
        groups.add(group);case_key=task['payload']['case_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        bundle=dict(result=old,training=runner._load(OLD/'artifacts'/identity/'training.json'),
            future=runner._load(OLD/'artifacts'/identity/'future.json'),
            cuts=runner._load(OLD/'artifacts'/identity/'cuts.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle)
        inputs[identity]=str(path.relative_to(ROOT))
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=case_key,work_limits=dict(lp=6,maps=7,checks=41000)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all six predeclared generated groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def accounts(manifest,summary):
    rows=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);result=record['result']
        if not result.get('passed'):continue
        task=next(t for t in manifest['tasks'] if t['identity']==result['identity'])
        names=sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-'))
        events=[runner._load(DATA/n) for n in names]
        rows.append(dict(identity=result['identity'],**reconcile(events,result['work'],task['payload']['work_limits'])))
    return rows


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);audited=accounts(manifest,summary)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    labels=['Globe with specified field','Globe with zero field','Flat disc']
    text=['# Can one calibration produce the extreme errors?','',
        f"{sum(r.get('passed',False) for r in rows)}/6 generated cases completed their correctness checks.",'',
        'This is a software diagnosis of prediction ranges. No aircraft model comparison was rerun.','',
        '| Candidate / removal | Exact witnesses | Mapped witnesses inside training region | Collapsed to known anchor | Largest signed-axis change (m) |',
        '|---|---:|---:|---:|---:|']
    for row in rows:
        if not row.get('passed'):
            text.append(f"| {row['identity']} | Unsupported | — | — | — |");continue
        maximum=max((abs(F(a['total'])) for p in row['proposals'] for a in p.get('changes',[])),default=F(0))
        text.append(f"| {labels[row['model']]} / {'profiled' if row['profile'] else 'zero'} | "
            f"{row['supported_witnesses']}/6 | {row['mapped_training_feasible']}/{row['mapped_witnesses']} | "
            f"{row['boundary_collapses']} | {float(maximum):.6f} |")
    totals={k:sum(r[k] for r in audited) for k in ('lp','maps','checks')}
    text+=['',f"Elapsed {summary['elapsed_s']:.1f} seconds. Reconciled {totals['lp']}/36 LP proposals, "
        f"{totals['maps']}/42 complete map evaluations and {totals['checks']:,}/246,000 scalar checks.",'',
        'Each LP point was saved, repaired with exact arithmetic toward its known generated '
        'anchor and independently checked. Its 27 physical values were then converted explicitly '
        'to binary numbers. All 24 common errors were recomputed from that same calibration; '
        'the 27 arithmetic products were rebuilt without clipping. Signed changes retain '
        'cancellation between blocks. The known anchor is unavailable to a real prediction method.','',
        'A failing mapped point is not a feasible physical example for the saved extreme. '
        'A passing point is only a surrogate example, not a global optimum, native trajectory '
        'or calibrated interval. Failed proposals and conversions remain without replacements. '
        'There were zero new native predictions, integration bounds, original-aircraft reads '
        'or observed fits. The 53 aircraft findings are unchanged.','',
        '[Frozen scope](PLAN.md) · [Preceding comparison](../ilvis0-product-prediction/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=audited,complete=len(audited)==6,totals=totals,
        maxima=dict(lp=36,maps=42,checks=246000),new_numerical_evaluations=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six cases: at most 36 LP / 42 maps / 246000 scalar checks; zero native work.')
    elif args.package_only:publish();print('Published complete calibration-map diagnosis.')
    else:publication.check(DATA,PUBLIC);print('Verified calibration-map diagnostic evidence.')

if __name__=='__main__':main()
