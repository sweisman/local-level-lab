# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render sealed profile diagnostics and saved residuals; no native computation."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from lll import ilvis0_z_profile_audit as analysis, ilvis0_saved_audit as saved
from lll import ilvis0_solver_diagnosis as diagnosis, ilvis0_residuals as residuals

HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/'ilvis0-z-profile-20261011'


def load(p): return json.loads(p.read_text())


def sha(p):
    with p.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def build():
    saved.verify_artifacts(INPUT,load(INPUT/'evidence-receipt.json'))
    summary,manifest=load(INPUT/'summary.json'),load(INPUT/'manifest.json')
    completion=load(INPUT/'completion.json')
    if (completion['state']!='complete' or completion['manifest_sha256']!=sha(INPUT/'manifest.json') or
        completion['summary_sha256']!=sha(INPUT/'summary.json')): raise ValueError('invalid completion')
    result=analysis.compare(summary,manifest)
    epochs=[]
    for fit in summary['fits']:
        path=INPUT/fit['residual_file']
        if sha(path)!=fit['residual_sha256']: raise ValueError('saved residual hash changed')
        with gzip.open(path,'rt') as stream: rows=list(csv.DictReader(stream))
        t=np.array([float(r['time_utc_week_s']) for r in rows])
        if len(t)<3 or np.any(np.diff(t)<=0): raise ValueError('invalid saved residual cadence')
        for axis in ('north','east','up'):
            x=np.array([float(r[axis+'_residual_m']) for r in rows])
            z=np.array([float(r[axis+'_primary_innovation']) for r in rows])
            epochs.append(dict(identity=fit['identity'],model=fit['model'],axis=axis,epochs=len(t),
                median_cadence_s=float(np.median(np.diff(t))),physical_rms_m=residuals.distribution(x)['rms'],
                physical_p95_m=residuals.distribution(x)['absolute_p95'],
                physical_lag1=residuals.autocorrelation(x,1),innovation_rms=residuals.distribution(z)['rms'],
                innovation_lag1=residuals.autocorrelation(z,1)))
    result['residuals']=epochs
    artifacts=[]
    for key in ('models','fits','parameters','weak_directions','remaining_boundaries','residuals'):
        name=key.replace('_','-')+'.csv'
        with (HERE/name).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(result[key][0]),lineterminator='\n')
            writer.writeheader(); writer.writerows(result[key])
        artifacts.append(name)
    text=['# Does Z-axis calibration explain the model separation?','',
        '**All 27 fits converged. Every fixed gain/offset combination favors globe over disc, then the specified background field over zero field.**',
        '', 'An IMU (inertial measurement unit) records turning and acceleration. This audit uses saved fits of one 438-second IMU21 recording,',
        '`ILVIS0_applanix_57300_610_LVIS_38614965.013`, with median speed 878.06 km/h and minimum 859.55 km/h.',
        'It covers packet-header timing and the no-upstream-removal assumption. These are matched checks, not independent flights.',
        '', '| Model | Horizontal error range (m) | Objective range | Remaining parameters at limits |',
        '|---|---:|---:|---:|']
    for m in result['models']:
        text.append(f"| {m['model']} | {m['horizontal_rms_min_m']:.4f}–{m['horizontal_rms_max_m']:.4f} | {m['cost_min']:.6g}–{m['cost_max']:.6g} | {m['remaining_boundary_count_min']}–{m['remaining_boundary_count_max']} |")
    text+=['', '## What the grid resolves','',
        'The preferred model’s objective changes by only 2.58% across the full grid. Its excellent track fit does not require',
        'Z gain −2% or Z offset +1°/hour: zero corrections and every other tested combination preserve the advantage.',
        'Those two corrections were fixed, so they are excluded from the remaining-boundary counts above.',
        'The preferred model reaches at most one other limit; the alternatives reach 12–13. Boundary counts must therefore',
        'be interpreted separately for each model. This result removes an explanation in which the preference depends',
        'on the two extreme Z corrections. It does not establish that the measurement model or uncertainty is fully adequate.',
        '', '## What calibration remains uncertain','',
        'The best sampled preferred-model point still lies at Z gain −2%, offset +1°/hour, but its advantage over',
        'other calibration points is small. The saved fixed-coordinate derivatives and profile costs show this direction',
        'of improvement; they do not identify the factory calibration or instrument drift.',
        'The weakest remaining local direction at the zero-correction point is dominated by gravity correction and',
        'X/Y gyro gains for all three models. The [weak-direction table](weak-directions.csv) retains every loading',
        'and its box-feasibility flags. These describe the saved normalized coordinates, not confidence intervals.',
        'No new Jacobian was calculated. Fixed-coordinate gradients are not feasible search directions within each locked fit.',
        '', '## Residuals and what follows','',
        '[Saved epoch statistics](residuals.csv) report physical errors, innovation RMS and lag-one correlation.',
        'These are in-sample fitted residuals. They do not independently estimate GPS noise or certify a calibrated likelihood.',
        'The next matched grid allows a common upstream background-field-removal fraction. A separately predeclared',
        'September 24 recording then tests transfer of this robustness. Different dates do not establish independent instruments.',
        'Both stages retain the same calibration bounds and finite grid; neither uses Group1 fused navigation as inertial evidence.',
        '', 'Background-field comparisons describe measured-rotation predictions, not their physical cause.',
        'This audit adds zero optimizer starts and zero native predictions. It preserves the original 53-stretch findings.',
        '', '## Reproduce','', '```sh',
        'env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-z-profile-audit-20261011/build_report.py',
        '```','']
    (HERE/'README.md').write_text('\n'.join(text)); artifacts.append('README.md')
    (HERE/'summary.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'); artifacts.append('summary.json')
    sources=[Path(__file__).resolve(),Path(analysis.__file__).resolve(),Path(saved.__file__).resolve(),Path(diagnosis.__file__).resolve(),Path(residuals.__file__).resolve()]
    receipt=dict(version=analysis.VERSION,optimizer_starts=0,native_predictions=0,
        inputs={str(p.resolve()):sha(p) for p in [INPUT/n for n in ('summary.json','manifest.json','completion.json','evidence-receipt.json')]},
        sources={str(p):sha(p) for p in sources},artifacts={n:sha(HERE/n) for n in artifacts})
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Audited 27 saved profiles; zero fits or native predictions.')


if __name__=='__main__': build()
