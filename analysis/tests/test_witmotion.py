# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import numpy as np
import pytest

from lll import witmotion as w

V = json.loads((Path(__file__).parents[2] / "docs" / "test_vectors.json").read_text())["witmotion"]
SPP = {"variant": "spp", "config": {"rate_hz": 100}}
BLE = {"variant": "ble", "config": {"rate_hz": 100}}


def _spp_cycle():
    return b"".join(bytes.fromhex(v["hex"]) for v in V["spp"])


def test_spp_vectors():
    s, st = w.decode(np.array([10 ** 9]), [_spp_cycle()], SPP)
    exp = {v["type"]: v["expect"] for v in V["spp"]}
    np.testing.assert_allclose([s["gyro"][c][0] for c in "xyz"], np.radians(exp["gyro"]["gyro_dps"]), rtol=1e-12)
    np.testing.assert_allclose(s["imu_volt"]["volt"][0], exp["gyro"]["volt"])
    np.testing.assert_allclose([s["accel"][c][0] for c in "xyz"], np.array(exp["accel"]["accel_g"]) * w.G0)
    np.testing.assert_allclose(s["imu_temp"]["temp_c"][0], exp["accel"]["temp_c"])
    np.testing.assert_allclose([s["mag"][c][0] for c in "xyz"], exp["mag"]["mag_counts"])
    assert st["bad_checksums"] == 0 and st["unparsed_bytes"] == 0 and st["time_base"] == "device_clock"
    # the time packet decodes to the stated calendar time
    buf = np.frombuffer(bytes.fromhex(V["spp"][0]["hex"]), np.uint8)
    t = w._spp_time_s(buf, np.array([0]))[0]
    ref = (np.datetime64("2026-10-02T13:45:07.500") - np.datetime64("1970-01-01T00:00:00")) / np.timedelta64(1, "s")
    assert t == pytest.approx(ref, abs=1e-6)


def test_spp_rejects_bad_checksum_and_resyncs_after_junk():
    good = _spp_cycle()
    data = b"\x55\x52\x01" + bytes.fromhex(V["spp_bad_checksum"]) + good + b"\x00\x55" + good
    s, st = w.decode(np.array([10 ** 9]), [data], SPP)
    assert len(s["gyro"]["t_ns"]) == 2
    assert st["bad_checksums"] >= 1 and st["unparsed_bytes"] == 3 + 11 + 2


def test_spp_packets_split_across_reads():
    data = _spp_cycle() * 3
    cuts = [5, 17, 40, 41, 100]
    chunks = [data[a:b] for a, b in zip([0] + cuts, cuts + [len(data)])]
    s, st = w.decode(np.arange(len(chunks)) * 10 ** 7, chunks, SPP)
    assert len(s["gyro"]["t_ns"]) == 3 and st["unparsed_bytes"] == 0


def test_ble_vectors():
    chunks = [bytes.fromhex(v["hex"]) for v in V["ble"]]
    s, st = w.decode(np.array([10 ** 9, 10 ** 9 + 5]), chunks, BLE)
    d, r = V["ble"][0]["expect"], V["ble"][1]["expect"]
    np.testing.assert_allclose([s["accel"][c][0] for c in "xyz"], np.array(d["accel_g"]) * w.G0)
    np.testing.assert_allclose([s["gyro"][c][0] for c in "xyz"], np.radians(d["gyro_dps"]), rtol=1e-12)
    np.testing.assert_allclose([s["mag"][c][0] for c in "xyz"], r["mag_counts"])
    np.testing.assert_allclose(s["imu_temp"]["temp_c"][0], r["temp_c"])


def test_records_round_trip_and_truncation():
    raw = w.write_records([5, 7], [b"abc", b"\x55" * 300])
    t, c = w.read_records(raw + w.REC_HEADER.pack(9, 50) + b"short")  # app killed mid-write
    assert t.tolist() == [5, 7] and c == [b"abc", b"\x55" * 300]


@pytest.mark.parametrize("ppm", [-80.0, 0.0, 120.0])
def test_clock_map_recovers_sample_times(ppm):
    rng = np.random.default_rng(1)
    n = 100 * 3600  # one hour at 100 Hz
    true_s = np.arange(n) / 100.0
    x = true_s * (1 + ppm * 1e-6) + 1234.5          # device clock: offset and rate error
    # reads every 1-4 samples; every sample in a read arrives when the read does
    ends = np.unique(np.append(np.cumsum(rng.integers(1, 5, n)), n - 1))
    ends = ends[ends < n]
    lat = 0.004 + rng.exponential(0.015, len(ends))
    lat[rng.random(len(ends)) < 0.01] += 0.3                        # occasional long stall
    read_arr = true_s[ends] + lat
    arr = np.maximum.accumulate(read_arr[np.searchsorted(ends, np.arange(n))])
    t, run = w.clock_map(x, np.round(arr * 1e9).astype(np.int64))
    err = t / 1e9 - true_s
    assert run.max() == 0
    # recovered to within a few ms of the true time, plus the constant minimum latency
    assert np.abs(err - np.median(err)).max() < 0.005
    assert 0.0 <= np.median(err) < 0.010


