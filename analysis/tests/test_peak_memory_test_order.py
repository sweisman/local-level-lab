"""Peak-RSS controls run before unrelated tests inflate process history."""

from types import SimpleNamespace

import conftest


def test_peak_memory_modules_run_first_without_changing_other_order():
    paths = [
        'analysis/tests/test_other_a.py::test_one',
        'analysis/tests/test_ilvis0_native_prefix_long.py::test_limit',
        'analysis/tests/test_other_b.py::test_two',
        'analysis/tests/test_ilvis0_dense_bound_batches.py::test_limit',
        'analysis/tests/test_ilvis0_native_prefix_recovery.py::test_limit',
    ]
    items = [SimpleNamespace(nodeid=path) for path in paths]
    conftest.prioritize_peak_memory_tests(items)
    assert [item.nodeid for item in items] == [
        paths[1], paths[3], paths[4], paths[0], paths[2],
    ]
