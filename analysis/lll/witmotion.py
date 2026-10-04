# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decode WitMotion WT901 byte streams (docs/FORMAT.md, imu.bin.gz).

The app stores every Bluetooth read verbatim, stamped with the phone's elapsedRealtimeNanos at
arrival. All decoding happens here, so it can be audited and re-run.

Two variants:

  spp  ICM-42605 / MMC3630 behind an HC-06 (Bluetooth 2.0 serial). WIT serial protocol: 11-byte
       packets 0x55 <type> <8 data bytes> <checksum>, checksum = low byte of the sum of the first 10.
         0x50 time   YY MM DD hh mm ss msL msH   (device clock)
         0x51 accel  ax ay az T                  a = raw/32768*range_g g, T = raw/100 °C
         0x52 gyro   wx wy wz V                  w = raw/32768*range_dps °/s, V = raw/100 V
         0x54 mag    hx hy hz T                  raw counts (scale unverified), T = raw/100 °C
         0x53 angle and 0x59 quaternion are the device's own fusion output, and 0x5F is a
         register readback from the app's config check. All three are skipped.
  ble  MPU9250 with BLE 5.0. 20-byte notifications, no checksum:
         0x55 0x61   ax ay az wx wy wz roll pitch yaw   (int16 LE, same scales as above)
         0x55 0x71   regL regH + 8 int16 registers (reply to a register read the app polls).
                     Starting at 0x3A: HX HY HZ Roll Pitch Yaw TEMP(/100 °C) status.

All scale factors and register meanings come from WitMotion's published protocol documents and
must be confirmed against real captures (plan, Phase 0).

