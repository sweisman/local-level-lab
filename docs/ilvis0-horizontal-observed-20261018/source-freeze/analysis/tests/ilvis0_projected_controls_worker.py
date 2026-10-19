# SPDX-License-Identifier: AGPL-3.0-or-later
"""One sealed generated-motion qualification batch; never fits recorded flights."""
import argparse
import fcntl
import hashlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment as compute_environment
from lll.ilvis0_receipt_journal import durable_write,encoded

OUTPUT=ROOT/'data/ilvis0-projected-fitting-controls-20261018'
GUIDE=ROOT/'docs'/OUTPUT.name
TEST='analysis/tests/qualify_ilvis0_projected_fitting.py'
EXPECTED_TESTS=43
LIMITS=dict(maximum_batches=1,maximum_generated_starts=24,maximum_native_sweeps=2400,
    maximum_tangents_per_fit=80,maximum_extra_values_per_fit=2,maximum_wall_s=600,
    numerical_threads=4,observed_starts=0,original_recording_reads=0,retries=0)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def write(path,value):durable_write(path,encoded(value),replace=True)


def environment():
    return dict(python=platform.python_version(),numpy=importlib.metadata.version('numpy'),
        scipy=importlib.metadata.version('scipy'),pytest=importlib.metadata.version('pytest'))


def sources():
    names=[TEST,'analysis/tests/ilvis0_projected_controls_worker.py','analysis/tests/run_numerical.py',
        'analysis/tests/conftest.py','analysis/tests/public_fixtures.py']
    names.extend('analysis/lll/'+name for name in ('ilvis0_projected_fitting.py',
        'ilvis0_observation_projection.py','ilvis0_geographic_controls.py','ilvis0_shape.py','ilvis0_precision.py',
        'ilvis0_exploratory.py','ilvis0_estimator.py','ilvis0_forward.py','models.py',
        'ilvis0_solver_position.py','ilvis0_solver_boundary.py','ilvis0_solver_verified_stop.py',
        'ilvis0_solver_refinement.py','compute_budget.py','ilvis0_receipt_journal.py',
        'ilvis0_tangent.cpp','ilvis0_native.c'))
    return {name:sha(ROOT/name) for name in names}


def verify():
    manifest=load(OUTPUT/'manifest.json')
    if manifest['environment']!=environment() or manifest['limits']!=LIMITS:
        raise ValueError('qualification environment or finite allowance changed')
    if load(OUTPUT/'authorization.json')!=dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS):
        raise ValueError('qualification authorization changed')
    for name,digest in manifest['sources'].items():
        if sha(ROOT/name)!=digest or sha(OUTPUT/'source-freeze'/name)!=digest:
            raise ValueError('qualification source changed: '+name)
    if sha(GUIDE/'PLAN.md')!=manifest['plan_sha256']:raise ValueError('qualification plan changed')
    return manifest


def prepare():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if (OUTPUT/'manifest.json').exists():return verify()
    command=[sys.executable,'-m','pytest',TEST,'--collect-only','-q']
    collected=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True,timeout=30)
    identities=[line.strip() for line in collected.stdout.splitlines() if line.startswith('tests/') or line.startswith('analysis/tests/')]
    if len(identities)!=EXPECTED_TESTS or len(set(identities))!=EXPECTED_TESTS:
        raise ValueError('exact qualification test collection required: '+str(len(identities)))
    values=sources()
    manifest=dict(version='ilvis0-projected-fitting-qualification-v1',environment=environment(),
        limits=LIMITS,tests=identities,sources=values,plan_sha256=sha(GUIDE/'PLAN.md'),
        generated_fit_identities=[dict(model=m,clock=c,coordinates=a,start=s) for m,c,a,s in
            itertools.product(('sphere_rotating','sphere_still','flat_still'),('nominal','variable'),
                              ('horizontal','height'),('zero','opposed'))])
    for name in values:
        target=OUTPUT/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target)
    write(OUTPUT/'manifest.json',manifest)
    write(OUTPUT/'authorization.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),**LIMITS))
    return verify()


def run():
    prepare()
    with (OUTPUT/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists() or (OUTPUT/'completion.json').exists():
            raise ValueError('charged qualification batch cannot restart')
        manifest=verify();start=time.monotonic()
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),pid=os.getpid()))
        write(OUTPUT/'status.json',dict(state='running',pid=os.getpid(),numerical_threads=4))
        command=[sys.executable,'-m','pytest',TEST,'-q','-x','--tb=short','-o','junit_family=xunit1',
                 '--junitxml='+str(OUTPUT/'tests.xml')]
        timeout=False
        with (OUTPUT/'pytest.log').open('w') as stream:
            try:
                result=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                                      timeout=LIMITS['maximum_wall_s'])
                exit_code=result.returncode
            except subprocess.TimeoutExpired:
                timeout=True;exit_code=124
        records=[];controls=[];budget=None;native_metadata=[]
        if (OUTPUT/'tests.xml').exists():
            tree=ET.parse(OUTPUT/'tests.xml')
            native_metadata=[json.loads(p.attrib['value']) for p in tree.findall('.//testsuite/properties/property') if p.attrib['name']=='native']
            totals=[json.loads(p.attrib['value']) for p in tree.findall('.//testsuite/properties/property') if p.attrib['name']=='budget']
            if totals:budget=totals[-1]
            for node in tree.iter('testcase'):
                outcome=next((t for t in ('failure','error','skipped') if node.find(t) is not None),'passed')
                records.append(dict(name=node.attrib['name'],outcome=outcome,elapsed_s=float(node.attrib.get('time',0))))
                for prop in node.findall('properties/property'):
                    if prop.attrib['name']=='control':controls.append(dict(json.loads(prop.attrib['value']),test_passed=outcome=='passed'))
                    if prop.attrib['name']=='budget':budget=json.loads(prop.attrib['value'])
        verify()
        expected_names={name.split('::')[-1] for name in manifest['tests']}
        exact_tests=len(records)==len({r['name'] for r in records})==EXPECTED_TESTS and {r['name'] for r in records}==expected_names
        passed=bool(not timeout and exit_code==0 and exact_tests
            and all(r['outcome']=='passed' for r in records) and len(controls)==24
            and budget and budget['starts']==24 and budget['native_sweeps']<=2400)
        summary=dict(state='complete',passed=passed,tests=records,controls=controls,budget=budget,native_metadata=native_metadata,
            planned_tests=EXPECTED_TESTS,unrun_tests=sorted(expected_names-{r['name'] for r in records}),
            exit_code=exit_code,timeout=timeout,elapsed_s=time.monotonic()-start,
            observed_starts=0,original_recording_reads=0,scientific_decision='abstain',
            archival_stability_qualified=False)
        write(OUTPUT/'summary.json',summary)
        write(OUTPUT/'completion.json',dict(state='complete',passed=passed,
            manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',numerical_threads=0,passed=passed,
            results=len(records),errors=sum(r['outcome']!='passed' for r in records)))
    publish()
    print(json.dumps(dict(passed=passed,tests=len(records),budget=budget)))


