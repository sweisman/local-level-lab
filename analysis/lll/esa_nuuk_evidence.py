# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the two permanent Nuuk support sets and their station-error bounds."""

from collections import Counter
from contextlib import closing
import json

from . import esa_nuuk_carrier_screen as screen
from . import esa_nuuk_clock_aware as clock
from . import esa_nuuk_near_stations as near
from .esa_airborne_carrier_evidence import _check_rows, _close, verify_stations
from .esa_ground_reference_evidence import _require_values
from .studies.closed import ClosedStudy


REPORTS = (
    (near, screen.PARENT_SHA, 'evidence', 'shared-range-evidence.json'),
    (screen, clock.AUDIT_SHA, 'rows', 'interval-screen.json'),
    (clock, '00216724a283a8fa4d78156ce61f129f9f2842334f574948d9ef7e93b627fbde',
     'evidence', 'shared-range-evidence.json'),
)


def _summary(report, expected_times):
    table = report['evidence']
    rows = table['near']
    gap = report['score_gap']
    shares = report['nearby_shares']
    parent = dict(score_gap=gap, withheld_rows=[dict(row, nkar_m=row['museum_m'], qaq_m=row['permanent_m'])
                                               for row in rows])
    bounds = dict(ranges=report['nearby_ranges'], intervals=report['nearby_intervals'], score_gap=gap,
                  station_score_shares=[shares['museum'], shares['permanent']],
                  witnesses=table['witnesses'], cases=report['cases'])
    count = verify_stations(parent, bounds, expected_times=expected_times)
    fields = ('museum_m', 'permanent_m', 'qaqortoq_m')
    triple = table['triple']
    _check_rows(triple, 'start_gps_s', (*fields, 'weights', 'aircraft_m'), expected_times)
    for left, right in zip(rows, triple, strict=True):
        if any(right[key] != value for key, value in left.items()):
            raise ValueError('Nuuk two- and three-station support differs')
    a, b, c = (near.flatten(triple, field) for field in fields)
    _require_values([len(triple), len(a), min(len(row['satellites']) for row in rows)],
                    [report[k] for k in ('triple_intervals', 'triple_ranges', 'minimum_nearby_satellites')],
                    'Nuuk range counts')
    for name, diff in zip(('museum_permanent', 'museum_qaqortoq', 'permanent_qaqortoq'),
                          (near._difference(a, b), near._difference(a, c), near._difference(b, c)), strict=True):
        _close(report['triple_rms_m'][name], diff, 'Nuuk paired RMS')
    _close(report['nearby_difference_rms_m'], near._difference(a, b), 'Nuuk nearby RMS')
    return count


def verify_comparisons(original, diagnostic, extended):
    all_times = list(range(near.FIRST, near.LAST))
    audits = diagnostic['rows']
    if [row['time_gps_s'] for row in audits] != all_times:
        raise ValueError('Nuuk diagnostic times differ')
    counters = {'retained': Counter(), 'excluded': Counter()}
    for row in audits:
        counters[row['state']].update(row['reasons'])
    retained = [row['time_gps_s'] for row in audits if row['state'] == 'retained']
    excluded = [row for row in audits if row['state'] == 'excluded']
    if (diagnostic['parent_sha256'] != screen.PARENT_SHA or not diagnostic['thresholds_unchanged']
            or diagnostic['counts'] != counters or diagnostic['intervals'] != len(all_times)
            or diagnostic['excluded'] != len(excluded) or diagnostic['excluded_before_geometry'] != len(excluded)
            or diagnostic['excluded_doppler_profiles'] != len(excluded)
            or diagnostic['excluded_median_beyond_doppler_limit'] != len(excluded)
            or any(row['pregeometry_passes'] >= 5 or abs(row['doppler']['median_cycles'])
                   <= screen.L1_DOPPLER_LIMIT_CYCLES for row in excluded)):
        raise ValueError('Nuuk original Doppler-screen accounting differs')

    try:
        support = clock.compare_support(original['evidence']['near'], extended['evidence']['near'])
    except ValueError as exc:
        raise ValueError('Nuuk shared ranges differ') from exc
    _require_values(support, extended['support_check'], 'Nuuk shared ranges')
    if support['additional_intervals'] != len(excluded) or support['lost_intervals']:
        raise ValueError('Nuuk recovered interval counts differ')
    _close(original['score_gap'], extended['score_gap'], 'Nuuk same frozen score gap')
    count = _summary(original, retained) + _summary(extended, all_times)
    return dict(verified_nuuk_shared_ranges=support['shared_ranges'], verified_nuuk_extended_ranges=extended['nearby_ranges'],
                verified_nuuk_recovered_seconds=len(excluded), verified_nuuk_station_witnesses=count)


def evidence(root, *, store=None):
    reports = [json.loads(near._verified(root, module.RESULT, sha)) for module, sha, _, _ in REPORTS]
    checks = verify_comparisons(*reports)
    studies = []
    for report, (module, sha, key, filename) in zip(reports, REPORTS, strict=True):
        if (not report['passed'] or report['completion']['state'] != 'complete'
                or report['scientific_decision'] != 'abstain' or report['charged'] != module.TASK['limits']
                or any(report.get(k) for k in ('new_fits', 'protected_reads', 'original_downloads',
                                              'independent_aircraft_error_cap_established'))):
            raise ValueError('Nuuk development disposition differs')
        if store is not None:
            task = module.TASK['identity']
            with closing(ClosedStudy(root, 'data/'+module.ID, store=store)) as study:
                env = study.envelope(task)
                if (report['completion'] != study.completion or report['charged'] != env['charged']
                        or report[key] != study.artifact(task, filename)
                        or any(report[k] != value for k, value in env['result'].items())):
                    raise ValueError('sealed Nuuk result differs')
                for source, expected in study.manifest['sources'].items():
                    study.read('source-freeze/'+source, expected, raw=True)
                for input_key in study.manifest['inputs']:
                    study.input(input_key, raw=True)
        studies.append(dict(path=module.RESULT, sha256=sha, study=module.ID, completion=report['completion']))
    return dict(studies=studies), checks
