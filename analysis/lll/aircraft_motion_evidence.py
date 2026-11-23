# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the NASA and ESA motion checks against their frozen receipts."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy


ESA = 'docs/prediction-observed-development/'
NASA = 'docs/ilvis0-measurement-contribution/'
FILES = {
    'prefix': (ESA+'esa-girafe-level1-prefix-result.json',
               '2b7b99d05a457b5379e7ecc161f655efbd5ae757bac723a67e6f4b1bed6b90e7'),
    'acquisition': (ESA+'esa-girafe-level1-airborne-acquisition.json',
                    'b5b552f760cdea6063a565d05399b26fa968fd4f148004bd28146f22de7cc80b'),
    'airborne': (ESA+'esa-girafe-level1-airborne-result.json',
                 'fec1efcdac3d8c9445666aa40b2beab59e8306ad084e28c36be115a37d52359d'),
    'tilt': (ESA+'esa-girafe-tilt-identifiability-result.json',
             'e1f6aee09ff565ea985b1503441fa92609e2bbb31619df581f0f95466d0e3782'),
    'recorder_motion': (NASA+'paired-gyro-motion-result.json',
                        'f46e0adf2123c1624bcf150d7c6778d584b906e3bb69d36cb64ba13d96ee49c9'),
    'intervals': (NASA+'paired-gyro-intervals-result.json',
                  'af6ad8847b6ce60ab52453f44044693383bf72dd81d409bb93ec4470d9f0718d'),
    'averages': (NASA+'paired-gyro-average-result.json',
                 'b3fc7bcd166fdd539fd6d7b3f22ff52af535e952adf6e41b2149f24d9c8be003'),
}
MODELS = {'flat_geographic_field', 'flat_still', 'sphere_rotating', 'sphere_still'}
LEG20 = 'leg-13805a9a35c4'
LEG24 = 'leg-590ee7971efb'
PAIRS = {
    LEG20: ('f39deb582f207574911dd3a16e6c389a8baac76ceace13ec2f13aefdc42341dd',
            '1d3907d662c774b03b41bbb3675ac3f49009a663d82c0e28b7d64af756c90dc2'),
    LEG24: ('5e597ef0cd42c391c2fa032a8392300e69bf40dd0420360eea89c30119a85363',
            'dc223d82d68dd667db8bb628fd67546aa793934754c552982d363da54b9380de'),
}


def clock_scores(scores, samples, *, copied):
    matches = []
    for block, count in zip(scores['blocks'], samples, strict=True):
        if ([r['shift_s'] for r in block] != [i/10 for i in range(-20, 21)]
                or any(r['matches'] != count or not 0 <= r['rms_mps2'] <= r['max_abs_mps2']
                       for r in block)):
            raise ValueError('unaltered clock grid and sample counts required')
        matches.append([r['shift_s'] for r in block if r['rms_mps2'] <= 1e-6])
        at_zero = block[20]
        if copied and any(at_zero[k] != 0 for k in
                ('rms_mps2', 'min_time_offset_s', 'max_time_offset_s', 'mean_time_offset_s')):
            raise ValueError('copied values must agree exactly at zero shift')
    if (matches != ([[0.], [0.]] if copied else [[], []])
            or scores['within_tolerance'] != matches):
        raise ValueError('clock threshold result differs')


def tilt_vectors(rows):
    keys = {(r['model'], r['width_s'], r['center_gps_s']) for r in rows}
    if len(rows) != 20 or len(keys) != 20:
        raise ValueError('20 distinct paired force vectors required')
    for row in rows:
        a, b = row['original_ned_mps2'], row['displaced_ned_mps2']
        a_length, b_length = math.hypot(*a), math.hypot(*b)
        a_unit = [x/a_length for x in a]
        b_unit = [x/b_length for x in b]
        angle = 2*math.asin(math.dist(a_unit, b_unit)/2)
        if (abs(angle-row['minimum_rotation_rad']) > 1e-15
                or abs(b_length-a_length-row['magnitude_change_mps2']) > 5e-15):
            raise ValueError('tilt and force-magnitude changes do not reproduce')


def paired_histories(intervals, averages):
    def key(row):
        return tuple(row[name] for name in ('side', 'clock', 'track', 'model'))

    single = {key(r): r for r in intervals}
    expected = {(side, clock, track, model) for side in ('training', 'later')
                for clock in ('nominal_200Hz', 'header_elapsed')
                for track in ('onboard', 'carrier_phase') for model in MODELS}
    if len(intervals) != len(expected) or set(single) != expected:
        raise ValueError('the complete single-packet comparison is required')
    if (len(averages) != 64 or {(r['width_s'], key(r)) for r in averages} !=
            {(width, k) for width in (.25, 1.) for k in expected}):
        raise ValueError('the complete average comparison is required')
    for row in averages:
        previous = single[key(row)]
        expected_count = 414 if row['side'] == 'training' else 192
        if (previous['covered'] != expected_count or row['covered_pairs'] != expected_count
                or not expected_count/2 < previous['above_both'] <= expected_count
                or row['count_only']['above_both'] != 0 or row['with_internal_motion']['above_both'] != 0):
            raise ValueError('paired support counts or shortfalls differ')


