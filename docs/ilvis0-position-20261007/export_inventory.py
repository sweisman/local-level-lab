# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and package a completed positioning audit; never rerun its solver."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def main():
    evidence = Path(__file__).resolve().parent
    root = evidence.parents[1]
    data = root / 'data/ilvis0-position-20261007'
    completion = load(data / 'completion.json')
    if completion['state'] != 'complete':
        raise ValueError('requires a completed audit')
    for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
        if digest(data / name) != completion[key]:
            raise ValueError('completion evidence mismatch: ' + name)
    manifest = load(data / 'manifest.json')
    summary = load(data / 'summary.json.gz')
    if len(summary['results']) != completion['files']:
        raise ValueError('file count mismatch')
    # The old original hashes are verified via the existing frozen input evidence;
    # this packaging step does not rescan or alter archived originals.
    for name, expected in manifest['inputs'].items():
        if digest(Path(name)) != expected:
            raise ValueError('input changed: ' + name)
    snapshots = evidence / 'source-freeze'
    snapshots.mkdir(exist_ok=True)
    for name, expected in manifest['sources'].items():
        frozen = data / 'source-freeze' / Path(name).name
        if digest(frozen) != expected:
            raise ValueError('source snapshot mismatch: ' + name)
        shutil.copyfile(frozen, snapshots / frozen.name)
    copies = ['manifest.json', 'completion.json', 'summary.json.gz']
    rows = []
    for report in summary['results']:
        task = report['task_id']
        report_name, receipt_name = task + '.json.gz', task + '.receipt.json'
        receipt = load(data / receipt_name)
        if receipt['manifest_sha256'] != completion['manifest_sha256']:
            raise ValueError('receipt manifest mismatch: ' + task)
        if digest(data / report_name) != receipt['report_sha256'] or load(data / report_name) != report:
            raise ValueError('report mismatch: ' + task)
        for name, expected in report['artifacts_sha256'].items():
            if digest(data / name) != expected:
                raise ValueError('position export mismatch: ' + name)
        copies.extend((report_name, receipt_name))
        for method, stats in report['method_summaries'].items():
            row = dict(task_id=task, filename=report['filename'],
                source_sha256=report['source_sha256'], method=method,
                epochs=report['preselected_epochs'], converged=stats['converged'],
                abstained=stats['abstained'], covariance_calibrated=False,
                empirical_earth_fit_attempts=report['empirical_earth_fit_attempts'],
                alternate_seed_max_difference_m=max(c['position_difference_m']
                    for c in report['alternate_seed_checks'] if c['method'] == method),
                range_rms_median_m=stats['range_rms_m']['median'])
            for index, axis in enumerate(('north', 'east', 'up')):
                difference = stats['difference_from_receiver_neu_m'][axis]
                for statistic in ('mean', 'std', 'rms', 'p95_absolute', 'maximum_absolute'):
                    row[axis + '_difference_' + statistic + '_m'] = difference[statistic]
                row[axis + '_formal_sigma_median_m'] = stats['formal_sigma_neu_m'][axis]['median']
                row[axis + '_lag1_difference_correlation'] = stats['lag1_receiver_difference_correlation_neu'][index]
            rows.append(row)
    for name in copies:
        shutil.copyfile(data / name, evidence / name)
    with (evidence / 'inventory.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    artifacts = copies + ['README.md', 'export_inventory.py', 'inventory.csv']
    artifacts += ['source-freeze/' + Path(name).name for name in manifest['sources']]
    receipt = dict(manifest_sha256=completion['manifest_sha256'],
        summary_sha256=completion['summary_sha256'], files=completion['files'],
        method_rows=len(rows), covariance_calibrated=False,
        empirical_earth_fit_attempts=0,
        artifact_sha256={name: digest(evidence / name) for name in sorted(artifacts)})
    (evidence / 'evidence-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(files=completion['files'], inventory_rows=len(rows),
        verified_position_exports=2 * completion['files'], packaged_artifacts=len(artifacts))))


if __name__ == '__main__':
    main()
