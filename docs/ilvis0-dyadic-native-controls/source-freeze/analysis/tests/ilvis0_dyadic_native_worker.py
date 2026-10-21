# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish component-preserving native transport controls."""
import argparse,subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/ilvis0-dyadic-native-controls-20261021'
PUBLIC=ROOT/'docs/ilvis0-dyadic-native-controls';OLD=ROOT/'docs/ilvis0-transform-native-controls'
STATIC=ROOT/'docs/ilvis0-directional-force-controls'
ADAPTER='analysis/lll/ilvis0_dyadic_native_controls.py';PLAN='docs/ilvis0-dyadic-native-controls/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/lll/ilvis0_taylor_native.py','analysis/lll/ilvis0_compiled_relative.py','analysis/lll/ilvis0_compiled_transport.py','analysis/lll/ilvis0_component_transport.py','analysis/lll/ilvis0_component_geography.py','analysis/lll/ilvis0_component_relative.py','analysis/lll/ilvis0_directional_values.py','analysis/lll/ilvis0_directional_matrices.py','analysis/lll/ilvis0_directional_acceleration.py',
    'analysis/tests/ilvis0_dyadic_native_worker.py','analysis/tests/test_ilvis0_taylor_native.py','analysis/tests/test_ilvis0_compiled_transport.py','analysis/tests/test_ilvis0_component_transport.py','analysis/tests/test_ilvis0_conditioned_transform_native.py','analysis/tests/test_ilvis0_regrouped_history.py','analysis/tests/test_ilvis0_native_box_bounds.py',
    'analysis/tests/test_ilvis0_directional_acceleration.py','analysis/tests/ilvis0_control_shards.py','analysis/tests/run_numerical.py']


