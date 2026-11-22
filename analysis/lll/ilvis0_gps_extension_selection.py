# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze receiver epochs for the two still-unused, preselected NASA flight groups."""

from contextlib import closing
import gzip
import json
from pathlib import Path

from . import ilvis0_gps_reconstruction_pilot as pilot, ilvis0_raw_gps_preflight as preflight
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


PLAN = pilot.FOLDER+'GPS_RECONSTRUCTION_EXTENSION_PLAN.md'
OUTPUT = pilot.FOLDER+'gps-reconstruction-extension-selection.json'
CANDIDATES = pilot.FOLDER+'matched-pilot-candidates-receipt.json'
REFERENCES = {
    CANDIDATES: 'd68ce7200bb45cb01b3c421598061a51442ccc52da5bdb7f3ecc9977521f875c',
    pilot.SELECTION: '5bd35e65c4d125e4fbf6d67448744b6cb98e989146cb1e5818e915b760a2613f',
    pilot.PREFLIGHT_RECEIPT: 'da2fbaf6b9964e1a1b6af57286e70faf297efdbb561dc41b8f08836a36dde405',
}
MAX_TAGS = 750


def additional_groups(candidates, originals):
    if (len(candidates) != 4 or len({row['group_id'] for row in candidates}) != 4
            or len({row['segment_id'] for row in candidates}) != 4):
        raise ValueError('four distinct segments and flight groups are required')
    if any(row['passes_checked_metadata'] is not True for row in candidates):
        raise ValueError('every case must pass the original metadata gate')
    prior = {(row['segment_id'], row['group_id']) for row in candidates if row['prior_preflight_group']}
    if len(originals) != 2 or prior != {(row['segment_id'], row['group_id']) for row in originals}:
        raise ValueError('the two earlier flight groups must match the original selection')
    selected = sorted((row for row in candidates if not row['prior_preflight_group']),
                      key=lambda row: int(row['imu_type']))
    if [row['imu_type'] for row in selected] != ['8', '21']:
        raise ValueError('one unused flight group per recorder type is required')
    return selected


def selected_tags(rows):
    tags = pilot.one_per_second([row['gps_millisecond_tag'] for row in rows])
    retained = set(tags)
    if len(tags) > MAX_TAGS or any(row[method]['eligible'] is not True
            for row in rows if row['gps_millisecond_tag'] in retained for method in pilot.METHODS):
        raise ValueError('required input support is missing or the tag limit was exceeded')
    return tags


def build(root):
    inputs = {}
    for path, expected in REFERENCES.items():
        raw = (root/path).read_bytes()
        if digest(raw) != expected:
            raise ValueError('frozen selection input changed: '+path)
        inputs[path] = json.loads(raw)
    candidates = inputs[CANDIDATES]
    if candidates['fit_outcomes_used'] or candidates['pilot_fit_authorized']:
        raise ValueError('a metadata-only candidate selection is required')
    picks = additional_groups(candidates['candidates'], inputs[pilot.SELECTION]['selected'])
    receipt = inputs[pilot.PREFLIGHT_RECEIPT]
    selection = []
    with closing(ClosedStudy(root, 'data/'+preflight.IDENTITY)) as study:
        if (study.completion != {key: receipt[key] for key in ('state', 'manifest_sha256', 'summary_sha256')}
                or study.completion != inputs[pilot.SELECTION]['preflight'] or not study.summary['passed']):
            raise ValueError('the original satellite support check is required')
        by_segment = {row['segment_id']: row for row in study.tasks.values()}
        for pick in picks:
            task = by_segment[pick['segment_id']]
            identity = task['identity']
            if task['source_sha256'] != pick['source_sha256'] or not study.rows[identity]['passed']:
                raise ValueError('receiver support does not match the selected original')
            raw = study.artifact(identity, 'epochs.json.gz', raw=True)
            tags = selected_tags(json.loads(gzip.decompress(raw)))
            selection.append(dict(identity=identity, imu_type=pick['imu_type'],
                segment_id=pick['segment_id'], source_sha256=pick['source_sha256'], group_id=pick['group_id'],
                parent_epochs_sha256=digest(raw), gps_millisecond_tags=tags))
    return dict(version='raw-gps-reconstruction-extension-selection-v1', selected=selection,
        preflight=study.completion, plan_sha256=digest((root/PLAN).read_bytes()), source_inputs=REFERENCES,
        position_solve_starts=sum(len(row['gps_millisecond_tags'])*len(pilot.METHODS) for row in selection),
        maximum_iterations_per_start=pilot.MAX_ITERATIONS, imu_fit_budget=0)


def main():
    root = Path.cwd()
    selection = build(root)
    raw = encoded(selection)
    pilot._write_equal(root/OUTPUT, raw)
    print(json.dumps(dict(tags=[len(row['gps_millisecond_tags']) for row in selection['selected']],
                          starts=selection['position_solve_starts'], sha256=digest(raw)), sort_keys=True))


if __name__ == '__main__':
    main()
