# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit completed boundary-trial artifacts; never load the native fit worker."""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import platform

import numpy as np
import scipy

from lll import ilvis0_boundary_diagnosis as audit
from lll import ilvis0_rectangular_diagnosis as tangent
from lll import ilvis0_recovery_diagnosis as saved

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path(__file__).resolve().parent
RUNTIME = ROOT/'data/ilvis0-boundary-recovery-trial-20261012'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    summary, hashes = saved.load_completed(RUNTIME)
    hashes['completion.json'] = digest(RUNTIME/'completion.json')
    manifest = json.loads((RUNTIME/'manifest.json').read_text())
    roles = {task['identity']: task['role'] for task in manifest['proposal']['tasks']}
    if set(roles) != set(summary['results']) or len(roles) != 24:
        raise ValueError('frozen task list disagrees with completed results')
    rows, repeats = [], []
    for identity, fit in sorted(summary['results'].items()):
        value = tangent.load_linearization(RUNTIME, fit)
        hashes[fit['linearization_file']] = fit['linearization_sha256']
        # Verify every epoch artifact, including fits not selected for repeat checks.
        audit.load_epochs(RUNTIME, fit)
        hashes[fit['epoch_file']] = fit['epoch_sha256']
        row = audit.inspect_fit(identity, fit, value)
        row['task_role'] = roles[identity]
        rows.append(row)
        if roles[identity] == 'repeatability':
            primary_id = identity.rsplit('::', 1)[0]+'::primary'
            repeat = audit.compare_saved_predictions(RUNTIME, summary['results'][primary_id], fit)
            repeat.update(identity=identity, primary_identity=primary_id)
            repeats.append(repeat)
    counts = dict(collections.Counter(row['failure_class'] for row in rows))
    stalled = [row for row in rows if row['failure_class'] == 'stationary_stability_stall']
    exhausted = [row for row in rows if row['failure_class'] == 'budget_exhausted']
    result = dict(version=audit.VERSION, rows=rows, repeat_comparisons=repeats, counts=counts,
                  observed_fit_starts=0, native_predictions=0, original_labels_changed=False,
                  scientific_decision='abstain', trial_qualified=summary['qualification']['qualified'])
    (GUIDE/'diagnosis.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    columns = ['identity', 'task_role', 'converged', 'failure_class', 'evaluations',
               'cost', 'stationarity_ratio', 'predicted_cost_drop',
               'predicted_relative_cost_drop', 'predicted_residual_step',
               'predicted_residual_step_ratio', 'normalized_correction_norm',
               'roundoff_bound_count', 'accepted_steps', 'rejected_steps',
               'rejected_tail_count', 'last_full_step_cost_change',
               'smallest_rejected_fraction', 'smallest_step_cost_change', 'jacobian_condition_ratio']
    with (GUIDE/'fits.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    table = '\n'.join(
        f"| {row['segment_id'][:8]} / {row['case_id'].removeprefix('bias1_')} | "
        f"{row['model']} / {row['role']} | {row['evaluations']} | "
        f"{row['stationarity_ratio']:.3g} | "
        f"{row['predicted_residual_step_ratio']:.3g} |"
        for row in stalled)
    repeat_table = '\n'.join(
        f"| {row['identity'].split('::')[0][:8]} / {row['identity'].split('::')[2]} | "
        f"{row['primary_converged']} / {row['repeat_converged']} | "
        f"{row['relative_cost_difference']:.3g} | "
        f"{max(row['track_difference_rms_neu_m']):.3g} | {row['qualified_repeatability']} |"
        for row in repeats)
    near = sum(row['roundoff_bound_count'] > 0 for row in stalled)
    text = f'''# Why the boundary-aware trial remains incomplete

The trial finished **17/24 fits** successfully: all six completed controls,
nine of fifteen unfinished primary fits and two of three perturbed repeats.
It improved primary recovery over the earlier continuation trial (8/15) and
rectangular trial (2/15), but **none of the three test stretches became fully
resolved**. It did not qualify for a full recovery run. Published findings remain
**12 globe preferences, zero completed flat preferences and 41 unresolved stretches**.

This diagnosis checks sealed saved results, tangents and receiver-epoch errors.
It performs **zero archival fits and zero native predictions**. One small affine
calculation per saved tangent examines the optimizer's remaining local correction;
these are not additional observations or recovered flight fits.

## Six early stops, one budget failure

**{len(stalled)} failures already pass the gradient check.** Their remaining local
correction predicts a very small improvement in squared error, but a change in the
residual vector greater than the unchanged stability limit. Their actual nonlinear
costs did not decrease after up to 24 halvings of the proposed step. The saved
gradient and stability checks therefore disagree about whether work is complete;
the stricter combined gate correctly keeps these fits unresolved.

| Stretch / processing | Model / start | Calls | Gradient / limit | Residual correction / limit |
|---|---|---:|---:|---:|
{table}

For these six, predicted fractional cost improvement is below 1e-8, while the
relative residual correction exceeds 1e-6. Squared-error improvement and movement
of individual predictions are different quantities; a tiny improvement alone is
insufficient. **{near}/{len(stalled)}** have positive boundary slack of 1e-12 or less.
The earlier one-floating-point-step boundary-start explanation does not account
for these saved endpoints.

**{len(exhausted)} fit exhausts its tangent budget** and still fails stationarity.
It accepts many small fractions of its full local correction. Its largest remaining
correction includes gravity and gyro gains; a full step produces a much worse actual
cost despite the local tangent predicting improvement. This exposes a problem with
taking that full local step on the nonlinear objective, distinct from the six
nearly stationary stops. Increasing the budget might help this case, but has not
been tested and does not fix the early stops.

## What the repeated starts show

The comparison below uses the saved predictions at identical receiver timestamps.
Track difference is the largest axis-specific RMS difference. The original numerical
agreement limits are 1e-6 relative cost and 0.01 m on every axis; both fits must also
pass their own stopping checks. No repeat can replace an unsuccessful primary.

| Stretch / repeated model | Primary / repeat passed | Relative cost difference | Maximum axis RMS difference (m) | Repeatability qualified |
|---|---|---:|---:|---|
{repeat_table}

All three pairs satisfy the cost and track agreement limits, despite opposite
pass/fail stopping outcomes. Their largest axis-specific RMS difference is
**{max(max(row['track_difference_rms_neu_m']) for row in repeats)*1000:.3g} mm**.
This isolates sensitivity of the stopping checks at nearly identical reconstructed
tracks. It does not demonstrate a global optimum or validate a weaker acceptance rule.

`False` in the last column means the full qualification rule failed, even when the
costs and tracks agree. An approximately repeated prediction is useful numerical
evidence; it is not permission to relabel an unresolved fit.

## Smallest useful next test

Before another recovery trial, isolate **prediction/tangent accuracy near the saved
endpoints**. On independently generated integrated-motion controls and a separately
frozen small native diagnostic, compare fresh residual changes with tangent predictions
along predetermined feasible directions over several step sizes. Include a weak
calibration direction and a well-conditioned direction. Check receiver-boundary
timing behavior explicitly. Record objective changes and individual receiver-epoch
prediction changes, rather than relaxing stopping rules to raise completion counts.

The saved artifacts cannot establish a numerical noise floor or inaccurate derivatives:
they do not contain the full residual vectors for every rejected step. Large nonlinear
curvature, cancellation and timing-interval changes remain distinguishable hypotheses,
not established causes. A damped local correction is a candidate to test against
known answers, not a validated repair. Keep bounds, observations and physical models
unchanged; defer all-41 rollout until recovery and repeatability qualify.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-boundary-diagnosis-20261013/build_report.py
```

The CSV includes all 24 starts; the detailed report preserves local corrections and
the three repeat comparisons. The receipt hashes input summaries, journals, tangents,
epochs, audit code and generated artifacts, and records the numerical environment.
'''
    (GUIDE/'README.md').write_text(text)
    sources = [Path(__file__), ROOT/'analysis/lll/ilvis0_boundary_diagnosis.py',
               ROOT/'analysis/tests/test_ilvis0_boundary_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_rectangular_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_recovery_diagnosis.py',
               ROOT/'analysis/lll/ilvis0_solver_refinement.py']
    receipt = dict(inputs={str(RUNTIME.relative_to(ROOT)/name): value for name, value in hashes.items()},
                   sources={str(path.relative_to(ROOT)): digest(path) for path in sources},
                   artifacts={name: digest(GUIDE/name) for name in
                              ('README.md', 'PLAN.md', 'diagnosis.json', 'fits.csv')},
                   environment=dict(python=platform.python_version(), numpy=np.__version__,
                                    scipy=scipy.__version__, platform=platform.platform(),
                                    threads={key: os.environ.get(key) for key in
                                             ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')}),
                   observed_fit_starts=0, native_predictions=0)
    (GUIDE/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(counts=counts, starts=0, native_predictions=0,
                         qualified_repeats=sum(row['qualified_repeatability'] for row in repeats))))


if __name__ == '__main__':
    main()
