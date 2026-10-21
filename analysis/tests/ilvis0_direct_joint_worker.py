# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish the complete joint-adapter control matrix."""
import argparse
import importlib.metadata
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-direct-joint-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-direct-joint-controls'
PLAN='docs/ilvis0-direct-joint-controls/PLAN.md'
ADAPTER='analysis/lll/ilvis0_direct_joint_controls.py'


def prepare():
    from lll.ilvis0_direct_joint_controls import FIXTURE_LIMITS
    from lll.ilvis0_direct_prediction import allowances
    if DATA.exists():raise ValueError('joint-adapter qualification already frozen')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_direct_prediction.py','analysis/lll/ilvis0_direct_interface.py',
        'analysis/tests/test_ilvis0_direct_prediction.py','analysis/tests/test_ilvis0_direct_interface.py',
        'analysis/tests/ilvis0_direct_joint_worker.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,required in (('ilvis0-direct-native-controls',True),('ilvis0-direct-range-preflight',True),('ilvis0-complete-source-preflight',True),('ilvis0-directional-prediction',False)):
        directory=ROOT/'docs'/name
        for artifact,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,artifact))!=digest:raise ValueError('preserved dependency changed')
        if required and not runner._load(directory/'summary.json')['passed']:raise ValueError('passing source prerequisites required')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for artifact,digest in manifest['sources'].items():
            if artifact.startswith('analysis/lll/') or artifact in ('analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/test_ilvis0_regrouped_history.py'):
                if runner._sha(ROOT/artifact)!=digest:raise ValueError('qualified source changed: '+artifact)
                sources.add(artifact)
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0];tasks=[];catalog=[]
    for model in range(3):
        for profile in (False,True):
            identity=f'joint-{model}-{int(profile)}';item=dict(identity=identity,model=model,profile=profile,packets=13,
                dt_s=.005,training_s=[.015,.03],future_s=.05)
            catalog.append(item)
            tasks.append(dict(identity=identity,input_key='catalog',payload=dict(item,compiler=compiler,pytest=importlib.metadata.version('pytest'),
                fixture_limits=FIXTURE_LIMITS,target_limits=allowances(13,2)),
                limits=dict(native_calls=6,packet_visits=78,bound_calls=6,bound_steps=429)))
    path=PUBLIC/'control-catalog.json';runner._write(path,catalog)
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=dict(catalog=str(path.relative_to(ROOT))),
        adapter=ADAPTER,workers=4,threads=1,maximum_wall_s=300,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[];accounts=[]
    for record in summary['results']:
        task=next(task for task in manifest['tasks'] if task['identity']==record['identity'])
        envelope=runner._load(DATA/record['artifact']);row=envelope['result'];rows.append(row)
        for kind,limits in (('fixture',task['payload']['fixture_limits']),('target',task['payload']['target_limits'])):
            counts=dict.fromkeys(limits,0)
            names=sorted(name for name in envelope['artifacts'] if
                (Path(name).name.startswith('fixture-reservation-') if kind=='fixture' else
                    Path(name).parent.name=='adapter' and Path(name).name.startswith('reservation-')))
            for name in names:
                event=runner._load(DATA/name);inc=event['increase']
                if not inc or any(key not in counts or type(value) is not int or value<1 for key,value in inc.items()):
                    raise ValueError('invalid joint-control reservation')
                counts={key:value+inc.get(key,0) for key,value in counts.items()}
                if counts!=event['counts'] or any(value>limits[key] for key,value in counts.items()):raise ValueError('joint reservation changed')
            result_path=next((name for name in envelope['artifacts'] if Path(name).name=='adapter-result.json'),None)
            reported=row.get('fixture_work') if kind=='fixture' else (runner._load(DATA/result_path)['work'] if result_path else None)
            if reported is not None and reported!=counts:raise ValueError('joint work and reservations disagree')
            accounts.append(dict(identity=record['identity'],kind=kind,work=counts))
    text=['# Complete joint-adapter controls','',
        f"{sum(row.get('passed',False) for row in rows)}/6 model/processing controls passed.",'',
        f"Charged {summary['charged']['native_calls']}/36 native fixture evaluations and {summary['charged']['bound_calls']}/36 old/new bounds; "
        f"{summary['charged']['bound_steps']}/2,574 logical bound steps. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'These fixed generated controls check training-conditioned bounds, subdomain transfer, center/column preservation, '
        'independent training-row and prediction-endpoint audits, and the final known-truth check. '
        'They are unblinded software qualification, not aircraft validation or calibrated statistical coverage.','',
        '[Frozen scope](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],complete=len(accounts)==12,
        optimizer_starts=0,original_reads=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six joint controls / 36 native evaluations / 36 bounds / 2574 steps.')
    elif args.package_only:publish();print('Published joint-adapter qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified joint-adapter qualification.')


if __name__=='__main__':main()
