# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze only missing future queries under the qualified serial recipe."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-serial-future-bounds-20261021';PUBLIC=ROOT/'docs/ilvis0-serial-future-bounds'
PLAN='docs/ilvis0-serial-future-bounds/PLAN.md';ADAPTER='analysis/lll/ilvis0_serial_future.py'


def sealed(directory,environment):
    for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
        if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
    manifest=runner._load(directory/'manifest.json');summary=runner._load(directory/'summary.json')
    completion=runner._load(directory/'completion.json')
    if (manifest['environment']!=environment or completion['manifest_sha256']!=runner._sha(directory/'manifest.json')
            or completion['summary_sha256']!=runner._sha(directory/'summary.json') or completion['state']!=summary['state']):
        raise ValueError('sealed completion/environment mismatch')
    return manifest,summary


def time_only(row):
    return row.get('passed') is False and row.get('error_type')=='Unsupported' and row.get('reason')=='time allowance exhausted'


def prepare():
    if DATA.exists():raise ValueError('serial future generation already frozen')
    environment=runner.runtime_environment();qualified=ROOT/'docs/ilvis0-serial-bound-screen'
    qualification,qualified_summary=sealed(qualified,environment)
    if (not qualified_summary['passed'] or not runner._load(qualified/'verdict.json')['qualified']
            or qualification['allocation']['workers']!=1 or qualification['allocation']['threads']!=1):
        raise ValueError('qualified serial execution required')
    direct=ROOT/'docs/ilvis0-direct-complete-prediction';previous,summary=sealed(direct,environment)
    earlier=ROOT/'docs/ilvis0-taylor-complete-prediction';_,earlier_summary=sealed(earlier,environment)
    sources={PLAN,ADAPTER,'analysis/tests/ilvis0_serial_future_worker.py',
        'analysis/tests/test_ilvis0_serial_future_source.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for manifest in (previous,qualification):
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    records={r['identity']:runner._load(direct/r['artifact']) for r in summary['results']}
    older={r['identity']:runner._load(earlier/r['artifact']) for r in earlier_summary['results']}
    if len(records)!=48 or any(not (r['result'].get('passed') is True or time_only(r['result'])) for r in records.values()):
        raise ValueError('original source failures must be solely time limits')
    tasks=[];inputs={};selection=[]
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    for task in previous['tasks']:
        record=records[task['identity']]
        if not time_only(record['result']):continue
        if any(Path(n).name=='bound-07.json' for n in record['artifacts']):
            raise ValueError('selected future query is already complete')
        key=task['input_key'];payload=task['payload']
        bundle=runner._load(direct/previous['inputs'][key]['path']);tag=bundle['result']['task']
        if type(tag['sector']) is not int or not 0<=tag['sector']<8 or tag['packets']!=1600 or bundle['future']['time_s']!=7.2:
            raise ValueError('unchanged original sector, source and future time required')
        for name in (key,payload['case_key'],payload['condition_key']):
            inputs[name]=str((direct/previous['inputs'][name]['path']).relative_to(ROOT))
        before=older[task['identity']]
        if not (before['result'].get('passed') is True or time_only(before['result'])):
            raise ValueError('older future source has a mathematical failure')
        names=[n for n in before['artifacts'] if Path(n).name=='bound-07.json']
        if len(names)>1:raise ValueError('ambiguous older future query')
        baseline_key=None
        if names:
            baseline_key=task['identity']+'-earlier-future';inputs[baseline_key]=str((earlier/names[0]).relative_to(ROOT))
        limits=dict(setups=1,proofs=1,parent_supports=6,source_setups=1,source_steps=1600,source_body_bounds=1600,
            source_derivative_setups=1,source_derivative_steps=1600,source_point_setups=1,source_point_steps=1600,source_direct_steps=1600)
        identity='serial-future-'+task['identity']
        tasks.append(dict(identity=identity,input_key=key,
            payload=dict(case_key=payload['case_key'],condition_key=payload['condition_key'],sector=tag['sector'],
                baseline_key=baseline_key,maximum_bound_seconds=120.,compiler=compiler,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=14400)))
        selection.append(dict(identity=identity,source_identity=task['identity'],model=tag['model'],profile=tag['profile'],
            sector=tag['sector'],source_result_sha256=record['result_sha256'],older_future_available=bool(names)))
    if len(tasks)!=12:raise ValueError('all twelve and only missing future queries required')
    selection_path=PUBLIC/'saved-inputs/selection.json';runner._write(selection_path,dict(queries=selection,
        original_manifest_sha256=runner._sha(direct/'manifest.json'),serial_manifest_sha256=runner._sha(qualified/'manifest.json')))
    inputs['selection']=str(selection_path.relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=1500,environment=environment)


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);row=envelope['result'];rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity']);limits=task['payload']['limits']
        counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('future work changed')
        if 'work' in row and (row['work']!=counts or counts!=limits):raise ValueError('future resource mismatch')
        compilation=next((n for n in envelope['artifacts'] if Path(n).name=='compilation.json'),None)
        if compilation:
            for metadata in runner._load(DATA/compilation).values():
                if metadata['compiler']!=task['payload']['compiler']:raise ValueError('compiled environment changed')
                for name,digest in metadata['sources'].items():
                    if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('compiled source changed')
        if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
            raise ValueError('unauthorized future work')
        accounts.append(dict(identity=item['identity'],**counts))
    text=['# Missing future certificates under serial execution','',
        f"{sum(r.get('passed',False) for r in rows)}/12 newly frozen future queries passed.",'',
        '| Query | Seconds | Older future available |','|---|---:|---|']
    for item,row in zip(summary['results'],rows,strict=True):
        elapsed=f"{row['bound_elapsed_s']:.3f}" if 'bound_elapsed_s' in row else 'unfinished'
        available='Yes' if row.get('predecessor_available') else 'No'
        text.append(f"| {item['identity']} | {elapsed} | {available} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; charged {summary['charged']['bound_calls']}/12 bounds and "
        f"{summary['charged']['bound_steps']}/172,800 logical steps. One worker and one thread; the 120-second "
        'per-bound limit is unchanged. No training bound was recalculated.','',
        'The original algorithm, measurements, domains and references remain. Earlier timeouts keep their '
        'original labels. These certificates need a separate saved-only complete-cover comparison before '
        'the fixed width target can be assessed. They establish no aircraft confidence level.','',
        '[Frozen scope](PLAN.md) · [Serial qualification](../ilvis0-serial-bound-screen/README.md) · '
        '[Current width result](../ilvis0-reused-complete-prediction/INTERPRETATION.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen twelve missing future bounds / 172,800 steps / one thread / 1,500 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Serial future generation: '+result['state'])
    elif args.package_only:publish();print('Published serial future bounds.')
    else:publication.check(DATA,PUBLIC);print('Verified serial future bounds.')


if __name__=='__main__':main()