def prepare():
    if DATA.exists():raise ValueError("batched qualification already frozen")
    predecessor=ROOT/"docs/ilvis0-taylor-native-controls"
    for name,digest in runner._load(predecessor/"evidence-receipt.json")["artifacts"].items():
        if runner._sha(runner.path_within(predecessor,name))!=digest:raise ValueError("sealed predecessor changed")
    summary=runner._load(predecessor/"summary.json");previous=runner._load(predecessor/"manifest.json")
    if not summary["passed"] or previous["environment"]!=runner.runtime_environment():
        raise ValueError("passing predecessor in the unchanged environment required")
    sources=set(SOURCES)|set(previous["sources"])
    sources.update("analysis/lll/ilvis0_dyadic_"+name for name in ("source.py","body_interval.py","source_taylor.py","native.py"))
    sources.update(("analysis/tests/test_ilvis0_dyadic_source.py","analysis/tests/test_ilvis0_dyadic_native.py"))
    for name,digest in previous["sources"].items():
        if name.startswith("analysis/lll/") and runner._sha(ROOT/name)!=digest:
            raise ValueError("qualified source changed: "+name)
    for name in ("bounds.cpp","bounds.py","transport.py","relative.py","source_values.py","body_interval.py","native.py"):
        sources.add("analysis/lll/ilvis0_batched_"+name)
    sources.add("analysis/tests/test_ilvis0_batched_bounds.py")
    derivative=ROOT/"docs/ilvis0-source-derivative-v2-controls"
    for name,digest in runner._load(derivative/"evidence-receipt.json")["artifacts"].items():
        if runner._sha(runner.path_within(derivative,name))!=digest:raise ValueError("derivative qualification changed")
    if not runner._load(derivative/"summary.json")["passed"]:raise ValueError("qualified derivative component required")
    for name,digest in runner._load(derivative/"manifest.json")["sources"].items():
        if name.startswith("analysis/lll/"):
            if runner._sha(ROOT/name)!=digest:raise ValueError("derivative source changed")
            sources.add(name)
    sources.update(("analysis/lll/ilvis0_source_taylor.py","analysis/lll/ilvis0_taylor_native.py"))
    fields=("center","unshared_remainder","position_unshared_remainder","force_unshared_remainder","lever_unshared_remainder","source_derivative_steps",
        "previous_coefficients","acceleration_coefficients","transform_coefficients","previous_caps","acceleration_caps",
        "lower","upper","reference_binding","shared_binding","acceleration_binding",
        "transform_binding","source_id","source_initial_padding","rounded_source_prefixes","source_reference_steps","conditioning")
    records={row["identity"]:row for row in summary["results"]}
    compiler=subprocess.check_output(["c++","--version"],text=True).splitlines()[0]
    tasks=[];inputs={};prepared=ROOT/"data/ilvis0-dyadic-native-inputs-20261021"
    if prepared.exists():raise ValueError("matched input preparation already exists")
    for old in previous["tasks"]:
        identity="dyadic-"+old["identity"];record=previous["inputs"][old["input_key"]]
        path=predecessor/record["path"]
        if runner._sha(path)!=record["sha256"]:raise ValueError("generated input changed")
        inputs[identity]=str(path.relative_to(ROOT));artifact=runner._load(predecessor/records[old["identity"]]["artifact"])
        bounds={};ceilings={}
        for name in artifact["artifacts"]:
            if not Path(name).name.startswith("bound-"):continue
            row=runner._load(predecessor/name);index=str(int(Path(name).stem.split("-")[-1]))
            bounds[index]={key:row[key] for key in fields}
            ceilings[index]={key:row[key] for key in ("unshared_remainder","position_unshared_remainder","force_unshared_remainder","lever_unshared_remainder")}
        if len(bounds)!=old["limits"]["bound_calls"]:raise ValueError("complete matched bounds required")
        baseline_key=identity+"-baseline";path=prepared/(identity+".json")
        runner._write(path,dict(fields=fields,bounds=bounds,ceilings=ceilings));inputs[baseline_key]=str(path.relative_to(ROOT))
        limits=dict(old["limits"])
        source_limits=dict(old["payload"]["source_limits"],source_derivative_setups=limits["bound_calls"],source_derivative_steps=old["payload"]["packets"]*limits["bound_calls"])
        tasks.append(dict(identity=identity,input_key=identity,limits=limits,
            payload=dict(old["payload"],identity=identity,compiler=compiler,baseline_key=baseline_key,source_limits=source_limits)))
    totals={key:sum(task["limits"][key] for task in tasks) for key in ("native_calls","packet_visits","bound_calls","bound_steps")}
    if len(tasks)!=24 or totals!=dict(native_calls=78,packet_visits=19632,bound_calls=348,bound_steps=60288):
        raise ValueError("original finite all-model control matrix required")
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
    accounts=[]
    for item,row in zip(summary['results'],rows,strict=True):
        envelope=runner._load(DATA/item['artifact'])
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['source_limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);increase=event['increase']
            if not increase or any(k not in counts or type(v)!=int or v<1 for k,v in increase.items()):
                raise ValueError('invalid native-source reservation')
            counts={k:v+increase.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('native-source reservation changed')
        if 'work' in row and row['work']!=counts:raise ValueError('source work and reservations differ')
        for name,digest in row.get('source_derivative_compilation',{}).get('sources',{}).items():
            if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('derivative compiler input changed')
        if row.get('source_derivative_steps',0)>counts['source_derivative_steps']:raise ValueError('uncharged derivative work')
        if row.get('source_steps',0)>counts['source_steps'] or row.get('source_body_bounds',0)>counts['source_body_bounds']:
            raise ValueError('native source work lacks reservation')
        if 'arithmetic' in row:
            for name,digest in row['arithmetic']['sources'].items():
                if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('batched arithmetic source changed')
            for name,digest in row['source_compilation']['sources'].items():
                if digest!=manifest['sources']['analysis/lll/'+name]:raise ValueError('source-reference compiler input changed')
        accounts.append(dict(identity=task['identity'],**counts))
    text=['# Native propagation with exact integer source bounds','',
        f"{sum(r.get('passed',False) for r in rows)}/24 matched native controls passed.",'',
        f"Charged {summary['charged']['native_calls']} native evaluations and {summary['charged']['bound_calls']} bounds; "
        f"preserved {certificates} directional acceleration certificates. Elapsed {summary['elapsed_s']:.2f} seconds.",'',
        f"Reserved {sum(a['source_steps'] for a in accounts):,}/7,536 source-reference steps and "
        f"{sum(a['source_body_bounds'] for a in accounts):,}/7,536 rounded body bounds separately from full native evaluations.",'',
        'Every successful bound preserves the sealed predecessor prediction, three coefficient matrices, physical bindings and all four remainder arrays exactly. '
        'The control matrix retains the original center, stationary-pose, derivative '
        'and nonlinear-containment criteria for all three candidates and both '
        'processing assumptions. Every physical and shared-error column remains. '
        'The original acceleration remainder and shared-error caps are preserved; compiled primitive arithmetic rounds outward and includes center-operation error. '
        'coordinate bounds now survive force, velocity and geographic extraction. The qualified rounded source interval is installed at each actual midpoint; later force differences and the original numerical centers are retained.','',
        'These controls qualify the native component on generated inputs. They do '
        'not establish useful full-recording prediction ranges, floating-execution '
        'enclosure or calibrated observation-error coverage. No aircraft observation '
        'was fitted, and no protected ESA data was used.','',
        '[Frozen scope](PLAN.md) · [Source reference](../ilvis0-source-reference/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'accounting.json',dict(charged=summary['charged'],directional_certificates=certificates,
        registered_identities=24,complete=len(rows)==24,source_reservations=accounts,
        source_steps_reserved=sum(a['source_steps'] for a in accounts),
        source_body_bounds_reserved=sum(a['source_body_bounds'] for a in accounts),optimizer_starts=0,original_reads=0))
    receipt=runner._load(PUBLIC/'evidence-receipt.json');receipt['artifacts']['accounting.json']=runner._sha(PUBLIC/'accounting.json')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 24 matched native controls / 78 native calls / 348 bounds / 60288 bound steps.')
    elif args.package_only:publish();print('Published native directional qualification.')
    else:publication.check(DATA,PUBLIC);print('Verified compiled transport evidence.')


if __name__=='__main__':main()
