# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render completed residual diagnostics; never import prediction or fitting code."""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from lll.ilvis0_saved_audit import verify_artifacts

HERE = Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def plot(directory, results):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt'] = 'ilvis0-residual-diagnostic-v1'
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), constrained_layout=True)
    for i, sid in enumerate(dict.fromkeys(r['segment_id'] for r in results)):
        subset = [r for r in results if r['segment_id'] == sid and r['case_id'] == 'bias1_unsubtracted']
        for model, label in [('sphere_rotating', 'Rotating globe'), ('sphere_still', 'Still globe'), ('flat_still', 'Flat disc')]:
            r = next(r for r in subset if r['clock'] == 'nominal_200Hz' and r['model'] == model)
            with gzip.open(directory/r['residual_file'], 'rt') as stream:
                data = list(csv.DictReader(stream))
            t = np.array([float(e['elapsed_s']) for e in data])/60
            horizontal = np.hypot(*[[float(e[a+'_residual_m']) for e in data] for a in ('north', 'east')])
            axes[i, 0].plot(t, horizontal, label=label, linewidth=1)
        for clock, label in [('nominal_200Hz', 'Nominal 200 Hz'), ('header_elapsed', 'Packet-header intervals')]:
            r = next(r for r in subset if r['clock'] == clock and r['model'] == 'sphere_rotating')
            with gzip.open(directory/r['residual_file'], 'rt') as stream:
                data = list(csv.DictReader(stream))
            axes[i, 1].plot([float(e['elapsed_s'])/60 for e in data],
                            [float(e['up_residual_m']) for e in data], label=label, linewidth=1)
        axes[i, 0].set_yscale('symlog', linthresh=.1)
        axes[i, 0].set_ylabel('Horizontal error (m)')
        axes[i, 1].set_ylabel('Vertical error (m)')
        for ax in axes[i]:
            ax.set_xlabel('Minutes from first receiver epoch'); ax.grid(alpha=.2); ax.legend(fontsize=8)
        title = 'Completed control' if i == 0 else 'Unfinished diagnostic comparison'
        axes[i, 0].set_title(title+' — nominal timing', fontsize=10)
        axes[i, 1].set_title(title+' — rotating-globe clock check', fontsize=10)
    fig.suptitle('Saved parameters: full retained stretches, fixed-zero removal case', fontsize=12)
    fig.savefig(directory/'residuals.svg', metadata={'Date': None, 'Creator': 'Local Level Lab'})
    plt.close(fig)
    return matplotlib.__version__


