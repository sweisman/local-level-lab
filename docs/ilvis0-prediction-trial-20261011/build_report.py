# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish completed prediction diagnostics from saved metadata only."""
import csv
import hashlib
import json
from pathlib import Path

from lll import ilvis0_saved_audit as audit

HERE=Path(__file__).resolve().parent
VERSION='ilvis0-training-prediction-trial-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
MODEL_NAMES={'sphere_rotating':'Rotating globe','sphere_still':'Stationary globe',
    'flat_still':'Stationary flat disc'}
CASE_NAMES={'bias1_unsubtracted':'No upstream removal',
    'bias1_profiled_removal':'Upstream removal allowed'}


def load(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def number(value):
    return 'Unavailable' if value is None else f'{value:.6g}'


def render(summary,rows):
    successful=sum(r['status']=='converged' for r in rows)
    shape=summary['prediction_profile']['conditional_shape_preference']
    findings=[]
    for profile in summary['prediction_profile'].get('shape_profiles',[]):
        case=CASE_NAMES.get(profile['case_id'],profile['case_id'])
        contrast=profile.get('conditional_disc_minus_globe_cost')
        if contrast is None:
            unfinished=', '.join(MODEL_NAMES[m] for m in profile.get('unresolved_optimizations',[]))
            findings += [f'**{case} remains unresolved.** '+
                (f'{unfinished} has not converged. ' if unfinished else '')+
                'Its best permitted fit has not been established; an unfinished fit '
                'does not count as equal support for the models.','']
        elif contrast>0:
            findings += [f'**{case} favors globe** in the completed prediction comparison: '
                'the globe family has lower prediction cost than the stationary flat disc.','']
        elif contrast<0:
            findings += [f'**{case} favors flat** in the completed prediction comparison.','']
        else:
            findings += [f'**{case} is tied** in the completed prediction comparison.','']
    lines=['# Retrospective prediction results','',
        f'**{successful}/6 training fits converged. Prediction comparison: {shape}.** '
        'All results below come from the same previously selected recording. The final '
        'portion was withheld from these new fits, but the whole recording had already '
        'been examined during development. This is a retrospective prediction check, '
        'not an independent confirmation or a calibrated statistical detection.','',
        *findings,
        'An IMU (inertial measurement unit) records turning and acceleration. The source '
        'is `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21, '
        '2015-10-05 12:45:50–12:53:08 UTC, median ground speed 878.1 km/h. '
        'Fit the first 292 receiver epochs (291 seconds) and predict the remaining '
        '147 epochs (146 seconds), with one second between portions. The model '
        'propagates continuously from its initial state; it receives no GPS reset at the split.','',
        '## Direct prediction errors','',
        'Direct errors compare the propagated track with the later receiver positions '
        'without applying a correlated-error adjustment. Horizontal distance uses the '
        'same common reference coordinate metric as the clock trial. Calibration and '
        'initialization use training inputs only. Both cases ask whether a fraction '
        'of the background rotation was removed before the IMU measurements were '
        'logged: one fixes that removal to zero, and the other fits a common fraction. '
        'These retain the original processing assumptions.','',
        '| Processing case | Model | Fit status | Training horizontal / vertical RMS (m) | Prediction horizontal / vertical RMS (m) | Evaluations |',
        '|---|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {CASE_NAMES.get(r['case_id'],r['case_id'])} | {MODEL_NAMES[r['model']]} | {r['status']} | "
            f"{number(r['training_horizontal_m'])} / {number(r['training_vertical_m'])} | "
            f"{number(r['prediction_horizontal_m'])} / {number(r['prediction_vertical_m'])} | "
            f"{r['evaluations']} |")
    lines += ['', '## Covariance-adjusted diagnostics','',
        'These diagnostics condition the assumed receiver errors on the training '
        'residuals using the full-window cross-covariance. They do not alter the '
        'predicted aircraft track or add GPS fixes to its propagation. Costs remain '
        'separate from the direct errors above. Parameter uncertainty is omitted; '
        'these are plug-in checks at fitted parameters, not calibrated predictive coverage.','',
        '| Processing case | Model | Training cost | Primary prediction cost | Conservative prediction cost, same parameters |',
        '|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {CASE_NAMES.get(r['case_id'],r['case_id'])} | {MODEL_NAMES[r['model']]} | {number(r['training_cost'])} | "
            f"{number(r['prediction_cost'])} | {number(r['conservative_prediction_cost'])} |")
    reason=summary['prediction_profile'].get('rotation_withheld_reason')
    lines += ['', 'Model ordering is descriptive. Both globe candidates are profiled '
        'at the shape stage; the rotation comparison is reported only after all six '
        'fits converge and both processing cases favor globe. Unfinished fits are '
        'retained as unfinished and are not treated as equally good model fits.']
    if reason: lines += ['', 'Rotation comparison is withheld because shape is not consistently resolved in favor of globe.']
    else: lines += ['', 'The saved rotation cost differences are in the numerical summary; '
                          'they are model comparisons without a calibrated significance level.']
    errors=[r for r in rows if r['error']]
    if errors:
        lines += ['', '## Preserved failures','']
        lines += [f"- {r['case_id']} / {r['model']}: {r['error']}" for r in errors]
    elapsed=sum(r['elapsed_s'] for r in rows)
    evaluations=sum(r['evaluations'] for r in rows)
    lines += ['', '## Evidence and reproduction','',
        f'The six starts used {evaluations} recorded evaluations and about {elapsed/60:.1f} '
        'minutes of fitting/diagnostics. An interrupted or failed start remains charged '
        'and has no retry allowance. [Fit ledger](fit-comparisons.csv) records stopping '
        'messages and gradients; per-epoch compressed CSV files preserve training/prediction '
        'roles, direct errors and both innovation streams. [Plan](PLAN.md) records the '
        'split, assumptions and finite scope. Original studies remain frozen.','',
        'This renderer verifies publication hashes and reads saved metadata only. '
        'It performs no native prediction or optimization.','', '```sh',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-prediction-trial-20261011/build_report.py',
        '```','']
    return '\n'.join(lines)


def build(directory=HERE):
    directory=Path(directory)
    audit.verify_artifacts(directory,load(directory/'evidence-receipt.json'))
    summary,manifest,complete=[load(directory/n) for n in ('summary.json','manifest.json','completion.json')]
    if (summary.get('version')!=VERSION or summary.get('state')!='complete' or summary.get('starts')!=6
        or manifest.get('version')!=VERSION or manifest.get('maximum_starts')!=6
        or complete.get('state')!='complete' or complete.get('summary_sha256')!=sha(directory/'summary.json')
        or complete.get('manifest_sha256')!=sha(directory/'manifest.json')):
        raise ValueError('incompatible completed prediction evidence')
    expected={(c['case_id'],m) for c in manifest['cases'] for m in MODELS}
    actual=[(c['case_id'],f['model']) for c in summary['cases'] for f in c['fits']]
    if len(expected)!=6 or len(actual)!=6 or set(actual)!=expected:
        raise ValueError('incomplete or duplicate prediction population')
    rows=[]
    for case in summary['cases']:
        for fit in case['fits']:
            diagnostic=fit.get('prediction_diagnostics',{}); train=diagnostic.get('training',{})
            future=diagnostic.get('prediction',{})
            rows.append(dict(case_id=case['case_id'],model=fit['model'],status=audit.fit_status(fit),
                training_horizontal_m=train.get('horizontal_rms_m'),training_vertical_m=train.get('vertical_rms_m'),
                prediction_horizontal_m=future.get('horizontal_rms_m'),prediction_vertical_m=future.get('vertical_rms_m'),
                training_cost=fit.get('residual_sum_squares'),prediction_cost=future.get('primary_conditional_cost'),
                conservative_prediction_cost=future.get('conservative_conditional_cost'),
                gradient=fit.get('exact_projected_gradient_relative'),evaluations=fit.get('evaluations',0),
                elapsed_s=fit.get('elapsed_s',0.),stopping_message=fit.get('message',''),error=fit.get('error','')))
    with (directory/'fit-comparisons.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    (directory/'RESULTS.md').write_text(render(summary,rows))
    inputs=[directory/n for n in ('evidence-receipt.json','manifest.json','completion.json','summary.json')]
    sources=[Path(__file__).resolve(),Path(audit.__file__).resolve()]
    receipt=dict(version=VERSION,optimizer_starts=0,native_predictions=0,
        inputs={str(p.resolve()):sha(p) for p in inputs},sources={str(p):sha(p) for p in sources},
        artifacts={n:sha(directory/n) for n in ('RESULTS.md','fit-comparisons.csv')})
    (directory/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Prediction report published from saved metadata; zero new evaluations.')
    return rows


if __name__=='__main__': build()