Sample times. Bluetooth only ever adds latency, so arrival time is an upper bound on when a
sample was taken. Within each contiguous run, the device's own time base (the 0x50 clock on spp,
the sample index on ble) is mapped to the phone clock by a straight-line fit corrected to the
lower envelope of arrival times. That removes the crystal's rate error and the link jitter.
"""
from __future__ import annotations

import struct

import numpy as np

G0 = 9.80665
VARIANTS = ("spp", "ble")
SPP_TYPES = (0x50, 0x51, 0x52, 0x53, 0x54, 0x59, 0x5F)  # 0x5F: register readback (app config check)
BLE_LEN = 20
REG_MAG = 0x3A
REC_HEADER = struct.Struct("<qH")
# Gyro full-scale register (0x20), from WitMotion's protocol; unverified until the bench test.
REG_GYRO_RANGE = 0x20
GYRO_RANGE_DPS = {0: 250.0, 1: 500.0, 2: 1000.0, 3: 2000.0}
REG_ACC_RANGE = 0x21
ACC_RANGE_G = {0: 2.0, 1: 4.0, 2: 8.0, 3: 16.0}


def range_from_events(events, reg=REG_GYRO_RANGE, table=GYRO_RANGE_DPS):
    """A full scale the device itself reported in the app's config readbacks (imu_config events,
    e.g. "0x20=0x1 …"). Returns (value or None, consistent). Gyro by default; pass
    reg=REG_ACC_RANGE, table=ACC_RANGE_G for the accelerometer."""
    seen = set()
    key = f"0x{reg:02x}="
    for _, kind, detail in events:
        if kind != "imu_config":
            continue
        for tok in detail.split():
            if tok.startswith(key) and tok[len(key):] not in ("?", ""):
                code = int(tok[len(key):], 16)
                if code in table:
                    seen.add(table[code])
    if not seen:
        return None, True
    return (seen.pop(), True) if len(seen) == 1 else (None, False)


# ---------- framing of imu.bin ----------

def write_records(arrival_ns, chunks) -> bytes:
    return b"".join(REC_HEADER.pack(int(t), len(c)) + bytes(c) for t, c in zip(arrival_ns, chunks))


def read_records(raw: bytes):
    """imu.bin (decompressed) → (arrival_ns int64 array, list of chunk bytes)."""
    ts, chunks, i, n = [], [], 0, len(raw)
    while i + REC_HEADER.size <= n:
        t, ln = REC_HEADER.unpack_from(raw, i)
        i += REC_HEADER.size
        if i + ln > n:
            break  # truncated final record (app killed mid-write)
        ts.append(t)
        chunks.append(raw[i:i + ln])
        i += ln
    return np.array(ts, dtype=np.int64), chunks


# ---------- encoding (synth and test fixtures) ----------

def to_raw(v, full_scale):
    return np.clip(np.round(np.asarray(v, float) / full_scale * 32768.0), -32768, 32767).astype(np.int16)


def spp_packets(ptype: int, vals) -> np.ndarray:
    """(n, 4) int16 → (n, 11) uint8 packets with checksums."""
    vals = np.asarray(vals, dtype="<i2").reshape(-1, 4)
    out = np.empty((len(vals), 11), np.uint8)
    out[:, 0], out[:, 1] = 0x55, ptype
    out[:, 2:10] = vals.view(np.uint8).reshape(-1, 8)
    out[:, 10] = (out[:, :10].astype(np.int64).sum(axis=1) & 0xFF).astype(np.uint8)
    return out


def spp_time_packets(dev_ms) -> np.ndarray:
    """Device clock (ms since 2000-01-01) → (n, 11) 0x50 packets."""
    d = np.datetime64("2000-01-01T00:00:00.000", "ms") + np.asarray(dev_ms, np.int64).astype("timedelta64[ms]")
    day = d.astype("M8[D]")
    month = d.astype("M8[M]")
    ms_day = (d - day).astype(np.int64)
    b = np.empty((len(d), 8), np.uint8)
    b[:, 0] = d.astype("M8[Y]").astype(np.int64) + 1970 - 2000
    b[:, 1] = month.astype(np.int64) % 12 + 1
    b[:, 2] = (day - month.astype("M8[D]")).astype(np.int64) + 1
    b[:, 3] = ms_day // 3_600_000
    b[:, 4] = ms_day // 60_000 % 60
    b[:, 5] = ms_day // 1000 % 60
    b[:, 6] = ms_day % 1000 & 0xFF
    b[:, 7] = ms_day % 1000 >> 8
    return spp_packets(0x50, b.view("<i2"))


def ble_packets(head: int, vals) -> np.ndarray:
    """head 0x61: (n, 9) int16. head 0x71: (n, 9) int16 where column 0 is the start register."""
    vals = np.asarray(vals, dtype="<i2").reshape(-1, 9)
    out = np.empty((len(vals), BLE_LEN), np.uint8)
    out[:, 0], out[:, 1] = 0x55, head
    out[:, 2:] = vals.view(np.uint8).reshape(-1, 18)
    return out


# ---------- decoding ----------

def _i16(buf: np.ndarray, pos: np.ndarray, n: int) -> np.ndarray:
    """n little-endian int16 values starting at buf[pos] for each pos → (len(pos), n)."""
    idx = pos[:, None] + np.arange(2 * n)[None, :]
    return buf[idx].copy().view("<i2").reshape(len(pos), n).astype(np.int64)


def _spp_packets(buf: np.ndarray):
    """Positions and types of valid 11-byte packets, chosen greedily without overlap."""
    if len(buf) < 11:
        return np.zeros(0, np.int64), np.zeros(0, np.uint8), 0
    head = np.where((buf[:-10] == 0x55) & np.isin(buf[1:-9], SPP_TYPES))[0]
    cs = np.concatenate([[0], np.cumsum(buf, dtype=np.int64)])
    ok = ((cs[head + 10] - cs[head]) & 0xFF) == buf[head + 10]
    bad = int((~ok).sum())
    cand = head[ok]
    keep, last = [], -11
    for p in cand.tolist():
        if p >= last + 11:
            keep.append(p)
            last = p
    pos = np.array(keep, dtype=np.int64)
    return pos, buf[pos + 1] if len(pos) else np.zeros(0, np.uint8), bad


def _spp_time_s(buf, pos):
    """0x50 packets → device time in seconds (float). Falls back to day-of-month arithmetic if
    the device's calendar fields are not a valid date (clock never set)."""
    b = buf[pos[:, None] + np.arange(2, 10)[None, :]].astype(np.int64)
    yy, mo, dd, hh, mi, ss = (b[:, i] for i in range(6))
    tod = ((hh * 60 + mi) * 60 + ss) + (b[:, 6] | (b[:, 7] << 8)) / 1000.0
    # days from civil date (H. Hinnant's algorithm), vectorized
    y = 2000 + yy - (mo <= 2)
    era = y // 400
    yoe = y - era * 400
    doy = (153 * ((mo + 9) % 12) + 2) // 5 + dd - 1
    days = era * 146097 + yoe * 365 + yoe // 4 - yoe // 100 + doy - 719468  # since 1970-01-01
    valid = (mo >= 1) & (mo <= 12) & (dd >= 1) & (dd <= 31)
    return np.where(valid, days * 86400.0 + tod, dd * 86400.0 + tod)


