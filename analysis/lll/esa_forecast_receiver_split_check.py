# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify nested training-only inputs on the saved ESA development cut."""

import argparse
import csv
import io
import json
from pathlib import Path

from .airquantumgrav_error_policy import build, policies
from .airquantumgrav_inventory import METADATA, RECEIVER_PATH, validate_context
from .esa_confirmation_cadence import DEVELOPMENT, DEVELOPMENT_SHA
from .esa_forecast_receiver_split import QUERY_STRIDE, read_split
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_MATCHED_SPLIT_PLAN.md'
FREEZE = FOLDER+'esa-matched-split-v2-freeze.json'
RESULT = FOLDER+'esa-matched-split-v2-result.json'
SOURCE_BYTES = 21_727_186
TRAINING = (400, 800)
WITHHELD = 120


def run(root, action):
    root = Path(root).resolve()
    reference = (root/DEVELOPMENT).read_bytes()
    if digest(reference) != DEVELOPMENT_SHA:
        raise ValueError('exact archived development study ledger required')
    row, = (r for r in csv.DictReader(io.StringIO(reference.decode())) if r['id'] == 'rolling-800')
    raw = {key:(root/path).read_bytes() for key, path in METADATA.items()}
    context = validate_context(**{key:json.loads(value) for key, value in raw.items()})
    first, last = int(row['train_first']), int(row['later_last'])
    queries = range(first, last+1, QUERY_STRIDE)
    if (row['group_id'] != context['group_id'] or int(row['receiver_row_stride']) != QUERY_STRIDE
            or int(row['training_reports']) != TRAINING[-1] or int(row['later_reports']) != WITHHELD
            or len(queries) != TRAINING[-1]+WITHHELD or queries[TRAINING[-1]] != int(row['later_first'])):
        raise ValueError('the archived development cut and group must match exactly')
    receiver = safe_path(root, RECEIVER_PATH)
    if receiver.stat().st_size != SOURCE_BYTES:
        raise ValueError('original development receiver size required')
    own = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (
        own, PLAN, FOLDER+'ESA_MATCHED_SPLIT_CORRECTION.md',
        'analysis/tests/test_esa_forecast_receiver_split.py',
        'analysis/tests/test_airquantumgrav_receiver.py'))
    freeze = encoded(dict(
        environment=runtime_environment(), sources={p:digest((root/p).read_bytes()) for p in sources},
        metadata_sha256={key:digest(byte) for key, byte in raw.items()},
        receiver_group=context['group_id'], receiver_sha256=context['receiver_sha256'],
        receiver_report_count=context['expected_receiver_epochs'], receiver_path=RECEIVER_PATH,
        development_ledger_sha256=DEVELOPMENT_SHA, receiver_bytes_per_pass=SOURCE_BYTES,
        receiver_passes=len(TRAINING), first_index=first, last_index=last,
        training_reports=TRAINING, withheld_reports=WITHHELD, threads=1,
        maximum_weight_constructions=len(TRAINING)*len(policies()),
        raw_imu_reads=0, protected_reads=0, new_fits=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('unchanged development sources and time layout required')

    splits = {}
    for count in TRAINING:
        offset = TRAINING[-1]-count
        with receiver.open('rb') as stream:
            splits[count] = read_split(
                stream, indices=queries[offset:], training_count=count,
                source_bytes=SOURCE_BYTES, source_reports=context['expected_receiver_epochs'],
                source_sha256=context['receiver_sha256'])
    shorter, longer = (splits[count] for count in TRAINING)
    if (shorter['training_rows'] != longer['training_rows'][-TRAINING[0]:]
            or shorter['query_times_s'] != longer['query_times_s'][-(TRAINING[0]+WITHHELD):]
            or shorter['gps_week'] != longer['gps_week']):
        raise ValueError('training inputs do not share the exact withheld times')
    layouts = {}
    for count, split in splits.items():
        training = split['training_rows']
        layouts[str(count)] = dict(
            training_rows_sha256=digest(encoded(training)),
            training_times_sha256=digest(encoded(split['query_times_s'][:count])),
            first_source_index=queries[TRAINING[-1]-count], last_source_index=queries[TRAINING[-1]-1],
            weights={key:build(training, policy_id=key).configuration for key in policies()})
    later = longer['query_times_s'][TRAINING[-1]:]
    result = dict(freeze_sha256=digest(freeze), training=layouts, withheld_times_sha256=digest(encoded(later)),
                  withheld_first_source_index=queries[TRAINING[-1]], withheld_last_source_index=last,
                  withheld_reports=len(later), submitted_layouts=len(layouts), later_coordinates_decoded=0,
                  new_fits=0, raw_imu_reads=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return {key:value for key, value in result.items() if key != 'training'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.action), sort_keys=True))


if __name__ == '__main__':
    main()
