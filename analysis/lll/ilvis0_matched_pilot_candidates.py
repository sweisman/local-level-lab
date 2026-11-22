# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep the future NASA pilot selection independent of fit outcomes."""

import csv
import itertools
import json
from pathlib import Path

from .ilvis0_matched_observed_inputs import FOLDER, RECEIPT, _write_equal
from .ilvis0_matched_pilot_audit import INPUTS
from .studies.artifacts import digest, encoded


ELIGIBILITY = FOLDER+'matched-pilot-metadata.json'
PLAN = FOLDER+'MATCHED_PILOT_CANDIDATES_PLAN.md'
OUTPUT = FOLDER+'matched-pilot-candidates-receipt.json'


def select(rows):
    eligible = [row for row in rows if row['passes_checked_metadata']]
    if any(row['mean_latitude_deg']>=0. for row in eligible):
        raise ValueError('the southern reservation requires the original southern-only inventory')
    imu8 = sorted((row for row in eligible if row['imu_type']=='8'), key=lambda r:r['course_sector'])
    groups = {row['group_id'] for row in imu8}
    if len(groups)!=2 or [row['course_sector'] for row in imu8]!=['east', 'south']:
        raise ValueError('exact east and south IMU8 controls required')
    imu21 = sorted((row for row in eligible if row['imu_type']=='21' and row['group_id'] not in groups),
                   key=lambda row:(-row['mean_latitude_deg'], row['segment_id']))
    pairs = [(north, south) for north, south in itertools.combinations(imu21, 2)
             if north['group_id']!=south['group_id']]
    if not pairs:
        raise ValueError('distinct IMU21 flight groups required')
    best = min(pairs, key=lambda p:(p[1]['mean_latitude_deg']-p[0]['mean_latitude_deg'],
                                   p[0]['segment_id'], p[1]['segment_id']))
    return [*imu8, *best]


def build(root):
    data = {path:(root/path).read_bytes() for path in (ELIGIBILITY, PLAN, INPUTS[0], RECEIPT)}
    eligibility = json.loads(data[ELIGIBILITY])
    rows = eligibility['rows']
    if (len(rows)!=53 or sum(r['passes_checked_metadata'] for r in rows)!=21
            or len({r['group_id'] for r in rows if r['passes_checked_metadata']})!=18
            or eligibility['inspected_fit_outcomes']
            or digest(data[INPUTS[0]])!=eligibility['inputs'][INPUTS[0]]):
        raise ValueError('original 53-stretch engineering inventory required')
    baseline = {row['segment_id']:row for row in csv.DictReader(data[INPUTS[0]].decode().splitlines())}
    groups = {row['segment_id']:row['group_id'] for row in rows}
    earlier = {groups[case['segment_id']] for case in json.loads(data[RECEIPT])['recordings']}
    if len(baseline)!=53 or len(earlier)!=2 or set(baseline)!=set(groups):
        raise ValueError('changed candidate or preflight group identities')
    reserved = []
    for case in select(rows):
        identity = case['segment_id']
        source = baseline[identity]
        if any(float(source[key])!=case[key] for key in ('mean_latitude_deg','mean_course_deg')):
            raise ValueError('changed saved route geometry')
        reserved.append(dict(case, prior_preflight_group=case['group_id'] in earlier,
            **{key:source[key] for key in ('filename','start_utc','end_utc','source_sha256')},
            **{key:float(source[key]) for key in ('duration_s','median_ground_speed_kmh')}))
    return dict(inputs={path:digest(raw) for path,raw in data.items()},
                source_sha256=digest(Path(__file__).read_bytes()), candidates=reserved, distinct_groups=4,
                fit_outcomes_used=False, native_calls=0, pilot_fit_authorized=False,
                scope='metadata reservation for a possible southern pilot')


if __name__=='__main__':
    root = Path.cwd()
    payload = encoded(build(root))
    _write_equal(root/OUTPUT, payload)
    print(digest(payload))
