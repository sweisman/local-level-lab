# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit completed published grids; no raw extraction, prediction or fitting."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from lll import ilvis0_z_followup_audit as analysis
from lll import ilvis0_z_profile_audit as profiles
from lll import ilvis0_saved_audit as saved
from lll import ilvis0_solver_diagnosis as diagnosis
from lll import ilvis0_residuals as residuals

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INVENTORY=HERE.parent/'ilvis0-highspeed-segments-20261008'/'eligible-stretches.csv'
INPUTS=dict(original=HERE.parent/'ilvis0-z-profile-20261011',
            removal=HERE.parent/'ilvis0-z-profile-removal-20261011',
            replication=HERE.parent/'ilvis0-z-profile-replication-20261011')


def load(p):return json.loads(p.read_text())


def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read_inputs():
    grids={}
    for study,path in INPUTS.items():
        saved.verify_artifacts(path,load(path/'evidence-receipt.json'))
        completion=load(path/'completion.json')
        if (completion['state']!='complete' or completion['starts']!=27 or
            completion['manifest_sha256']!=sha(path/'manifest.json') or
            completion['summary_sha256']!=sha(path/'summary.json')):
            raise ValueError('invalid completed grid')
        grids[study]=load(path/'summary.json'),load(path/'manifest.json')
    return grids


def residual_table(grids):
    table=[]
    for study,(summary,_) in grids.items():
        for fit in summary['fits']:
            path=INPUTS[study]/fit['residual_file']
            if path.resolve().parent!=INPUTS[study].resolve() or sha(path)!=fit['residual_sha256']:
                raise ValueError('invalid saved residual artifact')
            with gzip.open(path,'rt') as stream:rows=list(csv.DictReader(stream))
            times=np.array([float(r['time_utc_week_s']) for r in rows])
            if len(times)<3 or not np.all(np.isfinite(times)) or np.any(np.diff(times)<=0):
                raise ValueError('invalid residual epochs')
            physical=np.array([[float(r[a+'_residual_m']) for a in ('north','east','up')] for r in rows])
            innovations=np.array([[float(r[a+'_primary_innovation']) for a in ('north','east','up')] for r in rows])
            if not np.all(np.isfinite(physical)) or not np.all(np.isfinite(innovations)):
                raise ValueError('invalid residual measurements')
            rms=np.sqrt(np.mean(physical**2,axis=0))
            if (not np.allclose(rms,fit['residual_rms_neu_m'],rtol=1e-10,atol=1e-12) or
                not np.isclose(np.sum(innovations**2),fit['residual_sum_squares'],rtol=1e-6,atol=1e-9)):
                raise ValueError('saved epoch residuals disagree with fitted cost or RMS')
            for j,axis in enumerate(('north','east','up')):
                x,z=physical[:,j],innovations[:,j]
                table.append(dict(study=study,identity=fit['identity'],model=fit['model'],
                    status=saved.fit_status(fit),axis=axis,epochs=len(times),
                    median_cadence_s=float(np.median(np.diff(times))),rms_m=float(rms[j]),
                    absolute_p95_m=residuals.distribution(x)['absolute_p95'],
                    physical_lag1=residuals.autocorrelation(x,1),
                    innovation_rms=residuals.distribution(z)['rms'],
                    innovation_lag1=residuals.autocorrelation(z,1)))
    return table


