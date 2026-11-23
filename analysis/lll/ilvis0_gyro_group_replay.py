# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the fixed NASA pitch predictions at matched fields by recording group."""

import argparse
from collections import defaultdict
import csv
import gzip
import io
from itertools import product
import json
import math
from pathlib import Path
from statistics import median
import sys

from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


FOLDER = Path('docs/ilvis0-gyro-companion-v2')
RECEIPT_SHA = '6b58054786e515c9066e09c41de5b237ca46b0c2af20693f919e202b7a42c0e6'
SCENARIOS = 'scenario-comparisons.csv.gz'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
POSE_COLUMNS = ('crab_deg', 'roll_deg', 'pitch_deg')
POSES = tuple(product((-10., 0., 10.), (-3., 0., 3.), (-3., 0., 3.)))
REMOVALS = (0., .5, 1.)
GRID = tuple(product(POSES, REMOVALS))
REFERENCE = GRID.index(((0., 0., 0.), 0.))
CONTRASTS = ('shape_at_zero_field', 'shape_at_specified_field', 'field_on_globe')
STRETCH_COUNT = 53
GROUP_COUNT = 27
MAX_ROWS = STRETCH_COUNT * len(GRID) * len(MODELS)


def read_predictions(packed):
    """Validate the full grid and identical measured support for paired rows."""
    predictions = defaultdict(dict)
    metadata = {}
    with io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(packed)), newline='') as stream:
        for i, row in enumerate(csv.DictReader(stream), 1):
            identity = row['segment_id']
            pose = tuple(float(row[name]) for name in POSE_COLUMNS)
            attempt = (pose, float(row['removal']), row['model'])
            observed = float(row['observed_nose_down_dph'])
            rate = float(row['predicted_nose_down_dph'])
            binding = (row['group_id'], observed, row['source_sha256'],
                       row['matched_bins'], row['matched_duration_s'])
            if (i > MAX_ROWS or not identity or not binding[0] or not math.isfinite(observed)
                    or not math.isfinite(rate) or attempt in predictions[identity]
                    or row['supported'] != 'True' or row['fused_attitude_used'] != 'False'
                    or metadata.setdefault(identity, binding) != binding):
                raise ValueError('invalid scenario or unmatched observation support')
            predictions[identity][attempt] = rate
    expected = {(pose, fraction, model) for pose, fraction in GRID for model in MODELS}
    if (len(predictions) != STRETCH_COUNT or len({row[0] for row in metadata.values()}) != GROUP_COUNT
            or any(set(attempts) != expected for attempts in predictions.values())):
        raise ValueError('original complete scenario and recording group grid required')
    return predictions, metadata


def differences(attempts, pose, removal, observed):
    # The logged subtraction projects the same field into each model's own aircraft axes.
    def rate(model, fraction):
        return attempts[(pose, fraction, model)]

    for model in MODELS:
        midpoint = (rate(model, 0.)+rate(model, 1.))/2
        if not math.isclose(rate(model, .5), midpoint, abs_tol=1e-10, rel_tol=0.):
            raise ValueError('the saved field-removal contrast is not affine')
    if not math.isclose(rate('sphere_rotating', 1.), rate('sphere_still', 0.),
                        abs_tol=1e-10, rel_tol=0.):
        raise ValueError('globe field removal is inconsistent')
    disc = rate('flat_still', removal)
    disc_with_field = disc + rate('flat_still', 0.) - rate('flat_still', 1.)
    globe = rate('sphere_still', removal)
    globe_with_field = rate('sphere_rotating', removal)
    return (abs(observed-disc)-abs(observed-globe),
            abs(observed-disc_with_field)-abs(observed-globe_with_field),
            abs(observed-globe)-abs(observed-globe_with_field))


def summarize(group_scores):
    groups = {group: dict(reference_dph=values[REFERENCE], minimum_dph=min(values),
                         maximum_dph=max(values)) for group, values in sorted(group_scores.items())}
    common = [median(values) for values in zip(*group_scores.values(), strict=True)]
    return dict(
        reference_dph=common[REFERENCE], same_assumptions_range_dph=[min(common), max(common)],
        group_specific_assumptions_range_dph=[median(r['minimum_dph'] for r in groups.values()),
                                             median(r['maximum_dph'] for r in groups.values())],
        reference_groups_positive=sum(r['reference_dph'] > 0 for r in groups.values()),
        reference_groups_negative=sum(r['reference_dph'] < 0 for r in groups.values()),
        positive_in_all_settings=sum(r['minimum_dph'] > 0 for r in groups.values()),
        negative_in_all_settings=sum(r['maximum_dph'] < 0 for r in groups.values()),
        groups=groups)


def compare(data, metadata):
    rows = defaultdict(list)
    for identity, attempts in sorted(data.items()):
        group, observed, *_ = metadata[identity]
        rows[group].append([differences(attempts, pose, removal, observed) for pose, removal in GRID])
    result = {name: {} for name in CONTRASTS}
    for group, tracks in sorted(rows.items()):
        cells = [[median(values) for values in zip(*track_scores, strict=True)]
                 for track_scores in zip(*tracks, strict=True)]
        for name, values in zip(CONTRASTS, zip(*cells, strict=True), strict=True):
            result[name][group] = values
    return {name: summarize(scores) for name, scores in result.items()}


def run(root, action):
    root = Path(root).resolve()
    folder = root/FOLDER
    receipt = (folder/'evidence-receipt.json').read_bytes()
    if digest(receipt) != RECEIPT_SHA:
        raise ValueError('original gyro comparison receipt required')
    scenario_hash = json.loads(receipt)['artifacts'][SCENARIOS]
    own = Path(__file__).relative_to(root).as_posix()
    inputs = (own, (FOLDER/'MATCHED_GROUP_PLAN.md').as_posix())
    freeze = encoded(dict(
        source_receipt_sha256=RECEIPT_SHA, scenarios_sha256=scenario_hash,
        sources={name:digest((root/name).read_bytes()) for name in inputs},
        python=sys.version, groups=GROUP_COUNT, stretches=STRETCH_COUNT,
        maximum_input_rows=MAX_ROWS, settings_per_pair=len(GRID), new_fits=0,
        original_reads=0, protected_reads=0))
    path = folder/'matched-group-freeze.json'
    if action == 'freeze':
        _write_equal(path, freeze)
        return dict(freeze_sha256=digest(freeze))
    if path.read_bytes() != freeze:
        raise ValueError('unchanged matched comparison freeze required')
    packed = (folder/SCENARIOS).read_bytes()
    if digest(packed) != scenario_hash:
        raise ValueError('scenario file differs from the published receipt')
    result = dict(freeze_sha256=digest(freeze), comparisons=compare(*read_predictions(packed)),
                  stretches=STRETCH_COUNT, groups=GROUP_COUNT, settings=len(GRID),
                  new_fits=0, original_reads=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(folder/'matched-group-result.json', encoded(result))
    return {key: value for key, value in result.items() if key != 'comparisons'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'check'))
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.action), sort_keys=True))


if __name__ == '__main__':
    main()
