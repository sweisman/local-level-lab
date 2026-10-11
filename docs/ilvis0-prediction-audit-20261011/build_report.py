# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit published prediction evidence only; no original data or numerical kernels."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

from lll import ilvis0_prediction_audit as analysis
from lll import ilvis0_saved_audit as saved

HERE=Path(__file__).resolve().parent
PREDICTION=HERE.parent/'ilvis0-prediction-trial-20261011'
CLOCK=HERE.parent/'ilvis0-clock-trial-20261010'
MODEL={'sphere_rotating':'Rotating globe','sphere_still':'Still globe','flat_still':'Flat disc'}
CASE={'bias1_unsubtracted':'No removal','bias1_profiled_removal':'Removal allowed'}


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def verified(directory):
    saved.verify_artifacts(directory,load(directory/'evidence-receipt.json'))
    done=load(directory/'completion.json')
    if (done['state']!='complete' or done['summary_sha256']!=sha(directory/'summary.json')
        or done['manifest_sha256']!=sha(directory/'manifest.json')):
        raise ValueError('invalid completed evidence')
    return load(directory/'summary.json'),load(directory/'manifest.json')


def index(cases,expected):
    rows={}
    for case in cases:
        for fit in case['fits']:
            key=case['case_id'],fit['model']
            if key in rows: raise ValueError('duplicate matched fit')
            rows[key]=fit
    if set(rows)!=expected: raise ValueError('incomplete matched population')
    return rows


def render(out):
    lines=['# What grows when GPS fitting stops?','',
        '**The rotating-globe track remains much closer horizontally during prediction, '
        'but its errors grow after GPS fitting stops.** Five of six training fits converged. '
        'The flat-disc fit with removal allowed exhausted its allowance, so the full '
        'two-case comparison remains unresolved.','',
        'An IMU (inertial measurement unit) records turning and acceleration. This audit '
        'uses saved results from one IMU-type-21 recording, '
        '`ILVIS0_applanix_57300_610_LVIS_38614965.013`, on 2015-10-05. '
        'The stretch lasts 7.30 minutes at median ground speed 878.1 km/h. '
        'The first 4.85 minutes supplied GPS fitting positions; the final 2.43 minutes '
        'were propagated without GPS resets. This recording was examined earlier, so '
        'the test is retrospective development, not independent confirmation.','',
        '## Error growth','',
        'These are direct distances to the recorded receiver positions. The endpoint '
        'column describes the final instant; RMS describes the entire prediction portion. '
        'Vertical endpoint error retains its sign.','',
        '| Processing | Model | Status | Training H / V RMS (m) | Prediction H / V RMS (m) | Final H / signed V (m) |',
        '|---|---|---|---:|---:|---:|']
    for r in out['fits']:
        lines.append(f"| {CASE[r['case_id']]} | {MODEL[r['model']]} | {r['status']} | "
            f"{r['training_horizontal_m']:.3f} / {r['training_vertical_m']:.3f} | "
            f"{r['prediction_horizontal_m']:.3f} / {r['prediction_vertical_m']:.3f} | "
            f"{r['endpoint_horizontal_m']:.3f} / {r['endpoint_up_m']:.3f} |")
    lines+=['','[Thirty-second prediction sections](error-growth.csv) show where errors '
        'accumulate at the same fixed parameters. They are not refits or independent trials.','',
        '| Processing | Seconds after prediction begins | Rotating-globe H / V RMS (m) |',
        '|---|---:|---:|']
    for case in CASE:
        part=[r for r in out['windows'] if r['case_id']==case and r['model']=='sphere_rotating']
        origin=part[0]['first_time_s']
        for r in part:
            lines.append(f"| {CASE[case]} | {r['offset_start_s']:.0f}–{r['last_time_s']-origin:.0f} | "
                f"{r['horizontal_rms_m']:.3f} / {r['vertical_rms_m']:.3f} |")
    lines+=['',
        '## Calibration changes with the fitting window','',
        'This compares earlier whole-stretch header-clock fits with the new training-only '
        'fits. Bounds and processing assumptions are matched, but the observations fitted '
        'differ. Parameter movements show readjustment; they do not establish its cause '
        'or measure factory calibration.','',
        '| Processing | Model | Parameters at limits: full / training | Jacobian condition ratio | Stationarity / limit |',
        '|---|---|---:|---:|---:|']
    for r in out['fits']:
        condition=r['jacobian_condition_ratio']
        lines.append(f"| {CASE[r['case_id']]} | {MODEL[r['model']]} | "
            f"{r['full_window_boundary_count']} / {r['training_boundary_count']} | "
            f"{condition:.4g} | {r['stationarity_ratio']:.4g} |")
    lines+=['','The condition ratio uses the saved Jacobian’s largest and smallest singular '
        'values in normalized parameter coordinates. It is not a confidence interval or '
        'a unique diagnosis. Converged fits can also have large ratios. The original '
        'prediction fitter did not save Jacobian vectors, gradient components or iteration '
        'history, so this audit cannot identify which parameter caused the unfinished fit.','',
        '| Processing | Rotating-globe parameter | Unit | Full-window value | Training value | Full / training limit |',
        '|---|---|---|---:|---:|---|']
    for r in out['parameters']:
        if r['model']=='sphere_rotating' and r['parameter'] in ('gyro_gain_z','gyro_bias_z','gravity_delta','accel_bias_z','time_offset'):
            lines.append(f"| {CASE[r['case_id']]} | {r['parameter']} | {r['unit']} | "
                f"{r['full_window_value']:.6g} | {r['training_value']:.6g} | "
                f"{r['full_window_boundary']} / {r['training_boundary']} |")
    gains=[r for r in out['parameters'] if r['model']=='sphere_rotating' and r['parameter']=='gyro_gain_z']
    if len(gains)==2 and all(r['full_window_value']< -1.99 and r['training_value']>1.99 for r in gains):
        lines+=['','**Z gyro gain flips from −2% in the whole-stretch fits to +2% in '
            'the training-only fits under both processing cases.** The estimated constant '
            'Z offset stays at +1°/hour, and gravity correction returns to its lower limit. '
            'These shifts demonstrate sensitivity to the fitting window; they do not '
            'prove that the instrument calibration changed during the flight. Completing '
            'the solver alone will not settle this calibration question.']
    lines+=['','[All parameter changes](parameter-changes.csv) preserve signed limits and '
        'units. The [fit ledger](fit-diagnostics.csv) preserves stopping messages and '
        'stationarity checks, including the unfinished flat fit.','',
        '## What to do next','',
        'Test a solver alternative on independently known optima before any new observed '
        'fits. Keep the physical models, bounds, covariance, split and initialization '
        'unchanged in a separately frozen matched comparison. Save accepted-step history, '
        'fresh gradient components and weak parameter directions. Neither increasing '
        'the old allowance nor relabeling its failure is authorized. See the '
        '[solver and replication plan](NEXT_PLAN.md).','',
        'This audit verifies published hashes, matched fits and per-epoch RMS. It makes '
        '**zero optimizer starts and zero native predictions**. It cannot calibrate '
        'statistical significance or attribute the retained rotation field’s physical cause.','',
        '```sh','env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-prediction-audit-20261011/build_report.py','```','']
    return '\n'.join(lines)


