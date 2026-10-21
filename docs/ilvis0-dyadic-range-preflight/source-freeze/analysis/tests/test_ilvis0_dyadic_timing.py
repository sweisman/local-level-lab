# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import json
from pathlib import Path


def saved_bound():
    root=Path(__file__).resolve().parents[2]
    return json.loads((root/'docs/ilvis0-taylor-complete-prediction/artifacts/transform-full-0-0-0/bound-07.json').read_text())


def test_timing_comparison_requires_exact_remainders_and_all_fields():
    from lll.ilvis0_dyadic_timing import matched_bounds
    original=saved_bound();same=deepcopy(original)
    assert matched_bounds(original,same)['passed']
    same['force_unshared_remainder'][0]+=1e-12
    result=matched_bounds(original,same)
    assert not result['passed'] and 'force_unshared_remainder' in result['different_fields']
    same=deepcopy(original);del same['previous_coefficients']
    assert not matched_bounds(original,same)['passed']
