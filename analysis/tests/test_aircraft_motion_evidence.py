import json
from pathlib import Path

import pytest

from lll.aircraft_motion_evidence import FILES, clock_scores, verify


def test_public_motion_evidence():
    result = verify(Path(__file__).resolve().parents[2])
    assert result['complete_studies'] == 7
    assert result['terminal_studies'] == 2
    assert result['averaged_histories'] == 64
    assert result['tilt_vectors'] == 20


def test_clock_result_rejects_a_nonzero_offset_in_a_claimed_copy():
    path, _ = FILES['airborne']
    scores = json.loads((Path(__file__).resolve().parents[2]/path).read_bytes())['scores']
    scores['blocks'][0][20]['max_time_offset_s'] = .001
    with pytest.raises(ValueError, match='zero shift'):
        clock_scores(scores, (100, 1200), copied=True)
