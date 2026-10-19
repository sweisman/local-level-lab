#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of the two left-boundary failures; no numerical imports."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'docs/ilvis0-profile-boundary-20261017'
OUTPUT=ROOT/'data/ilvis0-left-boundary-audit-20261017'
GUIDE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded


def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):durable_write(p,encoded(value),replace=True)


def render():
    c=load(OUTPUT/'completion.json')
    if c['summary_sha256']!=sha(OUTPUT/'summary.json'):raise ValueError('audit changed')
    s=load(OUTPUT/'summary.json')
    text='# The left-side failures\n\n'
    text+='Both preserved endpoints fail in the same way: the left branch reaches an unchecked neighboring packet boundary. '
    text+='Its cost and position changes pass the existing stability limits, but its aggregate stationarity check remains above the limit. '
    text+='The continuation guard therefore stops before checking both sides of that neighbor. The right branch passes.\n\n'
    text+='| Source | Left stationarity | Limit | Cost change | Neighbor spacing (ps) |\n|---|---:|---:|---:|---:|\n'
    for r in s['targets']:text+=f"| {r['source']} | {r['stationarity']:.9g} | {r['limit']} | {r['relative_cost_change']:.6g} | {r['spacing_s']*1e12:.6g} |\n"
    text+='\nThe saved branch reports contain aggregate gradient measures, so they do not establish which coordinate dominates every fresh left-side probe. '
    text+='They do establish that the current boundary has not passed its final stopping test. '
    text+='These failures must not be relabeled.\n\n'
    text+='The existing complete-cluster search can instead look for a negative-to-positive timing slope change across the nearby packet boundaries, '
    text+='then apply the unchanged final two-sided gate at the selected knot. This avoids relaxing stationarity to cross an unchecked neighbor. '
    text+='Any observed test requires a separate finite freeze, source-to-final movement checks and both source endpoints.\n\n'
    text+='This audit checked two saved target reports and their sealed publication receipt. It made zero native calls, '
    text+='read no original measurements, performed no fits and changed no labels. Findings remain 49 globe / zero flat / four unresolved.\n'
    (GUIDE/'README.md').write_text(text)
    for n in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/n,GUIDE/n)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in ('manifest.json','summary.json','completion.json','README.md')}))


def build():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'start.json').exists():raise ValueError('saved audit cannot rerun; use --render-only')
    receipt=load(PARENT/'evidence-receipt.json')
    for name,h in receipt['artifacts'].items():
        if '..' in Path(name).parts or Path(name).is_absolute() or sha(PARENT/name)!=h:raise ValueError('parent evidence changed')
    complete=load(PARENT/'completion.json')
    if complete['summary_sha256']!=sha(PARENT/'summary.json') or complete['manifest_sha256']!=sha(PARENT/'manifest.json'):
        raise ValueError('parent completion changed')
    paths=[PARENT/n for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json')]
    inputs={str(p):sha(p) for p in paths}
    write(OUTPUT/'manifest.json',dict(inputs=inputs,source_sha256=sha(Path(__file__)),maximum_target_reports=2,
        native_predictions=0,optimizer_starts=0,original_reads=0,numerical_threads=0))
    write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
    targets=[]
    for r in load(PARENT/'summary.json')['results']:
        if r['kind']!='target':continue
        check=r['checks'][0];left,right=check['branches']
        if (r['passed'] or r['reason']!='nonedge_failure_preserved' or left['side']!='left'
                or left['reason']!='unchecked_neighbor_boundary' or right['side']!='right' or not right['passed']):
            raise ValueError('unexpected saved failure pattern')
        p=check['policy']
        movement=left['relative_cost_change']<=p['relative_cost_tolerance'] and all(
            x<=p['position_rms_tolerance_m'] for x in left['position_rms']) and all(
            x<=p['position_max_tolerance_m'] for x in left['position_maximum'])
        targets.append(dict(source=r['source_role'],stationarity=max(left['side_stationarity']+[left['fresh_stationarity']]),
            limit=p['stationarity_tolerance'],relative_cost_change=left['relative_cost_change'],movement_passed=movement,
            spacing_s=r['geometries'][0]['left_interval_width_s']))
    if len(targets)!=2 or not all(r['movement_passed'] for r in targets):raise ValueError('two stable but nonstationary left branches required')
    for path,h in inputs.items():
        if sha(Path(path))!=h:raise ValueError('audit input changed')
    write(OUTPUT/'summary.json',dict(state='complete',targets=targets,native_predictions=0,optimizer_starts=0,original_labels_changed=False))
    write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),summary_sha256=sha(OUTPUT/'summary.json')))
    freeze=OUTPUT/'source-freeze';freeze.mkdir();shutil.copyfile(__file__,freeze/'build_report.py')
    shutil.copytree(freeze,GUIDE/'source-freeze',dirs_exist_ok=True)
    render();print(json.dumps(dict(targets=len(targets),native_predictions=0,optimizer_starts=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
