#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render verified saved evidence only; no numerical imports or predictions."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent


def _path(directory,name):
    if not isinstance(name,str) or Path(name).is_absolute():raise ValueError('relative evidence path required')
    root=directory.resolve();path=(directory/name).resolve()
    if not path.is_relative_to(root):raise ValueError('evidence path escapes publication')
    return path


def _sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def _load(path):return json.loads(path.read_text())


def audit(directory):
    directory=Path(directory)
    receipt=_load(directory/'evidence-receipt.json')['artifacts']
    for name,digest in receipt.items():
        if _sha(_path(directory,name))!=digest:raise ValueError('changed publication artifact: '+name)
    required=('manifest.json','summary.json','completion.json','case-unions.json','case-comparison.json')
    if any(name not in receipt for name in required):raise ValueError('incomplete evidence receipt')
    manifest=_load(directory/'manifest.json');summary=_load(directory/'summary.json');completion=_load(directory/'completion.json')
    if (completion['manifest_sha256']!=_sha(directory/'manifest.json')
            or completion['summary_sha256']!=_sha(directory/'summary.json')
            or completion['state']!=summary['state'] or summary['state'] not in ('complete','terminal')):
        raise ValueError('unsealed or inconsistent completion')
    tasks=manifest['tasks'];results=summary['results'];identities=[t['identity'] for t in tasks]
    if len(identities)!=48 or len(set(identities))!=48:raise ValueError('full 48-identity freeze required')
    expected={(m,p,s) for m in range(3) for p in (False,True) for s in range(8)}
    if ({(t['model'],t['profile'],t['sector']) for t in tasks}!=expected
            or any(type(t['profile']) is not bool or t['packets']!=400 or t['future_time']!=1.8
                   or t['training_times']!=[.2,.35,.6,.9,1.2,1.5] for t in tasks)):
        raise ValueError('original full candidate/sector/time selection required')
    task_by_id={t['identity']:t for t in tasks}
    baseline_record=manifest['inputs']['baselines'];baseline_path=baseline_record['path']
    if baseline_path not in receipt or _sha(_path(directory,baseline_path))!=baseline_record['sha256']:
        raise ValueError('original broad-box baseline is not sealed')
    baselines=_load(_path(directory,baseline_path))
    seen=set();rows=[]
    for row in results:
        name=row['artifact']
        if row['identity'] not in identities or row['identity'] in seen or name not in receipt:
            raise ValueError('unrecognized, duplicate or unreceipted result')
        if _sha(_path(directory,name))!=row['artifact_sha256']:raise ValueError('result hash mismatch')
        result=_load(_path(directory,name))
        if result['identity']!=row['identity'] or result['passed']!=row['passed']:
            raise ValueError('result identity/acceptance mismatch')
        seen.add(row['identity']);rows.append(result)
    complete=summary['state']=='complete' and len(rows)==48 and all(r['passed'] for r in rows)
    if bool(summary['passed'])!=complete:raise ValueError('summary completion is inconsistent')
    unions=_load(directory/'case-unions.json');comparison=_load(directory/'case-comparison.json')
    cases=unions['cases'];case_keys={f'case-{m}-{p}-400' for m in range(3) for p in (0,1)}
    if {c['case_key'] for c in cases}!=case_keys or len(cases)!=6:
        raise ValueError('all six intended comparisons must remain visible')
    if complete:
        if not unions['all_cases_complete'] or not comparison['all_cases_complete']:
            raise ValueError('complete rows without complete unions')
        for case in cases:
            group=[r for r in rows if r.get('case_key')==case['case_key']]
            sectors={r['task']['sector'] for r in group}
            if (len(group)!=8 or sectors!=set(range(8)) or not case['completed']
                    or any(r['task']!=task_by_id[r['identity']] for r in group)):
                raise ValueError('a complete case lacks an original sector')
            included=[r for r in group if not r.get('excluded',False)]
            if not included:raise ValueError('all generated sectors excluded')
            lower=[min(r['future_lower_m'][a] for r in included) for a in range(3)]
            upper=[max(r['future_upper_m'][a] for r in included) for a in range(3)]
            width=[b-a for a,b in zip(lower,upper)]
            truth=included[0]['future_truth_m'];baseline=baselines[case['case_key']]['width_after_m']
            if (len(truth)!=3 or any(r['future_truth_m']!=truth for r in included)
                    or len(baseline)!=3 or any(not math.isfinite(v) or v<=0 for v in baseline)
                    or any(not math.isfinite(v) for v in lower+upper+truth)):
                raise ValueError('finite aligned future oracle and positive baseline required')
            retained=all(a<=v<=b for a,v,b in zip(lower,truth,upper))
            ratio=[w/b for w,b in zip(width,baseline)];improvement=all(w<=b/10 for w,b in zip(width,baseline))
            if (case['union_lower_m']!=lower or case['union_upper_m']!=upper or case['union_width_m']!=width
                    or any(not r['known_truth_retained'] for r in group)
                    or not retained or case['future_truth_contained']!=retained
                    or case['baseline_width_m']!=baseline or case['width_ratio']!=ratio
                    or case['tenfold_width_improvement']!=improvement):
                raise ValueError('case union or known-control retention mismatch')
    target=complete and all(c.get('tenfold_width_improvement',False) for c in cases)
    if bool(comparison['tenfold_vs_original'])!=target:raise ValueError('usefulness summary mismatch')
    return dict(manifest=manifest,summary=summary,cases=cases,comparison=comparison,
        complete=complete,target=target,receipt_sha256=_sha(directory/'evidence-receipt.json'))


