# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a six-source value-only rotation preflight."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-source-norm-preflight-20261020';PUBLIC=ROOT/'docs/ilvis0-source-norm-preflight'
OLD=ROOT/'docs/ilvis0-coupled-prediction';ADAPTER='analysis/lll/ilvis0_source_norm_preflight.py'
PLAN='docs/ilvis0-source-norm-preflight/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_rotation_interval.py','analysis/lll/ilvis0_directional_scalar.py',
    'analysis/lll/ilvis0_directional_values.py','analysis/lll/ilvis0_directional_matrices.py',
    'analysis/tests/ilvis0_source_norm_worker.py','analysis/tests/test_ilvis0_source_norm_preflight.py',
    'analysis/tests/test_ilvis0_rotation_interval.py','analysis/tests/test_ilvis0_directional_scalar.py',
    'analysis/tests/test_ilvis0_directional_values.py','analysis/tests/test_ilvis0_directional_matrices.py',
    'analysis/tests/test_ilvis0_native_box_bounds.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('source preflight already frozen')
    for name,digest in runner._load(OLD/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(OLD,name))!=digest:raise ValueError('sealed source prerequisite changed')
    previous=runner._load(OLD/'manifest.json');summary=runner._load(OLD/'summary.json');sources=set(SOURCES)
    if not summary['passed'] or previous['environment']!=runner.runtime_environment():raise ValueError('qualified source environment required')
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    tasks=[];inputs={};groups=set()
    for old_task in previous['tasks']:
        identity=old_task['identity'];item=next(r for r in summary['results'] if r['identity']==identity)
        result=runner._load(OLD/item['artifact'])['result']
        if result['task']['sector']!=4:continue
        if not result['passed'] or not result['truth_in_sector'] or not result['known_truth_retained']:
            raise ValueError('fixed sector must have its previously qualified source control')
        group=(result['task']['model'],result['task']['profile'])
        if group in groups:raise ValueError('one source per model/processing group required')
        groups.add(group);case_key=old_task['payload']['case_key'];record=previous['inputs'][case_key]
        inputs[case_key]=str((OLD/record['path']).relative_to(ROOT))
        bundle=dict(result=result,future=runner._load(OLD/'artifacts'/identity/'future.json'))
        path=PUBLIC/'saved-inputs'/(identity+'.json');runner._write(path,bundle);inputs[identity]=str(path.relative_to(ROOT))
        limits=dict(setups=1,prefixes=1,prefix_packets=1600,closures=1,point_oracles=1,oracle_packets=1600,checks=14)
        tasks.append(dict(identity=identity,input_key=identity,payload=dict(case_key=case_key,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('all six fixed source groups required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=120,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']];accounts=[]
    for record,row in zip(summary['results'],rows,strict=True):
        if 'work' not in row:continue
        artifacts=runner._load(DATA/record['artifact'])['artifacts'];task=next(t for t in manifest['tasks'] if t['identity']==row['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in artifacts if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('work journal changed')
        if counts!=limits or counts!=row['work'] or max(row['actual_prefix_packets'],row['actual_oracle_packets'])>1600:
            raise ValueError('source work and finite reservations disagree')
        accounts.append(dict(identity=row['identity'],**counts))
    text=['# Source-level norm preflight','',f"{sum(r.get('passed',False) for r in rows)}/6 source controls passed.",'',
        '| Candidate / removal | Passed | Original vertical width (m/s²) | Geometric width (m/s²) | Combined width (m/s²) | Fraction retained |',
        '|---|---|---:|---:|---:|---:|']
    for row in rows:
        if 'model' not in row:continue
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if row['passed'] else 'No'} | {row['baseline_vertical_width']:.7g} | "
            f"{row['raw_vertical_width']:.7g} | {row['combined_vertical_width']:.7g} | {row['width_ratio']:.6f} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds. Reserved {sum(r['prefix_packets'] for r in accounts)}/9,600 bounded-prefix "
        f"visits and {sum(r['oracle_packets'] for r in accounts)}/9,600 point-oracle visits, plus {sum(r['checks'] for r in accounts)}/84 scalar checks.",'',
        'The baseline uses the same saved source, body prefix and training-conditioned force range. '
        'The literal installation-matrix metric defect is bounded explicitly. All ranges are fixed '
        'before the known calibration is read. No original aircraft data or protected ESA data is used.','',
        'This is a value-only component diagnostic. It does not qualify a Taylor remainder, '
        'native reference coefficients, a full position prediction or observational coverage. '
        'No full native integration, propagation bound, LP or fit ran.','',
        '[Frozen scope](PLAN.md) · [Operator derivation](../ilvis0-directional-dynamics/OPERATOR_DERIVATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,complete=len(accounts)==6,new_native_evaluations=0,optimizer_starts=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six source prefixes / six point oracles / 19200 reserved visits; zero native trajectories.')
    elif args.package_only:publish();print('Published source norm preflight.')
    else:publication.check(DATA,PUBLIC);print('Verified source norm preflight.')


if __name__=='__main__':main()
