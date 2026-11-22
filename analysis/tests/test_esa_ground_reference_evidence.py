# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import pytest

from lll.esa_ground_reference_evidence import (ADDITIONAL, BASE, COMBINED, QAQ_INTAKE, verify,
                                                verify_carrier_reports, verify_qaq_reports)


ROOT = Path(__file__).resolve().parents[2]


def test_current_nuuk_evidence_reproduces_without_runtime_data():
    index, checks = verify(ROOT, version=2)
    assert index['development_flight_groups'] == 1
    assert index['reserved_groups_opened'] == 0
    assert not index['aircraft_error_coverage_qualified']
    assert checks['public_reports'] == 12
    assert checks['verified_carrier_reports'] == 4


def test_combined_reference_evidence_keeps_both_stations_on_one_development_flight():
    index, checks = verify(ROOT, version=3)
    assert index['development_flight_groups'] == 1 and index['reserved_groups_opened'] == 0
    assert index['distant_high_rate_ground_coverage_verified'] is True
    assert index['high_rate_ground_coverage_verified'] is False
    assert index['joint_error_budget']['decision'] == 'abstain'
    assert len(index['studies']) == 14 and checks['public_reports'] == 17


def test_combined_reference_refuses_changed_distant_transfer_even_without_digest_check():
    def load(name):
        return json.loads((ROOT/BASE/name).read_bytes())

    intake = load(QAQ_INTAKE)
    products, score = [load(row[0]) for row in ADDITIONAL[:2]]
    ground, transfer = [load(row[0]) for row in COMBINED[:2]]
    transfer['withheld']['earlier_gain_rms_m'] += .001
    with pytest.raises(ValueError, match='chronological range transfer'):
        verify_qaq_reports(intake, products, score, ground, transfer)


@pytest.mark.parametrize('report,path', [
    (0, ('product_summary', 'final_fixed_rms_m')),
    (1, ('minimum_range_rms_m',)),
    (2, ('tolerances', 2, 'maximum_anchor_axis_error_m')),
    (3, ('cadences', 'ideal_1s', 'observable_norm_fraction')),
])
def test_nuuk_arithmetic_rejects_changed_summary_even_without_digest_check(report, path):
    rows = [json.loads((ROOT/BASE/name).read_bytes()) for name, *_ in ADDITIONAL]
    altered = rows[report]
    for part in path[:-1]:
        altered = altered[part]
    altered[path[-1]] += .01
    verify_carrier_reports(*[json.loads((ROOT/BASE/name).read_bytes()) for name, *_ in ADDITIONAL])
    with pytest.raises(ValueError, match='carrier evidence'):
        verify_carrier_reports(*rows)
