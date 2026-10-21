# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a finite fifty-second full-prior growth screen."""
import argparse,gzip,json,math,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-recording-growth-screen-20261021';PUBLIC=ROOT/'docs/ilvis0-recording-growth-screen'
PLAN='docs/ilvis0-recording-growth-screen/PLAN.md';ADAPTER='analysis/lll/ilvis0_recording_growth_screen.py'
OLD=ROOT/'docs/ilvis0-recording-scale-bounds';QUALIFIED=ROOT/'docs/ilvis0-recording-adapter-controls'


def prepare():
    if DATA.exists():raise ValueError('recording growth screen already frozen')
    for directory in (OLD,QUALIFIED):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed recording prerequisite changed')
    previous=runner._load(QUALIFIED/'manifest.json');old_summary=runner._load(OLD/'summary.json')
    environment=runner.runtime_environment()
    if not runner._load(QUALIFIED/'summary.json')['passed'] or previous['environment']!=environment:
        raise ValueError('passing format controls in the same environment required')
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_recording_case_checks.py',
        'analysis/tests/test_ilvis0_recording_growth_checks.py','analysis/tests/ilvis0_recording_growth_worker.py',
        'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py'}
    for name,digest in previous['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    tasks=[];inputs={};baselines=[]
    for original in previous['tasks']:
        spec=original['payload'];model=spec['model'];profile=spec['profile']
        legacy_path=QUALIFIED/previous['inputs'][original['input_key']]['path']
        with gzip.open(legacy_path,'rt') as stream:legacy=json.load(stream)
        case_path=QUALIFIED/previous['inputs'][spec['case_key']]['path'];case=runner._load(case_path)
        if (len(case['dt'])!=48000 or case['configuration']['limits']!=legacy['limits']
                or case['provenance']['source_sha256']!=runner._sha(legacy_path)):
            raise ValueError('original whole recording or calibration limits changed')
        time_s=legacy['starts'][9999]+legacy['durations'][9999];scale=legacy['metre_scale']
        if len(scale)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in scale):
            raise ValueError('original positive comparison-frame scales required')
        recipe=dict(time_s=time_s,center=case['center'],lower=[-1.]*27,upper=[1.]*27,coordinate_scale=scale)
        identity=f'growth-50-{model}-{int(profile)}';path=PUBLIC/'saved-inputs'/(identity+'.json')
        runner._write(path,recipe);inputs[identity]=str(path.relative_to(ROOT))
        key=spec['case_key'];inputs[key]=str(case_path.relative_to(ROOT))
        limits=dict(setups=1,proofs=1,source_setups=1,source_steps=48000,source_body_bounds=48000,
            source_derivative_setups=1,source_derivative_steps=48000,source_point_setups=1,source_point_steps=48000,source_direct_steps=48000)
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(case_key=key,model=model,profile=profile,time_s=time_s,compiler=compiler,limits=limits,
                maximum_bound_seconds=900.),limits=dict(native_calls=4,packet_visits=192000,bound_calls=1,bound_steps=432000)))
        baseline=None
        if profile:
            historic=next((r for r in old_summary['results'] if r['identity']==legacy['model']+'-broad'),None)
            if historic:
                result=runner._load(OLD/historic['artifact'])
                found=[r for r in result.get('checkpoints',[]) if r['packets']==10000]
                if found:
                    if len(found)!=1 or found[0]['elapsed_s']!=time_s:raise ValueError('historical query time differs')
                    baseline=dict(full_domain_radius_m=found[0]['change_m'],unshared_remainder_m=found[0]['remainder_m'],
                        artifact=historic['artifact'],artifact_sha256=historic['artifact_sha256'])
        baselines.append(dict(identity=identity,model=model,profile=profile,query_time_s=time_s,historical=baseline))
    if len(tasks)!=6:raise ValueError('all three candidates and processing variants required')
    path=PUBLIC/'saved-inputs/historical.json';runner._write(path,dict(cases=baselines))
    inputs['historical']=str(path.relative_to(ROOT))
    inputs['format-manifest']=str((QUALIFIED/'manifest.json').relative_to(ROOT))
    inputs['format-receipt']=str((QUALIFIED/'evidence-receipt.json').relative_to(ROOT))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=1,threads=1,maximum_wall_s=5700,environment=environment)


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
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('growth work changed')
        if 'work' in row and (row['work']!=counts or counts!=limits):raise ValueError('growth resources lack reservation')
        compilation=next((n for n in envelope['artifacts'] if Path(n).name=='compilation.json'),None)
        if compilation:
            for kind,metadata in runner._load(DATA/compilation).items():
                if metadata['compiler']!=task['payload']['compiler']:raise ValueError('compiled environment changed')
                if kind=='native':
                    if metadata['source_sha256']!=manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:raise ValueError('native source changed')
                else:
                    for name,digest in metadata['sources'].items():
                        if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('compiled source changed')
        if row.get('original_reads',0) or row.get('optimizer_starts',0):raise ValueError('unauthorized archival/fitting work')
        accounts.append(dict(identity=item['identity'],**counts))
    historical=runner._load(DATA/manifest['inputs']['historical']['path'])['cases']
    text=['# Fifty-second bound growth on complete four-minute inputs','',
        f"{sum(r.get('passed',False) for r in rows)}/6 numerical cases passed; elapsed {summary['elapsed_s']:.2f} seconds.",'',
        '| Candidate / processing | Numerical checks | Bound time | Largest unshared radius | Largest full-domain radius |',
        '|---|---|---:|---:|---:|']
    for item,row in zip(summary['results'],rows,strict=True):
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity']);spec=task['payload']
        label=('Specified-field globe','Zero-field globe','Flat disc')[spec['model']]+(' / profiled' if spec['profile'] else ' / zero')
        values=(f"{row['bound_elapsed_s']:.2f} s | {max(row['unshared_radius_m']):.5g} m | {max(row['conditional_full_domain_radius_m']):.5g} m"
            if 'bound_elapsed_s' in row else 'unfinished | unavailable | unavailable')
        text.append(f"| {label} | {'Pass' if row.get('passed') else 'Fail'} | {values} |")
    text+=['','Radii use the original frozen coordinate comparison frame. Full-domain radii include the shared '
        'terms as well as approximation error; they are not confidence intervals or measured aircraft errors. '
        'The entire original broad parameter domain is retained, with no orientation-sector selection or '
        'training constraints. The original clock offset remains fixed.','',
        f"Charged {summary['charged']['native_calls']}/24 native queries, {summary['charged']['bound_calls']}/6 bounds "
        f"and {summary['charged']['bound_steps']}/2,592,000 logical steps. Unused reservations remain charged. "
        'No original-aircraft observations, LP or optimizer were used.','',
        'This is a nominal fifty-second runtime/growth screen on complete four-minute inputs. Even a passing '
        'numerical screen does not establish useful four-minute prediction bounds, an uncertain clock or '
        'observational coverage. The earlier four-minute failures and all 53 aircraft findings stay unchanged.','',
        '[Frozen scope](PLAN.md) · [Format checks](../ilvis0-recording-adapter-controls/README.md) · '
        '[Next gates](../ilvis0-three-source-complete/NEXT_PLAN.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    runner._replace(PUBLIC/'growth.json',dict(cases=[dict(identity=item['identity'],result=row,
        historical=next(r['historical'] for r in historical if r['identity']==item['identity']))
        for item,row in zip(summary['results'],rows,strict=True)],recording_length_usefulness_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain'))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('accounting.json','growth.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six 50-second global-domain cases / 2,592,000 steps / one thread / 5,700 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Recording growth screen: '+result['state'])
    elif args.package_only:publish();print('Published growth screen.')
    else:publication.check(DATA,PUBLIC);print('Verified growth screen.')


if __name__=='__main__':main()
