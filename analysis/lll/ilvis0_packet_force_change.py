# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary limits on body-frame force change from adjacent accelerometer packets."""

import argparse
from contextlib import closing
import gzip
import io
import json
import math
from pathlib import Path

from . import ilvis0_matched_extension_inputs as aligned
from .ilvis0_matched_extension_forecast import INPUT_MANIFEST, INPUT_SUMMARY
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-packet-force-change-v1'
FOLDER = aligned.shared.FOLDER
PLAN = FOLDER+'PACKET_FORCE_CHANGE_PLAN.md'
REQUEST = FOLDER+'packet-force-change-qualification.json'
TEST_REPORT = FOLDER+'packet-force-change-tests.xml'
RESULT = FOLDER+'packet-force-change-result.json'
SCOPE = 'conditional lower limits on body-frame force change on two NASA stretches'
TEST = 'analysis/tests/test_ilvis0_packet_force_change.py'
TESTS = ('test_two_packet_mean_differences_recover_linear_force_change_before_allowances',
         'test_force_change_split_keeps_whole_pairs_clear_of_the_cut')
EXTRA = (0., .02, .1, .5)
GAIN, HALF_COUNT, OFFSET = .15, .5, .15
PASSES = len(EXTRA)*len(aligned.shared.CLOCKS)
RECOVERY_POLICY = dict(aligned.gps.RECOVERY_POLICY, maximum_wall_s=180)


def rate_lower_bounds(counts, durations, *, scale, gain, half_count, extra_error):
    import numpy as np

    count, dt = np.asarray(counts, float), np.asarray(durations, float)
    options = (scale, gain, half_count, extra_error)
    if (dt.ndim != 1 or len(dt) < 2 or count.shape != (len(dt), 3) or not np.isfinite(count).all()
            or not np.isfinite(dt).all() or np.any(dt <= 0.) or any(not math.isfinite(x) for x in options)
            or scale <= 0. or not 0. <= gain < 1. or min(half_count, extra_error) < 0.):
        raise ValueError('finite adjacent counts, positive periods and declared error limits required')
    raw_rate = count*scale/dt[:, None]
    error = (half_count*scale/dt + extra_error)
    roundoff = 8.*np.finfo(float).eps
    difference = np.abs(np.diff(raw_rate, axis=0))
    allowance = (error[:-1]+error[1:])[:, None]+roundoff*(abs(raw_rate[:-1])+abs(raw_rate[1:]))
    least = np.maximum(difference-allowance, 0.)
    spacing = (dt[1:]+dt[:-1])/2.
    return (1.-roundoff)*np.linalg.norm(least, axis=1)/((1.+gain)*spacing)


def split_pairs(durations, *, earlier_end, later_start, offset):
    import numpy as np

    dt = np.asarray(durations, float)
    if (dt.ndim != 1 or len(dt) < 2 or not np.isfinite(dt).all() or np.any(dt <= 0.)
            or not all(math.isfinite(x) for x in (earlier_end, later_start, offset))
            or not 0. <= earlier_end < later_start or offset < 0.):
        raise ValueError('ordered finite packets and fixed receiver cut required')
    ends = np.cumsum(dt)
    starts = np.r_[0., ends[:-2]]
    return ends[1:]+offset <= earlier_end, starts-offset >= later_start


