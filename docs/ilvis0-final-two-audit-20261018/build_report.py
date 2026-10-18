# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect sealed branch outcomes without native calls, solves or original reads."""
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
GUIDE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data'/GUIDE.name
PARENT=ROOT/'docs/ilvis0-boundary-review-20261016'
TARGETS=('370cec66878c4c1cf84b4ceb','b4e44ddc0f130ecd45674c78')
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write,encoded


def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):durable_write(path,encoded(value),replace=True)


def nonnegative(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('finite nonnegative saved metric required')
    return value


def diagnose(row,names):
    if not names or len(set(names))!=len(names):raise ValueError('unique parameter layout required')
    result=dict(identity=row['identity'],original_passed=row['passed'],reason=row['reason'],branches=[],
        needs_geometry_check=row['reason']=='side_geometry_unsupported',needs_neighbor_check=False,
        needs_correction_investigation=False)
    check=row.get('boundary_check')
    if not check:return result
    p=check['policy']
    for key in ('stationarity_tolerance','relative_cost_tolerance','position_rms_tolerance_m','position_max_tolerance_m'):
        if nonnegative(p[key])==0:raise ValueError('positive scientific tolerance required')
    for b in check['branches']:
        correction=b['correction'];rms=b['position_rms'];maximum=b['position_maximum']
        if (len(correction)!=len(names) or len(rms)!=3 or len(maximum)!=3
                or len(b['side_stationarity'])!=2 or b['side'] not in ('left','right')
                or any(not math.isfinite(v) for v in correction)):
            raise ValueError('compatible finite branch arrays required')
        for value in rms+maximum+b['side_stationarity']+[b['fresh_stationarity'],b['relative_cost_change']]:nonnegative(value)
        branch=dict(side=b['side'],original_passed=b['passed'],reason=b['reason'],
            endpoint_stationarity_passed=max(b['side_stationarity'])<=p['stationarity_tolerance'],
            fresh_stationarity_passed=b['fresh_stationarity']<=p['stationarity_tolerance'],
            cost_passed=b['relative_cost_change']<=p['relative_cost_tolerance'],
            position_passed=all(v<=p['position_rms_tolerance_m'] for v in rms)
                and all(v<=p['position_max_tolerance_m'] for v in maximum),
            unchecked_neighbor=b['reason']=='unchecked_neighbor_boundary',
            side_stationarity=b['side_stationarity'],fresh_stationarity=b['fresh_stationarity'],
            relative_cost_change=b['relative_cost_change'],position_rms_m=rms,position_maximum_m=maximum,
            continuity_passed=None if b['probe_continuity'] is None else b['probe_continuity']['passed'],
            largest_corrections=[list(v) for v in sorted(zip(names,correction),key=lambda x:abs(x[1]),reverse=True)[:4]])
        result['needs_neighbor_check']|=branch['unchecked_neighbor']
        result['needs_correction_investigation']|=not all(branch[k] for k in
            ('endpoint_stationarity_passed','fresh_stationarity_passed','cost_passed','position_passed'))
        result['branches'].append(branch)
    return result


def verified(path,expected,inputs):
    if sha(path)!=expected:raise ValueError('saved evidence changed: '+str(path.relative_to(ROOT)))
    inputs[str(path.relative_to(ROOT))]=expected
    return load(path)


def select_result(identity,records):
    matches=[]
    for record in records:
        if 'result' in record:
            row=record['result']
            if row['identity']==identity:matches.append((row,record))
        elif record.get('state')=='complete':
            rows=record.get('results',[])
            if isinstance(rows,dict):rows=rows.values()
            matches.extend((row,None) for row in rows if isinstance(row,dict) and row.get('identity')==identity)
    if len(matches)!=1:raise ValueError('unique sealed diagnostic result required')
    return matches[0]


def render():
    c=load(OUTPUT/'completion.json')
    for name,key in (('manifest.json','manifest_sha256'),('summary.json','summary_sha256')):
        if sha(OUTPUT/name)!=c[key]:raise ValueError('completed audit changed')
    summary=load(OUTPUT/'summary.json')
    text='# Why two stretches remain unresolved\n\n'
    text+='The saved checks distinguish problems with timing boundaries from unstable joint calibration corrections. '
    text+='This audit examines nine earlier diagnostic outcomes and fourteen branch reports; it performs no fits, integrations or numerical solves. '
    text+='The published tally remains **51 globe / 0 flat / 2 unresolved**.\n\n'
    text+='| Stretch / case / model / start | Saved outcome | Fresh correction issue |\n|---|---|---|\n'
    for row in summary['reports']:
        label=row['source_identity'].replace('::',' / ')
        flags=[b['side']+': '+', '.join(k for k in ('fresh_stationarity','cost','position') if not b[k+'_passed'])
               for b in row['branches'] if any(not b[k+'_passed'] for k in ('fresh_stationarity','cost','position'))]
        text+=f"| `{label}` | {row['reason']} | {'; '.join(flags) or 'None in the saved branch metrics'} |\n"
    text+='\n## Nearby timing solutions\n\n'
    text+='For `370cec66878c4c1cf84b4ceb`, the unsubtracted specified-field primary and repeat already pass. '
    text+='The profiled-removal primary passes the left check but fails the right fresh correction: '
    text+='its largest changes are in gravity, Y gyro gain and Z acceleration offset. The right correction changes '
    text+='the objective by about 0.049% and the reconstructed position by up to 20 mm RMS per axis, above the 1 mm numerical limit. '
    text+='Its endpoint side gradients pass; the new corrected point does not. The interrupted profiled-removal repeat '
    text+='has no completed diagnostic and remains a preserved failure.\n\n'
    text+='A focused complete-cluster check from both original, fully saved fit endpoints can test whether a nearby '
    text+='supported boundary avoids this unstable correction. It must retain the full two-sided test, source-to-final '
    text+='movement limits and processing-case repeat comparison. It cannot reuse the interrupted identity or its allowance.\n\n'
    text+='## Separated timing solutions and additional calibration failures\n\n'
    text+='For `b4e44ddc0f130ecd45674c78`, the two zero-field-globe primaries stopped at the old geometry guard. '
    text+='They have not failed a measured-position stability test. The separately qualified representability check '
    text+='is relevant, but the saved primary/repeat time separation also calls for a bounded nonlinear timing profile. '
    text+='The specified-field failures reach an unchecked neighboring boundary on the right. Two also take a full-span '
    text+='gravity correction with metre-scale position changes; one has stable movement but still lacks the neighbor check. '
    text+='Thus checking a neighbor alone cannot justify accepting every endpoint.\n\n'
    text+='The reports save aggregate stationarity values, not the fresh per-coordinate gradients. '
    text+='Large normalized correction components suggest where to inspect the numerical solve; they do not establish '
    text+='that gravity or a sensor calibration is physically wrong. No model preference is inferred from these failures.\n\n'
    text+='[Current status](../CURRENT_STATUS.md) · [Next steps](../NEXT_STEPS.md) · [Finite audit plan](PLAN.md).\n'
    (GUIDE/'README.md').write_text(text)
    for n in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/n,GUIDE/n)
    write(GUIDE/'evidence-receipt.json',dict(artifacts={n:sha(GUIDE/n) for n in
        ('manifest.json','summary.json','completion.json','README.md')},native_calls=0,optimizer_starts=0))