def _fit_run(xs, ys, block_s):
    """Straight line through (device time, arrival) corrected to the lower envelope. Returns the
    mapped times (s, relative) and the raw block minima of the residual (for step detection)."""
    c1, c0 = np.polyfit(xs, ys, 1)
    res = ys - (c0 + c1 * xs)
    blk = np.floor((xs - xs[0]) / block_s).astype(np.int64)
    bx, br, bstart = [], [], []
    for b in np.unique(blk):
        m = np.where(blk == b)[0]
        j = m[np.argmin(res[m])]
        bx.append(xs[j]); br.append(res[j]); bstart.append(m[0])
    br = np.array(br)
    sm = np.array([np.median(br[max(0, k - 2):k + 3]) for k in range(len(br))]) if len(br) >= 5 else br
    return c0 + c1 * xs + np.interp(xs, bx, sm), br, np.array(bstart)


def clock_map(x, arrival_ns, gap_s=1.0, block_s=30.0, period_s=None, info=None):
    """Map device time x (s) to phone time (ns) per contiguous run. Returns (t_ns, run_id).

    Runs break at arrival gaps, at backward or forward jumps of x, and, when period_s is given
    (BLE, where x counts received samples), where the arrival envelope steps up by more than
    0.6 periods and stays there: lost samples make every later x too early by one period each.
    Finally no time may be later than its own arrival, since a sample can't arrive before it is
    taken. (There is no lower bound: a Bluetooth stall can legitimately delay a read by more than
    a second.)"""
    x = np.asarray(x, float)
    a = np.asarray(arrival_ns, np.int64)
    n = len(x)
    t = a.copy()
    run = np.zeros(n, np.int64)
    if n == 0:
        return t, run
    brk = np.where((np.diff(a) > gap_s * 1e9) | (np.diff(x) < 0) | (np.diff(x) > gap_s))[0] + 1
    queue = list(zip(np.concatenate([[0], brk]), np.concatenate([brk, [n]])))
    runs, steps = [], 0
    while queue:
        i0, i1 = queue.pop(0)
        if i1 - i0 < 50:
            runs.append((i0, i1, None))
            continue
        xs = x[i0:i1] - x[i0]
        ys = (a[i0:i1] - a[i0]) / 1e9
        tt, br, bstart = _fit_run(xs, ys, block_s)
        if period_s and len(br) >= 3:
            d = np.diff(br)
            # a persistent rise: this block and the next both sit above the previous minimum
            up = np.where((d[:-1] > 0.6 * period_s) & (br[2:] - br[:-2] > 0.6 * period_s))[0]
            if len(up) and bstart[up[0] + 1] > 0:
                cut = i0 + int(bstart[up[0] + 1])
                queue[:0] = [(i0, cut), (cut, i1)]
                steps += 1
                continue
        runs.append((i0, i1, tt))
    for r, (i0, i1, tt) in enumerate(sorted(runs, key=lambda q: q[0])):
        run[i0:i1] = r
        if tt is not None:
            t[i0:i1] = a[i0] + np.round(tt * 1e9).astype(np.int64)
    t = np.minimum(t, a)
    if info is not None:
        info["envelope_steps"] = steps
    return t, run


