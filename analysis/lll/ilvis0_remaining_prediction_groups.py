# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outcome-blind inventory of unused NASA prediction-development groups."""

import csv
import hashlib
import io
import math
from pathlib import Path

from .ilvis0_prediction_pilot import FIELDS


INPUTS = {
    'cohort': 'docs/ilvis0-current-findings-20261015/stretch-analytics.csv',
    'provenance': 'docs/analysis-provenance/recording-groups.csv',
    'pilot': 'docs/ilvis0-prediction-pilot-preparation/selection.csv',
    'transfer': 'docs/prediction-group-transfer/selection.csv',
}
OUTPUT_FIELDS = (*FIELDS, 'group_id')


def select(cohort, provenance, pilot, transfer):
    """Choose one longest stretch per group unused by the two prior studies."""
    if len(cohort) != 53 or len(pilot) != 3 or len(transfer) != 4:
        raise ValueError('unchanged cohort and prior selections required')
    lookup = {}
    for row in provenance:
        if row['archive'] != 'ilvis0':
            continue
        identity = row['record_id']
        if identity in lookup:
            raise ValueError('duplicate recording provenance')
        lookup[identity] = row
    selected = {}
    for row in cohort:
        item = {key: row[key] for key in FIELDS}
        identity = item['segment_id']
        if not identity or identity in selected:
            raise ValueError('duplicate or missing saved stretch')
        source = lookup.get('ilvis0:'+identity)
        if (source is None or source['role'] != 'retrospective_development'
                or not source['group_id']
                or any(source[key] != item[key]
                       for key in ('filename', 'source_sha256'))):
            raise ValueError('verified retrospective provenance required')
        duration = float(item['duration_s'])
        latitude = float(item['mean_latitude_deg'])
        course = float(item['mean_course_deg'])
        minimum = float(item['minimum_ground_speed_kmh'])
        median = float(item['median_ground_speed_kmh'])
        if (not all(math.isfinite(v) for v in
                    (duration, latitude, course, minimum, median))
                or duration < 240 or minimum < 700 or median < minimum
                or not -90 < latitude < 90 or not 0 <= course < 360
                or item['imu_type'] not in ('8', '21')
                or not all(item[key] for key in
                    ('filename', 'source_sha256', 'start_utc', 'end_utc'))):
            raise ValueError('saved route eligibility metadata required')
        item['group_id'] = source['group_id']
        selected[identity] = item
    prior_groups = set()
    for name, rows in (('pilot', pilot), ('transfer', transfer)):
        groups = set()
        for row in rows:
            item = selected.get(row['segment_id'])
            if (item is None or row['group_id'] != item['group_id']
                    or any(row[key] != item[key] for key in FIELDS)):
                raise ValueError(name+' selection differs from saved cohort')
            groups.add(item['group_id'])
        if len(groups) != len(rows) or prior_groups & groups:
            raise ValueError('distinct prior groups required')
        prior_groups.update(groups)
    grouped = {}
    for item in selected.values():
        grouped.setdefault(item['group_id'], []).append(item)
    if len(grouped) != 27 or len(prior_groups) != 7:
        raise ValueError('27 conservative groups and seven prior groups required')
    return [min(grouped[group],
                key=lambda row: (-float(row['duration_s']), row['segment_id']))
            for group in sorted(grouped) if group not in prior_groups]


def build(root):
    """Read only saved tables and return selection plus input/source hashes."""
    root = Path(root).resolve()
    raw = {key: (root/path).read_bytes() for key, path in INPUTS.items()}
    parsed = {key: list(csv.DictReader(io.StringIO(value.decode('utf-8'))))
              for key, value in raw.items()}
    rows = select(**parsed)
    if len(rows) != 20:
        raise ValueError('exact remaining group count required')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=OUTPUT_FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    content = output.getvalue().encode('utf-8')
    return dict(rows=rows, csv=content, receipt=dict(
        version='ilvis0-remaining-prediction-groups-v1',
        policy='longest duration then segment ID; one per unused conservative group',
        input_sha256={INPUTS[key]: hashlib.sha256(value).hexdigest()
                      for key, value in raw.items()},
        selector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        selection_sha256=hashlib.sha256(content).hexdigest(),
        groups=20, prior_groups=7, original_reads=0, observed_fits=0,
        model_outcomes_used=False, protected_esa_reads=0,
        scientific_decision='abstain'))


def publish(root, output='docs/prediction-group-transfer'):
    """Write a durable metadata-only inventory without overwriting it."""
    from .studies.artifacts import atomic, encoded, safe_path

    result = build(root)
    base = safe_path(Path(root).resolve(), output)
    csv_path, receipt_path = (base/'remaining-groups.csv',
                              base/'remaining-groups-receipt.json')
    if csv_path.exists() or receipt_path.exists():
        raise ValueError('fresh inventory output required')
    atomic(csv_path, result['csv'])
    atomic(receipt_path, encoded(result['receipt']))
    return result['receipt']
