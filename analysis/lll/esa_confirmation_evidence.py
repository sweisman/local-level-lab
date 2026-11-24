# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the saved ESA layouts and earlier-only profiles from public evidence."""

import csv
import io
import json
from math import isfinite
from pathlib import Path

from .esa_confirmation_cadence import STRIDE
from .esa_confirmation_queries import GUARD_S, MAX_GAP_S, TICKS, TRAINING, WITHHELD, cases
from .esa_confirmation_training_profile import (
    CADENCE, CADENCE_SHA, FREEZE, PARENTS, REQUEST, RESULT, TIMES, TIMES_SHA, XML, _read, definitions,
)
from .esa_group_evidence import SOURCES
from .studies.artifacts import digest


FREEZE_SHA = 'a53fc89efe55ddfa6b39755e85064ea69c5ff2609f241a83145290fab5daf246'
RESULT_SHA = '0aa9fcfe7193b2b5dfef81bd41b2860b9214316fbef11ba042dd636cdd0a4ec5'
DEVELOPMENT = '187'
IMU_CATALOG = 'docs/external-imu-data/esa-live-imu-files.csv'
IMU_CATALOG_SHA = 'd589c4a64e5b30cef286050c6cc67388a46c80ea6fcb95998a8a1fe5ca0b2dd8'
SPLITS = tuple(str(n) for n in TRAINING)
PROFILE_FIELDS = ('horizontal_speed_mps', 'absolute_course_rate_degps', 'ellipsoidal_height_m',
                  'absolute_vertical_speed_mps', 'pdop', 'satellites', 'reported_height_sd_m')


def verify_layout(layout):
    earlier, later = layout['training'], layout['withheld']
    if (layout['supported'] is not True or layout['source_stride'] != STRIDE
            or set(earlier) != set(SPLITS) or not 0 < layout['maximum_source_gap_s'] <= MAX_GAP_S
            or not 0 < layout['maximum_query_gap_s'] <= STRIDE*layout['maximum_source_gap_s']):
        raise ValueError('the verified cadence and both training lengths are required')
    for count, block in zip((*TRAINING, WITHHELD), (*(earlier[n] for n in SPLITS), later), strict=True):
        start, end = block['first_source_index'], block['last_source_index']
        t0, t1 = block['first_time_s'], block['last_time_s']
        if (block['reports'] != count or not 0 <= start < end or end-start != STRIDE*(count-1)
                or not 0 <= t0 < t1 < 604800 or t1-t0 != block['duration_s']):
            raise ValueError('the saved report indices and elapsed times must agree')
    short, long = (earlier[n] for n in SPLITS)
    if (short['last_source_index'] != long['last_source_index']
            or short['last_time_s'] != long['last_time_s']
            or short['first_time_s'] <= long['first_time_s']
            or later['first_source_index'] != long['last_source_index']+STRIDE
            or not 0 < later['first_time_s']-long['last_time_s'] <= layout['maximum_query_gap_s']):
        raise ValueError('both earlier-only layouts must predict the same withheld reports')
    return long['first_time_s'], later['last_time_s']


def _profile_comparisons(profiles):
    for recording in profiles.values():
        if set(recording) != set(SPLITS):
            raise ValueError('each recording needs both saved profiles')
        for n, summary in recording.items():
            if summary['rows'] != int(n) or set(summary) != {'rows', *PROFILE_FIELDS}:
                raise ValueError('profile fields and training counts must match the plan')
            for field in PROFILE_FIELDS:
                distribution = summary[field]
                p05, median, p95 = (distribution[key] for key in ('p05', 'median', 'p95'))
                if not all(map(isfinite, (p05, median, p95))) or not p05 <= median <= p95:
                    raise ValueError('finite ordered profile quantiles required')
    development = profiles[DEVELOPMENT]
    outside, summary = {}, {}
    for n, baseline in development.items():
        other = {name: value[n] for name, value in profiles.items() if name != DEVELOPMENT}
        outside[n] = {name: sorted(field for field in PROFILE_FIELDS
                                  if not baseline[field]['p05'] <= row[field]['median'] <= baseline[field]['p95'])
                      for name, row in other.items()}
        pdop = [row['pdop']['median'] for row in other.values()]
        summary[n] = dict(development_median_pdop=baseline['pdop']['median'],
                          reserved_median_pdop_range=[min(pdop), max(pdop)],
                          higher_median_pdop=sum(p > baseline['pdop']['median'] for p in pdop),
                          higher_p95_course_rate=sum(row['absolute_course_rate_degps']['p95'] >
                                                     baseline['absolute_course_rate_degps']['p95']
                                                     for row in other.values()))
    return outside, summary


