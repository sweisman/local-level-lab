# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check saved ESA 187 carrier comparisons and their arithmetic without refitting."""

from contextlib import closing
import json
import math

from .studies.artifacts import digest
from .studies.closed import ClosedStudy


BASE = 'docs/prediction-observed-development/'
GPS_PARENT = ('esa-carrier-continuous-bound-result.json',
              '2081e8d8fc863ddf2e3ccb6cb5ac607e416b3fd8567e6c02623590b330e5b837')
STATION_PARENT = ('esa-nkar-phase-transfer-result.json',
                  'c43f33005a7844453ccd6c7c2d1ac094eb615f2799821b7b4564104b17c0740c')
STUDIES = (
    ('esa-two-station-score-result.json', '0cee408863d6d8c6201d2fae1f57060467f47239b57cb50a33475ed2865b1887',
     'esa-two-station-score-v1', 'common-ground-score', 'witnesses', 'common-range-witnesses.json'),
    ('esa-galileo-north-witness-result.json', '36a3412929981c0a84c8ba72518e1d9830c9196b1febff30b85f95ccbc6ff869',
     'esa-galileo-north-witness-v1', 'galileo-fixed-north', 'residuals', 'galileo-signed-ranges.json'),
    ('esa-galileo-joint-bound-result.json', '12e16119a8ae07681daa38bb3653b678125f538e68b986c58b340767bf1efbf6',
     'esa-galileo-joint-bound-v3', 'joint-gps-galileo', 'evidence', 'joint-carrier-certificate.json'),
)


def _require(condition, what):
    if not condition:
        raise ValueError('airborne carrier evidence differs: '+what)


def _close(a, b, what):
    _require(math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-12), what)


def _dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def _rms(a):
    return math.sqrt(_dot(a, a)/len(a))


def _column(rows, name):
    return [value for row in rows for value in row[name]]


def _check_rows(rows, time_key, fields, expected_times=range(388614, 388734)):
    _require([row[time_key] for row in rows] == list(expected_times), 'fixed interval')
    for row in rows:
        satellites = row['satellites']
        _require(5 <= len(satellites) <= 20 and satellites == sorted(set(satellites)), 'satellite support')
        for field in fields:
            values = row[field]
            _require(len(values) == len(satellites) and all(math.isfinite(v) for v in values)
                     and abs(math.fsum(values)) <= 2e-12, 'clock-centered '+field)


def verify_stations(parent, result, *, expected_times=range(388614, 388734)):
    rows = parent['withheld_rows']
    _check_rows(rows, 'start_gps_s', ('nkar_m', 'qaq_m', 'weights'), expected_times)
    a, b, w = (_column(rows, field) for field in ('nkar_m', 'qaq_m', 'weights'))
    gap = parent['score_gap']
    norm = math.sqrt(_dot(w, w))
    delta = [x-y for x, y in zip(a, b, strict=True)]
    difference = math.sqrt(_dot(delta, delta))
    projection = _dot(delta, w)/(norm*norm)
    perpendicular = [value-projection*weight for value, weight in zip(delta, w, strict=True)]
    separation = math.sqrt(_dot(perpendicular, perpendicular))
    _require(len(a) == result['ranges'] and result['intervals'] == len(expected_times), 'station counts')
    _close(result['score_gap'], gap, 'station score gap')
    for values, share in zip((a, b), result['station_score_shares'], strict=True):
        _close(_dot(values, w)/gap, share, 'station projection')
    for label, target in (('unrestricted', None), ('negative_gap', -gap), ('positive_gap', gap)):
        witness = result['witnesses'][label]
        common = witness['common']
        deviations = [_rms([x-y for x, y in zip(common, station, strict=True)]) for station in (a, b)]
        radius = max(deviations)*math.sqrt(len(a))
        score = _dot(w, common)
        for actual, expected in zip(deviations, witness['station_rms'], strict=True):
            _close(actual, expected, 'station witness deviation')
        _close(max(deviations), witness['maximum_rms'], 'station witness maximum')
        _close(score, witness['score'], 'station witness score')
        _require(result['cases'][label] == {k: v for k, v in witness.items() if k != 'common'}, 'station summary')
        if target is None:
            _close(radius, difference/2, 'unrestricted station optimum')
            continue
        _close(score, target, 'constrained station score')
        heights = [abs(_dot(station, w)-target)/norm for station in (a, b)]

        # In the score plane, the two station balls intersect exactly when
        # their in-plane radii cover the separation of the projected centers.
        def overlap(r):
            return sum(math.sqrt(max(0., r*r-h*h)) for h in heights) >= separation

        low, high = max(heights), radius+1e-12
        _require(high >= low and overlap(high), 'station feasibility')
        for _ in range(54):
            midpoint = (low+high)/2
            if overlap(midpoint):
                high = midpoint
            else:
                low = midpoint
        _close(radius, high, 'constrained station optimum')
    return len(result['witnesses'])


