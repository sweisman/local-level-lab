# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only audit of one same-realization generated IMU noise matrix."""

import json
import math
from pathlib import Path


def _rms(values):
    return math.sqrt(math.fsum(sum(value * value for value in row)
                               for row in values) / len(values))


def _difference(left, right):
    return [[a - b for a, b in zip(one, two)]
            for one, two in zip(left, right)]


def summarize(rows):
    """Summarize matched later error vectors without assigning unique causes."""
    from lll.noise_component_decomposition import variants

    names = variants()
    if (not isinstance(rows, dict) or set(rows) != set(names)
            or any(not isinstance(rows[name], list)
                   or len(rows[name]) != 400
                   or any(not isinstance(row, list) or len(row) != 3
                          or any(not isinstance(value, (int, float))
                                 or not math.isfinite(value) for value in row)
                          for row in rows[name])
                   for name in names)):
        raise ValueError('complete finite matched 400-epoch component matrix required')
    report_rows = {}
    for name in names:
        values = rows[name]
        horizontal = math.sqrt(math.fsum(row[0]**2 + row[1]**2
                                         for row in values) / 400)
        height = math.sqrt(math.fsum(row[2]**2 for row in values) / 400)
        report_rows[name] = dict(horizontal_rms_m=horizontal,
                                 height_rms_m=height,
                                 maximum_3d_m=max(math.hypot(*row)
                                                  for row in values),
                                 mean_error_neu_m=[math.fsum(row[i]
                                                              for row in values) / 400
                                                   for i in range(3)])
    components = ('gyro-white', 'gyro-bias',
                  'accel-white', 'accel-bias')
    clean, full = rows['clean'], rows['full']
    only = {name: _difference(rows['only-' + name], clean)
            for name in components}
    without = {name: _difference(full, rows['without-' + name])
               for name in components}
    combined = _difference(full, clean)
    interaction = [[combined[index][axis]
                    - math.fsum(only[name][index][axis]
                                for name in components)
                    for axis in range(3)]
                   for index in range(400)]
    return dict(version='noise-component-saved-audit-v1', verified=True,
                variants=10, prediction_epochs=400,
                rows=report_rows,
                only_change_3d_rms_m={name: _rms(only[name])
                                      for name in components},
                leave_out_change_3d_rms_m={name: _rms(without[name])
                                           for name in components},
                nonadditive_3d_rms_m=_rms(interaction),
                attribution_is_not_unique=True,
                original_reads=0, protected_reads=0,
                confidence_calibrated=False,
                scientific_decision='abstain', numerical_work=0)


def _close(actual, expected):
    return (isinstance(actual, (int, float)) and math.isfinite(actual)
            and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8))


def audit(root, prefix='data/noise-component-decomposition-20261111'):
    from lll.noise_component_study import SCOPE, recipe, tasks
    from lll.studies.artifacts import digest, encoded
    from lll.studies.closed import ClosedStudy

    study = ClosedStudy(root, prefix)
    try:
        if (study.completion['state'] != 'complete'
                or study.manifest['scope'] != SCOPE
                or study.input('recipe') != recipe()
                or len(study.tasks) != 10 or len(study.rows) != 10
                or set(study.tasks) != {task['identity'] for task in tasks()}
                or any(study.tasks[task['identity']]['payload'] !=
                       task['payload'] for task in tasks())):
            raise ValueError('complete unchanged ten-task component study required')
        proof = study.input('parent-proof')
        same = None
        rows = {}
        for task in tasks():
            identity = task['identity']
            variant = task['payload']['variant']
            envelope = study.envelope(identity)
            result = envelope['result']
            binding = study.artifact(identity, 'stream-binding.json')
            scores = study.artifact(identity, 'scores.json')
            forecast = study.artifact(identity, 'forecast.json')
            prepayment = study.artifact(identity, 'native-prepayment.json')
            if (result.get('passed') is not True
                    or result.get('technical_passed') is not True
                    or result.get('variant') != variant
                    or result.get('scientific_decision') != 'abstain'
                    or result.get('native_calls_attempted') != 1
                    or result.get('original_reads') != 0
                    or result.get('protected_reads') != 0
                    or result.get('optimizer_starts') != 0
                    or result.get('confidence_calibrated') is not False
                    or result.get('prediction') != scores.get('prediction')
                    or binding.get('variant') != variant
                    or binding.get('full_parent_sha256') !=
                    proof['selected_binding']['hashes']
                    or binding.get('same_realization_across_variants') is not True
                    or prepayment.get('state') != 'complete'
                    or prepayment.get('prepaid') !=
                    {'native_calls': 1, 'packet_visits': 432000000}
                    or prepayment.get('attempted') !=
                    prepayment.get('prepaid')
                    or scores.get('training_epochs') != 800
                    or scores.get('prediction_epochs') != 400
                    or len(scores.get('errors_neu_m', [])) != 1200
                    or len(forecast.get('coordinates', [])) != 1200):
                raise ValueError('saved component result or work charge differs')
            artifacts = envelope['artifacts']
            shared = (
                binding.get('component_sha256'),
                artifacts['artifacts/' + identity +
                          '/known-corrections.json'],
                artifacts['artifacts/' + identity +
                          '/scoring-observations.json'])
            if same is None:
                same = shared
            elif same != shared:
                raise ValueError('component draws, calibration or truth changed')
            if variant == 'full' and (
                    digest(encoded(forecast)) !=
                    proof['oracle_full_forecast_sha256']
                    or digest(encoded(scores)) !=
                    proof['oracle_full_scores_sha256']
                    or binding.get('selected_sha256') !=
                    proof['selected_binding']['hashes']):
                raise ValueError('full stream differs from sealed corrected oracle')
            rows[variant] = scores['errors_neu_m'][800:]
        report = summarize(rows)
        for task in tasks():
            identity = task['identity']
            variant = task['payload']['variant']
            saved = study.envelope(identity)['result']['prediction']
            derived = report['rows'][variant]
            for key in ('horizontal_rms_m', 'vertical_rms_m',
                        'maximum_3d_m'):
                actual = derived['height_rms_m'] if key == 'vertical_rms_m' else derived[key]
                if not _close(saved[key], actual):
                    raise ValueError('saved score differs from raw later errors')
        report.update(study=prefix,
                      manifest_sha256=study.completion['manifest_sha256'],
                      summary_sha256=study.completion['summary_sha256'],
                      source_parent_manifest_sha256=proof['parent_manifest_sha256'],
                      corrected_oracle_manifest_sha256=proof['oracle_manifest_sha256'])
        return report
    finally:
        study.close()