def publish():
    complete=load(OUTPUT/'completion.json');summary=load(OUTPUT/'summary.json')
    if (complete['manifest_sha256']!=sha(OUTPUT/'manifest.json')
            or complete['summary_sha256']!=sha(OUTPUT/'summary.json')):
        raise ValueError('completion receipt mismatch')
    GUIDE.mkdir(exist_ok=True)
    for name in ('manifest.json','authorization.json','summary.json','completion.json','start.json','tests.xml','pytest.log'):
        if (OUTPUT/name).exists():shutil.copy2(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    rows=summary['tests'];controls=summary['controls'];budget=summary['budget']
    text='# Generated-motion receiver refitting controls\n\n'
    text+=f"**{'Passed' if summary['passed'] else 'Not qualified'}:** {sum(r['outcome']=='passed' for r in rows)}/{len(rows)} controls passed. "
    text+='No archival recording was read and no observed-data fit was started.\n\n'
    text+=f"The batch stops at its first failed control. {len(summary['unrun_tests'])} planned controls were not run; they are neither passes nor measured failures.\n\n"
    if budget:text+=f"The batch used {budget['starts']} generated-motion starts and {budget['native_sweeps']} native sweeps within its frozen 24-start / 2,400-sweep allowance.\n\n"
    text+='| Model | Clock | Scored coordinates | Start | Pass | Maximum retained error (mm) | Maximum all-axis error (m) | Rank / columns |\n|---|---|---|---|---|---:|---:|---:|\n'
    for r in controls:
        f=r['fit'];axes='/'.join(r['axes'])
        text+=f"| {r['model']} | {r['clock']} | {axes} | {r['start']} | {r['test_passed']} | {1000*r['maximum_retained_error_m']:.4g} | {r['maximum_all_axis_error_m']:.4g} | {f['numerical_rank']} / {f['columns']} |\n"
    text+='\nPass requires the fresh numerical checks, retained error below 2 mm and objective recovery against independently generated truth. '
    text+='Unscored coordinates can move substantially; their errors are shown, not treated as measured constraints. '
    text+='All parameter columns are retained. Short generated controls do not demonstrate unique calibration, empirical uncertainty or Earth-model discrimination.\n\n'
    text+='A failed batch blocks observed refits. A passing batch would qualify this interface and these cases only. Observed refits still need a separate finite freeze, matched candidates, repeats and an explicitly qualified retained-coordinate stopping policy. '
    text+='The published 53/0/0 comparisons are unchanged.\n\n[Scope and limits](PLAN.md) · [Measurement-contribution work](../ilvis0-measurement-contribution/README.md).\n'
    (GUIDE/'README.md').write_text(text)
    names=['manifest.json','authorization.json','summary.json','completion.json','start.json','tests.xml','pytest.log','README.md','PLAN.md']
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in names if (GUIDE/n).exists()}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args()
    if args.prepare_only and args.package_only:raise ValueError('one mode required')
    if args.package_only:publish();return
    os.environ.update(compute_environment(workers=1,threads=4,reserved=0))
    os.environ['PYTHONPATH']=str(ROOT/'analysis')
    if args.prepare_only:prepare()
    else:run()


if __name__=='__main__':main()
