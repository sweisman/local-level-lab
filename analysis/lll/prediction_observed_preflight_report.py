# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit a sealed no-fit ESA operator preflight without numerical work."""

import argparse
import hashlib
import json
from pathlib import Path

from . import prediction_observed_preflight_study as study


def audit(root, identity=study.IDENTITY):
    from .ilvis0_control_shards import path_within, verify_completion
    from .studies.artifacts import digest

    root = Path(root).resolve()
    directory = root/'data'/identity
    summary = verify_completion(directory)
    manifest = json.loads((directory/'manifest.json').read_bytes())
    completion = json.loads((directory/'completion.json').read_bytes())
    expected = {row['identity']: row for row in study.tasks()}
    actual = {row['identity']: {key: value for key, value in row.items()
                                if key not in ('index', 'shard')}
              for row in manifest['tasks']}
    if (manifest['scope'] != study.SCOPE or actual != expected or
            'scoring' in manifest['inputs'] or
            summary['total'] != 4 or summary['completed'] != 4 or
            summary['scientific_decision'] != 'abstain' or
            summary['observational_coverage_qualified'] is not False):
        raise ValueError('closed no-fit preflight differs from its declared scope')
    rows = []
    for sealed in summary['results']:
        identity_key = sealed['identity']
        envelope = json.loads(path_within(directory, sealed['artifact']).read_bytes())
        result = envelope['result']
        task = expected[identity_key]
        row = dict(identity=identity_key, law=task['payload']['law'],
                   target=task['payload']['target'], passed=sealed['passed'],
                   charged_native_calls=sealed['charged']['native_calls'],
                   error_type=result.get('error_type'), reason=result.get('reason'))
        if sealed['passed']:
            artifact = f'artifacts/{identity_key}/operator-summary.json'
            if artifact not in envelope['artifacts']:
                raise ValueError('passing task lacks sealed operator summary')
            saved = json.loads(path_within(directory, artifact).read_bytes())
            if (digest(path_within(directory, artifact).read_bytes()) !=
                    envelope['artifacts'][artifact] or
                    any(result.get(key) != value for key, value in saved.items()) or
                    result.get('source_id') != study.GROUP_ID or
                    result.get('law') != row['law'] or
                    result.get('target') != row['target'] or
                    result.get('epoch_count') != study.RECEIVER_EPOCHS or
                    result.get('training_epochs') != study.TRAINING_EPOCHS or
                    result.get('training_prefix_packets') != study.TRAINING_PREFIX or
                    result.get('later_receiver_positions_read') is not False or
                    result.get('physical_position_truth_available') is not False or
                    result.get('error_law_calibrated') is not False or
                    any(result.get(key) != 0 for key in
                        ('original_reads', 'protected_reads', 'observed_fits',
                         'scored_epochs')) or
                    not 0 < result.get('native_calls', 0) <=
                    task['limits']['native_calls']):
                raise ValueError('sealed passing task differs from no-fit evidence')
            row.update(native_calls=result['native_calls'],
                       operator_storage_bytes=result['operator_storage_bytes'],
                       state_dimension=result['state_dimension'],
                       elapsed_s=result['elapsed_s'],
                       peak_resident_kib=result['peak_resident_kib'])
        rows.append(row)
    return dict(version='observed-law-preflight-report-v1',
                study='data/'+identity,
                reporter_sha256=hashlib.sha256(
                    (root/'analysis/lll/prediction_observed_preflight_report.py')
                    .read_bytes()).hexdigest(),
                manifest_sha256=completion['manifest_sha256'],
                summary_sha256=completion['summary_sha256'],
                state=summary['state'], passed=summary['passed'],
                completed=summary['completed'], total=summary['total'],
                charged=summary['charged'], rows=rows,
                scientific_decision='abstain',
                observed_coverage_qualified=False)


def render(report):
    success = report['passed'] is True
    lines = ['# Full-size observed-input preflight', '',
             f"**{sum(row['passed'] for row in report['rows'])}/4 technical "
             f"tasks passed.** The sealed study is {report['state']}.", '',
             'This check constructs prediction-error operators on the prepared '
             'ESA development recording. It does not fit an Earth model, score '
             'withheld receiver positions, or test the seven reserved ESA groups.', '',
             '| Supplied error law | Prediction target | Result | Native calls used | '
             'Operator storage | Elapsed | Peak worker memory |',
             '|---|---|---|---:|---:|---:|---:|']
    for row in report['rows']:
        result = ('passed' if row['passed'] else
                  row['error_type'] or row['reason'] or 'failed')
        calls = str(row.get('native_calls', '—'))
        storage = (f"{row['operator_storage_bytes']/1024**2:.1f} MiB"
                   if row['passed'] else '—')
        elapsed = f"{row['elapsed_s']/60:.1f} min" if row['passed'] else '—'
        peak = (f"{row['peak_resident_kib']/1024**2:.2f} GiB"
                if row['passed'] else '—')
        lines.append(f"| {row['law']} | {row['target']} | {result} | "
                     f'{calls} | {storage} | {elapsed} | {peak} |')
    lines += ['',
              ('All four technical constructions passed. This permits a '
               'separately frozen observed development study; it does not '
               'calibrate prediction coverage or support a scientific decision.'
               if success else
               'The technical gate did not pass. Dependent observed fits remain '
               'blocked; the sealed failures and charges remain preserved.'), '']
    return '\n'.join(lines)


def publish(root, *, identity=study.IDENTITY,
            directory='docs/prediction-observed-law-preflight'):
    from .studies.artifacts import atomic, encoded, safe_path
    root = Path(root).resolve()
    report = audit(root, identity)
    output = safe_path(root, directory)
    output.mkdir(parents=True, exist_ok=True)
    atomic(output/'report.json', encoded(report))
    atomic(output/'RESULT.md', render(report).encode())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--study-id', default=study.IDENTITY)
    args = parser.parse_args(argv)
    report = publish(args.root, identity=args.study_id)
    print(f"{sum(row['passed'] for row in report['rows'])}/4 passed; "
          f"state={report['state']}")


if __name__ == '__main__':
    main()
