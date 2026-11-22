"""Fixed calibration swaps partition every active direction once."""

import numpy as np
import pytest

from lll import ilvis0_calibration_groups as groups


def test_groups_cover_exactly_twenty_six_directions():
    names = tuple(name for block in groups.GROUPS.values() for name in block)
    assert len(names) == len(set(names)) == 26
    assert groups.VARIANTS == ('baseline','time','vertical','horizontal',
                               'state_mount','all')


def test_one_group_swap_and_full_vector_controls():
    names = tuple(name for block in groups.GROUPS.values() for name in block)
    first = np.zeros(26)
    second = np.linspace(-.8,.8,26)
    swap = groups.hybrid(names,first,second,'vertical')
    assert all(swap[names.index(name)] == second[names.index(name)]
               for name in groups.GROUPS['vertical'])
    assert all(swap[names.index(name)] == 0
               for name in names if name not in groups.GROUPS['vertical'])
    assert np.array_equal(groups.hybrid(names,first,second,'baseline'),first)
    assert np.array_equal(groups.hybrid(names,first,second,'all'),second)
    with pytest.raises(ValueError):
        groups.hybrid(names[:-1],first,second,'vertical')