def _instrument_files(root):
    raw = (root/IMU_CATALOG).read_bytes()
    if digest(raw) != IMU_CATALOG_SHA:
        raise ValueError('the original ESA instrument file catalog is required')
    catalog = [row['filename'] for row in csv.DictReader(io.StringIO(raw.decode('utf-8')))]
    policy = _read(root, *SOURCES['policy'])
    development, reserved = (policy[key] for key in ('development_files', 'confirmation_files'))
    if sorted(catalog) != sorted(development+reserved) or {name.rsplit('_', 1)[-1] for name in catalog} != {'rqh01.txt'}:
        raise ValueError('development and reserved instrument labels differ from the verified catalog')
    return dict(catalog_label='RQH01', development_files=len(development), reserved_files=len(reserved))


def check_public(root):
    selected = cases(root)
    cadence = _read(root, CADENCE, CADENCE_SHA)
    times = _read(root, TIMES, TIMES_SHA)
    if (cadence['cases'] != selected or set(times['records']) != set(selected)
            or times['freeze_sha256'] != CADENCE_SHA or not len(selected) == times['groups'] == 7
            or times['supported_groups'] != len(selected)):
        raise ValueError('the seven exact reserved identities and layouts are required')
    for name, layout in times['records'].items():
        start, end = verify_layout(layout)
        lower, upper = (tick/TICKS for tick in selected[name]['slice_ticks'])
        if start < lower+GUARD_S or end > upper-GUARD_S:
            raise ValueError('a layout leaves the timing-verified slice')
    freeze = _read(root, FREEZE, FREEZE_SHA)
    result = _read(root, RESULT, RESULT_SHA)
    if (freeze['cases'] != definitions(root) or freeze['source_sha256'] != PARENTS
            or digest((root/REQUEST).read_bytes()) != freeze['qualification_sha256']
            or digest((root/XML).read_bytes()) != freeze['tests_sha256']
            or result['freeze_sha256'] != FREEZE_SHA or result['reserved_groups'] != len(selected)
            or set(result['records']) != set(freeze['cases'])):
        raise ValueError('the saved earlier-only profile inputs and qualification must match')
    for artifact, withheld_values_key in ((times, 'receiver_coordinates_decoded'),
                                           (result, 'later_coordinates_decoded')):
        if (artifact['scientific_decision'] != 'abstain'
                or any(artifact[key] != 0 for key in ('new_fits', 'raw_imu_reads', 'protected_outcome_reads',
                                                    withheld_values_key))):
            raise ValueError('qualification receipts must preserve the protected observations')
    if times['confirmed_eligible'] != 0:
        raise ValueError('a timing layout alone cannot qualify eligibility')
    outside, summary = _profile_comparisons(result['records'])
    if outside != result['outside_development_central_90_percent']:
        raise ValueError('the reported profile comparisons must reproduce')
    return dict(groups=len(selected), query_layouts=len(selected)*len(TRAINING),
                training_profiles=len(result['records'])*len(TRAINING), compared_profiles=summary,
                instrument_files=_instrument_files(root),
                confirmed_eligible=0, protected_outcome_reads=0, new_fits=0, scientific_decision='abstain')


if __name__ == '__main__':
    print(json.dumps(check_public(Path.cwd()), sort_keys=True))
