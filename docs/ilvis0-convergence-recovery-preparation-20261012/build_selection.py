# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select recovery controls from frozen numerical status, never model preference."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'docs/ilvis0-highspeed-segments-20261008'
CONTROL='570b37d23af5e245dd461051'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def build():
    summary_path=PRIOR/'summary.json.gz';inventory_path=PRIOR/'eligible-stretches.csv'
    receipt=json.loads((PRIOR/'evidence-receipt.json').read_text())
    for path in (summary_path,inventory_path):
        if sha(path)!=receipt['artifacts'][path.name]:raise ValueError('frozen input hash mismatch')
    summary=json.loads(gzip.decompress(summary_path.read_bytes()))
    with inventory_path.open() as stream:inventory={r['segment_id']:r for r in csv.DictReader(stream)}
    rows=[];cases={r['segment_id']:r for r in summary['results']}
    for record in summary['results']:
        if record['profile']['conditional_shape_preference']!='unresolved':continue
        failed=[f for c in record['cases'] for f in c['fits'] if not f['converged']]
        stationary=[f for f in failed if f['exact_projected_gradient_relative']<=f['stationarity_tolerance']]
        if not failed:raise ValueError('unresolved comparison lacks unfinished fit')
        category=('all_failed_stationary' if len(stationary)==len(failed)
            else 'mixed_stationarity' if stationary else 'nonstationary')
        rows.append(dict(inventory[record['segment_id']],failure_category=category,
            unfinished_fits=len(failed),unfinished_fits_passing_saved_stationarity=len(stationary)))
    rows.sort(key=lambda r:(r['start_utc'],r['filename'],r['segment_id']))
    categories=('all_failed_stationary','mixed_stationarity','nonstationary')
    counts={name:sum(r['failure_category']==name for r in rows) for name in categories}
    if len(cases)!=53 or len(rows)!=41 or counts!=dict(zip(categories,(7,16,18))):
        raise ValueError('completed first-pass population differs from expected 53/41 freeze')
    selected=[dict(next(r for r in rows if r['failure_category']==name),role='recovery') for name in categories]
    control=cases[CONTROL]
    if any(not f['converged'] for c in control['cases'] for f in c['fits']):
        raise ValueError('control is not a completed six-fit comparison')
    selected.append(dict(inventory[CONTROL],failure_category='completed_control',
        unfinished_fits=0,unfinished_fits_passing_saved_stationarity=0,role='control'))
    write_csv(HERE/'all-unresolved.csv',rows);write_csv(HERE/'representative-subset.csv',selected)
    report=dict(version='ilvis0-recovery-subset-preparation-v1',state='metadata_preparation_only',
        unresolved_stretches=41,counts=counts,selected_segment_ids=[r['segment_id'] for r in selected],
        selection_policy='earliest UTC interval per failure category; filename/ID tie-break; fixed completed control',
        model_costs_used_for_selection=False,stationarity_only_changes_no_convergence_label=True,
        observed_fit_starts=0,native_predictions=0,archive_records_loaded=0,
        solver_and_budget_qualified=False,observed_allowance_authorized=False,scientific_decision='abstain')
    (HERE/'selection-summary.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    receipt=dict(version=report['version'],sources={str(Path(__file__).relative_to(ROOT)):sha(__file__)},
        inputs={str(p.relative_to(ROOT)):sha(p) for p in (summary_path,inventory_path,PRIOR/'evidence-receipt.json')},
        artifacts={name:sha(HERE/name) for name in ('all-unresolved.csv','representative-subset.csv',
            'selection-summary.json','README.md')})
    (HERE/'preparation-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Recorded all 41 unresolved stretches; selected three failure strata and one completed control. No fits or original reads.')


if __name__=='__main__':build()
