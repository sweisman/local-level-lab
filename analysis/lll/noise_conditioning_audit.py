# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and publish the saved conditioning comparison without rebuilding it."""

import json
import math
from pathlib import Path


def _close(actual, expected):
    return (isinstance(actual, (int, float)) and math.isfinite(actual)
            and math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9))


def validate(result, comparison, descriptor):
    if (result.get('passed') is not True
            or result.get('native_calls_attempted') != 361200
            or any(result.get(key) != 0 for key in
                   ('original_reads', 'protected_reads',
                    'optimizer_starts', 'random_draws'))
            or result.get('prediction_qualified') is not False
            or result.get('confidence_calibrated') is not False
            or result.get('scientific_decision') != 'abstain'
            or comparison.get('version') !=
            'same-operator-conditioning-comparison-v1'
            or comparison.get('training_epochs') != 800
            or comparison.get('later_epochs') != 400
            or comparison.get('realized_noise_used') is not False
            or comparison.get('fitted_calibration_used') is not False
            or comparison.get('confidence_calibrated') is not False
            or comparison.get('scientific_decision') != 'abstain'
            or any(descriptor.get(key) != value for key, value in
                   (('law', 'increment'), ('model', 'sphere_rotating'),
                    ('receiver_observation_epochs', 800),
                    ('original_reads', 0), ('protected_reads', 0),
                    ('confidence_calibrated', False)))):
        raise ValueError('saved comparison identity or scope differs')

    curves = []
    scales = {}
    for label, epochs in (('unconditional', 0), ('conditioned', 800)):
        entry = comparison.get(label, {})
        curve = entry.get('later_variance_neu_m2')
        if (entry.get('conditioning_epochs') != epochs
                or not isinstance(curve, list) or len(curve) != 400
                or any(not isinstance(row, list) or len(row) != 3
                       or any(not isinstance(v, (int, float))
                              or not math.isfinite(v) or v < 0 for v in row)
                       for row in curve)):
            raise ValueError('complete nonnegative saved variance curve required')
        horizontal = math.sqrt(sum(row[0] + row[1] for row in curve) / 400)
        height = math.sqrt(sum(row[2] for row in curve) / 400)
        if (not _close(entry.get('horizontal_rms_scale_m'), horizontal)
                or not _close(entry.get('height_rms_scale_m'), height)
                or not _close(result.get(label + '_horizontal_rms_scale_m'),
                              horizontal)
                or not _close(result.get(label + '_height_rms_scale_m'), height)):
            raise ValueError('saved scale differs from its variance curve')
        curves.append(curve)
        scales[label] = dict(horizontal=horizontal, height=height)
    if any(curves[1][i][axis] > curves[0][i][axis] * (1 + 1e-9) + 1e-9
           for i in range(400) for axis in range(3)):
        raise ValueError('saved conditional variance exceeds unconditional')
    return dict(verified=True, version='noise-conditioning-saved-audit-v1',
                training_epochs=800, later_epochs=400,
                unconditional_horizontal_rms_scale_m=scales['unconditional']['horizontal'],
                conditioned_horizontal_rms_scale_m=scales['conditioned']['horizontal'],
                unconditional_height_rms_scale_m=scales['unconditional']['height'],
                conditioned_height_rms_scale_m=scales['conditioned']['height'],
                native_calls_attempted=361200, scientific_decision='abstain',
                numerical_work=0)


def audit(root, prefix='data/noise-conditioning-comparison-20261111'):
    from lll.noise_conditioning_study import SCOPE, recipe, tasks
    from lll.studies.closed import ClosedStudy

    study = ClosedStudy(root, prefix)
    try:
        identity = tasks()[0]['identity']
        if (study.completion['state'] != 'complete'
                or study.manifest['scope'] != SCOPE
                or study.input('recipe') != recipe()
                or len(study.tasks) != 1 or len(study.rows) != 1
                or identity not in study.tasks
                or study.rows[identity]['passed'] is not True):
            raise ValueError('complete one-task conditioning study required')
        envelope = study.envelope(identity)
        report = validate(
            envelope['result'],
            study.artifact(identity, 'variance-comparison.json'),
            study.artifact(identity, 'error-operator.json'))
        prepayment = study.artifact(identity, 'native-prepayment.json')
        if (prepayment.get('state') != 'complete'
                or prepayment.get('prepaid') !=
                {'native_calls': 361200, 'packet_visits': 361200}
                or prepayment.get('attempted') !=
                prepayment.get('prepaid')):
            raise ValueError('complete exact native charge record required')
        report.update(study=prefix,
                      manifest_sha256=study.completion['manifest_sha256'],
                      summary_sha256=study.completion['summary_sha256'],
                      saved_artifact_hashes=dict(envelope['artifacts']))
        return report
    finally:
        study.close()


def publish(root, prefix='data/noise-conditioning-comparison-20261111'):
    from lll.studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    report = audit(root, prefix)
    location = root / 'docs/noisy-realization-attribution/conditioning-comparison'
    atomic(location / 'verified-report.json', encoded(report))
    text = (
        '# Receiver conditioning on the same noise model\n\n'
        'This generated-data comparison used one fixed rotating-globe trajectory, '
        'known calibration, and one recorded-increment error operator. It did '
        'not use an aircraft recording or fit an Earth model.\n\n'
        f"The later 400 receiver epochs have an **unconditional** horizontal "
        f"RMS error scale of {report['unconditional_horizontal_rms_scale_m']:.2f} m "
        f"and height scale of {report['unconditional_height_rms_scale_m']:.2f} m. "
        f"After conditioning on 800 earlier receiver epochs, the corresponding "
        f"scales are {report['conditioned_horizontal_rms_scale_m']:.2f} m "
        f"and {report['conditioned_height_rms_scale_m']:.2f} m.\n\n"
        'Both scales are expected error sizes, not one realized forecast error. '
        'This resolves the information-footing mismatch with the earlier '
        '33.77 m conditional benchmark. It does not establish a calibrated '
        'prediction interval or an Earth-model decision.\n\n'
        'The saved operator, charge record and variance curves were checked '
        'against the sealed study result. See [the finite plan](PLAN.md) for '
        'the exact input and limits.\n')
    atomic(location / 'README.md', text.encode())
    return report


if __name__ == '__main__':
    print(json.dumps(publish(Path(__file__).resolve().parents[2]),
                     sort_keys=True))
