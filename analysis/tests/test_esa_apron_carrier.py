import pytest

from lll.esa_apron_carrier import rms_steps


def test_pair_rms_uses_common_signals_and_removes_clock_per_report():
    result = rms_steps([{1: 2., 2: 4., 3: 3.}, {1: 20., 2: 24., 4: 26.}, {1: 5., 2: 1.}])
    assert result['half_second']['ranges'] == 8
    assert result['one_second']['ranges'] == 2
    assert result['one_second']['rms_m'] == pytest.approx(3.)


def test_empty_one_second_support_returns_no_rms():
    result = rms_steps([{1: .1, 2: .2}, {3: .3, 4: .4}])
    assert result['one_second'] == dict(intervals=0, ranges=0, rms_m=None)


def test_clock_correction_preserves_transmit_time():
    from lll.esa_apron_carrier import corrected_receive
    from lll.gnss_position import C

    raw = {'seconds': 350000., 'week': 2269}
    codes = [2.2e7, 2.5e7]
    corrected, ranges = corrected_receive(raw, codes, .00032)
    assert corrected['seconds'] == pytest.approx(349999.99968, abs=1e-10, rel=0)
    assert raw['seconds'] == 350000.
    assert [corrected['seconds']-code/C for code in ranges] == pytest.approx(
        [raw['seconds']-code/C for code in codes], abs=1e-10, rel=0)
