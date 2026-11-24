import pytest

from lll.esa_girafe_level1_prefix import STEP, compare


def test_signed_samples_recover_the_predeclared_clock_shift():
    original = [(index*STEP, -9.8+index**2/10000) for index in range(46)]
    processed = [(time-STEP, value) for time, value in original[21:25]]
    charges = []
    scores = compare(processed, original, charges.append)
    assert len(scores) == 41
    assert charges == [4]*41
    exact = [row for row in scores if row['rms_mps2'] == 0]
    assert [row['shift_s'] for row in exact] == [.1]
    assert exact[0]['mean_time_offset_s'] == .1


def test_missing_original_sample_fails_instead_of_reusing_a_neighbor():
    original = [(index*STEP, -9.8) for index in range(45) if index != 21]
    processed = [(index*STEP, -9.8) for index in range(20, 24)]
    with pytest.raises(ValueError, match='one-to-one time match'):
        compare(processed, original, lambda _: None)
