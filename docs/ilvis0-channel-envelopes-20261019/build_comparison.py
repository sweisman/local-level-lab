"""Saved-only comparison of the same recordings; no original reads or fits."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'ilvis0-current-findings-20261015'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((HERE/'evidence-receipt.json').read_text())
    baseline = json.loads((BASE/'findings-receipt.json').read_text())
    for directory, source, names in [(HERE, receipt, ['envelopes.csv', 'summary.json']),
            (BASE, baseline, ['current-stretches.csv'])]:
        for name in names:
            if sha(directory/name) != source['artifacts'][name]: raise ValueError('changed evidence: '+name)
    with (HERE/'envelopes.csv').open() as stream: envelopes = list(csv.DictReader(stream))
    with (BASE/'current-stretches.csv').open() as stream: stretches = list(csv.DictReader(stream))
    selected = {row['segment_id'] for row in envelopes}
    records = []
    for row in stretches:
        if row['segment_id'] not in selected: continue
        cases = [r for r in envelopes if r['segment_id'] == row['segment_id']]
        records.append({key: row[key] for key in ('segment_id','filename','source_sha256','start_utc','end_utc',
            'imu_type','duration_s','median_ground_speed_kmh','mean_latitude_deg','mean_course_deg','shape_preference')}
            | dict(acceleration_only_overlap=sum(r['relation']=='overlap' for r in cases),
                   acceleration_only_disjoint=sum(r['relation']=='disjoint' for r in cases),
                   acceleration_only_unsupported=sum(r['supported']!='True' for r in cases),
                   compared_snapshot_windows=3, scientific_decision='abstain'))
    if len(records) != 2 or len(envelopes) != 144: raise ValueError('wrong matched population')
    with (HERE/'matched-recordings.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(records)
    inputs = {str(path.relative_to(HERE.parent.parent)): sha(path) for path in
        (HERE/'evidence-receipt.json', HERE/'envelopes.csv', BASE/'findings-receipt.json', BASE/'current-stretches.csv')}
    (HERE/'comparison-receipt.json').write_text(json.dumps(dict(inputs=inputs,
        artifacts={'matched-recordings.csv':sha(HERE/'matched-recordings.csv')},
        source_sha256=sha(Path(__file__)), original_reads=0, fits=0, native_predictions=0), sort_keys=True)+'\n')
    print('Verified two-recording comparison; no original reads or numerical work.')


if __name__ == '__main__': main()
