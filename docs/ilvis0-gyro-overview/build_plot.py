"""Plot preserved raw gyro bins; no decoding, model fitting or GPS correction."""
import csv
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'analysis'))
from lll.compute_budget import environment
os.environ.update(environment(workers=1, threads=4, reserved=0))
os.environ.setdefault('MPLCONFIGDIR', '/tmp/local-level-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    inventory = ROOT / 'docs/ilvis0-current-findings-20261015/current-stretches.csv'
    receipt_path = ROOT / 'docs/ilvis0-position-stability-trial-20261013/analytics-receipt.json'
    receipt = json.loads(receipt_path.read_text())
    cache = ROOT / 'data/ilvis0-stretch-analytics-20261013'
    manifest_path = cache / 'manifest.json'
    assert sha(manifest_path) == receipt['cache_manifest_sha256']
    rows = list(csv.DictReader(inventory.open()))
    assert len(rows) == len({r['segment_id'] for r in rows}) == 53
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in (inventory, receipt_path, manifest_path)}
    traces, records, coverage = [], [], []
    for row in rows:
        path = cache / (row['segment_id'] + '.json.gz')
        digest = sha(path)
        assert digest == receipt['cache_artifacts'][str(path)]
        inputs[str(path.relative_to(ROOT))] = digest
        saved = json.loads(gzip.decompress(path.read_bytes()))
        assert saved['cache_manifest_sha256'] == inputs[str(manifest_path.relative_to(ROOT))]
        assert saved['provenance']['source_sha256'] == row['source_sha256']
        bins = sorted((int(k), v) for k, v in saved['seconds'].items())
        assert bins and all(bins[i][0] - bins[i-1][0] == 1 for i in range(1, len(bins)))
        # Recorded aircraft axes: x forward, y right, z down.
        # Negative y angular increments have the nose-down sign.
        angles, times = [0.0], [0.0]
        angle = 0.0
        for index, (second, bin_) in enumerate(bins, 1):
            duration = float(bin_['duration_s'])
            rate = float(bin_['raw_aircraft'][1])
            assert math.isfinite(rate) and 0 < duration <= 1
            angle += -rate * duration * 180 / math.pi
            # Align the first retained UTC-second boundary; preserve bin spacing.
            elapsed = second - bins[0][0] + 1
            angles.append(angle)
            times.append(elapsed / 60)
            records.append(dict(segment_id=row['segment_id'], bin_index=index,
                elapsed_s=elapsed, source_utc_week_second=second,
                recorded_duration_s=duration, raw_aircraft_y_rads=rate,
                accumulated_nose_down_axis_deg=angle))
        coverage.append(sum(v['duration_s'] for _, v in bins) / float(row['duration_s']))
        traces.append((times, angles))

    maximum = max(len(a) for _, a in traces)
    count = [sum(len(a) > i for _, a in traces) for i in range(maximum)]
    median = [statistics.median(a[i] for _, a in traces if len(a) > i) for i in range(maximum)]
    common = min(len(a) for _, a in traces)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'svg.fonttype': 'none', 'axes.spines.top': False,
                         'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('#fcfcfa')
    ax.set_facecolor('#fcfcfa')
    for index, (times, angles) in enumerate(traces):
        ax.plot(times, angles, color='#477c98', alpha=.28, linewidth=1,
                label='Each of the 53 stretches' if index == 0 else None)
    ax.axhline(0, color='#59646d', linewidth=.9, alpha=.7)
    ax.plot([i/60 for i in range(common)], median[:common], color='#123e50',
            linewidth=3, label='Median: all 53 stretches')
    # Beyond the common interval, a changing subset remains. Show it explicitly.
    tail = [i for i in range(common-1, maximum) if count[i] >= 5]
    ax.plot([i/60 for i in tail], [median[i] for i in tail], color='#123e50',
            linewidth=2.5, linestyle='--', label='Median: available stretches (at least 5)')
    ax.set_xlabel('Elapsed time from first retained one-second bin (minutes)', labelpad=12)
    ax.set_ylabel('Accumulated pitch-axis increments (degrees)\nNose-down positive; axis increases downward', labelpad=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(t[-1] for t, _ in traces) + .15)
    ax.grid(axis='y', alpha=.16)
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.text(.98, .97, f'{sum(a[-1] > 0 for _, a in traces)} of 53 end nose-down',
            transform=ax.transAxes, ha='right', va='top', fontsize=14,
            color='#123e50', fontweight='bold')
    fig.text(.10, .95, 'Recorded gyro motion across 53 flight stretches',
             fontsize=21, fontweight='bold', color='#142f3a')
    fig.text(.10, .905, 'Same starting zero. Recorded mounting axes. No fitted corrections.',
             fontsize=12, color='#475962')
    fig.text(.10, .055, 'Raw pitch-axis sums include aircraft motion and background rotation; they do not isolate surface curvature.',
             fontsize=10, color='#475962')
    fig.text(.10, .026, 'Dashed median uses a shrinking subset as shorter stretches end. Overlapping recorders are not independent replications.',
             fontsize=9, color='#475962')
    fig.subplots_adjust(left=.10, right=.97, top=.86, bottom=.17)
    for extension in ('png', 'svg'):
        target = HERE / ('raw-pitch.' + extension)
        fig.savefig(target, dpi=180)
        if extension == 'svg':
            target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()) + '\n')
    plt.close(fig)
    import io
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
    (HERE / 'plotted-bins.csv.gz').write_bytes(gzip.compress(output.getvalue().encode(), mtime=0))
    summary = dict(stretches=len(traces), nose_down_endpoints=sum(a[-1] > 0 for _, a in traces),
        endpoint_minimum_deg=min(a[-1] for _, a in traces),
        endpoint_median_deg=statistics.median(a[-1] for _, a in traces),
        endpoint_maximum_deg=max(a[-1] for _, a in traces),
        common_interval_s=common-1, minimum_retained_coverage=min(coverage),
        numerical_threads=4, observed_fit_starts=0, native_predictions=0,
        gps_values_in_angle_calculation=False, fused_attitude_in_angle_calculation=False,
        selection_uses_receiver_data=True, original_files_read=0,
        quantity='negative cumulative recorded aircraft-y gyro increments; not Euler pitch or isolated curvature',
        vertical_axis='inverted: positive nose-down increments increase down the page',
        inputs=inputs, source_sha256=sha(Path(__file__)),
        artifacts={name:sha(HERE/name) for name in ('raw-pitch.png','raw-pitch.svg','plotted-bins.csv.gz')})
    (HERE / 'provenance.json').write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','artifacts')}))


if __name__ == '__main__':
    build()