def recover_lost_samples(arrival_ns, rate, block=50, gap_s=1.0):
    """For streams timed by counting samples (BLE): find how many samples were lost, and where.

    r_i = arrival_i − i/rate steps up by one period at each lost sample. Within a short block
    (default 50 samples, half a second at 100 Hz) the smallest latency is very stable, so the
    difference between consecutive blocks' minima is a whole number of lost periods plus a
    negligible crystal drift. Losses are placed at the start of the block that follows them,
    which costs at most one period per loss for the samples in between. Returns the corrected
    sample index and the number of samples judged lost (reconnection gaps aren't counted)."""
    a = (np.asarray(arrival_ns, np.int64) - int(arrival_ns[0])) / 1e9
    n = len(a)
    T = 1.0 / rate
    idx = np.arange(n, dtype=float)
    if n < 3 * block:
        return idx, 0
    r = a - idx * T
    nb = n // block
    bmin = r[:nb * block].reshape(nb, block).min(axis=1)
    if n > nb * block:
        bmin = np.append(bmin, r[nb * block:].min())
    starts = np.arange(len(bmin)) * block
    steps = np.round(np.diff(bmin) / T)
    gap_at = np.concatenate([[False], np.diff(a) > gap_s])
    for b in range(len(steps)):          # a reconnection gap isn't a loss
        if gap_at[starts[b]:starts[b + 1] + 1].any():
            steps[b] = 0
    steps = np.maximum(steps, 0)
    lost = np.zeros(n)
    lost[starts[1:]] = steps
    return idx + np.cumsum(lost), int(steps.sum())


def decode(arrival_ns, chunks, imu: dict):
    """→ (streams, stats). Streams: gyro (rad/s), accel (m/s²), mag (counts), imu_temp (°C),
    imu_volt (V, spp only). Each is {"t_ns", columns...} sorted by time."""
    cfg = imu.get("config") or {}
    rng_dps = float(cfg.get("gyro_range_dps", 2000.0))
    rng_g = float(cfg.get("accel_range_g", 16.0))
    rate = float(cfg.get("rate_hz", 100.0))
    variant = imu.get("variant")
    if variant == "spp":
        return _decode_spp(arrival_ns, chunks, rng_dps, rng_g, rate)
    if variant == "ble":
        return _decode_ble(arrival_ns, chunks, rng_dps, rng_g, rate)
    raise ValueError(f"unknown imu variant {variant!r}")


def _vec_stream(t, v, names=("x", "y", "z"), extra=None):
    o = np.argsort(t, kind="stable")
    out = {"t_ns": t[o], **{n: v[o, i] for i, n in enumerate(names)}}
    for k, col in (extra or {}).items():
        out[k] = col[o]
    return out


def _saturated(raw3):
    """1 where any gyro axis sits at a full-scale count (the rate may have been clipped)."""
    return (np.abs(raw3) >= 32767).any(axis=1).astype(np.float64)


