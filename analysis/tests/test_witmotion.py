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
