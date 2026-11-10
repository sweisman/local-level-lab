# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only extraction must not expose withheld receiver coordinates."""
import csv
import hashlib
import io
import json

import pytest

from lll.receiver_training_prefix import extract_prefix


SOURCE = (b'time1_s,latitude_deg,longitude_deg,fix_quality,ellipsoidal_height_m\n'
          b'0,-60,-75,1,12000\n'
          b'1,-59.9,-74.9,1,12001\n'
          b'2,-59.8,-74.8,1,12002\n'
          b'3,-59.7,-74.7,1,12003\n')
SPLIT = dict(segment_id='selected', first_training_utc_week_s=1,
             last_training_utc_week_s=2, first_prediction_utc_week_s=3,
             training_epochs=2)


def _times(payload):
    return [row['time1_s'] for row in csv.DictReader(io.StringIO(payload.decode()))]


def test_extract_prefix_keeps_only_saved_training_epochs():
    split_bytes = json.dumps(SPLIT).encode()
    prefix, receipt = extract_prefix(SOURCE, split_bytes)
    assert _times(prefix) == ['1', '2']
    assert receipt['source_sha256'] == hashlib.sha256(SOURCE).hexdigest()
    assert receipt['split_sha256'] == hashlib.sha256(split_bytes).hexdigest()
    assert receipt['prefix_sha256'] == hashlib.sha256(prefix).hexdigest()
    assert receipt['training_epochs'] == 2
    assert receipt['withheld_receiver_epochs_in_output'] == 0


def test_extract_prefix_rejects_missing_training_epoch():
    missing = SOURCE.replace(b'2,-59.8,-74.8,1,12002\n', b'')
    with pytest.raises(ValueError, match='training epochs'):
        extract_prefix(missing, json.dumps(SPLIT).encode())


def test_extract_prefix_rejects_bad_fix_quality():
    invalid = SOURCE.replace(b'2,-59.8,-74.8,1,12002\n', b'2,-59.8,-74.8,0,12002\n')
    with pytest.raises(ValueError, match='fix quality'):
        extract_prefix(invalid, json.dumps(SPLIT).encode())


def test_extract_prefix_derives_first_second_from_frozen_last_and_count():
    split = {key: value for key, value in SPLIT.items()
             if key != 'first_training_utc_week_s'}
    prefix, receipt = extract_prefix(SOURCE, json.dumps(split).encode())
    assert _times(prefix) == ['1', '2']
    assert receipt['first_time1_s'] == '1'