def build(directory=HERE):
    directory = Path(directory)
    receipt_path = directory/'evidence-receipt.json'
    receipt = json.loads(receipt_path.read_text())
    verify_artifacts(directory, receipt)
    summary = json.loads((directory/'summary.json').read_text()); results = summary['results']
    identities = {r['identity'] for r in results}
    if (summary['charged_predictions'] != 24 or summary['optimizer_starts'] != 0
            or len(results) != 24 or len(identities) != 24 or any(r['state'] != 'complete' for r in results)):
        raise ValueError('incomplete or incompatible diagnostic publication')
    for r in results:
        if sha(directory/r['residual_file']) != r['residual_sha256'] or not r['baseline_reproduced']:
            raise ValueError('residual integrity/reproduction failure')
    labels = dict(sphere_rotating='Rotating globe', sphere_still='Still globe', flat_still='Flat disc')
    texts = [
        '# Individual residuals and integration timing', '',
        '**The completed control still fits rotating globe much better than still globe or flat disc.** '
        'Recovering individual errors also exposes temporal structure and substantial vertical sensitivity '
        'to the integration clock. The second stretch remains formally unresolved; these diagnostics do '
        'not change the original 12 globe preferences or promote an unfinished comparison.', '',
        'An **IMU (inertial measurement unit)** records turning and acceleration. This pass reuses the '
        'original fitted parameters for two survey-grade IMU21 recordings already chosen for the '
        '[matched solver trial](../ilvis0-solver-trial-20261010/README.md). It evaluates all three models '
        'under both processing cases and two clocks: **24 predictions, zero optimizer starts, no failures**. '
        'The native source/build and numerical environment match the original study. All nominal costs '
        'and both-clock physical RMS errors reproduce the saved evidence within the declared tolerances.', '',
        'The control is `ILVIS0_applanix_57300_610_LVIS_38614965.013` '
        '(7.30 minutes, median ground speed 878.1 km/h). The diagnostic recording is '
        '`ILVIS0_applanix_57320_610_LVIS_38614965.013` '
        '(7.22 minutes, 824.9 km/h). All qualifying receiver epochs and raw increments in '
        'the preselected stretches are retained. Their original source hashes and receiver epochs are '
        'preserved. These two stretches are development checks, not a representative or independent '
        'sample of the whole archive.', '',
        '## Model errors under the original nominal clock', '',
        '| Stretch | Processing case | Model | Original fit status | Horizontal RMS (m) | Vertical RMS (m) | Whitened RMS |',
        '|---|---|---|---|---:|---:|---:|']
    for r in results:
        if r['clock'] != 'nominal_200Hz':
            continue
        a = r['report']['axes']; horizontal = np.hypot(a[0]['physical']['rms'], a[1]['physical']['rms'])
        whitened = np.sqrt(r['cost']/(3*r['report']['epochs']))
        texts.append(f"| {'Control' if r['segment_id'].startswith('570b') else 'Diagnostic'} | "
                     f"{'Retained' if r['case_id'].endswith('unsubtracted') else 'Removal profiled'} | "
                     f"{labels[r['model']]} | {r['baseline_status']} | {horizontal:.4g} | "
                     f"{a[2]['physical']['rms']:.4g} | {whitened:.4g} |")
    texts += ['', '“Retained” fixes upstream Earth-rate removal at zero. “Removal profiled” permits the '
        'original shared removal parameter. Both retain the original ±1 degree/hour constant-offset '
        'allowance. Whitened RMS measures error relative to the assumed covariance, with no degrees-of-freedom '
        'adjustment or statistical-significance claim. Physical metres use each model’s declared coordinate '
        'metric. The original nominal-fit status applies to the saved parameters; header-clock evaluations '
        'have not been optimized or independently checked for stationarity.', '',
        '![Errors along each stretch and fixed-parameter clock sensitivity](residuals.svg)', '',
        'The figure uses the fixed-zero removal case. Its horizontal scale is linear below 0.1 m and '
        'logarithmic above it, so centimetre and tens-of-metres errors remain visible together. These are '
        'the same observations used to fit the parameters, not held-out predictions.', '',
        '## What individual residuals reveal', '',
        '- Rotating-globe nominal residuals are small, but remain temporally correlated after the original '
        'covariance whitening. Across both stretches and cases, centered lag-one correlations are '
        'about 0.42–0.49 north, 0.49–0.59 east and 0.74–0.76 vertically. Receiver intervals are approximately '
        'one second; exact lag durations and longer lags are retained in the diagnostic record. '
        'A small RMS does not establish independent, correctly modeled errors.',
        '- The largest absolute primary-whitened rotating-globe component under nominal timing is '
        'about 0.47; still-globe and flat errors are much larger and have strong temporal structure. '
        'No normalized rotating-globe component exceeds three in these checks. This describes the '
        'chosen covariance and fitted observations, not a calibrated outlier or adequacy test.',
        '- In the diagnostic stretch, north/east rotating-globe physical errors have rank associations '
        'of roughly +0.80/−0.86 with a speed proxy derived from receiver coordinates. Their horizontal '
        'RMS is still only about 0.085 m. Such associations can reflect modeling, coordinate rounding '
        'or shared measurement errors; they do not identify a physical cause. Altitude, latitude and '
        'elapsed time also co-vary along these short routes.', '',
        '## Integration-clock sensitivity', '',
        '| Stretch / processing case | Nominal vertical RMS (m) | Header vertical RMS (m) | Nominal horizontal RMS (m) | Header horizontal RMS (m) |',
        '|---|---:|---:|---:|---:|']
    for r in results:
        if r['clock'] != 'nominal_200Hz' or r['model'] != 'sphere_rotating':
            continue
        h = next(v for v in results if v['segment_id'] == r['segment_id'] and v['case_id'] == r['case_id']
                 and v['model'] == r['model'] and v['clock'] == 'header_elapsed')
        a, b = r['report']['axes'], h['report']['axes']
        texts.append(f"| {'Control' if r['segment_id'].startswith('570b') else 'Diagnostic'} / "
            f"{'retained' if r['case_id'].endswith('unsubtracted') else 'removal profiled'} | "
            f"{a[2]['physical']['rms']:.3f} | {b[2]['physical']['rms']:.3f} | "
            f"{np.hypot(a[0]['physical']['rms'],a[1]['physical']['rms']):.3f} | "
            f"{np.hypot(b[0]['physical']['rms'],b[1]['physical']['rms']):.3f} |")
    texts += ['', 'Replacing nominal 200 Hz intervals with packet-header intervals at the same saved '
        'parameters raises rotating-globe vertical error to about 9.2–9.4 m. The horizontal model-error '
        'separation remains large in these fixed-parameter checks. This does not establish which clock '
        'convention is physically correct or what the best refitted header-clock solution would be. '
        'A matched, reoptimized clock comparison is the next numerical question; all three candidates '
        'must receive the same assumptions and budget.', '',
        '## What is saved and what remains', '',
        '[Axis diagnostics](diagnostics.csv) give distributions, signed means, RMS and lag-one '
        'correlations for every fit/clock. The compressed per-prediction CSV files alongside this guide '
        'preserve every receiver epoch, observed coordinates, coordinate errors, physical errors and '
        'primary/conservative whitened innovations. The report record retains 95th/99th percentiles, '
        'maxima, longer lags and descriptive rank associations.', '',
        'The motion proxies are derivatives of receiver coordinates under an explicitly named reference '
        'globe metric. They are not the recorded VTG speed samples used for eligibility, nor an '
        'independent validation of that metric. Longitude wrapping is preserved in residual calculations. '
        'Cholesky innovations use the stacked latitude/longitude/height order; they are not physical '
        'north/east/up error magnitudes. No temperature channel is invented.', '',
        'No absolute-fit acceptance threshold, held-out test or independent uncertainty calibration '
        'has been established. No original fit, source, selection or scientific decision is changed. '
        'The diagnostic stretch’s small unfinished rotating-globe residual remains useful for solver '
        'diagnosis, but it is not a finished model comparison.', '',
        'Next: specify a small timing/calibration comparison, qualify the revised solver on independent '
        'controls, and assess genuine prediction checks. Exact device documentation remains parallel '
        'work. See the [analysis roadmap](../ANALYSIS_ROADMAP.md).', '',
        '## Reproduction and recovery', '',
        'The numerical run is complete and frozen. Do not launch it again. Packaging does not make '
        'predictions:', '', '```sh',
        'env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_residual_diagnostic.py --package-only',
        'env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-residual-diagnostic-20261010/build_report.py',
        '```', '',
        'The worker has an exclusive lock, immutable identities, pre-evaluation charges, hashed caches '
        'and atomic outputs. Interrupted charged predictions have no automatic retry. The publication '
        'receipt verifies numerical outputs; a separate report receipt records this renderer, its '
        'input receipt and the generated prose/figure. Neither renderer invokes native prediction.', '']
    version = plot(directory, results)
    (directory/'README.md').write_text('\n'.join(texts))
    (directory/'report-receipt.json').write_text(json.dumps(dict(
        version='ilvis0-residual-report-v1', input_receipt_sha256=sha(receipt_path),
        reporting_source_sha256=sha(__file__), reporting_numpy=np.__version__, reporting_matplotlib=version,
        native_predictions=0, optimizer_starts=0,
        artifacts={name: sha(directory/name) for name in ('README.md', 'residuals.svg')}), sort_keys=True, indent=2)+'\n')
    print('Rendered completed residual diagnostics without predictions or fits.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=HERE)
    build(parser.parse_args().directory)
