# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved whitened training residuals in ESA and generated fits."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def summarize_saved_residual(fit, *, training_epochs=600, lags=(1, 20, 100)):
    """Describe a saved fit; this does not estimate a null distribution."""
    import numpy as np

    local = fit.get('local_linearization', {})
    residual = np.asarray(local.get('residual'), dtype=float)
    if (training_epochs != 600 or residual.shape != (3*training_epochs,) or
            local.get('convention') !=
                'whitened residual derivative by normalized parameter' or
            not np.all(np.isfinite(residual)) or
            any(type(lag) is not int or not 1 <= lag < training_epochs
                for lag in lags) or len(set(lags)) != len(lags)):
        raise ValueError('complete saved 600-report whitened residual required')
    cost = float(residual @ residual)
    if (not math.isfinite(fit.get('residual_sum_squares', math.nan)) or
            abs(cost-fit['residual_sum_squares']) >
                max(1e-8, 1e-10*abs(cost))):
        raise ValueError('saved residual does not reproduce fitted cost')
    values = residual.reshape(training_epochs, 3)
    channels = []
    for axis in range(3):
        series = values[:, axis]
        correlations = {}
        for lag in lags:
            left, right = series[:-lag], series[lag:]
            left_sd, right_sd = np.std(left), np.std(right)
            correlations[str(lag)] = (None if left_sd == 0 or right_sd == 0
                else float(np.mean((left-left.mean())*(right-right.mean()))/
                           (left_sd*right_sd)))
        channels.append(dict(axis=('north', 'east', 'height')[axis],
            rms=float(np.sqrt(np.mean(series*series))),
            mean=float(series.mean()),
            first_half_rms=float(np.sqrt(np.mean(series[:300]**2))),
            second_half_rms=float(np.sqrt(np.mean(series[300:]**2))),
            lag_correlations=correlations))
    return dict(training_epochs=training_epochs, quadratic=cost,
        overall_rms=float(np.sqrt(np.mean(values*values))), channels=channels,
        fit_adjusted_reference_calibrated=False)


def build(root):
    from .esa_fit_adjusted_control_report import build as control_build, _study
    from .esa_fit_adjusted_control_study import LAWS
    from .esa_training_split_study import ID as OBSERVED_ID
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    control = control_build(root)
    generated, lineage = _study(root)
    observed = ClosedStudy(root, 'data/'+OBSERVED_ID)
    try:
        if (observed.completion['state'] != 'complete' or
                set(control['cases']) != set(LAWS) or
                lineage != control['continuation_lineage_sha256']):
            raise ValueError('unchanged sealed generated and observed fits required')
        generated_rows = {}
        for truth in LAWS:
            generated_rows[truth] = {}
            for law in LAWS:
                fit = generated.artifact(truth, law+'/fit.json')
                if (control['cases'][truth]['candidates'][law]['status'] !=
                        'bound_active'):
                    raise ValueError('generated fit status differs')
                generated_rows[truth][law] = summarize_saved_residual(fit)
        observed_rows = {}
        for law in LAWS:
            fit = observed.artifact(law, 'fit.json')
            summary = summarize_saved_residual(fit)
            expected = control['observed_esa_training_reference']['laws'][law][
                'quadratic']
            if abs(summary['quadratic']-expected) > 1e-8:
                raise ValueError('observed reference differs')
            observed_rows[law] = summary
        return dict(version='esa-fit-adjusted-residual-report-v1',
            generated_study=control['study'],
            generated_manifest_sha256=control['study_manifest_sha256'],
            generated_summary_sha256=control['study_summary_sha256'],
            observed_study='data/'+OBSERVED_ID,
            observed_manifest_sha256=observed.completion['manifest_sha256'],
            control_report_source_sha256=control['report_source_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_fit_adjusted_residual_report.py').read_bytes()
                ).hexdigest(),
            generated=generated_rows, observed=observed_rows,
            nonlinear_refit_performed=False,
            later_receiver_values_used=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        generated.close()
        observed.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(generated={truth:{law:row['overall_rms']
        for law,row in laws.items()} for truth,laws in result['generated'].items()},
        observed={law:row['overall_rms']
        for law,row in result['observed'].items()}),sort_keys=True))


if __name__ == '__main__':
    main()