def bindings(values):
    prefix = values['prefix']
    for identity, record in sorted(prefix.items()):
        yield identity, 'prefix-clock', record, 'clock-scores.json', 'scores'
    yield 'esa-girafe-level1-airborne-clock-v1', 'airborne-clock', values['airborne'], 'clock-scores.json', 'scores'
    yield ('esa-girafe-tilt-identifiability-v1', 'paired-force-orientation', values['tilt'],
           'orientation-sensitivity.json', 'result')
    yield 'ilvis0-paired-gyro-motion-v1', LEG20, values['recorder_motion'], 'recorded-motion.json', 'result'
    yield 'ilvis0-paired-gyro-intervals-v1', LEG20, values['intervals']['earlier_attempt'], None, None
    yield 'ilvis0-paired-gyro-intervals-v2', LEG24, values['intervals'], 'paired-gyro-intervals.json', 'result'
    yield 'ilvis0-paired-gyro-average-v1', LEG24, values['averages'], 'paired-averages.json', 'result'


def _verify_runtime(root, entries):
    source_count = input_count = 0
    with closing(ArchiveStore(root)) as store:
        for identity, task, report, name, field in entries:
            with closing(ClosedStudy(root, 'data/'+identity, store=store)) as closed:
                envelope = closed.envelope(task)
                if closed.completion != report['completion'] or envelope['charged'] != report['charged']:
                    raise ValueError('runtime closure or charged operations differ: '+identity)
                if closed.completion['state'] == 'complete':
                    if closed.artifact(task, name) != report[field] or envelope['artifacts'] != report['artifacts']:
                        raise ValueError('runtime result artifact differs: '+identity)
                elif envelope['result'] != report['result']:
                    raise ValueError('runtime terminal evidence differs: '+identity)
                for source, expected in closed.manifest['sources'].items():
                    closed.read('source-freeze/'+source, expected, raw=True)
                    source_count += 1
                for key in closed.manifest['inputs']:
                    closed.input(key, raw=True)
                    input_count += 1
                if task in PAIRS:
                    layout = closed.input('layout')
                    hashes = tuple(side['context']['inspection']['source_sha256'] for side in layout['sides'])
                    if hashes != PAIRS[task]:
                        raise ValueError('20 and 24 October recorder pairs must stay separate: '+identity)
    return source_count, input_count


def verify(root, *, runtime=False):
    values = {}
    for label, (name, expected) in FILES.items():
        raw = (root/name).read_bytes()
        if digest(raw) != expected:
            raise ValueError('public motion evidence hash differs: '+name)
        values[label] = json.loads(raw)
    signed = values['prefix']['esa-girafe-level1-prefix-clock-v2']['scores']
    reversed_sign = values['prefix']['esa-girafe-level1-prefix-sign-v1']['scores']
    clock_scores(signed, (660, 660), copied=False)
    clock_scores(reversed_sign, (660, 660), copied=True)
    airborne = values['airborne']['scores']
    acquisition = values['acquisition']
    if (reversed_sign['export_sign'] != airborne['export_sign'] or airborne['export_sign'] != -1
            or acquisition['gps_week'] != 2269 or acquisition['records'] != 38_415
            or acquisition['byte_count'] != 9_565_584 or acquisition['protected_reads'] != 0
            or acquisition['windows'] != airborne['windows']):
        raise ValueError('frozen airborne response and sign must agree')
    clock_scores(airborne, (100, 1200), copied=True)
    tilt = values['tilt']['result']['rows']
    tilt_vectors(tilt)
    records = values['recorder_motion']['result']['records']
    if (len(records) != 4 or {row['imu_type'] for row in records} != {8, 21}
            or {row['whole_second_windows'] for row in records} != {552}
            or {row['source']['source_sha256'] for row in records} != set(PAIRS[LEG20])
            or any(row['source']['group1_observations_used'] for row in records)):
        raise ValueError('paired recorded motion evidence differs')
    paired_histories(values['intervals']['result']['summaries'], values['averages']['result']['summaries'])

    entries = tuple(bindings(values))
    counts = dict(complete=0, terminal=0)
    for identity, task, report, artifact, key in entries:
        state = report['completion']['state']
        if any(report['charged'][k] for k in ('native_calls', 'packet_visits')):
            raise ValueError('motion verifier expects zero native fits: '+identity)
        if state == 'complete':
            data = report[key]
            if (data['scientific_decision'] != 'abstain' or data.get('protected_reads', 0)
                    or data.get('fit_starts', 0) or data.get('group1_observations_used', False)
                    or digest(encoded(data)) != report['artifacts'][f'artifacts/{task}/{artifact}']):
                raise ValueError('public motion artifact does not match its record: '+identity)
        elif state != 'terminal' or report['result']['passed'] is not False:
            raise ValueError('terminal outcome must remain in the evidence: '+identity)
        counts[state] += 1
    sources, inputs = _verify_runtime(root, entries) if runtime else (0, 0)
    return dict(complete_studies=counts['complete'], terminal_studies=counts['terminal'],
                tilt_vectors=len(tilt), averaged_histories=64, runtime_source_bindings=sources,
                runtime_inputs=inputs, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', action='store_true', help='also check local frozen sources and inputs')
    args = parser.parse_args()
    print(json.dumps(verify(Path.cwd(), runtime=args.runtime), sort_keys=True))


if __name__ == '__main__':
    main()
