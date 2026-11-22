# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and describe the frozen ESA five-hertz motion-context study."""

import hashlib
import io
import json
from pathlib import Path


STUDY = 'data/esa-gnss-motion-context-v1-20261116'
PUBLIC = 'docs/prediction-observed-development'


def inspect(root):
    import numpy as np
    from .esa_gnss_motion_context import compare_course_rate
    from .esa_gnss_motion_context_study import POLICY, tasks
    from .studies.closed import ClosedStudy

    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 2 or
                set(study.rows) != {item['identity'] for item in tasks()} or
                any(study.summary['charged'].values()) or
                study.input('policy') != POLICY):
            raise ValueError('complete zero-work two-span study required')
        binding = study.input('binding')
        raw = study.input('staged', raw=True)
        if hashlib.sha256(raw).hexdigest() != binding['staged_sha256']:
            raise ValueError('frozen staged source differs')
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            arrays = {name: archive[name] for name in (
                'imu_time_s', 'gyro_body_rads', 'receiver_time_s',
                'receiver_ne_mps', 'center_time_s')}
        summaries = []
        for task in tasks():
            identity = task['identity']
            envelope = study.envelope(identity)
            saved = study.artifact(identity, 'motion.json')
            replay = compare_course_rate(
                arrays['imu_time_s'], arrays['gyro_body_rads'],
                arrays['receiver_time_s'], arrays['receiver_ne_mps'],
                arrays['center_time_s'],
                half_window_s=task['payload']['half_window_s'],
                maximum_imu_gap_s=POLICY['maximum_imu_gap_s'],
                maximum_receiver_gap_s=POLICY['maximum_receiver_gap_s'],
                maximum_receiver_match_s=POLICY['maximum_receiver_match_s'])
            if (not envelope['result']['passed'] or
                    envelope['result']['technical_support'] != saved['count'] or
                    saved['count'] < POLICY['minimum_supported_centers'] or
                    any(saved.get(key) != value for key, value in replay.items()) or
                    saved['staged_sha256'] != binding['staged_sha256'] or
                    saved['scientific_decision'] != 'abstain' or
                    any(row['stop_s'] > binding['last_training_s']+.002
                        for row in saved['rows']) or
                    saved['count'] + len(saved['rejected']) != saved['candidate_count']):
                raise ValueError('saved course/gyro result differs from replay')
            gyro = np.array([row['imu_body_down_dph'] for row in saved['rows']])
            course = np.array([row['gnss_course_rate_dph'] for row in saved['rows']])
            summaries.append(dict(span_s=int(2*task['payload']['half_window_s']),
                                  supported=saved['count'],
                                  candidates=saved['candidate_count'],
                                  correlation=saved['correlation'],
                                  mean_difference_dph=saved['mean_imu_minus_course_dph'],
                                  demeaned_rms_difference_dph=saved[
                                      'demeaned_rms_difference_dph'],
                                  gyro_sd_dph=float(np.std(gyro)),
                                  course_sd_dph=float(np.std(course))))
        return dict(version='esa-gnss-motion-report-v1',
                    study=STUDY, manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    input_sha256=binding['staged_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    spans=summaries, technical_tasks_passed=2,
                    native_calls=0, earth_model_fits=0,
                    later_receiver_reports_decoded=0,
                    protected_group_reads=0,
                    sensor_noise_identified=False,
                    error_law_qualified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def _page(report):
    rows = []
    for span in report['spans']:
        rows.append('| {} | {}/{} | {:.3f} | {:.0f} | {:.0f} |'.format(
            span['span_s'], span['supported'], span['candidates'],
            span['correlation'], span['mean_difference_dph'],
            span['demeaned_rms_difference_dph']))
    return ('# Receiver course changes and logged gyroscope rate\n\n'
        'The opened ESA development flight has a 5 Hz GNSS-only PPP export as '
        'well as the recorded 300 Hz IMU stream. This fixed comparison uses '
        'only the earlier 400 receiver report times and no later outcome. '
        'It compares course change from GNSS velocity with the mean logged '
        'body-down gyro rate over the same span.\n\n'
        '| Span (seconds) | Supported centers | Correlation | Mean gyro minus '
        'course (°/hour) | RMS of changing difference (°/hour) |\n'
        '|---:|---:|---:|---:|---:|\n' + '\n'.join(rows) + '\n\n'
        'The common low-frequency variation is substantial. The remaining '
        'difference includes aircraft heading versus ground course (crab), '
        'bank and pitch coupling, mount alignment, time tagging and possible '
        'instrument error. It is **not an estimate of gyro noise or the '
        'background rotation field**. The spans overlap and are not '
        'independent flights or trials. No Earth model was fitted.\n\n'
        'Both frozen tasks passed their support checks, with zero native '
        'calculations. This result does not qualify a prediction-error '
        'range or release the seven reserved ESA flight groups.\n\n'
        '[Fixed plan](GNSS_5HZ_MOTION_PLAN.md) · '
        '[Saved numerical summary](GNSS_5HZ_MOTION_RESULT.json) · '
        '[Observed error plan](OBSERVED_ERROR_PLAN.md).\n')


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = inspect(root)
    directory = root / PUBLIC
    atomic(directory / 'GNSS_5HZ_MOTION_RESULT.json', encoded(report))
    atomic(directory / 'GNSS_5HZ_MOTION_RESULT.md', _page(report).encode())
    return report


def verify(root):
    from .studies.artifacts import encoded
    root = Path(root).resolve()
    report = inspect(root)
    directory = root / PUBLIC
    if ((directory/'GNSS_5HZ_MOTION_RESULT.json').read_bytes() != encoded(report) or
            (directory/'GNSS_5HZ_MOTION_RESULT.md').read_bytes() !=
            _page(report).encode()):
        raise ValueError('published motion report differs')
    return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('publish', 'verify'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root) if args.action == 'publish' else verify(args.root)
    print(json.dumps(dict(tasks=result['technical_tasks_passed'],
                          spans=result['spans'],
                          scientific_decision=result['scientific_decision']),
                     sort_keys=True))


if __name__ == '__main__':
    main()
