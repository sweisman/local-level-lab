# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish matched rounded-source training-transfer controls."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication
from lll.ilvis0_sharded_native import read

DATA=ROOT/'data/ilvis0-rounded-source-controls-20261020';PUBLIC=ROOT/'docs/ilvis0-rounded-source-controls'
OLD=ROOT/'docs/ilvis0-source-value-controls';PARENT=ROOT/'docs/ilvis0-conditioned-native-controls'
ADAPTER='analysis/lll/ilvis0_rounded_source_controls.py';PLAN='docs/ilvis0-rounded-source-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_rounded_body_interval.py','analysis/lll/ilvis0_initial_source_bridge.py',
    'analysis/lll/ilvis0_rotation_derivative.py','analysis/lll/ilvis0_body_interval.py',
    'analysis/tests/ilvis0_rounded_source_worker.py','analysis/tests/test_ilvis0_rounded_body_interval.py',
    'analysis/tests/test_ilvis0_initial_source_bridge.py','analysis/tests/test_ilvis0_rotation_derivative.py',
    'analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']
PREFIXES=[0,15,63,127,511,1023,1438,1439,1440,1599]


def prepare():
    if DATA.exists():raise ValueError('rounded-source qualification already frozen')
    sources=set(SOURCES)
    for directory in (OLD,PARENT):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        manifest=runner._load(directory/'manifest.json')
        if not runner._load(directory/'summary.json')['passed'] or manifest['environment']!=runner.runtime_environment():
            raise ValueError('qualified prerequisites and unchanged environment required')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified implementation changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');parents=runner._load(PARENT/'manifest.json')
    compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    tasks=[];inputs={};groups=set()
    for old in previous['tasks']:
        key=old['input_key'];path=OLD/previous['inputs'][key]['path'];bundle=read(path)
        group=(bundle['result']['model'],bundle['result']['profile'])
        if not bundle['result']['passed'] or group in groups:raise ValueError('six unique source groups required')
        groups.add(group);inputs[key]=str(path.relative_to(ROOT));case_key=old['payload']['case_key']
        inputs[case_key]=str((OLD/previous['inputs'][case_key]['path']).relative_to(ROOT))
        parent=next(t for t in parents['tasks'] if t['identity']==key)
        parent_path=PARENT/parents['inputs'][parent['input_key']]['path'];record=read(parent_path)
        if record['projection']['input_binding']!=bundle['future']['bound']['conditioning']['input_binding']:
            raise ValueError('training/source conditioning identity mismatch')
        conditioning_key='conditioning-'+key;inputs[conditioning_key]=str(parent_path.relative_to(ROOT))
        tasks.append(dict(identity='rounded-'+key,input_key=key,payload=dict(case_key=case_key,
            conditioning_key=conditioning_key,compiler=compiler,prefixes=PREFIXES,maximum_seconds=120.,
            limits=dict(setups=1,source_steps=3200,exact_supports=6,body_bounds=20,truth_checks=240)),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=3200)))
    if len(tasks)!=6 or groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('complete source matrix required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        envelope=runner._load(DATA/item['artifact']);artifacts=envelope['artifacts'];row=envelope['result']
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        bundle=read(DATA/manifest['inputs'][task['input_key']]['path']);old=bundle['result']
        rows.append(dict(row,identity=task['identity'],model=old['model'],profile=old['profile']))
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in artifacts if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):raise ValueError('invalid reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('source reservation changed')
        if 'work' in row and row['work']!=counts:raise ValueError('source work and reservations differ')
        if row.get('passed'):
            if (counts!=limits or row.get('body_bounds')!=20 or row.get('truth_checks')!=240
                    or row.get('source_steps')!=3200 or not row.get('known_calibration_read_after_sealed_bounds')
                    or not row.get('stated_centers_and_rows_unchanged')):
                raise ValueError('passing rounded source has incomplete evidence')
            sealed=next(name for name in artifacts if Path(name).name=='bounds-sealed.json')
            record=runner._load(DATA/sealed)
            if record['count']!=20 or record['known_calibration_inspected']:
                raise ValueError('known-calibration ordering evidence changed')
        for name in artifacts:
            if row.get('passed') and Path(name).name=='initial-source-bridge.json' and not runner._load(DATA/name)['nonlinear_cap_sufficient']:
                raise ValueError('insufficient common-source cap cannot be published as qualified')
            if Path(name).name=='compilation.json':
                compilation=runner._load(DATA/name)
                if compilation['arithmetic']['source_sha256']!=manifest['sources']['analysis/lll/ilvis0_compiled_bounds.cpp']:
                    raise ValueError('compiled arithmetic source differs from freeze')
                for source,digest in compilation['source']['sources'].items():
                    if digest!=manifest['sources']['analysis/lll/'+source]:raise ValueError('compiled source-reference input changed')
        accounts.append(dict(identity=task['identity'],**counts,passed=row.get('passed',False)))
    text=['# Rounded source bounds with saved training constraints','',
        f"**{sum(row.get('passed',False) for row in rows)}/6 generated-source comparisons passed.**",'',
        '| Candidate / removal | Result | Body bounds | Known-calibration checks |',
        '|---|---|---:|---:|']
    for row in rows:
        label=('Globe with specified field','Globe with zero field','Flat disc')[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        result='Passed' if row.get('passed') else row.get('reason','Failed')
        text.append(f"| {label} | {result} | {row.get('body_bounds',0)} | {row.get('truth_checks',0)} |")
    text+=['',f"Charged {summary['charged']['bound_calls']}/6 complete physical bounds and {summary['charged']['bound_steps']}/19,200 "
        f"bound steps. Reserved {sum(a['source_steps'] for a in accounts):,}/19,200 compiled source steps, "
        f"{sum(a['exact_supports'] for a in accounts)}/36 training supports, "
        f"{sum(a['body_bounds'] for a in accounts)}/120 rounded body bounds and "
        f"{sum(a['truth_checks'] for a in accounts):,}/1,440 known-calibration comparisons. "
        f"Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The bounds retain the original training certificates, physical domains, stated centers '
        'and all 27 affine columns. The reference bridge checks the existing nonlinear cap without '
        'expanding it. Physical norm closure precedes conversion to numerical centers. '
        'Known calibrations are inspected only after all selected bounds have been sealed. '
        'Value and affine-error comparisons use no added numerical margin.','',
        'This is generated-data component qualification. It does not qualify complete native '
        'position propagation, useful prediction widths or calibrated observation-error coverage. '
        'No aircraft fit, full native trajectory, protected ESA data or optimizer was used. '
        'Earlier point failures remain preserved in their original implementation.','',
        '[Frozen scope](PLAN.md) · [Physical source qualification](../ilvis0-source-value-controls/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged'],complete=len(accounts)==6,
        full_native_trajectory_evaluations=0,optimizer_starts=0,shared_columns_changed=False))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen six rounded-source controls / 120 body bounds / 1440 truth checks.')
    elif args.package_only:publish();print('Published rounded-source qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified rounded-source qualification.')


if __name__=='__main__':main()
