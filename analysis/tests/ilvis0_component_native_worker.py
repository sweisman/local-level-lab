# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish component-preserving native transport controls."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-component-transport-controls-20261020'
PUBLIC=ROOT/'docs/ilvis0-component-transport-controls';OLD=ROOT/'docs/ilvis0-transform-native-controls'
STATIC=ROOT/'docs/ilvis0-directional-force-controls'
ADAPTER='analysis/lll/ilvis0_component_native_controls.py';PLAN='docs/ilvis0-component-transport-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_component_native.py','analysis/lll/ilvis0_component_transport.py','analysis/lll/ilvis0_component_geography.py','analysis/lll/ilvis0_component_relative.py','analysis/lll/ilvis0_directional_values.py','analysis/lll/ilvis0_directional_matrices.py','analysis/lll/ilvis0_directional_acceleration.py',
    'analysis/tests/ilvis0_component_native_worker.py','analysis/tests/test_ilvis0_component_native.py','analysis/tests/test_ilvis0_component_transport.py','analysis/tests/test_ilvis0_conditioned_transform_native.py','analysis/tests/test_ilvis0_regrouped_history.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/test_ilvis0_directional_acceleration.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError('component transport qualification already frozen')
    sources=set(SOURCES)
    for directory in (OLD,STATIC,ROOT/'docs/ilvis0-source-reference'):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(runner.path_within(directory,name))!=digest:raise ValueError('sealed prerequisite changed')
        if not runner._load(directory/'summary.json')['passed']:raise ValueError('passing prerequisites required')
        manifest=runner._load(directory/'manifest.json')
        if manifest['environment']!=runner.runtime_environment():raise ValueError('numerical environment changed')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
                sources.add(name)
    previous=runner._load(OLD/'manifest.json');compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
    tasks=[];inputs={}
    for old in previous['tasks']:
        identity='component-'+old['identity'];record=previous['inputs'][old['input_key']];path=OLD/record['path']
        if runner._sha(path)!=record['sha256']:raise ValueError('matched native input changed')
        inputs[identity]=str(path.relative_to(ROOT));limits=dict(old['limits']);limits['bound_steps']*=2
        tasks.append(dict(identity=identity,input_key=identity,
            payload=dict(old['payload'],identity=identity,compiler=compiler),limits=limits))
    totals={k:sum(t['limits'][k] for t in tasks) for k in ('native_calls','packet_visits','bound_calls','bound_steps')}
    if len(tasks)!=24 or totals!=dict(native_calls=78,packet_visits=19632,bound_calls=348,bound_steps=15072):
        raise ValueError('original finite control matrix and corrected two-pass bound ceiling required')
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=runner.runtime_environment())


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    rows=[runner._load(DATA/r['artifact'])['result'] for r in summary['results']]
    certificates=0
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=record['result']
        found=[name for name in record['artifacts'] if Path(name).name.startswith('component-source-')]
        if 'bound_evaluations' in row and len(found)!=row['bound_evaluations']:
            raise ValueError('component proof artifacts and bound count disagree')
        certificates+=len(found)
    text=['# Coordinate-preserving native propagation','',
        f"{sum(r.get('passed',False) for r in rows)}/24 matched native controls passed.",'',
        f"Charged {summary['charged']['native_calls']} native evaluations and {summary['charged']['bound_calls']} bounds; "
        f"preserved {certificates} directional acceleration certificates. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        'The control matrix retains the original center, stationary-pose, derivative '
        'and nonlinear-containment criteria for all three candidates and both '
        'processing assumptions. Every physical and shared-error column remains. '
        'The original acceleration remainder and shared-error caps are preserved; '
        'coordinate bounds now survive force, velocity and geographic extraction. The new norm-constrained source interval is not installed yet.','',
        'These controls qualify the native component on generated inputs. They do '
        'not establish useful full-recording prediction ranges, floating-execution '
        'enclosure or calibrated observation-error coverage. No aircraft observation '
        'was fitted, and no protected ESA data was used.','',
        '[Frozen scope](PLAN.md) · [Source reference](../ilvis0-source-reference/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(charged=summary['charged'],directional_certificates=certificates,
        registered_identities=24,complete=len(rows)==24,optimizer_starts=0,original_reads=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 matched native controls / 78 native calls / 348 bounds / 15072 bound steps.')
    elif args.package_only:publish();print('Published native directional qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified component transport evidence.')


if __name__=='__main__':main()
