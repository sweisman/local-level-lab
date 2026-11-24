# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recompute the public Nuuk apron diagnostics without using the raw aircraft data."""

from contextlib import closing
import json
import math

from .studies.artifacts import digest
from .studies.closed import ClosedStudy


BASE = 'docs/prediction-observed-development/'
ACQUISITION = ('esa-apron-imu-overlap-acquisition.json',
               '6c2aa57cbf73b31b9dd0d7b5b76e6a5aa596d1b4bdc127411c3c2e52b4396ea3')
COMPLETED = (
    ('esa-apron-carrier-result.json', 'a9c72b08c56f5dbbd701cfeff4768dc81b82557908c7a993d5bd079ef9825be8',
     'esa-apron-carrier-v2', 'fixed-apron-ranges', {'cases': 'apron-residuals.json'}),
    ('esa-apron-nkar-result.json', 'cc2e1b6985d188bfd61a8d66ec3cc83f2ab3dbfbc0c9b952f22994e3d0c3fb09',
     'esa-apron-nkar-v1', 'apron-ground-common-phase', {'rows': 'apron-ground-ranges.json'}),
    ('esa-apron-imu-ranges-result.json', '10843f68f08bf570777e3e2172ecfd95dab369789cceebe9c2f5ceb629ae3f92',
     'esa-apron-imu-ranges-v2', 'apron-overlap', {'ranges': 'matched-ranges.json', 'motion': 'ground-motion.json'}),
)
STOPS = (
    ('esa-apron-carrier-v1-terminal.json', '661c03aa44c7bc06c6b131a045019fc09810274e0701b249391794908f220774',
     'esa-apron-carrier-v1', 'fixed-apron-ranges', 1, 'unexpected recorded receiver time offset'),
    ('esa-apron-imu-ranges-v1-terminal.json', 'b62bf2a60ad7d9b75bf60147f4162fe1c08e9ac2f720e339e14ba6bec8b25a9e',
     'esa-apron-imu-ranges-v1', 'apron-overlap', 0, 'one complete finite operation reservation required'),
)


def _close(observed, reported, label):
    if not math.isclose(observed, reported, rel_tol=2e-12, abs_tol=2e-12):
        raise ValueError('apron '+label+' differs from the saved observations')


def _range_summary(rows, reported):
    air, ground = [], []
    for row in rows:
        satellites = row['satellites']
        a, b = row['aircraft_m'], row['ground_m']
        if (len(satellites) != len(a) or len(a) != len(b) or len(a) != 12
                or satellites != sorted(set(satellites))):
            raise ValueError('apron satellite membership or row size differs')
        for values in (a, b):
            if not all(math.isfinite(v) for v in values) or abs(math.fsum(values)) > 2e-12:
                raise ValueError('apron range rows require finite clock-centred residuals')
        air.extend(a)
        ground.extend(b)
    n = len(air)
    aa, bb = [math.fsum(value**2 for value in samples) for samples in (air, ground)]
    if not n or not (aa > 0 and bb > 0):
        raise ValueError('apron correlation needs nonzero residuals from both receivers')
    changes = zip(air, ground, strict=True)
    rms_difference = math.sqrt(math.fsum((a-b)**2 for a, b in changes)/n)
    correlation = math.fsum(a*b for a, b in zip(air, ground, strict=True))/math.sqrt(aa*bb)
    if (reported['matched_intervals'], reported['matched_ranges']) != (len(rows), n):
        raise ValueError('apron matched range counts differ')
    for key, actual in (('aircraft_rms_m', math.sqrt(aa/n)), ('ground_rms_m', math.sqrt(bb/n)),
                        ('difference_rms_m', rms_difference), ('correlation', correlation)):
        _close(actual, reported[key], key)


def _verify_times(rows, first, last):
    if [row['gps_s'] for row in rows] != list(range(first, last)):
        raise ValueError('apron ranges must cover each fixed second in order')


