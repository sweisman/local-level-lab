# SPDX-License-Identifier: AGPL-3.0-or-later
"""Once-charged saved-clock screen; no native predictions or observed fits."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data/ilvis0-boundary-adapter-preparation-20261016'
PARENT=ROOT/'docs/ilvis0-stopping-audit-20261016'
QUALIFIED=ROOT/'docs/ilvis0-boundary-stop-qualification-20261016'


def load(path):return json.loads(path.read_text())


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def seal(directory,artifact,key):
    c=load(directory/'completion.json')
    if c['manifest_sha256']!=sha(directory/'manifest.json') or c[key]!=sha(directory/artifact):
        raise ValueError('sealed dependency mismatch')
    r=load(directory/'evidence-receipt.json')
    if any(Path(n).name!=n or sha(directory/n)!=h for n,h in r['artifacts'].items()):raise ValueError('publication hash mismatch')


def prepare(clock,runtime):
    seal(PARENT,'diagnosis.json','diagnosis_sha256');seal(QUALIFIED,'result.json','result_sha256')
    q=load(QUALIFIED/'result.json')
    if not q['passed'] or q['tests']!=43 or q['failures'] or q['errors']:raise ValueError('complete gate qualification required')
    prior=load(PARENT/'manifest.json');sources=dict(load(QUALIFIED/'manifest.json')['sources'])
    for path in (Path(__file__),Path(clock.__file__),ROOT/'analysis/tests/test_ilvis0_clock_brackets.py',ROOT/'analysis/tests/ilvis0_clock_reference.cpp'):
        sources[str(path.resolve())]=sha(path)
    inputs=dict(prior['inputs'])
    for directory,names in ((PARENT,('manifest.json','diagnosis.json','completion.json','evidence-receipt.json')),
                            (QUALIFIED,('manifest.json','result.json','completion.json','evidence-receipt.json')),
                            (HERE,('PLAN.md',))):
        for name in names:inputs[str(directory/name)]=sha(directory/name)
    if len(prior['tasks'])!=22 or len({t['task']['segment_id'] for t in prior['tasks']})!=6:
        raise ValueError('fixed six-stretch population required')
    snapshots={n:str(Path(n).relative_to(ROOT)) for n in sources}
    for name,digest in sources.items():
        if sha(Path(name))!=digest:raise ValueError('source mismatch')
        target=OUTPUT/'source-freeze'/snapshots[name];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(name,target)
    value=dict(version=clock.VERSION,tasks=prior['tasks'],sources=sources,source_snapshots=snapshots,inputs=inputs,
        environment=runtime.numerical_environment(),maximum_endpoints=22,maximum_clock_queries=22528,
        maximum_queries_per_endpoint=1024,numerical_threads=4,retries=0,native_predictions=0,observed_fit_starts=0,original_files_read=0)
    atomic(OUTPUT/'manifest.json',value);return value


def verify(manifest,runtime):
    for group in ('inputs','sources'):
        for name,digest in manifest[group].items():
            if sha(Path(name))!=digest:raise ValueError('frozen source/input mismatch')
    for name,digest in manifest['sources'].items():
        if sha(OUTPUT/'source-freeze'/manifest['source_snapshots'][name])!=digest:raise ValueError('source snapshot mismatch')
    runtime.check_environment(manifest['environment'])


def render(summary):
    text='# Clock geometry for the remaining six stretches\n\n'
    text+='This saved-only screen checks whether the two-sided policy can obtain the correct adjacent '
    text+='packet intervals. **No original recordings, native predictions or observed fits.** '
    text+='Supported geometry does not establish convergence or change any disposition.\n\n'
    text+='| Stretch | Failed primary checks with supported geometry | Failed repeat checks with supported geometry | Passing smooth repeats farther than 1 µs from proposed knot |\n'
    text+='|---|---:|---:|---:|\n'
    for sid in sorted({r['segment_id'] for r in summary['results']}):
        rows=[r for r in summary['results'] if r['segment_id']==sid]
        p=[r for r in rows if r['role']=='primary'];f=[r for r in rows if r['role']=='repeat' and not r['original_converged']]
        smooth=sum(r['role']=='repeat' and r['original_converged'] and abs(r.get('geometry',{}).get('center_relocation_s',0))>1e-6 for r in rows)
        count=lambda group:sum(r.get('geometry',{}).get('side_geometry_supported',False) for r in group)
        text+=f"| `{sid}` | {count(p)}/{len(p)} | {count(f)}/{len(f)} | {smooth} |\n"
    text+='\n[All endpoint geometry](endpoints.csv) · [Preserved clock calculations](summary.json) · '
    text+='[Two-sided software qualification](../ilvis0-boundary-stop-qualification-20261016/RESULTS.md).\n\n'
    text+='Each proposed boundary relocation is recorded. Close transitions are retained separately; '
    text+='a side sample that cannot be placed reliably must abstain. Native integration, continuity '
    text+='and nuisance-correction checks still need separate finite validation. Passing repeats at '
    text+='different smooth endpoints require timing-profile investigation; they are not replaced by '
    text+='a newly proposed boundary. The current tally remains **47 globe / 0 flat / 6 unresolved**.\n'
    (HERE/'README.md').write_text(text)
    fields=['segment_id','identity','filename','role','original_converged','status','side_geometry_supported',
            'center_relocation_s','left_interval_width_s','right_interval_width_s','minimum_side_probe_s',
            'boundary_changed_epochs','queries','error']
    with (HERE/'endpoints.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for r in summary['results']:
            row={k:r.get(k,'') for k in fields};row.update({k:r['geometry'][k] for k in fields if k in r.get('geometry',{})});writer.writerow(row)
    names=('manifest.json','summary.json','start.json','completion.json')
    for name in names:shutil.copyfile(OUTPUT/name,HERE/name)
    shutil.copytree(OUTPUT/'source-freeze',HERE/'source-freeze',dirs_exist_ok=True)
    atomic(HERE/'evidence-receipt.json',dict(artifacts={n:sha(HERE/n) for n in (*names,'README.md','endpoints.csv')},
        native_predictions=0,observed_fit_starts=0,original_files_read=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.render_only or (OUTPUT/'completion.json').exists():
            c=load(OUTPUT/'completion.json')
            if c['manifest_sha256']!=sha(OUTPUT/'manifest.json') or c['summary_sha256']!=sha(OUTPUT/'summary.json'):
                raise ValueError('completed screen mismatch')
            render(load(OUTPUT/'summary.json'));return
        if (OUTPUT/'start.json').exists():raise ValueError('charged screen cannot restart')
        sys.path.insert(0,str(ROOT/'analysis'))
        from lll.compute_budget import environment
        os.environ.update(environment(workers=1,threads=4,reserved=0))
        from lll import ilvis0_clock_brackets as clock,runtime
        manifest=prepare(clock,runtime);verify(manifest,runtime)
        atomic(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json'),maximum_clock_queries=22528))
        results=[]
        for t in manifest['tasks']:
            fit=t['fit'];row=dict(identity=t['identity'],segment_id=t['task']['segment_id'],filename=t['stretch']['filename'],
                                  role=t['identity'].split('::')[-1],original_converged=fit['converged'])
            try:
                path=ROOT/'docs'/t['stage']/fit['epoch_file']
                with gzip.open(path,'rt') as stream:epochs=json.load(stream)
                point=fit['normalized_parameters'][fit['active_parameters'].index('time_offset')]
                geometry=clock.bracket(epochs['times_s'],t['task']['provenance']['native_packets'],t['time_scale_s'],point)
                row.update(status='complete',geometry=geometry,queries_charged=geometry['queries'])
            except Exception as error:row.update(status='error',error=type(error).__name__+': '+str(error),queries_charged=1024)
            results.append(row)
        verify(manifest,runtime)
        charged=sum(r['queries_charged'] for r in results)
        if charged>22528:raise ValueError('finite clock allowance exceeded')
        summary=dict(state='complete',results=results,clock_queries_charged=charged,
            native_predictions=0,observed_fit_starts=0,original_files_read=0,original_labels_changed=False)
        atomic(OUTPUT/'summary.json',summary)
        atomic(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render(summary)
        print(json.dumps(dict(endpoints=len(results),clock_queries=charged,
            supported_geometry=sum(r.get('geometry',{}).get('side_geometry_supported',False) for r in results),
            errors=sum(r['status']=='error' for r in results),native_predictions=0,observed_fit_starts=0)))


if __name__=='__main__':main()