def _decode_spp(arrival_ns, chunks, rng_dps, rng_g, rate):
    lens = np.array([len(c) for c in chunks], np.int64)
    buf = np.frombuffer(b"".join(chunks), np.uint8)
    ends = np.cumsum(lens)
    pos, typ, bad = _spp_packets(buf)
    arr = np.asarray(arrival_ns, np.int64)[np.searchsorted(ends, pos + 11 - 1, side="right")] if len(pos) else np.zeros(0, np.int64)
    stats = {"variant": "spp", "bytes": int(len(buf)), "packets": int(len(pos)),
             "unparsed_bytes": int(len(buf) - 11 * len(pos)), "bad_checksums": bad,
             "packet_counts": {f"0x{k:02x}": int((typ == k).sum()) for k in SPP_TYPES if (typ == k).any()}}
    # device time for every packet: from the latest 0x50 at or before it, else the gyro index
    tp = typ == 0x50
    gp = typ == 0x52
    if tp.any() and gp.sum() > 1.05 * tp.sum():
        # The device sends its clock less often than the gyro: date each gyro packet from the nearest
        # preceding clock packet plus its sample offset times the device's sample period.
        tsec = _spp_time_s(buf, pos[tp])
        gidx = np.cumsum(gp) - 1                    # gyro index at each packet (for gyro packets)
        anchor = np.cumsum(gp)[tp]                  # index of the gyro packet that follows each clock packet
        # the device's sample period, from clock packets that are close in both index and time
        da, dt = np.diff(anchor), np.diff(tsec)
        ok = (da > 0) & (dt > 0) & (dt < 2.0 * da / rate)
        period = float(np.median(dt[ok] / da[ok])) if ok.any() else 1.0 / rate
        x = np.full(len(pos), np.nan)
        gi = gidx[gp]
        # each gyro sample: its nearest preceding clock packet plus whole sample periods (never
        # across a gap, where the next clock packet may be many seconds later)
        p = np.clip(np.searchsorted(anchor, gi, side="right") - 1, 0, len(anchor) - 1)
        x[gp] = tsec[p] + (gi - anchor[p]) * period
        # other packets share the device time of the gyro packet in their cycle
        lastg = np.maximum.accumulate(np.where(gp, np.arange(len(pos)), -1))
        other = ~gp & ~tp & (lastg >= 0)
        x[other] = x[lastg[other]]
        stats["time_base"] = "device_clock_interpolated"
        stats["gyro_per_clock_packet"] = float(gp.sum() / tp.sum())
    elif tp.any():
        tsec = _spp_time_s(buf, pos[tp])
        last = np.maximum.accumulate(np.where(tp, np.arange(len(pos)), -1))
        has = last >= 0
        x = np.full(len(pos), np.nan)
        x[has] = tsec[np.searchsorted(np.where(tp)[0], last[has])]
        stats["time_base"] = "device_clock"
    else:
        x = np.cumsum(typ == 0x52) / rate
        stats["time_base"] = "gyro_index"
    use = np.isfinite(x) & ~tp
    t_ns = np.zeros(len(pos), np.int64)
    run = np.zeros(len(pos), np.int64)
    # one fit per run using the gyro packets, applied to every packet type at the same device time
    gm = use & (typ == 0x52)
    if gm.sum():
        tg, rg = clock_map(x[gm], arr[gm])
        t_ns[gm], run[gm] = tg, rg
        other = np.where(use & ~gm)[0]
        if len(other):
            # anchor each other packet to the nearest preceding gyro packet (same cycle, same
            # device time), so device-clock resets between runs can't scramble the mapping
            gi = np.where(gm)[0]
            k = gi[np.clip(np.searchsorted(gi, other) - 1, 0, len(gi) - 1)]
            t_ns[other] = t_ns[k] + np.round((x[other] - x[k]) * 1e9).astype(np.int64)
            run[other] = run[k]
    stats["runs"] = int(run[gm].max() + 1) if gm.any() else 0
    out = {}
    for ptype, name in ((0x52, "gyro"), (0x51, "accel"), (0x54, "mag")):
        m = use & (typ == ptype)
        if not m.any():
            continue
        raw = _i16(buf, pos[m] + 2, 4)
        if ptype == 0x52:
            v = np.radians(raw[:, :3] / 32768.0 * rng_dps)
            sat = _saturated(raw[:, :3])
            stats["gyro_saturated_samples"] = int(sat.sum())
            out["gyro"] = _vec_stream(t_ns[m], v, extra={"sat": sat})
            out["imu_volt"] = _vec_stream(t_ns[m], raw[:, 3:4] / 100.0, ("volt",))
        elif ptype == 0x51:
            out["accel"] = _vec_stream(t_ns[m], raw[:, :3] / 32768.0 * rng_g * G0)
            out["imu_temp"] = _vec_stream(t_ns[m], raw[:, 3:4] / 100.0, ("temp_c",))
        else:
            out["mag"] = _vec_stream(t_ns[m], raw[:, :3].astype(float))
    return out, stats


