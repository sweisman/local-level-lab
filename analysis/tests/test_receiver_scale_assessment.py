# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed receiver chart and training-only study inputs."""
from fractions import Fraction as F
import csv
import hashlib
import json
from pathlib import Path

import pytest

from lll.receiver_scale_assessment import axis_chart_values, evaluate, fit_reference


def test_fixed_chart_and_normalized_training_time_use_exact_decimals():
    rows = [
        dict(time1_s='100', latitude_deg='-60', longitude_deg='-75', ellipsoidal_height_m='12000'),
        dict(time1_s='101', latitude_deg='-59.999', longitude_deg='-74.998', ellipsoidal_height_m='12000.5'),
        dict(time1_s='102', latitude_deg='-59.998', longitude_deg='-74.996', ellipsoidal_height_m='12001'),
    ]
    times, north = axis_chart_values(rows, 'north')
    assert times == (F(0), F(1, 2), F(1))
    assert north == (F(0), F(111), F(222))
    assert axis_chart_values(rows, 'east')[1] == (F(0), F(111), F(222))
    assert axis_chart_values(rows, 'up')[1] == (F(0), F(1, 2), F(1))


def test_reference_coefficients_are_decimal_and_close_to_known_polynomial():
    times = tuple(F(i, 11) for i in range(12))
    values = tuple(1 + 2 * time + 3 * time * time for time in times)
    coefficients = fit_reference(times, values, 3)
    assert len(coefficients) == 4
    assert all(isinstance(value, str) and len(value.split('.')[1]) == 12
               for value in coefficients)
    assert all(abs(F(value) - expected) < F(1, 10**9)
               for value, expected in zip(coefficients, (1, 2, 3, 0), strict=True))


@pytest.mark.parametrize('family,degree,axis', [
    ('tau10', 3, 'north'), ('tau300', 7, 'up')])
def test_one_task_reads_only_frozen_receiver_prefix_and_preserves_abstention(
        tmp_path, family, degree, axis):
    frozen = tmp_path / 'source-freeze/analysis/lll/ilvis0_exact_reference_scale.py'
    frozen.parent.mkdir(parents=True)
    frozen.write_bytes((Path(__file__).resolve().parents[1] / 'lll/ilvis0_exact_reference_scale.py').read_bytes())
    prefix = tmp_path / 'receiver-prefix.csv'
    with prefix.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=('time1_s', 'latitude_deg',
                                 'longitude_deg', 'ellipsoidal_height_m'), lineterminator='\n')
        writer.writeheader()
        for index in range(292):
            writer.writerow(dict(time1_s=132350 + index,
                                 latitude_deg=str(F(-60) + F(index, 10000)),
                                 longitude_deg='-75',
                                 ellipsoidal_height_m=str(F(12000) + F(index, 10))))
    prefix_hash = hashlib.sha256(prefix.read_bytes()).hexdigest()
    receipt = tmp_path / 'prefix-receipt.json'
    receipt.write_text(json.dumps(dict(training_epochs=292,
                                       first_time1_s='132350', last_time1_s='132641',
                                       prefix_sha256=prefix_hash,
                                       source_sha256='source-hash', split_sha256='split-hash')))

    class Context:
        root = tmp_path
        saved = None

        def input_path(self, key=None):
            return dict(receiver_prefix=prefix, prefix_receipt=receipt)[key]

        def save(self, name, value):
            assert name == 'assessment.json'
            self.saved = value
            return name

    task = dict(identity=f'{family}-d{degree}-{axis}', family=family, degree=degree, axis=axis,
                input_key='receiver_prefix', prefix_sha256=prefix_hash,
                source_sha256='source-hash', split_sha256='split-hash')
    context = Context()
    result = evaluate(task, context)
    assert result['passed'] is True
    assert result['scientific_decision'] == 'abstain'
    assert context.saved['training_epochs'] == 292
    assert context.saved['coefficient_count'] == degree + 1
    assert context.saved['reason'] == 'certified_under_declared_covariance'
    assert F(int(context.saved['residual_quadratic_num_hex'], 16),
             int(context.saved['residual_quadratic_den_hex'], 16)) >= 0
    assert 'later_positions' not in context.saved
