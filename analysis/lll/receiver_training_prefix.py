# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extract a saved primary-receiver training prefix without later positions."""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json


FIELDS = ('time1_s', 'latitude_deg', 'longitude_deg', 'fix_quality',
          'ellipsoidal_height_m')


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError('finite decimal receiver field required') from error
    if not result.is_finite():
        raise ValueError('finite decimal receiver field required')
    return result


def extract_prefix(source_csv_bytes, split_json_bytes):
    """Return prefix CSV bytes and hashes for a preselected training split.

    Only the saved receiver CSV and split enter. Later position values are never
    converted or emitted; the caller gives only returned bytes to assessment.
    """
    if not isinstance(source_csv_bytes, bytes) or not isinstance(split_json_bytes, bytes):
        raise ValueError('immutable source and split bytes required')
    try:
        split = json.loads(split_json_bytes)
        source_text = source_csv_bytes.decode('utf-8')
        last = _decimal(split['last_training_utc_week_s'])
        future = _decimal(split['first_prediction_utc_week_s'])
        count = split['training_epochs']
        segment_id = split['segment_id']
    except (UnicodeDecodeError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError('valid saved receiver CSV and split required') from error
    if type(count) is not int or count < 1:
        raise ValueError('valid preselected training interval required')
    first = (_decimal(split['first_training_utc_week_s'])
             if 'first_training_utc_week_s' in split else last - (count - 1))
    if (not isinstance(segment_id, str) or not segment_id
            or not first <= last < future):
        raise ValueError('valid preselected training interval required')
    reader = csv.DictReader(io.StringIO(source_text, newline=''))
    if (reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames))
            or any(field not in reader.fieldnames for field in FIELDS)):
        raise ValueError('complete unique receiver columns required')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames,
                            lineterminator='\n')
    writer.writeheader()
    selected = []
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('malformed receiver CSV row')
        epoch = _decimal(row['time1_s'])
        if not first <= epoch <= last:
            continue
        if row['fix_quality'] != '1':
            raise ValueError('training receiver fix quality is not 1')
        for field in ('latitude_deg', 'longitude_deg', 'ellipsoidal_height_m'):
            _decimal(row[field])
        selected.append(epoch)
        writer.writerow(row)
    if (len(selected) != count or selected[0] != first or selected[-1] != last
            or any(right - left != 1 for left, right in zip(selected, selected[1:]))):
        raise ValueError('saved training epochs are missing or not one second apart')
    prefix = output.getvalue().encode('utf-8')
    receipt = dict(segment_id=segment_id, training_epochs=count,
                   first_time1_s=str(first), last_time1_s=str(last),
                   source_sha256=hashlib.sha256(source_csv_bytes).hexdigest(),
                   split_sha256=hashlib.sha256(split_json_bytes).hexdigest(),
                   prefix_sha256=hashlib.sha256(prefix).hexdigest(),
                   withheld_receiver_epochs_in_output=0)
    return prefix, receipt