def test_bench_on_synthetic_session(tmp_path):
    from lll.cli import bench
    from lll.synth import synthesize
    p = tmp_path / "s.zip"
    synthesize(p, "sphere_still", seed=3, fs=20.0, cal=("pre",), legs=((90.0, 15.0),))
    r = bench(p)
    assert r["decode"]["bad_checksums"] == 0
    assert r["rate_hz"] == pytest.approx(20.0, rel=1e-3)
    assert r["gyro_lsb_dph"] == pytest.approx(2000 / 32768 * 3600, rel=1e-9)
    assert all(0 < f < 1 for f in r["gyro_mode_fraction"])


def test_sparse_spp_clock_packets_time_correctly(tmp_path):
    """If the device sends its clock packet only every 5th sample, each gyro sample is dated from
    the nearest preceding clock packet plus whole sample periods."""
    from lll.format import read_session
    from lll.synth import synthesize
    out = {}
    for every in (1, 5):
        p = tmp_path / f"e{every}.zip"
        synthesize(p, "sphere_still", seed=2, fs=20.0, cal=("pre",), legs=((90.0, 30.0),), spp_time_every=every)
        out[every] = read_session(p)
    s = out[5]
    assert s.imu_stats["time_base"] == "device_clock_interpolated" and s.imu_stats["runs"] == out[1].imu_stats["runs"]
    d = np.diff(s.streams["gyro"]["t_ns"]) / 1e9
    assert np.abs(d[d < 1] - 0.05).max() < 0.003


@pytest.mark.parametrize("loss,p95_ms", [(0.001, 5.0), (0.01, 20.0)])
def test_ble_lost_samples_are_recovered(loss, p95_ms):
    """BLE samples are timed by counting packets, so each lost notification would make every later
    sample early by one period. The decoder finds the losses from steps in the arrival envelope
    and restores the true sample index."""
    rng = np.random.default_rng(4)
    rate, n = 100.0, 100 * 1800
    true_s = np.arange(n) / rate
    kept = rng.random(n) >= loss
    ts = true_s[kept]
    arr = np.round(np.maximum.accumulate(np.ceil(ts / 7.5e-3) * 7.5e-3 + rng.exponential(0.002, len(ts)) + 0.003) * 1e9).astype(np.int64)
    idx, n_lost = w.recover_lost_samples(arr, rate)
    assert abs(n_lost - (n - kept.sum())) <= 0.01 * (n - kept.sum()) + 1
    t, _ = w.clock_map(idx / rate, arr, period_s=1 / rate)
    err = t / 1e9 - ts
    assert np.all(t <= arr)                                     # never later than its own arrival
    assert np.percentile(np.abs(err - np.median(err)), 95) < p95_ms / 1000


def test_ble_loss_rate_is_reported(tmp_path):
    from lll.format import read_session
    from lll.synth import synthesize
    p = tmp_path / "b.zip"
    synthesize(p, "sphere_still", seed=2, fs=20.0, cal=("pre",), legs=((90.0, 30.0),), variant="ble", ble_loss=0.02)
    st = read_session(p).imu_stats
    assert abs(st["loss_estimate"] - 0.02) < 0.004


def test_bench_reports_reversal_stability_and_comparison(tmp_path):
    from lll.cli import bench, bench_compare
    from lll.synth import synthesize
    out = {}
    for rng in (2000.0, 250.0):
        p = tmp_path / f"r{rng:.0f}.zip"
        synthesize(p, "sphere_rotating", seed=3, fs=20.0, cal=("pre",), legs=((90.0, 12.0),), reversal_pairs=3,
                   drift_runs=True, gyro_range_dps=rng, temp_coef_dph_per_c=(1.0, 0, 0), flight_temp_rise_c=0.0)
        out[rng] = bench(p)
    r = out[250.0]
    assert r["stability_phase"] == "drift_pre" and r["reversal"]["pairs"] == 3
    assert "300" in r["adev_at_dph"] and r["samples_received"] <= r["samples_expected"] + 1
    assert r["gyro_lsb_dph"] < out[2000.0]["gyro_lsb_dph"] / 7
    c = bench_compare(out[2000.0], r)
    assert c["a"]["gyro_lsb_dph"] > c["b"]["gyro_lsb_dph"]
