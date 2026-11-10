# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only receiver chart for a separate, declared error-law assessment."""
from fractions import Fraction
import csv
import hashlib
import importlib.util
import json


CHART = dict(latitude_origin_deg=Fraction(-60), longitude_origin_deg=Fraction(-75),
             height_origin_m=Fraction(12000), north_m_per_degree=Fraction(111000),
             east_m_per_degree=Fraction(55500))


def _exact(value):
    if isinstance(value, (float, bool)):
        raise ValueError('saved decimal text required')
    try:
        return Fraction(value)
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError('finite saved decimal text required') from error


def axis_chart_values(rows, axis):
    """Use the fixed chart and exact 0-to-1 training time; no Earth fit enters."""
    if axis not in ('north', 'east', 'up'):
        raise ValueError('north, east or up axis required')
    rows = tuple(rows)
    if len(rows) < 2:
        raise ValueError('at least two saved training epochs required')
    epochs = tuple(_exact(row['time1_s']) for row in rows)
    if any(right <= left for left, right in zip(epochs, epochs[1:])):
        raise ValueError('strictly increasing saved receiver times required')
    span = epochs[-1] - epochs[0]
    times = tuple((epoch - epochs[0]) / span for epoch in epochs)
    if axis == 'north':
        values = tuple(CHART['north_m_per_degree']
                       * (_exact(row['latitude_deg']) - CHART['latitude_origin_deg'])
                       for row in rows)
    elif axis == 'east':
        values = tuple(CHART['east_m_per_degree']
                       * (_exact(row['longitude_deg']) - CHART['longitude_origin_deg'])
                       for row in rows)
    else:
        values = tuple(_exact(row['ellipsoidal_height_m']) - CHART['height_origin_m']
                       for row in rows)
    return times, values


def fit_reference(times, values, degree):
    """Choose a decimal coefficient vector from training rows only.

    This numerical choice need not be optimal: the exact quadratic at any
    coefficient vector is at least the fixed-space minimum. It cannot narrow
    the resulting bound spuriously under the declared covariance law.
    """
    import numpy as np

    if type(degree) is not int or degree not in (3, 5, 7):
        raise ValueError('fixed polynomial degree 3, 5 or 7 required')
    times, values = tuple(times), tuple(values)
    if len(times) != len(values) or len(times) <= degree:
        raise ValueError('complete training values and residual dimension required')
    x = np.asarray([float(_exact(time)) for time in times], dtype=float)
    y = np.asarray([float(_exact(value)) for value in values], dtype=float)
    if (not np.all(np.isfinite(x)) or not np.all(np.isfinite(y))
            or np.any(np.diff(x) <= 0)):
        raise ValueError('finite ordered training reference required')
    design = np.column_stack(tuple(x ** power for power in range(degree + 1)))
    coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != degree + 1 or not np.all(np.isfinite(coefficients)):
        raise ValueError('full-rank finite training reference required')
    return tuple(f'{float(value):.12f}' for value in coefficients)


TRANSITIONS = dict(tau10=Fraction(904837418036, 10**12),
                   tau300=Fraction(996672216055, 10**12))


def evaluate(task, context):
    """One frozen family/degree/axis assessment, with no withheld positions."""
    axis, family, degree = task['axis'], task['family'], task['degree']
    if axis not in ('north', 'east', 'up') or family not in TRANSITIONS or degree not in (3, 5, 7):
        raise ValueError('predeclared axis, covariance family and degree required')
    prefix = context.input_path('receiver_prefix')
    receipt = json.loads(context.input_path('prefix_receipt').read_text())
    if (hashlib.sha256(prefix.read_bytes()).hexdigest() != task['prefix_sha256']
            or receipt['prefix_sha256'] != task['prefix_sha256']
            or receipt['source_sha256'] != task['source_sha256']
            or receipt['split_sha256'] != task['split_sha256']
            or receipt['training_epochs'] != 292
            or Fraction(receipt['first_time1_s']) != 132350
            or Fraction(receipt['last_time1_s']) != 132641):
        raise ValueError('frozen receiver prefix or selection receipt changed')
    with prefix.open(newline='') as stream:
        rows = tuple(csv.DictReader(stream))
    if (len(rows) != 292 or Fraction(rows[0]['time1_s']) != 132350
            or Fraction(rows[-1]['time1_s']) != 132641
            or any(Fraction(right['time1_s']) - Fraction(left['time1_s']) != 1
                   for left, right in zip(rows, rows[1:]))):
        raise ValueError('exact saved one-second training support required')
    times, values = axis_chart_values(rows, axis)
    coefficients = fit_reference(times, values, degree)
    frozen_module = context.root / 'source-freeze/analysis/lll/ilvis0_exact_reference_scale.py'
    spec = importlib.util.spec_from_file_location('_frozen_exact_reference_scale', frozen_module)
    if spec is None or spec.loader is None:
        raise ValueError('frozen exact-reference source required')
    exact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exact)
    variance = Fraction(9 if axis != 'up' else 49, 100)
    shared = Fraction(1 if axis != 'up' else 9)
    assessment = exact.certify_scale(
        values, times, (TRANSITIONS[family],) * (len(rows) - 1),
        coefficients=coefficients, ou=shared, offset=shared, drift=shared,
        white=variance, alpha=Fraction(1, 100), k=16,
        source_id=task['prefix_sha256'],
        covariance_id=family + '-' + axis,
        design_is_fixed=True, error_distribution='gaussian',
        decimal_places=6, max_bits=32768, max_epochs=292, max_seconds=30)
    quadratic = assessment['residual_quadratic']
    record = dict(identity=task['identity'], axis=axis, family=family, degree=degree,
                  training_epochs=len(rows), coefficient_count=len(coefficients),
                  coefficients=coefficients, transition=str(TRANSITIONS[family]),
                  white_variance=str(variance), ou_variance=str(shared),
                  offset_variance=str(shared), drift_variance=str(shared),
                  residual_quadratic_num_hex=hex(quadratic.numerator) if quadratic is not None else None,
                  residual_quadratic_den_hex=hex(quadratic.denominator) if quadratic is not None else None,
                  quantile_floor=str(assessment['quantile_floor']),
                  scale_upper=str(assessment['scale_upper']),
                  reason=assessment['reason'],
                  covariance_law_established=False, aircraft_coverage_established=False,
                  scientific_decision='abstain')
    artifact = context.save('assessment.json', record)
    return dict(passed=assessment['reason'] == 'certified_under_declared_covariance',
                scientific_decision='abstain', reason=assessment['reason'],
                result_artifact=artifact, axis=axis, family=family, degree=degree,
                original_imu_reads=0, model_fits=0)