def build():
    grids=read_inputs();out=analysis.compare(grids);out['residuals']=residual_table(grids)
    artifacts=[]
    for key in ('studies','fits','models','nodes','failures','processing_changes','boundary_frequencies',
                'weak_directions','residuals'):
        name=key.replace('_','-')+'.csv'
        with (HERE/name).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(out[key][0]),lineterminator='\n')
            writer.writeheader();writer.writerows(out[key])
        artifacts.append(name)
    inventory=INVENTORY
    inventory_receipt=inventory.parent/'evidence-receipt.json'
    if sha(inventory)!=load(inventory_receipt)['artifacts'][inventory.name]:
        raise ValueError('published interval inventory changed')
    with inventory.open(newline='') as stream:selection={r['segment_id']:r for r in csv.DictReader(stream)}
    sources=[selection[analysis.TARGETS[s]] for s in ('original','replication')]
    for study,row in zip(('original','replication'),sources):
        if row['source_sha256']!=grids[study][0]['provenance']['source_sha256']:
            raise ValueError('interval inventory and fitted source disagree')
    text=['# What the completed calibration follow-ups show','',
        '**The first recording favors globe at every tested Z correction under both processing assumptions.**',
        'The other preselected recording favors globe in all seven complete comparisons. Two comparisons remain unfinished,',
        'so its full-grid background-field conclusion is withheld. No complete comparison favors the specified disc.',
        '', 'An IMU (inertial measurement unit) records turning and acceleration. These are survey-grade airborne recordings.',
        'The grids reuse whole, independently selected fast/level stretches; they do not create extra flights.',
        '', '## Source recordings','',
        '| File | Selected UTC interval | Duration | Median / minimum ground speed | IMU type |',
        '|---|---|---:|---:|---:|']
    for r in sources:
        text.append(f"| `{r['filename']}` | {r['start_utc']}–{r['end_utc']} | {float(r['duration_s']):.0f} s | {float(r['median_ground_speed_kmh']):.2f} / {float(r['minimum_ground_speed_kmh']):.2f} km/h | {r['imu_type']} |")
    text+=['', 'Both dates have the same recorded configuration family. This does not establish independent physical instruments',
        'or verified installation continuity. The September 24 recording was preselected without model fits, but had already',
        'appeared in the original archive analysis. This is development evidence, not unseen-data confirmation.',
        '', '## Complete and incomplete fits','',
        '| Grid | Converged fits | Complete three-model nodes | Whole-grid shape |', '|---|---:|---:|---|']
    for r in out['studies']:
        text.append(f"| {r['study']} | {r['converged']}/27 | {r['complete_nodes']}/9 | {r['shape_preference']} |")
    text+=['', 'Original and removal grids use the same October 5 recording. The replication grid uses September 24.',
        'Each grid fixes Z gyro gain at −2%, zero or +2%, and constant Z offset at −1, zero or +1 degree/hour.',
        'Remaining parameters are reestimated with unchanged bounds, original integration, packet-header timing and solver.',
        'The removal grid additionally allows the existing common upstream field-removal fraction.',
        '', '| Grid / model | Completed horizontal error range (m) | Remaining parameters at limits, all saved fits |',
        '|---|---:|---:|']
    for r in out['models']:
        text.append(f"| {r['study']} / {r['model']} | {r['completed_horizontal_min_m']:.4f}–{r['completed_horizontal_max_m']:.4f} | {r['remaining_bounds_min']}–{r['remaining_bounds_max']} |")
    text+=['', 'Error ranges use converged nodes only. The two locked Z coordinates are excluded from remaining-boundary counts.',
        'The [model table](models.csv) lists completed objective ranges separately from unfinished achieved costs.',
        'An unfinished achieved cost is an upper bound on that fit’s unknown optimum, not a completed comparison.',
        '', '## Why two fits remain unfinished','',
        'Both are specified-field globe fits on September 24. They exhausted the original evaluation allowance without',
        'solver-reported success. Both saved feasible-gradient stationarity checks nevertheless pass:',
        '', '| Z gain / offset | Native sweeps | Stationarity / required threshold | Horizontal / vertical achieved error |',
        '|---|---:|---:|---:|']
    for f in out['failures']:
        text.append(f"| {f['gain_percent']:+d}% / {f['bias_dph']:+d}°/hour | {f['evaluations']} | {f['stationarity_ratio']:.5f} | {f['horizontal_rms_m']:.4f} / {f['vertical_rms_m']:.4f} m |")
    text+=['', 'A ratio below one passes stationarity. Neither fit has another free parameter at its bound.',
        'These saved checks indicate a stopping-budget issue rather than a large remaining projected gradient.',
        'They do not prove a global minimum or justify relabeling either fit as converged. Accepted-step histories',
        'were not retained, so their objective stability over successive iterations cannot be reconstructed.',
        'All original failures and full-grid abstentions remain unchanged; no retry allowance remains.',
        '', 'The [failure table](failures.csv) preserves stopping messages, gradients and weak directions.',
        '', '## Processing and calibration behavior','']
    for model in profiles.MODELS:
        rows=[r for r in out['processing_changes'] if r['model']==model]
        fractions=[r['removal_fraction'] for r in rows]
        changes=[100*r['relative_cost_change'] for r in rows]
        text.append(f"- `{model}`: fitted removal fraction {min(fractions):.6g}–{max(fractions):.6g}; objective change {min(changes):.6g}%–{max(changes):.6g}% at matched grid nodes.")
    text+=['', 'The preferred globe’s removal fraction stays essentially zero and its costs are nearly unchanged.',
        'Allowing removal therefore does not explain away its advantage on this recording. A fitted near-zero fraction',
        'does not establish the actual electronics’ processing. Nor can an arbitrary original field and its unknown',
        'subtraction be recovered independently from these logged data.',
        '', '[Boundary frequencies](boundary-frequencies.csv) separate model, processing case and boundary sign.',
        '[Weak directions](weak-directions.csv) preserve normalized-coordinate singular-vector loadings and box-feasibility.',
        'These local diagnostics describe calibration trade-offs, not physical uncertainty or unique factory calibration.',
        '', '## Residual quality and next work','',
        'The [epoch residual audit](residuals.csv) checks every saved RMS and objective against its original epoch file,',
        'then reports axis errors, innovation RMS and lag-one dependence for all 81 saved fits, including unfinished ones.',
        'These are in-sample residuals. A small RMS does not calibrate GPS covariance, predictive intervals or model significance.',
        '', 'The next useful step is a saved-residual covariance audit: longer lags, cross-axis dependence and low-frequency',
        'behavior under one declared reference metric. That can prepare a shared error-model alternative before any refits.',
        'A new stopping-rule or larger-budget test would require independent qualification and a separate finite allowance.',
        'There is no archive rerun, new synthetic campaign or threshold promotion in this audit.',
        '', 'The specified-field/zero-field comparison is reported only after complete globe-favoring shape comparisons.',
        'It does not identify the background field’s physical cause or distinguish solar from sidereal rate.',
        'Group1 fused navigation supplies no independent inertial evidence. This audit performs **zero fits and zero native predictions**.',
        '', '## Reproduce','', '```sh',
        'env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-z-followup-audit-20261012/build_report.py',
        '```','']
    (HERE/'README.md').write_text('\n'.join(text));artifacts.append('README.md')
    (HERE/'summary.json').write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n');artifacts.append('summary.json')
    dependencies=[Path(__file__).resolve(),*[Path(m.__file__).resolve() for m in (analysis,profiles,saved,diagnosis,residuals)],
                  ROOT/'analysis/tests/test_ilvis0_z_followup_audit.py',
                  ROOT/'analysis/tests/test_ilvis0_z_followup_report.py']
    receipt=dict(version=analysis.VERSION,optimizer_starts=0,native_predictions=0,
        inputs={str(p.resolve()):sha(p) for directory in INPUTS.values()
                for p in (directory/'summary.json',directory/'manifest.json',directory/'completion.json',directory/'evidence-receipt.json')},
        sources={str(p):sha(p) for p in dependencies},artifacts={n:sha(HERE/n) for n in artifacts})
    receipt['inputs'][str(inventory.resolve())]=sha(inventory)
    receipt['inputs'][str(inventory_receipt.resolve())]=sha(inventory_receipt)
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Audited 81 saved fits, two stopping failures and 243 residual series; zero fits or native predictions.')


if __name__=='__main__':build()
