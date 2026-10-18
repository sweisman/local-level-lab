# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sealed-metadata preparation only; no original scans or numerical predictions."""
import csv
import hashlib
import json
from pathlib import Path
from lll import ilvis0_precision_recovery_plan as planning

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RECOVERY=ROOT/'docs/ilvis0-position-recovery-20261013'
TRIAL=ROOT/'docs/ilvis0-paired-precision-trial-20261014'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def sealed(directory):
    receipt=json.loads((directory/'evidence-receipt.json').read_text())
    complete=json.loads((directory/'completion.json').read_text())
    for name in ('summary.json','manifest.json','completion.json','starts.jsonl','sweeps.jsonl'):
        if sha(directory/name)!=receipt['artifacts'][name]: raise ValueError('publication hash mismatch')
    if (complete['state']!='complete' or sha(directory/'summary.json')!=complete['summary_sha256']
            or sha(directory/'manifest.json')!=complete['manifest_sha256']):
        raise ValueError('sealed completion required')
    return json.loads((directory/'summary.json').read_text()),json.loads((directory/'manifest.json').read_text())


def main():
    recovery,manifest=sealed(RECOVERY);trial,_=sealed(TRIAL)
    plan=planning.build(recovery,trial,manifest)
    if len(plan['inventory'])!=21 or len(plan['target_segment_ids'])!=12:
        raise ValueError('remaining population changed')
    inventory_path=ROOT/'docs/ilvis0-position-stability-trial-20261013/current-stretches.csv'
    with inventory_path.open() as stream: inventory={r['segment_id']:r for r in csv.DictReader(stream)}
    rows=[]
    for r in plan['inventory']:
        old=inventory[r['segment_id']]
        if old['shape_preference']!='unresolved': raise ValueError('resolved target in remaining inventory')
        rows.append(dict(segment_id=r['segment_id'],filename=old['filename'],source_sha256=old['source_sha256'],
                         start_utc=old['start_utc'],end_utc=old['end_utc'],imu_type=old['imu_type'],
                         duration_s=old['duration_s'],minimum_ground_speed_kmh=old['minimum_ground_speed_kmh'],
                         median_ground_speed_kmh=old['median_ground_speed_kmh'],eligible=r['eligible'],
                         failed_checks=';'.join(f"{f['role']}:{f['case_id']}:{f['model']}:{','.join(f['failed_gates'])}" for f in r['failures']),
                         repeat_case_id=r['repeat_case_id'],repeat_model=r['repeat_model']))
    with (HERE/'remaining-stretches.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    (HERE/'selection.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
    # Estimate from the measured paired trial, scaling per sweep by IMU samples
    # (duration), including every permitted fitting/diagnostic call.
    old_lengths={sid:float(inventory[sid]['duration_s']) for sid in inventory}
    sample_seconds=sum(old_lengths[f['identity'].split('::')[0]]*(f['fit_native_sweeps']+f['diagnostic_native_sweeps']) for f in trial['results'].values())
    elapsed=sum(f['elapsed_s'] for f in trial['results'].values())
    ceiling=sum(old_lengths[t['segment_id']]*(t['maximum_evaluations']+2) for t in plan['tasks'])*elapsed/sample_seconds/3600
    text='# Finite precision-recovery plan\n\n'
    text+=f"Twelve of 21 remaining stretches qualify by saved failure class. Limits: {plan['maximum_starts']} starts and {plan['maximum_native_sweeps']} native sweeps.\n\n"
    text+='- 72 primary fits: all three models and both processing cases, forty fitting evaluations each.\n'
    text+='- Two completed controls: forty fitting evaluations each.\n'
    text+='- Twelve predetermined repeats: two hundred fitting evaluations each.\n'
    text+='- Two diagnostic predictions per start, included in the total ceiling.\n'
    text+='- One worker, four total numerical threads; no retries.\n\n'
    text+=f'The ceiling is approximately **{ceiling:.1f} serial hours**, estimated from the completed paired trial and each selected interval\'s duration. This is a planning estimate, not a deadline. Warm starts can finish well below the ceiling, as the qualification trial did.\n\n'
    text+='The arithmetic, models and stopping rules are those of the qualified paired trial. Gradient tolerance remains 1e-4; fresh relative objective change 1e-8; position change at most 1 mm axis RMS and 1 cm at any epoch. Repeats and controls require relative objective agreement within 1e-6 and coordinate RMS agreement within 1 cm per axis. These are numerical tolerances, not instrument accuracy claims.\n\n'
    text+='A stretch contributes only after all six primary fits, its repeat and both controls pass. Failed original checks remain recorded. No result is chosen by taking the lowest cost from repeated starts. The stationary/position-failure strata remain excluded. Every retained source, selected interval, dependency, runtime environment and native kernel is hashed in the new freeze.\n'
    (HERE/'PLAN.md').write_text(text)
    inputs={str(d/n):sha(d/n) for d in (RECOVERY,TRIAL) for n in ('summary.json','manifest.json','completion.json','evidence-receipt.json')}
    inputs[str(inventory_path)]=sha(inventory_path)
    receipt=dict(inputs=inputs,sources={str(Path(__file__)):sha(Path(__file__)),str(Path(planning.__file__)):sha(Path(planning.__file__))},
                 artifacts={n:sha(HERE/n) for n in ('remaining-stretches.csv','selection.json','PLAN.md')},
                 observed_starts=0,native_predictions=0,originals_read=0,estimated_ceiling_hours=ceiling)
    (HERE/'preparation-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(targets=12,excluded=9,starts=plan['maximum_starts'],sweeps=plan['maximum_native_sweeps'],ceiling_hours=round(ceiling,1))))


if __name__=='__main__': main()