def limits(pairs):
    return dict(native_calls=0, packet_visits=0, bound_calls=PASSES, bound_steps=PASSES*pairs)


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=aligned.shared.runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    import numpy as np

    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the original recorded rate-check allowance')
    deps, environment = sources(root), aligned.shared.runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, aligned.gps.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, alignment_receipt=aligned.RECEIPT)
    raw = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
               recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    tasks = []
    with closing(ClosedStudy(root, 'data/'+aligned.ID)) as study:
        if ((study.completion['manifest_sha256'], study.completion['summary_sha256']) !=
                (INPUT_MANIFEST, INPUT_SUMMARY) or not study.summary['passed'] or len(study.rows) != 2):
            raise ValueError('the two sealed packet alignments are required')
        for segment in study.rows:
            row = study.envelope(segment)['result']
            original = np.load(io.BytesIO(gzip.decompress(study.artifact(segment, 'packets.npy.gz', raw=True))),
                               allow_pickle=False)
            tags = study.artifact(segment, 'queries.json')
            provenance = study.artifact(segment, 'packet-provenance.json')
            if (original.shape != (row['source_packets'], 15) or provenance['group1_observations_used']
                    or not provenance['all_original_integers_preserved'] or not row['passed']):
                raise ValueError('the retained accelerometer fields and packet intervals must match')
            counts = original[:, 3:6]
            if (np.any(counts != np.rint(counts)) or np.any(counts < -(2**31)) or np.any(counts >= 2**31)):
                raise ValueError('original signed integer accelerometer counts required')
            cut = tags['training_epochs']
            raw[segment] = gzip.compress(encoded(dict(imu_type=row['imu_type'],
                source_sha256=provenance['source_sha256'], periods_s=original[:, 2].tolist(),
                raw_accelerometer=counts.astype(np.int64).tolist(),
                scale=provenance['velocity_scale_mps_per_count'], earlier_end=tags['query_times_s'][cut-1],
                later_start=tags['query_times_s'][cut])), mtime=0)
            pairs = len(original)-1
            tasks.append(dict(identity=segment, input_key=segment, pairs=pairs, limits=limits(pairs)))
    for key, values in raw.items():
        path = f'data/{ID}-inputs/{key}'
        aligned.shared._write_equal(root/path, values)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, tasks=tasks, sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    record = json.loads(gzip.decompress(context.input_path().read_bytes()))
    header, counts = np.asarray(record['periods_s']), np.asarray(record['raw_accelerometer'])
    if (context.manifest['scope'] != SCOPE or len(header) != task['pairs']+1
            or task['limits'] != limits(task['pairs']) or not np.issubdtype(counts.dtype, np.integer)
            or np.any(counts < -(2**31)) or np.any(counts >= 2**31)
            or np.any((header < .0025)|(header > .0075))):
        raise ValueError('original signed accelerometer counts and supported packet periods required')
    rows = []
    for clock, dt in zip(aligned.shared.CLOCKS, (np.full(len(header), .005), header), strict=True):
        earlier, later = split_pairs(dt, earlier_end=record['earlier_end'], later_start=record['later_start'], offset=OFFSET)
        for error in EXTRA:
            context.charge(bound_calls=1, bound_steps=task['pairs'])
            values = rate_lower_bounds(counts, dt, scale=record['scale'], gain=GAIN, half_count=HALF_COUNT,
                                      extra_error=error)
            counts_by_role = {}
            for role, sample in (('all', values), ('earlier', values[earlier]), ('later', values[later])):
                if not len(sample):
                    raise ValueError('each original split needs some adjacent packet support')
                counts_by_role[role] = dict(pairs=len(sample), nonzero=int(np.count_nonzero(sample)),
                    median_mps3=float(np.median(sample)), p95_mps3=float(np.percentile(sample, 95)),
                    maximum_mps3=float(sample.max()))
            rows.append(dict(clock=clock, extra_per_axis_mps2=error, by_role=counts_by_role))
    result = dict(passed=True, imu_type=record['imu_type'], source_sha256=record['source_sha256'],
        pairs=task['pairs'], cases=rows, upper_force_change_qualified=False, scientific_decision='abstain')
    context.save('change-bounds.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 2 or study.manifest['scope'] != SCOPE:
            raise ValueError('both recorded-change tasks must seal')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed'] and (result != study.artifact(identity, 'change-bounds.json')
                    or envelope['charged'] != limits(result['pairs'])):
                raise ValueError('summary and charged comparison phases differ')
            rows.append(result)
        value = dict(study.completion, flights=rows, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    aligned.shared._write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), charged=value['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
