# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare two finite studies from sealed metadata, without scans or new predictions."""
import csv
import hashlib
import json
from pathlib import Path
from lll import ilvis0_precision_continuation_plan as planning
from lll.ilvis0_pair_diagnosis import stopping_gates,history_summary

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'docs/ilvis0-cost-precision-recovery-20261014'
OLD=ROOT/'docs/ilvis0-position-recovery-20261013'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    complete=json.loads((PARENT/'completion.json').read_text());summary=json.loads((PARENT/'summary.json').read_text())
    parent=json.loads((PARENT/'manifest.json').read_text())
    if (complete['state']!='complete' or sha(PARENT/'manifest.json')!=complete['manifest_sha256']
            or sha(PARENT/'summary.json')!=complete['summary_sha256']): raise ValueError('sealed parent required')
    receipt=json.loads((PARENT/'evidence-receipt.json').read_text())
    for n,h in receipt['artifacts'].items():
        if sha(PARENT/n)!=h: raise ValueError('published artifact mismatch')
    old=json.loads((OLD/'summary.json').read_text());old_manifest=json.loads((OLD/'manifest.json').read_text())
    old_receipt=json.loads((OLD/'evidence-receipt.json').read_text())
    for n in ('summary.json','manifest.json','completion.json'):
        if sha(OLD/n)!=old_receipt['artifacts'][n]: raise ValueError('earlier publication mismatch')
    old_records={r['segment_id']:r for r in old['comparisons']}
    current={r['segment_id']:r for r in summary['comparisons']}
    path=ROOT/'docs/ilvis0-position-stability-trial-20261013/current-stretches.csv'
    with path.open() as stream: inventory={r['segment_id']:r for r in csv.DictReader(stream)}
    lengths={sid:float(r['duration_s']) for sid,r in inventory.items()}
    weighted=sum(lengths[k.split('::')[0]]*(f['fit_native_sweeps']+f['diagnostic_native_sweeps']) for k,f in summary['results'].items())
    seconds=sum(f['elapsed_s'] for f in summary['results'].values())/weighted
    diagnoses=[];outputs=[]
    for stage in ('budget','remaining'):
        name,starts,sweeps=planning.STAGES[stage];guide=ROOT/'docs'/name;guide.mkdir(exist_ok=True)
        plan=planning.build(stage,summary,parent)
        if (plan['maximum_starts'],plan['maximum_native_sweeps'])!=(starts,sweeps): raise ValueError('continuation scope changed')
        ceiling=sum(lengths[t['segment_id']]*(t['maximum_evaluations']+2) for t in plan['tasks'])*seconds/3600
        (guide/'selection.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
        rows=[]
        for sid in plan['target_segment_ids']:
            source=current[sid] if stage=='budget' else old_records[sid]
            failures=[dict(case_id=f['case_id'],model=f['model'],**stopping_gates(f),**history_summary(f)) for c in source['cases'] for f in c['fits'] if not f['converged']]
            if inventory[sid]['shape_preference']!='unresolved': raise ValueError('resolved stretch cannot be targeted')
            row=dict(inventory[sid],stage=stage,failed_gates=';'.join(f"{f['case_id']}:{f['model']}:{','.join(f['failed_gates'])}" for f in failures))
            rows.append(row);diagnoses.append(dict(segment_id=sid,stage=stage,failures=failures))
        with (guide/'targets.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
        text=f'# Frozen {stage} precision-study plan\n\n'
        text+=f"{len(plan['target_segment_ids'])} fixed targets; **{starts} starts / {sweeps:,} native sweeps maximum**. "
        text+=f'The ceiling estimate is **{ceiling:.1f} serial hours**, scaled by interval duration from the completed precision study. Actual endpoint continuations may finish much earlier.\n\n'
        text+='One worker uses four numerical threads. Every primary/repeat has at most 200 fitting evaluations; each control has forty. Each start permits two diagnostic predictions. No retries or budget expansion.\n\n'
        text+='Gradient tolerance stays 1e-4, fresh relative objective change 1e-8, predicted position change at most 1 mm axis RMS and 1 cm at any epoch. Repeat/control agreement requires relative objective difference ≤1e-6 and receiver-position RMS difference ≤1 cm per axis. These are numerical criteria, not measured sensor accuracy.\n\n'
        text+='Complete selected stretches, observed increments and receiver positions, models, bounds, weights, clock and qualified wider-arithmetic kernel are unchanged. Starts use frozen primary endpoints, not whichever earlier attempt has the lowest cost. Every charged interruption remains failed. Journals, source/input/environment hashes, exclusive locks and atomic results preserve the audit trail.\n\n'
        if stage=='budget':
            text+='Only the three failed primaries are continued. Their fifteen already passing companion primaries are reused with verified hashes. Each failed model gets its own fresh repeat. Both fresh controls must pass; an unfinished target cannot be promoted using its repeat instead of its primary.\n'
        else:
            text+='All six primaries are fitted afresh on each of the nine earlier excluded stretches, with the original scheduled repeat. Launch requires completion of the preceding budget stage with passing controls. That gate cannot alter the preselected targets. Per-stretch completion requires every primary, its repeat and both controls.\n'
        (guide/'PLAN.md').write_text(text)
        inputs={str(p):sha(p) for p in (PARENT/'manifest.json',PARENT/'summary.json',PARENT/'completion.json',OLD/'summary.json',OLD/'manifest.json',path)}
        data=dict(inputs=inputs,sources={str(Path(__file__)):sha(Path(__file__)),str(Path(planning.__file__)):sha(Path(planning.__file__))},
                  artifacts={n:sha(guide/n) for n in ('selection.json','PLAN.md','targets.csv')},
                  observed_starts=0,native_predictions=0,original_files_read=0,estimated_ceiling_hours=ceiling)
        (guide/'preparation-receipt.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
        outputs.append(dict(stage=stage,targets=len(rows),starts=starts,sweeps=sweeps,ceiling_hours=round(ceiling,1)))
    guide=ROOT/'docs'/planning.STAGES['remaining'][0]
    (guide/'saved-diagnosis.json').write_text(json.dumps(diagnoses,sort_keys=True,indent=2)+'\n')
    text='# Saved failure diagnosis\n\nAll twelve current unfinished stretches remain selected by the original motion and receiver criteria. This audit reads saved stopping probes and histories; it runs no native prediction or fit.\n\n'
    text+='| Stretch | Stage | Failed primary model/case | Remaining gate |\n|---|---|---|---|\n'
    for d in diagnoses:
        for f in d['failures']:
            text+=f"| `{d['segment_id']}` | {d['stage']} | {f['model']} / {f['case_id']} | {', '.join(f['failed_gates'])} |\n"
    text+='\nThe nine earlier exclusions combine nonstationary endpoints and unstable receiver predictions. Wider arithmetic with a separately finite allowance is a tested numerical alternative, not a guarantee of recovery. Calibration bounds and physical models stay fixed; failures do not favor either geometry. The saved vertical RMS gate uses a legacy `down` label for unsigned receiver-local vertical changes.\n'
    (guide/'DIAGNOSIS.md').write_text(text)
    print(json.dumps(outputs))


if __name__=='__main__': main()
