import copy

import numpy as np
import pytest

from lll.collate import collate, gate
from lll.policy import PRIMARY_EXCLUSIONS, heading_diversity, provenance_reasons
from test_analysis import _fake, _approvals


def eligible():
    r = _fake("u", (1, 1, 0), (.1, .1, .1))
    return r, _approvals([r])[r["input_sha256"]]


def test_upload_cannot_self_approve():
    r, a = eligible()
    r["provenance"] = a
    assert "unverified provenance" in gate(r, {})
    assert not gate(r, {}, approval=a)
    a["sha256"] = "changed"
    assert "approval hash mismatch" in gate(r, {}, approval=a)


@pytest.mark.parametrize("flag", PRIMARY_EXCLUSIONS)
def test_every_integrity_gate(flag):
    r, a = eligible()
    r["flags"].append(flag)
    assert PRIMARY_EXCLUSIONS[flag] in gate(r, {}, approval=a)


def test_bench_must_be_complete_and_precede_flight():
    r, a = eligible()
    for change in (lambda b: b["checks"].pop("temperature"),
                   lambda b: b.update(approved_at=r["flight_started_utc"]),
                   lambda b: b.update(config={})):
        altered = copy.deepcopy(a)
        change(altered["bench"])
        assert provenance_reasons(r, altered)


def test_heading_policy_counts_retained_time_and_wraps_north():
    assert heading_diversity({"psi": np.radians([359, 1, 40]), "dt": [300, 300, 600]})["adequate"]
    assert not heading_diversity({"psi": np.radians([0, 90]), "dt": [600, 599]})["adequate"]


def test_empty_term_and_untrusted_downgrade():
    r, a = eligible()
    r["fit"]["identifiability"] = {"identified_by_term": {"k_rot_sphere": True, "k_curv": True, "k_disc": False}}
    bad = _fake("u", (3, 3, 3), (.01, .01, .01), tier="exploratory")
    col = collate([r, bad], provenance={r["input_sha256"]: a})
    assert col["n_primary"] == 1
    assert col["pooled_k"]["k_disc"] is None
    assert col["ground"]["fit"] is None


def test_exact_zero_rice_and_duplicate_turn():
    from lll.calib import rice_interval
    from lll.attitude import mount_epochs
    r = rice_interval([0, 0], [1, 1])
    assert r["ci95"][0] == 0 and r["p_zero"] == 1
    t = np.arange(0, 80, .05)
    gyro = np.zeros((len(t), 3))
    gyro[(t >= 20) & (t < 25), 2] = np.radians(36)
    epochs, _ = mount_epochs(t, gyro, [(30, "index_turn"), (31, "index_turn"), (60, "placement_shift")])
    assert len(epochs) == 2
    np.testing.assert_allclose(epochs[-1]["R0"], np.diag([-1, -1, 1]), atol=1e-8)


def test_configuration_requires_rate_range_and_autozero_readbacks():
    from lll.policy import verified_config
    imu = {"variant": "spp", "config": {"rate_hz": 100}}
    good = "0x02=0x17 0x03=0x9 0x20=0x3 0x21=0x3 0x63=0x1 ok=true"
    assert verified_config(good, imu)
    for bad in (good.replace("0x20=0x3", "0x20=?"), good.replace("0x03=0x9", "0x03=0x8"),
                good.replace("0x63=0x1", "0x63=0x0"), good.replace("0x02=0x17 ", "")):
        assert not verified_config(bad, imu)


def test_bad_incomplete_observation_cannot_be_blessed_by_certificate():
    from lll.analyze import unit_quality
    q = unit_quality({"drift": {"bench": {"adev_at_dph": {"300": [10, 10, 10]}}}}, {"imu": {"unit_id": "u"}})
    assert q["tier"] == "exploratory"
    r, a = eligible()
    r["unit_quality"] = q
    assert "IMU unit tier exploratory" in gate(r, {}, approval=a)


def test_report_plot_uses_reported_t_interval(monkeypatch):
    from lll import report
    observed = []
    from matplotlib.axes import Axes
    original = Axes.errorbar
    def capture(self, *args, **kwargs):
        observed.append(kwargs["xerr"])
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Axes, "errorbar", capture)
    report._k_figure({"k_curv": 1}, {"k_curv": .1}, {"k_curv": [.1, 1.9]})
    assert observed == pytest.approx([.9])
