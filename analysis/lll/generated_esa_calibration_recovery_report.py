# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare sealed generated fits with the generator's known sensor settings."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID, PLAN, recipe
from .generated_esa_bounded_pilot_v2_report import build as verified_pilot


AUDIT_PLAN = ('docs/prediction-observed-development/'
              'GENERATED_CALIBRATION_RECOVERY_PLAN.md')
SENSOR_NAMES = tuple(prefix + '_' + axis
                     for prefix in ('gyro_bias', 'accel_bias',
                                    'gyro_gain', 'accel_gain')
                     for axis in 'xyz') + ('gravity_delta', 'time_offset')


def compare(truth, fitted, limits):
    """Compare declared physical values in each parameter's half-range units."""
    if not isinstance(truth, dict) or not truth or not isinstance(fitted, dict) or not isinstance(limits, dict):
        raise ValueError('matched calibration dictionaries required')
    rows = {}
    for name, value in truth.items():
        fit = fitted.get(name)
        bound = limits.get(name)
        if (not isinstance(name, str) or not name
                or any(type(item) not in (int, float) or not math.isfinite(item)
                       for item in (value, fit, bound))
                or bound <= 0 or abs(value) > bound * (1 + 1e-10)
                or abs(fit) > bound * (1 + 1e-10)):
            raise ValueError('finite in-box matched calibration values required')
        delta = (fit-value)/bound
        rows[name] = dict(true_value=float(value), fitted_value=float(fit),
                          half_range=float(bound), normalized_error=float(delta),
                          fitted_at_bound=abs(fit) >= bound*(1-1e-8))
    magnitude = sum(row['normalized_error']**2 for row in rows.values())
    order = sorted(rows, key=lambda name: (-abs(rows[name]['normalized_error']), name))
    return dict(count=len(rows), parameters=rows,
                rms_normalized_error=math.sqrt(magnitude/len(rows)),
                maximum_absolute_normalized_error=abs(rows[order[0]]['normalized_error']),
                top_discrepancies=order[:5],
                fitted_bounds=[name for name in order if rows[name]['fitted_at_bound']])


def build(root):
    from .airquantumgrav_observation_truth import sensor_parameters
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    original = verified_pilot(root)
    if (original['tasks_total'] != 2 or original['technical_passing'] != 2
            or original['original_physical_passing'] != 0
            or original['scientific_decision'] != 'abstain'):
        raise ValueError('closed inaccurate two-law pilot required')
    study = ClosedStudy(root, 'data/' + ID)
    try:
        r = recipe()
        if (study.input('recipe') != r or r['sensor_case'] != 'interior'
                or set(study.tasks) != {'increment', 'point'}
                or any(study.tasks[law]['payload'].get('profile') is not False
                       for law in ('increment', 'point'))):
            raise ValueError('unchanged positive-sign interior generator required')
        generated = sensor_parameters(1, 'interior')
        truth = {name: generated[name] for name in SENSOR_NAMES}
        limits = {name: r['limits'][name] for name in SENSOR_NAMES}
        laws = {}
        for law in ('increment', 'point'):
            raw = study.artifact(law, 'fit.json', raw=True)
            fit = json.loads(raw)
            if (fit.get('converged') is not True
                    or fit.get('stopping_rule_verified') is not True
                    or fit.get('scientific_decision') != 'abstain'
                    or set(SENSOR_NAMES) - set(fit.get('active_parameters', []))
                    or not isinstance(fit.get('parameters'), dict)
                    or not isinstance(fit.get('active_bounds'), list)):
                raise ValueError('complete verified generated calibration fit required')
            row = compare(truth, fit['parameters'], limits)
            if set(row['fitted_bounds']) != set(fit['active_bounds']) & set(SENSOR_NAMES):
                raise ValueError('saved active-bound labels disagree with parameters')
            laws[law] = dict(**row,
                             fit_artifact_sha256=hashlib.sha256(raw).hexdigest(),
                             training_horizontal_rms_m=original['laws'][law]['training_horizontal_rms_m'],
                             future_horizontal_rms_m=original['laws'][law]['future_horizontal_rms_m'])
        return dict(version='generated-esa-calibration-recovery-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / AUDIT_PLAN).read_bytes()).hexdigest(),
                    original_plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2, original_physical_passing=0, laws=laws,
                    new_fits=0, original_reads=0, protected_reads=0,
                    aircraft_calibration_identified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved-calibration report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({law: dict(rms_normalized_error=row['rms_normalized_error'],
                                fitted_bounds=row['fitted_bounds'])
                      for law, row in result['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