def verify_north(result):
    counts = 0
    _require(set(result['residuals']) == {'mosaic03', 'pwrpak7'}, 'Galileo receivers')
    for receiver, rows in result['residuals'].items():
        cols = ('original_m', 'shifted_m', 'predicted_shift_m')
        _check_rows(rows, 'time_gps_s', cols)
        original, shifted, movement = (_column(rows, key) for key in cols)
        for a, b, delta in zip(original, shifted, movement, strict=True):
            _close(a-b, delta, 'signed Galileo displacement')
        summary = result['summaries'][receiver]
        _require(summary['ranges'] == len(original) == 1067, 'Galileo paired range count')
        for series, field in ((original, 'original_rms_m'), (shifted, 'shifted_rms_m'),
                              (movement, 'predicted_shift_rms_m')):
            _close(_rms(series), summary[field], field)
        _close(_dot(original, movement)/_dot(movement, movement), summary['signed_residual_scale'], 'Galileo signed scale')
        counts += len(original)
    return counts


def verify_joint(parent, result):
    evidence = result['evidence']
    _check_rows(evidence['galileo_rows'], 'gps_s', ('residual_m',))
    observed = _column(evidence['galileo_rows'], 'residual_m')
    count = len(observed)
    _require(result['galileo_ranges'] == count == 1067 and result['gps_caps'] == parent['caps'], 'joint input limits')
    _close(_rms(observed), result['galileo_reference_rms_m'], 'joint reference range RMS')
    scale = evidence['galileo_normalization']
    cap = result['galileo_cap_m']+result['geometric_buffer_rms_m']
    _close(scale, math.sqrt(_dot(observed, observed))+math.sqrt(count)*cap, 'joint prediction normalization')
    angles = [None, 0, 5, 10]
    for rows in (result['cases'], evidence['certificates'], parent['cases']):
        _require([row['initial_tilt_allowance_deg'] for row in rows] == angles, 'joint satellite cases')
    for row, cert, gps in zip(result['cases'], evidence['certificates'], parent['cases'], strict=True):
        norm = cert['norm_terms']
        galileo = cert['galileo_dual']
        slope = norm[3]*math.sqrt(count)/scale
        intercept = math.fsum((*norm[:3], *norm[4:], cert['remainder'], _dot(galileo, observed)/scale))
        bound = intercept+slope*cap
        best = min(bound, gps['verified_upper'])
        for a, b in ((slope, row['upper_per_m']), (intercept, row['upper_intercept']),
                     (bound, row['joint_upper']), (gps['verified_upper'], row['prior_gps_upper']),
                     (best, row['verified_upper'])):
            _close(a, b, 'joint upper-bound arithmetic')
        _require(row['status'] == ('excluded_under_caps' if best < 1 else 'undetermined'), 'joint bound disposition')
    return len(angles)


def evidence(root, *, store=None):
    def read(name, sha):
        raw = (root/BASE/name).read_bytes()
        _require(digest(raw) == sha, 'report hash '+name)
        return json.loads(raw)

    reports = [read(name, sha) for name, sha, *_ in STUDIES]
    station, north, joint = reports
    checks = dict(verified_two_station_witnesses=verify_stations(read(*STATION_PARENT), station),
                  verified_galileo_receiver_ranges=verify_north(north),
                  verified_galileo_joint_bounds=verify_joint(read(*GPS_PARENT), joint))
    studies = []
    for report, (name, sha, study_id, task, key, filename) in zip(reports, STUDIES, strict=True):
        _require(report['passed'] and report['completion']['state'] == 'complete'
                 and not (report['new_fits'] or report['protected_reads'] or report['original_downloads']
                          or report['independent_aircraft_error_cap_established'])
                 and report['scientific_decision'] == 'abstain', 'development disposition '+study_id)
        if store is not None:
            with closing(ClosedStudy(root, 'data/'+study_id, store=store)) as study:
                envelope = study.envelope(task)
                _require(report['completion'] == study.completion and report['charged'] == envelope['charged']
                         and envelope['charged'] == study.tasks[task]['limits']
                         and report[key] == study.artifact(task, filename)
                         and all(report[k] == v for k, v in envelope['result'].items()), 'sealed result '+study_id)
                for source, expected in study.manifest['sources'].items():
                    study.read('source-freeze/'+source, expected, raw=True)
                for input_key in study.manifest['inputs']:
                    study.input(input_key, raw=True)
        studies.append(dict(path=BASE+name, sha256=sha, study=study_id, completion=report['completion']))
    return dict(studies=studies, gps_bound_parent=dict(path=BASE+GPS_PARENT[0], sha256=GPS_PARENT[1])), checks