def build():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        lock=stack.enter_context((OUTPUT/'worker.lock').open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart; use --render-only')
        inputs={};receipt=load(PARENT/'evidence-receipt.json')
        inputs[str((PARENT/'evidence-receipt.json').relative_to(ROOT))]=sha(PARENT/'evidence-receipt.json')
        manifest=verified(PARENT/'manifest.json',receipt['artifacts']['manifest.json'],inputs)
        review=verified(PARENT/'review.json',receipt['artifacts']['review.json'],inputs)
        reports=[];records=[]
        for name,h in manifest['inputs'].items():
            if not (name.endswith('-summary.json') or any(
                    ('-'+sid+'-') in name and name.endswith('-boundary_diagnostic.json') for sid in TARGETS)):continue
            path=ROOT/name
            if path.parent!=PARENT or receipt['artifacts'].get(path.name)!=h:
                raise ValueError('conflicting source receipts')
            records.append(verified(path,h,inputs))
        for attempt in review['attempts']:
            if attempt['segment_id'] not in TARGETS or attempt['status']!='complete':continue
            row,envelope=select_result(attempt['identity'],records)
            digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
            if envelope is not None and envelope['result_sha256']!=digest:
                raise ValueError('diagnostic result envelope changed')
            report=diagnose(row,attempt['fit']['active_parameters'])
            report['source_identity']=attempt['source_identity'];reports.append(report)
        if len(reports)!=9 or sum(len(r['branches']) for r in reports)!=14:
            raise ValueError('exact nine-outcome/fourteen-branch audit required')
        sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),GUIDE/'PLAN.md',
            ROOT/'analysis/tests/test_ilvis0_final_two_audit.py',ROOT/'analysis/lll/ilvis0_receipt_journal.py')}
        write(OUTPUT/'manifest.json',dict(inputs=inputs,sources=sources,maximum_reports=9,maximum_branches=14,
            numerical_threads=0,native_calls=0,optimizer_starts=0,original_reads=0,maximum_batches=1))
        freeze=OUTPUT/'source-freeze';freeze.mkdir()
        for p in sources:
            destination=freeze/p;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,destination)
        write(OUTPUT/'start.json',dict(manifest_sha256=sha(OUTPUT/'manifest.json')))
        for p,h in {**inputs,**sources}.items():
            if sha(ROOT/p)!=h:raise ValueError('audit dependency changed')
        write(OUTPUT/'summary.json',dict(state='complete',reports=reports,labels_changed=False,
            native_calls=0,optimizer_starts=0,original_reads=0,numerical_solves=0))
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=sha(OUTPUT/'manifest.json'),
            summary_sha256=sha(OUTPUT/'summary.json')))
        render();print(json.dumps(dict(state='complete',reports=9,branches=14,native_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render-only',action='store_true')
    if parser.parse_args().render_only:render()
    else:build()
