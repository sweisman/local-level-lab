# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded saved-endpoint diagnosis; no originals, predictions or fitting."""
import argparse
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'data/ilvis0-remaining-free-time-v2-20261018'
PUBLISHED=ROOT/'docs/ilvis0-remaining-free-time-v2-20261018'
OUTPUT=ROOT/'data/ilvis0-remaining-free-time-audit-20261018'
GUIDE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def diagnose(row):
    names=row['active_parameters'];scaled=row['scaled_projected_gradient'];limit=row['stationarity_tolerance']
    if len(names)!=len(scaled) or names.count('time_offset')!=1:raise ValueError('compatible full stationarity vector required')
    probe=row['full_stability'];policy=row['stability_policy']
    return dict(identity=row['identity'],case_id=row['identity'].split('::')[1],start_role=row['start_role'],
        cost=row['residual_sum_squares'],time_offset_s=row['parameters']['time_offset'],
        stationarity=row['exact_projected_gradient_relative'],stationarity_limit=limit,
        failing_coordinates=[name for name,g in zip(names,scaled) if abs(g)>limit],
        probe_reason=probe['reason'],fresh_probe_stationarity=probe.get('fresh_stationarity'),
        actual_relative_cost_change=probe.get('actual_cost_change'),
        position_rms_neu_m=probe.get('position_rms_neu_m'),position_max_abs_neu_m=probe.get('position_max_abs_neu_m'),
        full_gate_passed=row['full_gate_verified'],step_count=len(row['step_history']),
        accepted_steps=sum(step['accepted'] for step in row['step_history']),
        seed_unchanged=row['normalized_parameters']==row['selected_profile']['normalized_parameters'],
        original_converged=row['converged'],position_rms_limit_m=policy['position_rms_tolerance_m'])


def render():
    summary=load(OUTPUT/'summary.json');completion=load(OUTPUT/'completion.json')
    if completion['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('saved audit changed')
    text='# Why the remaining free-time fits stopped\n\n'
    text+='Both fresh controls passed. All four target fits completed their calculations but failed the unchanged full stopping gate. '
    text+='The study used 198 of its 342 permitted native calls; it did not run out of its overall allowance. '
    text+='Primary and repeat predictions agree to roughly micrometres within each processing case, which establishes repeatability at these endpoints, not convergence.\n\n'
    text+='| Processing case / start | Endpoint stationarity | Fresh check | Nearest boundary |\n|---|---:|---|---:|\n'
    for row in summary['targets']:
        text+=f"| {row['case_id']} / {row['start_role']} | {row['stationarity']:.6g} | {row['probe_reason']} | {row['nearest_boundary_s']*1e9:.6g} ns |\n"
    text+='\nThe endpoint stationarity limit is **0.0001**. Without fitted upstream field removal, only timing exceeds that limit. '
    text+='With removal fitted, endpoint stationarity passes, but the fresh correction changes the cost too much and produces a new stationarity failure. '
    text+='Its position changes are within the existing millimetre RMS limit. The broad “position probe” failure label therefore does not mean that the position limit itself failed.\n\n'
    text+='The next useful numerical test should distinguish the two failure mechanisms. For timing-only endpoints, '
    text+='the existing source-preserving clustered-boundary checks are a candidate. For the profiled-removal endpoints, '
    text+='inspect the fresh correction direction and clock-branch crossings before choosing a correction. '
    text+='Neither diagnosis justifies a relaxed stopping rule or automatic acceptance.\n\n'
    text+='This audit reads sealed endpoints and saved observation times only. It uses no original IMU records, '
    text+='native predictions or optimizer starts. The completed trial remains frozen. Published findings remain '
    text+='**50 globe / zero flat / three unresolved**.\n\n[Source trial](../ilvis0-remaining-free-time-v2-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).\n'
    (GUIDE/'README.md').write_text(text)
    names=('manifest.json','summary.json','completion.json')
    for name in names:shutil.copyfile(OUTPUT/name,GUIDE/name)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in (*names,'README.md')},scientific_decision='abstain'))


def build():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory,mode,kind in ((OUTPUT,'a+',fcntl.LOCK_EX),(PARENT,'r',fcntl.LOCK_SH)):
            lock=stack.enter_context((directory/'worker.lock').open(mode));fcntl.flock(lock,kind|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('completed or charged audit cannot rerun; use --render-only')
        sys.path.insert(0,str(ROOT/'analysis'));sys.path.insert(0,str(ROOT/'analysis/tests'))
        from ilvis0_boundary_followup_worker import sealed
        sealed(PARENT,published=PUBLISHED)
        source=load(PARENT/'summary.json');targets=[r for r in source['results'] if r['kind']=='target']
        if len(targets)!=4 or not all(r['status']=='complete' and not r['converged'] for r in targets):
            raise ValueError('exact completed unresolved population required')
        inputs={str(PARENT/n):sha(PARENT/n) for n in ('manifest.json','summary.json','completion.json')}
        for row in targets:
            path=PARENT/row['linearization_file']
            if path.name!=row['linearization_file'] or sha(path)!=row['linearization_sha256']:raise ValueError('saved endpoint changed')
            inputs[str(path)]=sha(path)
        sources={str(p):sha(p) for p in (Path(__file__),ROOT/'analysis/lll/ilvis0_clock_brackets.py')}
        write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,maximum_endpoints=4,
            maximum_geometry_queries=4096,native_calls=0,optimizer_starts=0,original_reads=0,numerical_threads=4))
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        import numpy as np
        from lll.ilvis0_clock_brackets import bracket
        result=[]
        for row in targets:
            report=diagnose(row)
            with gzip.open(PARENT/row['linearization_file'],'rt') as stream:local=json.load(stream)
            times=np.asarray(local['times_s']);count=int(np.ceil((max(times)+.15)/.005))+2
            ends=np.cumsum(np.full(count,.005));shifted=times+report['time_offset_s'];index=np.searchsorted(ends,shifted)
            distance=np.minimum(abs(shifted-ends[index]),abs(shifted-ends[np.maximum(0,index-1)]))
            geometry=bracket(times,count,.15,row['normalized_parameters'][row['active_parameters'].index('time_offset')],maximum_queries=1024)
            report.update(nearest_boundary_s=float(min(distance)),clock_geometry=geometry);result.append(report)
        for path,h in dict(inputs,**sources).items():
            if sha(Path(path))!=h:raise ValueError('audit dependency changed')
        write(OUTPUT/'summary.json',dict(state='complete',targets=result,geometry_queries=sum(r['clock_geometry']['queries'] for r in result),
            native_calls=0,optimizer_starts=0,original_reads=0,original_labels_changed=False))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(dict(state='complete',targets=len(result),native_calls=0,geometry_queries=sum(r['clock_geometry']['queries'] for r in result))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