def publish(root, prefix='data/noise-component-decomposition-20261111'):
    from lll.studies.artifacts import atomic, encoded, digest
    import xml.etree.ElementTree as ET

    root = Path(root).resolve()
    report = audit(root, prefix)
    location = root / 'docs/noisy-realization-attribution/component-decomposition'
    test_path = location / 'audit-tests.xml'
    raw_tests = test_path.read_bytes()
    tree = ET.fromstring(raw_tests)
    cases = list(tree.iter('testcase'))
    expected = {'test_saved_component_summary_exposes_nonadditivity_and_leave_out',
                'test_saved_component_summary_requires_complete_finite_matrix'}
    if ({case.attrib.get('name') for case in cases} != expected
            or any(node.tag in ('failure', 'error', 'skipped')
                   for case in cases for node in case.iter())):
        raise ValueError('complete passing saved-audit tests required')
    report['audit_source_sha256'] = digest(Path(__file__).read_bytes())
    report['audit_test_report_sha256'] = digest(raw_tests)
    atomic(location / 'verified-report.json', encoded(report))
    row = report['rows']
    lines = [
        '# Which generated IMU errors moved the forecast?','',
        'One preselected twenty-minute generated flight was replayed ten ways, '
        'using the same four random error arrays in every comparison. '
        'The generating calibration and starting state were supplied, and '
        'the complete noisy replay matched the earlier sealed oracle exactly.','',
        '| Error stream | Later horizontal RMS | Later height RMS |',
        '|---|---:|---:|']
    for name in ('clean', 'full', 'only-gyro-white', 'only-gyro-bias',
                 'only-accel-white', 'only-accel-bias'):
        value = row[name]
        lines.append(f"| {name.replace('-', ' ')} | "
                     f"{value['horizontal_rms_m']:.2f} m | "
                     f"{value['height_rms_m']:.2f} m |")
    lines.extend(['',
        'In this one generated case, the changing gyro bias and random gyro '
        'increments produce far larger horizontal errors than either '
        'accelerometer component. The clean stream misses by about 5 cm; the '
        'complete noisy stream misses by 439 m. These are simulated error '
        'settings, not measured specifications for an archive IMU.','',
        'The [finite plan](PLAN.md) also checks each component by removing it '
        'from the complete noisy stream. The saved report records those changes '
        'and the nonadditive interaction. These counterfactual effects are '
        'descriptive; nonlinear effects cannot be assigned uniquely to one '
        'sensor channel. No aircraft data or protected ESA confirmation group '
        'was used, and this is not an Earth-model decision.',''])
    atomic(location / 'README.md', ('\n'.join(lines)).encode())
    return report


if __name__ == '__main__':
    print(json.dumps(publish(Path(__file__).resolve().parents[2]),
                     sort_keys=True))
