# SPDX-License-Identifier: AGPL-3.0-or-later
"""Twelve saved-clock queries; no native calls, original reads or fits."""
import argparse
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'data/ilvis0-remaining-boundary-20261018'
PUBLIC=ROOT/'docs/ilvis0-remaining-boundary-20261018'
OUTPUT=ROOT/'data/ilvis0-narrow-boundary-audit-20261018'
GUIDE=Path(__file__).resolve().parent


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def render():
    s=load(OUTPUT/'summary.json');c=load(OUTPUT/'completion.json')
    if c['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('saved audit changed')
    text='# The narrow timing branches\n\n'
    text+='The completed boundary study passed both controls and both profiled-removal endpoints, including their repeat comparison. '
    text+='Both unsubtracted endpoints stopped before native side checks because their final timing branches were below the fixed minimum probe spacing. '
    text+='This is a numerical qualification failure, not evidence in favor of either surface model.\n\n'
    text+='| Endpoint | Left width | Right width | Smallest probe | Probe distance in parameter ULPs | Clock states match |\n|---|---:|---:|---:|---:|---|\n'
    for r in s['targets']:
        text+=f"| {r['source']} | {r['left_width_s']*1e15:.6g} fs | {r['right_width_s']*1e15:.6g} fs | {r['minimum_probe_s']*1e15:.6g} fs | {min(r['probe_ulps']):.6g} | {all(r['clock_state_matches'])} |\n"
    text+='\nAn ULP is the spacing between adjacent representable floating-point numbers. '
    text+=f"The fixed guard requires at least {s['minimum_probe_guard_s']*1e15:.6g} femtoseconds here. "
    if all(all(r['clock_state_matches']) and r['probes_distinct'] for r in s['targets']):
        text+='All saved side points are distinct representable values and reproduce their intended clock states. '
        text+='That supports qualifying a separate representability-aware probe check, rather than using a fixed normalized spacing for every timing value. '
    else:
        text+='At least one saved probe does not establish the intended distinct clock state. Any replacement must diagnose that failure explicitly. '
    text+='The original failed checks remain failed. Correct clock-state geometry alone does not prove that native side derivatives, continuity or nuisance corrections pass.\n\n'
    text+='A revised candidate must demonstrate independent known-answer behavior on narrow minima, maxima, discontinuities, '
    text+='unrepresentable branches and nuisance failures before a fresh finite observed-data test. '
    text+='Keep stationarity, cost, physical-position, source-preservation and repeat limits unchanged. '
    text+='Do not simply turn off the minimum-spacing guard.\n\n'
    text+='This audit uses two saved endpoint artifacts and twelve clock-state queries. It performs zero native calls or fits, '
    text+='reads no original IMU data and changes no labels. Findings remain **50 globe / zero flat / three unresolved**.\n\n'
    text+='[Completed boundary study](../ilvis0-remaining-boundary-20261018/RESULTS.md) · [Next analyses](../NEXT_STEPS.md).\n'
    (GUIDE/'README.md').write_text(text)
    for name in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/name,GUIDE/name)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in ('manifest.json','summary.json','completion.json','README.md')},scientific_decision='abstain'))


def build():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory,mode,kind in ((OUTPUT,'a+',fcntl.LOCK_EX),(PARENT,'r',fcntl.LOCK_SH)):
            lock=stack.enter_context((directory/'worker.lock').open(mode));fcntl.flock(lock,kind|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot rerun; use --render-only')
        sys.path.insert(0,str(ROOT/'analysis'));sys.path.insert(0,str(ROOT/'analysis/tests'))
        from ilvis0_boundary_followup_worker import sealed
        sealed(PARENT,published=PUBLIC)
        source=load(PARENT/'summary.json');targets=[r for r in source['results'] if r['kind']=='target' and not r['passed']]
        if len(targets)!=2 or any(r['reason']!='side_geometry_unsupported' or not r['search']['passed'] for r in targets):
            raise ValueError('exact two saved narrow-geometry failures required')
        inputs={str(PARENT/n):sha(PARENT/n) for n in ('manifest.json','summary.json','completion.json')}
        for row in targets:
            path=PARENT/row['linearization_file']
            if path.name!=row['linearization_file'] or sha(path)!=row['linearization_sha256']:raise ValueError('saved endpoint changed')
            inputs[str(path)]=sha(path)
        sources={str(p):sha(p) for p in (Path(__file__),ROOT/'analysis/lll/ilvis0_clock_brackets.py')}
        write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,maximum_target_reports=2,maximum_clock_queries=12,
            native_calls=0,optimizer_starts=0,original_reads=0,numerical_threads=4))
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        import numpy as np
        from lll.ilvis0_clock_brackets import indices
        reports=[];queries=0;scale=.15;minimum=64*np.finfo(float).eps
        for row in targets:
            with gzip.open(PARENT/row['linearization_file'],'rt') as stream:local=json.load(stream)
            times=np.asarray(local['times_s']);count=int(np.ceil((max(times)+scale)/.005))+2
            ends=np.cumsum(np.full(count,.005));g=row['geometry'];knot=g['point'];points=g['side_points']
            before=indices(ends,times,scale,math.nextafter(knot,-math.inf));at=indices(ends,times,scale,knot);queries+=2
            matches=[]
            for i,point in enumerate(points):
                actual=indices(ends,times,scale,point);queries+=1
                matches.append(bool(np.array_equal(actual,before if i<2 else at)))
            reports.append(dict(source=row['source_role'],identity=row['identity'],knot_normalized=knot,
                left_width_s=g['left_interval_width_s'],right_width_s=g['right_interval_width_s'],
                minimum_probe_s=g['minimum_side_probe_s'],probe_guard_passed=g['minimum_side_probe_s']/scale>=minimum,
                probes_distinct=len(set(points+[knot]))==5,
                probe_ulps=[abs(p-knot)/math.ulp(knot) for p in points],clock_state_matches=matches,
                adjacent_clock_states_distinct=not np.array_equal(before,at),original_passed=row['passed']))
        if queries!=12:raise ValueError('fixed geometry-query accounting changed')
        for path,h in dict(inputs,**sources).items():
            if sha(Path(path))!=h:raise ValueError('audit input changed')
        write(OUTPUT/'summary.json',dict(state='complete',targets=reports,clock_queries=queries,
            minimum_probe_guard_s=minimum*scale,native_calls=0,optimizer_starts=0,original_reads=0,original_labels_changed=False))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(dict(targets=2,clock_queries=queries,clock_states_match=all(all(r['clock_state_matches']) for r in reports),native_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
