# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare identities and compute ceiling from published metadata, not originals."""
import gzip
import hashlib
import json
from pathlib import Path
import statistics

from lll import ilvis0_prediction_comparison_plan as plan, runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'docs/ilvis0-prediction-trial-20261011'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    summary=json.loads((PRIOR/'summary.json').read_text())
    manifest=json.loads((PRIOR/'manifest.json').read_text())
    selection=json.loads(gzip.decompress((PRIOR/'selection.json.gz').read_bytes()))
    selected=selection['selected']
    if len(selected)!=1 or selected[0]['segment']['segment_id']!=summary['split']['segment_id']:
        raise ValueError('published control selection disagrees with saved split')
    fits=[f for c in summary['cases'] for f in c['fits']]
    if len(fits)!=6 or any(f['evaluations']<=0 or f['elapsed_s']<=0 for f in fits):
        raise ValueError('six saved runtime references required')
    rates=[f['elapsed_s']/f['evaluations'] for f in fits]
    proposal=plan.make(summary['split'],statistics.median(rates),max(rates))
    proposal['recording']=dict(filename=selected[0]['filename'],
        imu_type=selected[0]['segment']['imu_type'],
        source_sha256=summary['provenance']['source_sha256'],
        compressed_original_sha256=manifest['inputs'][selected[0]['source_path']],
        selected_duration_s=selected[0]['segment']['duration_s'],
        minimum_ground_speed_kmh=selected[0]['segment']['minimum_receiver_ground_speed_kmh'],
        median_ground_speed_kmh=selected[0]['segment']['median_receiver_ground_speed_kmh'])
    proposal['cases']=manifest['cases']
    proposal['baseline']='preserved tau60 comparison; its unfinished fit remains unfinished'
    proposal['launch_requirements']=['implemented and control-tested durable worker',
        'new input/source/environment freeze and verified originals at launch',
        'explicit finite observed-data allowance','locks and append-only pre-call charge journals']
    proposal['source_commit']='42cd8f8'
    inputs=[PRIOR/name for name in ('summary.json','manifest.json','selection.json.gz')]
    inputs.append(ROOT/'docs/ilvis0-native-uncertainty-controls-20261012/report-receipt.json')
    sources=[Path(__file__).resolve(),Path(plan.__file__).resolve(),
        ROOT/'analysis/tests/test_ilvis0_prediction_comparison_plan.py']
    proposal['numerical_environment']=runtime.numerical_environment()
    proposal['references']={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    proposal['preparation_sources']={str(p.relative_to(ROOT)):sha(p) for p in sources}
    (HERE/'proposal.json').write_text(json.dumps(proposal,sort_keys=True,indent=2,allow_nan=False)+'\n')
    receipt=dict(version=plan.VERSION,inputs=proposal['references'],sources=proposal['preparation_sources'],
        artifacts={name:sha(HERE/name) for name in ('proposal.json','README.md')},
        archive_records_loaded=0,observed_fit_starts=0,native_predictions=0)
    (HERE/'preparation-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    estimate=proposal['runtime_estimate']
    print(f"Prepared 12 identities, 3060 maximum native sweeps; "
        f"runtime estimate {estimate['ceiling_minutes_at_median']:.0f}–"
        f"{estimate['ceiling_minutes_at_slowest']:.0f} minutes. Not launchable; no archive fits or reads.")


if __name__=='__main__':build()