def render(evidence):
    s=evidence['summary'];complete=evidence['complete'];target=evidence['target']
    if complete:
        opening=('All **48 sectors pass correctness**. '+
            ('All six cases also pass' if target else 'The six cases do not all pass')+
            ' the unchanged tenfold width-reduction target against the original broad-box baseline.')
    else:
        opening=(f"The finite study stopped with **{sum(r['passed'] for r in s['results'])} passing identities "
            f"among {len(s['results'])} saved results**, out of 48 planned. "
            'The complete usefulness gate is not established; unfinished cases remain visible.')
    if complete:
        widths=[v for c in evidence['cases'] for v in c['union_width_m']]
        opening+=f' Complete union widths range from **{min(widths):.3f} to {max(widths):.3f} m** across axes and cases.'
    lines=['# Common acceleration: complete comparison','',opening,'',
        '| Candidate / processing | Complete | North / east / height union width (m) | Ratio to original broad-box widths |',
        '|---|---|---:|---:|']
    models={0:'Globe + specified field',1:'Globe, zero field',2:'Flat disc'}
    for c in evidence['cases']:
        _,m,p,_=c['case_key'].split('-')
        show=lambda name:', '.join(format(v,'.3g' if name=='width_ratio' else '.3f') for v in c.get(name,[])) or 'Unavailable'
        lines.append(f"| {models[int(m)]}, {'profiled removal' if int(p) else 'zero removal'} | "
            f"{'Yes' if c['completed'] else 'No'} | {show('union_width_m')} | {show('width_ratio')} |")
    lines+=['','These are conservative calculated ranges at **1.8 seconds in generated data**, '
        'not measured aircraft errors, calibrated prediction intervals or a new model preference. '
        'All original physical models, 27 calibration directions and bounds remain. '
        'Fifteen auxiliary coordinates preserve common errors across measurement times; '
        'they are not new independent physical choices at each epoch.','',
        f"The study charged {s['charged']['native_calls']} native evaluations and completed in "
        f"{s['elapsed_s']:.1f} seconds. Source/input/environment freezes, native values/Jacobians, "
        'training inequalities and future support certificates remain available. '
        'This report verifies the published hashes and reconciles every complete union against its sectors, '
        'without numerical integration, optimization or original-file reads.','',
        'Longer recording-scale usefulness, whole-program floating-point treatment, actual receiver-error '
        'adequacy and independent confirmation remain separate gates. No protected ESA outcomes are used. '
        'The 53-stretch empirical comparison is unchanged; scientific decisions remain abstention.','',
        '[All saved results](README.md) · [Frozen method](PLAN.md) · '
        '[Native qualification](../ilvis0-acceleration-native-controls/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=render(audit(HERE));target=HERE/'INTERPRETATION.md'
    if args.check:
        if target.read_text()!=text:raise ValueError('saved interpretation is stale')
        print('Verified saved comparison and interpretation; no predictions.')
    else:
        temporary=HERE/'INTERPRETATION.md.tmp';temporary.write_text(text);temporary.replace(target)
        print('Rendered verified saved comparison; no predictions.')


if __name__=='__main__':main()
