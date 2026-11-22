# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import dataclass

import pytest

from lll.esa_full_fit_timing import CASES, MAXIMUM, METHODS, assess, tasks


def test_full_benchmark_retains_pairs_and_declares_exact_work():
    entries = tasks(native_packets=300, training_prefix_packets=200)
    assert tuple(entry['payload'] for entry in entries) == CASES
    assert all(case['start'] == 1 for case in CASES)
    assert len({entry['identity'] for entry in entries}) == 2
    for entry in entries:
        assert entry['limits'] == dict(native_calls=2*(MAXIMUM+1),
            packet_visits=2*(MAXIMUM*200*800+300*1200), bound_calls=0, bound_steps=0)
    with pytest.raises(ValueError):
        tasks(native_packets=200, training_prefix_packets=200)


@dataclass
class Pair:
    case: dict

    def fits(self):
        row = dict(**self.case, converged=True, all_columns_retained=True, passed=True,
                   training_cost=12.)
        return {key: dict(row) for key in METHODS}

    def paths(self):
        value = dict(fit=dict(active_parameters=['x'], residual_sum_squares=12., converged=True),
                     forecast=dict(coordinates=[[.2, .3, 300.]], times_s=[1.],
                                   prediction_receiver_positions_used=False))
        return {key: value for key in METHODS}


def test_full_equivalence_requires_each_method_agree_with_archived_result():
    sample = Pair(CASES[0])
    reference_fits, reference_paths = sample.fits(), sample.paths()
    fresh_fits, fresh_paths = sample.fits(), sample.paths()
    assert assess(fresh_fits, fresh_paths, reference_fits, reference_paths)['equivalent']
    for key in METHODS:
        fresh_fits[key]['training_cost'] = 20.
        fresh_paths[key]['fit']['residual_sum_squares'] = 20.
    result = assess(fresh_fits, fresh_paths, reference_fits, reference_paths)
    assert result['fresh']['passed']
    assert not result['equivalent']
