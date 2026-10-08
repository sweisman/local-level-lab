# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify/package a completed GPS sensitivity run without recomputing it."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    evidence = Path(__file__).resolve().parent
    data = evidence.parents[1]/'data/ilvis0-gps-sensitivity-20261007'
    complete = load(data/'completion.json')
    if complete['state'] != 'complete':
        raise ValueError('completed audit required')
    for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
        if digest(data/name) != complete[key]:
            raise ValueError('completion hash mismatch')
    manifest = load(data/'manifest.json'); summary = load(data/'summary.json.gz')
    if len(summary['results']) != complete['files']:
        raise ValueError('file count mismatch')
    for name, expected in manifest['inputs'].items():
        if digest(Path(name)) != expected:
            raise ValueError('input hash mismatch: '+name)
    snapshots = evidence/'source-freeze'; snapshots.mkdir(exist_ok=True)
    for name, expected in manifest['sources'].items():
        source = data/'source-freeze'/Path(name).name
        if digest(source) != expected:
            raise ValueError('snapshot hash mismatch: '+name)
        shutil.copyfile(source, snapshots/source.name)
    copies = ['manifest.json', 'completion.json', 'summary.json.gz']
    means = []; derivatives = []
    for report in summary['results']:
        task = report['task_id']; name = task+'.json.gz'; receipt = task+'.receipt.json'
        r = load(data/receipt)
        if r['manifest_sha256'] != complete['manifest_sha256'] or r['report_sha256'] != digest(data/name):
            raise ValueError('per-file receipt mismatch')
        if load(data/name) != report:
            raise ValueError('per-file report mismatch')
        for artifact, expected in report['artifacts_sha256'].items():
            if digest(data/artifact) != expected:
                raise ValueError('window export mismatch')
        copies.extend((name, receipt))
        base = dict(task_id=task, filename=report['filename'], source_sha256=report['source_sha256'],
            epochs=report['epochs'], covariance_calibrated=False, empirical_earth_fit_attempts=0)
        for row in report['mean_position_sensitivity']:
            entry = base | dict(method=row['method'], assumption=row['assumption'])
            for i, axis in enumerate(('north', 'east', 'up')):
                entry[axis+'_mean_sigma_m'] = row['sigma_neu_m'][i]
                entry[axis+'_ratio_to_formal_iid'] = row['sigma_ratio_to_formal_iid'][i]
            means.append(entry)
        for row in report['uncertainty_summaries']:
            entry = base | {key:row[key] for key in ('method', 'assumption', 'span_s')}
            for kind in ('velocity', 'acceleration'):
                for axis in ('north', 'east', 'up'):
                    stats = row[kind+'_sigma_neu'][axis]
                    entry[kind+'_'+axis+'_median_sigma'] = stats.get('median')
                    entry[kind+'_'+axis+'_p95_sigma'] = stats.get('p95')
                    entry[kind+'_'+axis+'_supported_windows'] = stats['samples']
            derivatives.append(entry)
    for name in copies:
        shutil.copyfile(data/name, evidence/name)
    write_csv(evidence/'mean-position-sensitivity.csv', means)
    write_csv(evidence/'kinematic-sensitivity.csv', derivatives)
    artifacts = copies+['README.md', 'export_inventory.py',
        'mean-position-sensitivity.csv', 'kinematic-sensitivity.csv']
    artifacts += ['source-freeze/'+Path(name).name for name in manifest['sources']]
    receipt = dict(manifest_sha256=complete['manifest_sha256'], files=complete['files'],
        covariance_calibrated=False, empirical_earth_fit_attempts=0,
        artifact_sha256={name:digest(evidence/name) for name in sorted(artifacts)})
    (evidence/'evidence-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(files=complete['files'], mean_rows=len(means),
        derivative_rows=len(derivatives), verified_window_exports=complete['files'])))


if __name__ == '__main__':
    main()