def verify_overlap(acquisition, result):
    start, end = 385020, 385140
    if ((acquisition['first_gps_s'], acquisition['last_gps_s'], acquisition['following_marker_gps_s'],
          acquisition['retained']['epochs'], acquisition['retained']['minimum_dual_band_gps_satellites'],
          acquisition['retained']['maximum_dual_band_gps_satellites']) != (start, end, end+.5, 241, 13, 13)
            or (result['first_gps_s'], result['last_gps_s']) != (start, end)
            or acquisition['original_model_fits'] or acquisition['protected_reads']
            or acquisition['scientific_decision'] != 'abstain' or result['unmatched_starts_gps_s']):
        raise ValueError('apron ground interval or acquisition scope differs')
    rows = result['ranges']
    _verify_times(rows, start, end)
    _range_summary(rows, result['matched'])
    if len(result['minutes']) != 2:
        raise ValueError('apron minute summaries must cover the whole interval')
    for minute, summary in enumerate(result['minutes']):
        _range_summary(rows[minute*60:(minute+1)*60], summary)
    motion = result['motion']
    bins = motion['complete_bin_means']
    samples = sum(row['count'] for row in bins)
    if ([row['index'] for row in bins] != list(range(end-start))
            or any(not 285 <= row['count'] <= 315 or len(row['mean_xyz_deg_per_hour']) != 3 for row in bins)
            or samples != motion['selected_samples'] or samples != result['imu_samples']
            or motion['complete_bins'] != len(bins) or motion['adjacent_complete_pairs'] != len(bins)-1
            or motion['omitted_partial_bins']):
        raise ValueError('apron inertial coverage differs')
    axes = zip(*(row['mean_xyz_deg_per_hour'] for row in bins), strict=True)
    for i, values in enumerate(axes):
        mean = math.fsum(values)/len(values)
        spread = math.sqrt(math.fsum((v-mean)**2 for v in values)/len(values))
        allan = math.sqrt(math.fsum((b-a)**2 for a, b in zip(values, values[1:]))/(2*(len(values)-1)))
        for actual, key in ((mean, 'mean_xyz_deg_per_hour'), (spread, 'spread_xyz_deg_per_hour'),
                            (allan, 'allan_xyz_deg_per_hour')):
            _close(actual, motion[key][i], key)
        _close(spread, result['imu_rate_spread_deg_per_hour'][i], 'gyro spread')


def evidence(root, *, store=None):
    def read(name, sha):
        raw = (root/BASE/name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('apron report hash differs: '+name)
        return json.loads(raw)

    acquisition = read(*ACQUISITION)
    completed = [read(name, sha) for name, sha, *_ in COMPLETED]
    nominal, short, overlap = completed
    verify_overlap(acquisition, overlap)
    _verify_times(short['rows'], 383697, 383715)
    _range_summary(short['rows'], short)
    _close(nominal['nominal']['one_second']['rms_m'], short['aircraft_rms_m'], 'short aircraft RMS')
    stops = []
    studies = []
    for report, (name, sha, study_id, task, artifacts) in zip(completed, COMPLETED, strict=True):
        if (not report['passed'] or report['completion']['state'] != 'complete' or report['new_fits']
                or report['protected_reads'] or report['aircraft_error_cap_established']
                or report['scientific_decision'] != 'abstain'):
            raise ValueError('apron development disposition differs')
        if store is not None:
            with closing(ClosedStudy(root, 'data/'+study_id, store=store)) as study:
                envelope = study.envelope(task)
                if (study.completion != report['completion'] or report['inputs'] != study.manifest['inputs']
                        or report['charged'] != envelope['charged'] or envelope['charged'] != study.tasks[task]['limits']
                        or any(report[k] != v for k, v in envelope['result'].items())
                        or any(study.artifact(task, v) != report[k] for k, v in artifacts.items())):
                    raise ValueError('apron sealed runtime differs: '+study_id)
                for path, expected in study.manifest['sources'].items():
                    study.read('source-freeze/'+path, expected, raw=True)
                for key in study.manifest['inputs']:
                    study.input(key, raw=True)
        studies.append(dict(path=BASE+name, sha256=sha, study=study_id, completion=report['completion']))
    for name, sha, study_id, task, charged, reason in STOPS:
        stop = read(name, sha)
        terminal = stop['terminal_result']
        if (stop['completion']['state'] != 'terminal' or terminal['result']['passed']
                or terminal['result']['reason'] != reason
                or terminal['charged'] != dict(native_calls=0, packet_visits=0, bound_calls=charged, bound_steps=charged)):
            raise ValueError('apron technical stop differs: '+study_id)
        if store is not None:
            with closing(ClosedStudy(root, 'data/'+study_id, store=store)) as study:
                if study.completion != stop['completion'] or study.envelope(task) != terminal:
                    raise ValueError('apron technical stop was not preserved: '+study_id)
        stops.append(dict(path=BASE+name, sha256=sha, study=study_id, completion=stop['completion']))
    checks = dict(verified_apron_range_steps=len(short['rows'])+len(overlap['ranges']),
                  verified_apron_motion_samples=overlap['imu_samples'])
    index = dict(acquisition=dict(path=BASE+ACQUISITION[0], sha256=ACQUISITION[1]),
                 studies=studies, technical_stops=stops)
    return index, checks
