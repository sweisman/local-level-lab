import pytest

from lll.esa_girafe_level1_airborne import select_block
from lll.esa_girafe_level1_prefix import STEP, TICKS


def test_fixed_airborne_interval_is_half_open_and_reverses_sign():
    rows = [(5*TICKS+STEP*i+1, -9.8) for i in range(-1, 12)]
    block = select_block(rows, 5, 6)
    assert block == [(5*TICKS+STEP*i+1, 9.8) for i in range(10)]
    with pytest.raises(ValueError, match='complete 10 Hz interval'):
        select_block(rows[2:], 5, 6)
