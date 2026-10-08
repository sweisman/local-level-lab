# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and package completed information diagnostics; no predictor calls."""
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


def main():
    evidence = Path(__file__).resolve().parent
    data = evidence.parents[1]/'data/ilvis0-information-20261007'
    complete = load(data/'completion.json')
    if complete['state'] != 'complete':
        raise ValueError('completed diagnostics required')
    for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
        if digest(data/name) != complete[key]:
            raise ValueError('completion mismatch')
    manifest = load(data/'manifest.json'); summary = load(data/'summary.json.gz')
    for name, expected in manifest['inputs'].items():
        if digest(Path(name)) != expected:
            raise ValueError('input changed')
    snapshots = evidence/'source-freeze'; snapshots.mkdir(exist_ok=True)
    for name, expected in manifest['sources'].items():
        source = data/'source-freeze'/Path(name).name
        if digest(source) != expected:
            raise ValueError('snapshot mismatch')
        shutil.copyfile(source, snapshots/source.name)
    tasks = [item['task'] for item in summary['results']]
    if len(set(tasks)) != len(tasks) or set(tasks) != set(manifest['tasks']):
        raise ValueError('missing or duplicate task')
    rows = []
    for item in summary['results']:
        r = item['result']; saved = load(data/(item['task']+'.json'))
        expected = hashlib.sha256(json.dumps(r, sort_keys=True, allow_nan=False).encode()).hexdigest()
        if (saved['result_sha256'] != expected or saved['result'] != r
                or saved['manifest_sha256'] != complete['manifest_sha256'] or saved['task'] != item['task']):
            raise ValueError('control receipt mismatch')
        for step in r['information']['steps']:
            for parameter, stats in step['parameters'].items():
                rows.append(dict(task=item['task'], duration_s=r['duration_s'], motion=r['motion'],
                    assumption=r['assumption']['name'], normalized_central_step=step['normalized_central_step'],
                    parameter=parameter, **stats,
                    modes_above_unit_information=step['modes_above_unit_information'],
                    proxy_subtracted_modes=step['modes_above_unit_information_with_proxy_subtracted'],
                    proxy_added_modes=step['modes_above_unit_information_with_proxy_added'],
                    maximum_resolution_operator_change=r['information']['maximum_resolution_operator_change'],
                    artificial_reference_penalty=True, covariance_calibrated=False,
                    empirical_earth_fit_attempts=0))
    with (data/'control-starts.jsonl').open() as stream:
        starts = [json.loads(line) for line in stream]
    if (any(r['start'] != i+1 or r['task'] not in manifest['tasks'] or
            r['manifest_sha256'] != complete['manifest_sha256'] for i,r in enumerate(starts))
            or len(starts) > manifest['maximum_total_starts'] or set(r['task'] for r in starts) != set(tasks)
            or any(sum(r['task'] == t for r in starts) > 2 for t in tasks)):
        raise ValueError('start journal mismatch')
    copies = ['manifest.json', 'completion.json', 'summary.json.gz', 'control-starts.jsonl']
    for name in copies:
        shutil.copyfile(data/name, evidence/name)
    with (evidence/'inventory.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    artifacts = copies+['README.md', 'export_inventory.py', 'inventory.csv']
    artifacts += ['source-freeze/'+Path(name).name for name in manifest['sources']]
    receipt = dict(verified_tasks=len(tasks), starts=len(starts), parameter_step_rows=len(rows),
        artifact_sha256={name:digest(evidence/name) for name in sorted(artifacts)})
    (evidence/'evidence-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(verified_tasks=len(tasks), starts=len(starts), parameter_step_rows=len(rows))))


if __name__ == '__main__':
    main()
