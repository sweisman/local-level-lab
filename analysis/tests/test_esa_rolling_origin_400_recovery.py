"""The 400/120 development fit gets a separate frozen recovery identity."""

import pytest


def test_rolling_recovery_has_distinct_parent_and_continuation():
    from lll.esa_rolling_origin_400_recovery import PARENT,CONTINUATION,POLICY

    assert PARENT=='data/esa-rolling-origin-400-development-v1-20261115'
    assert CONTINUATION==PARENT+'-continuation'
    assert 'rolling-origin-400' in POLICY


def test_rolling_recovery_refuses_unprepared_parent(tmp_path):
    from lll.esa_rolling_origin_400_recovery import freeze

    with pytest.raises((FileNotFoundError,ValueError)):
        freeze(tmp_path)