def build(prediction=PREDICTION,clock=CLOCK,output=HERE):
    prediction,clock,output=map(Path,(prediction,clock,output))
    summary,manifest=verified(prediction); reference,_=verified(clock)
    if summary['header_reference']!=reference: raise ValueError('header reference differs')
    if summary['starts']!=6: raise ValueError('unexpected prediction scope')
    expected={(c['case_id'],m) for c in manifest['cases'] for m in MODEL}
    if len(expected)!=6: raise ValueError('unexpected matched scope')
    current=index(summary['cases'],expected); old=index(reference['cases'],expected)
    fits=[]; windows=[]; parameters=[]
    for case in manifest['cases']:
        for model in MODEL:
            key=case['case_id'],model; fit=current[key]
            with gzip.open(prediction/fit['residual_file'],'rt',newline='') as stream:
                rows=list(csv.DictReader(stream))
            if len(rows)!=summary['split']['training_epochs']+summary['split']['prediction_epochs']:
                raise ValueError('epoch population differs from split')
            growth=analysis.error_growth(rows,summary['split']['training_epochs'])
            for role in ('training','prediction'):
                for field in ('horizontal_rms_m','vertical_rms_m'):
                    if not math.isclose(growth[role][field],fit['prediction_diagnostics'][role][field],rel_tol=1e-10,abs_tol=1e-12):
                        raise ValueError('saved epoch and diagnostic RMS differ')
            params=analysis.parameter_changes(fit,old[key],case)
            parameters += [dict(case_id=key[0],model=model,**r) for r in params]
            windows += [dict(case_id=key[0],model=model,**r) for r in growth['windows']]
            fits.append(dict(case_id=key[0],model=model,**analysis.conditioning(fit),
                training_horizontal_m=growth['training']['horizontal_rms_m'],
                training_vertical_m=growth['training']['vertical_rms_m'],
                prediction_horizontal_m=growth['prediction']['horizontal_rms_m'],
                prediction_vertical_m=growth['prediction']['vertical_rms_m'],
                endpoint_horizontal_m=growth['prediction']['endpoint_horizontal_m'],
                endpoint_up_m=growth['prediction']['endpoint_up_m'],
                full_window_boundary_count=len(old[key]['active_bounds']),
                training_boundary_count=len(fit['active_bounds']),evaluations=fit['evaluations'],
                stopping_message=fit['message']))
    out=dict(version=analysis.VERSION,fits=fits,windows=windows,parameters=parameters,
        optimizer_starts=0,native_predictions=0,windows_are_independent_trials=False)
    output.mkdir(parents=True,exist_ok=True)
    for name,rows in [('fit-diagnostics.csv',fits),('error-growth.csv',windows),('parameter-changes.csv',parameters)]:
        with (output/name).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
    (output/'README.md').write_text(render(out))
    (output/'summary.json').write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
    inputs=[d/n for d in (prediction,clock) for n in ('evidence-receipt.json','completion.json','manifest.json','summary.json')]
    inputs += [prediction/f['residual_file'] for f in current.values()]
    sources=[Path(__file__).resolve(),Path(analysis.__file__).resolve(),Path(saved.__file__).resolve()]
    artifacts=('README.md','summary.json','fit-diagnostics.csv','error-growth.csv','parameter-changes.csv')
    receipt=dict(version=analysis.VERSION,optimizer_starts=0,native_predictions=0,
        inputs={str(p.resolve()):sha(p) for p in inputs},sources={str(p):sha(p) for p in sources},
        artifacts={n:sha(output/n) for n in artifacts})
    (output/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Saved prediction audit complete; zero optimizer starts or native predictions.')
    return out


if __name__=='__main__': build()
