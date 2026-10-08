# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify/package completed correlated motion controls without repeating fits."""
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


def result_hash(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()


def main():
    evidence = Path(__file__).resolve().parent
    data = evidence.parents[1]/'data/ilvis0-correlated-controls-20261007'
    complete = load(data/'completion.json')
    if complete['state'] != 'complete':
        raise ValueError('completed controls required')
    for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
        if digest(data/name) != complete[key]:
            raise ValueError('completion evidence hash mismatch')
    manifest = load(data/'manifest.json'); summary = load(data/'summary.json.gz')
    for name, expected in manifest['inputs'].items():
        if digest(Path(name)) != expected:
            raise ValueError('input hash mismatch')
    snapshots = evidence/'source-freeze'; snapshots.mkdir(exist_ok=True)
    for name, expected in manifest['sources'].items():
        source = data/'source-freeze'/Path(name).name
        if digest(source) != expected:
            raise ValueError('snapshot mismatch')
        shutil.copyfile(source, snapshots/source.name)
    with (data/'control-starts.jsonl').open() as stream:
        starts = [json.loads(line) for line in stream]
    if any(r['start'] != i+1 or r['manifest_sha256'] != complete['manifest_sha256'] or
           r['task'] not in manifest['tasks'] for i, r in enumerate(starts)):
        raise ValueError('start ledger mismatch')
    rows = []
    for result in summary['results']:
        task = result['case']+'__'+result['assumption']['name']
        saved = load(data/(task+'.json'))
        if saved['manifest_sha256'] != complete['manifest_sha256'] or saved['task'] != task or (
                saved['result'] != result or saved['result_sha256'] != result_hash(result)):
            raise ValueError('per-control result mismatch')
        for parameter, precision in result['local_precision']['marginal_precision'].items():
            rows.append(dict(case=result['case'], assumption=result['assumption']['name'],
                parameter=parameter, unit=precision['unit'], truth=result['truth'].get(parameter, 0.),
                estimate=result['noiseless_fit']['parameters'][parameter],
                assumed_bound=result['bounds'][parameter], noiseless_recovery_passed=result['noiseless_recovery_passed'],
                converged=result['noiseless_fit']['converged'],
                active_parameters=len(result['bounds']),
                fit_nuisance_rank=result['noiseless_fit']['nuisance_rank'],
                truth_tangent_rank=result['local_precision']['nuisance_rank'],
                local_sigma=precision['local_sigma'], sigma_to_assumed_bound=precision['sigma_to_assumed_parameter_bound'],
                covariance_sha256=result['covariance_sha256'],
                residual_evaluations=result['noiseless_fit']['evaluations'],
                diagnostic_predictions=result['diagnostic_prediction_evaluations'],
                covariance_calibrated=False, empirical_earth_fit_attempts=0))
    copies = ['manifest.json', 'completion.json', 'summary.json.gz', 'control-starts.jsonl']
    for name in copies:
        shutil.copyfile(data/name, evidence/name)
    with (evidence/'inventory.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    artifacts = copies+['README.md', 'inventory.csv', 'export_inventory.py']
    artifacts += ['source-freeze/'+Path(name).name for name in manifest['sources']]
    receipt = dict(manifest_sha256=complete['manifest_sha256'], controls=len(summary['results']),
        starts=len(starts), parameter_rows=len(rows), covariance_calibrated=False,
        empirical_earth_fit_attempts=0,
        artifact_sha256={name:digest(evidence/name) for name in sorted(artifacts)})
    (evidence/'evidence-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(verified_controls=len(summary['results']), starts=len(starts), parameter_rows=len(rows))))


if __name__ == '__main__':
    main()