def _decode_ble(arrival_ns, chunks, rng_dps, rng_g, rate):
    arrival_ns = np.asarray(arrival_ns, np.int64)
    d_pos, d_arr, r_pos, r_arr = [], [], [], []
    bufs, off, skipped = [], 0, 0
    for ci, c in enumerate(chunks):
        i = 0
        while i + BLE_LEN <= len(c):
            if c[i] == 0x55 and c[i + 1] == 0x61:
                d_pos.append(off + i); d_arr.append(arrival_ns[ci]); i += BLE_LEN
            elif c[i] == 0x55 and c[i + 1] == 0x71:
                r_pos.append(off + i); r_arr.append(arrival_ns[ci]); i += BLE_LEN
            else:
                i += 1; skipped += 1
        skipped += len(c) - i
        bufs.append(c)
        off += len(c)
    buf = np.frombuffer(b"".join(bufs), np.uint8)
    d_pos, r_pos = np.array(d_pos, np.int64), np.array(r_pos, np.int64)
    d_arr, r_arr = np.array(d_arr, np.int64), np.array(r_arr, np.int64)
    stats = {"variant": "ble", "bytes": int(len(buf)), "packets": int(len(d_pos) + len(r_pos)),
             "unparsed_bytes": int(skipped), "bad_checksums": 0,
             "packet_counts": {"0x61": int(len(d_pos)), "0x71": int(len(r_pos))}, "time_base": "sample_index"}
    out = {}
    if len(d_pos):
        idx, n_lost = recover_lost_samples(d_arr, rate)
        x = idx / rate
        info = {}
        t, run = clock_map(x, d_arr, period_s=1.0 / rate, info=info)
        stats["samples_lost_detected"] = n_lost
        stats["runs"] = int(run.max() + 1)
        stats["envelope_steps"] = info["envelope_steps"]
        # received against expected samples, per run, from the arrival span
        exp = sum(max(1.0, (d_arr[run == r][-1] - d_arr[run == r][0]) / 1e9 * rate + 1) for r in np.unique(run))
        stats["samples_expected"] = float(exp)
        stats["samples_received"] = int(len(d_pos))
        stats["loss_estimate"] = float(max(0.0, 1 - len(d_pos) / exp))
        raw = _i16(buf, d_pos + 2, 9)
        out["accel"] = _vec_stream(t, raw[:, 0:3] / 32768.0 * rng_g * G0)
        sat = _saturated(raw[:, 3:6])
        stats["gyro_saturated_samples"] = int(sat.sum())
        out["gyro"] = _vec_stream(t, np.radians(raw[:, 3:6] / 32768.0 * rng_dps), extra={"sat": sat})
        lat = int(np.median(d_arr - t))  # typical link latency, for the polled registers
    else:
        stats["runs"] = 0
        lat = 0
    if len(r_pos):
        raw = _i16(buf, r_pos + 2, 9)
        m = raw[:, 0] == REG_MAG
        if m.any():
            t = r_arr[m] - lat
            out["mag"] = _vec_stream(t, raw[m, 1:4].astype(float))
            out["imu_temp"] = _vec_stream(t, raw[m, 7:8] / 100.0, ("temp_c",))
    return out, stats
