# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll.esa_confirmation_evidence import check_public, verify_layout
from lll.esa_confirmation_training_profile import TIMES, TIMES_SHA, _read


ROOT = Path(__file__).resolve().parents[2]


def test_public_confirmation_evidence_reproduces_both_training_lengths():
    result = check_public(ROOT)
    assert result['groups'] == 7
    assert result['query_layouts'] == 14
    assert result['training_profiles'] == 16
    assert result['compared_profiles']['400']['higher_p95_course_rate'] == 5
    assert result['compared_profiles']['800']['higher_p95_course_rate'] == 6
    assert result['compared_profiles']['800']['higher_median_pdop'] == 7
    assert result['confirmed_eligible'] == 0
    assert result['protected_outcome_reads'] == result['new_fits'] == 0
    assert result['instrument_files'] == {
        'catalog_label': 'RQH01', 'development_files': 1, 'reserved_files': 8,
    }


def test_confirmation_evidence_rejects_shifted_withheld_reports():
    layout = _read(ROOT, TIMES, TIMES_SHA)['records']['178a']
    layout['withheld']['first_source_index'] += 2
    layout['withheld']['last_source_index'] += 2
    with pytest.raises(ValueError, match='same withheld reports'):
        verify_layout(layout)
