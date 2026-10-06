# SPDX-License-Identifier: AGPL-3.0-or-later
"""Single-session analysis. Produces a JSON-serialisable result dict."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import numpy as np

from . import __version__, calib, drift, fit, models, slip
from .attitude import epoch_of, estimate_forward_axis, mount_epochs
from .format import read_session
from .segments import Thresholds, find_segments, make_bins, InvalidGnssData, gnss_kinematics
from .maneuvers import maneuver_mask
from .policy import POLICY_VERSION, heading_diversity, verified_config, scientific_exclusions
from .runtime import numerical_environment


def environment() -> dict:
    """What produced a result: the exact code and numerical libraries, so it can be reproduced."""
    # Build/campaign runners may supply VCS provenance explicitly. Analysis itself performs
    # no git operations; research manifests additionally hash the scientific source files.
    commit = os.environ.get("LLL_GIT_COMMIT") or None
    return {**numerical_environment(), "git_commit": commit}


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


# Provisional until real units have been measured (docs/BENCH.md).
QUALIFIED_ADEV300_DPH, USABLE_ADEV300_DPH = 3.0, 6.0  # Allan deviation at 300 s, worst axis
QUALIFIED_H_SD_DPH, USABLE_H_SD_DPH = 2.0, 4.0        # repeatability of the horizontal ground rate


def unit_quality(res: dict, m: dict) -> dict:
    """A quality tier for the IMU unit from this session's stationary data.

    The criteria are about the instrument, never about which model wins:
    - Allan deviation at 300 s on the worst axis, from a still run (drift or bench) long enough to
      have that averaging time;
    - repeatability of the horizontal ground rate: the scatter between pairs of the reversal test
      when there is one, else the palindrome calibration's horizontal σ.
    Collation applies to each session the latest tier measured at or before it."""
    a300 = [max(d["adev_at_dph"]["300"]) for d in (res.get("drift") or {}).values()
            if d and d.get("adev_at_dph", {}).get("300")]
    rv = res.get("reversal")
    if rv:
        h, h_src = rv["h_sd_dph"], "reversal test"
    else:
        hsd = [c["earth_h_sd_dph"] for c in (res.get("calibration") or {}).values()]
        h, h_src = (min(hsd), "palindrome calibration") if hsd else (None, None)
    a = max(a300) if a300 else None
    if a is None and h is None:
        tier = "unknown"
    elif a is not None and a <= QUALIFIED_ADEV300_DPH and h is not None and h <= QUALIFIED_H_SD_DPH:
        tier = "qualified"
    elif a is not None and h is not None and a <= USABLE_ADEV300_DPH and h <= USABLE_H_SD_DPH:
        tier = "usable"
    elif (a is not None and a > USABLE_ADEV300_DPH) or (h is not None and h > USABLE_H_SD_DPH):
        tier = "exploratory"
    elif a is None or h is None:
        tier = "incomplete"
    else:
        tier = "exploratory"
    return {"unit_id": (m.get("imu") or {}).get("unit_id"), "variant": (m.get("imu") or {}).get("variant"),
            "adev_300s_dph": a, "horizontal_repeatability_dph": h, "horizontal_repeatability_from": h_src,
            "tier": tier, "provisional": True, "bench_certificate": False,
            "criteria": {"qualified": f"Allan dev. at 300 s ≤ {QUALIFIED_ADEV300_DPH} °/h and horizontal repeatability ≤ {QUALIFIED_H_SD_DPH} °/h",
                         "usable": f"both measured: ≤ {USABLE_ADEV300_DPH} °/h and ≤ {USABLE_H_SD_DPH} °/h"}}


def analyze(path, th: Thresholds | None = None, *, fit_options=None, diagnostics_directory=None) -> dict:
    if diagnostics_directory is None:
        return _analyze(path,th,fit_options=fit_options)
    import json
    from pathlib import Path
    import shutil
    output = Path(diagnostics_directory)
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(path,output/'session.zip')
    try:
        result = _analyze(path,th,fit_options=fit_options,diagnostics_directory=output)
        (output/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        return result
    except Exception as exc:
        (output/'failure.json').write_text(json.dumps({'error':str(exc),'type':type(exc).__name__})+'\n')
        raise


def _analyze(path, th: Thresholds | None = None, *, fit_options=None, diagnostics_directory=None) -> dict:
    th = th or Thresholds()
    fit_options=dict(fit_options or {})
    reference_method = fit_options.get('forward_reference', 'legacy')
    if reference_method not in ('legacy', 'matched'):
        raise ValueError('invalid forward reference method')
    if reference_method == 'matched' and (not fit_options.get('research_candidate') or not fit_options.get('forward_uncertainty')):
        raise ValueError('matched forward reference requires research candidate and measured forward uncertainty')
    ambiguity_mode=fit_options.pop('magnetic_ambiguity','exclude')
    if ambiguity_mode not in ('exclude','model_and_compare'): raise ValueError('invalid magnetic ambiguity mode')
    if ambiguity_mode=='model_and_compare':
        if any(k in fit_options for k in ('mount_yaw_model','mount_yaw_segments')):
            raise ValueError('analyzer mount yaw boundaries must come from the watchdog')
        if fit_options.get('design_mode')!='envelope' or fit_options.get('pairwise_method')!='profile':
            raise ValueError('magnetic ambiguity comparison requires envelope and pair profiles')
        if any(fit_options.get(k) is not None for k in ('decision_policy','pairwise_decision_policy','decision_thresholds')):
            raise ValueError('magnetic two-path candidate has no empirical dual-path calibration')
    exclusion_options=dict(fit_options)
    sess = read_session(path)
    m = sess.manifest
    if 'domain_source' in fit_options:
        raise ValueError('analyzer acquisition source must come from the recording manifest')
    from .flight_domain import acquisition_source
    fit_options['domain_source'] = acquisition_source(m)
    if m.get('trajectory_replay') and any((fit_options or {}).get(key) is not None
            for key in ('decision_policy','pairwise_decision_policy','decision_thresholds')):
        raise ValueError('observed trajectory replay cannot apply empirical thresholds before domain enforcement')
    flags = list(m.get("quality", {}).get("flags", []))
    res = {
        "analysis_version": __version__,
        "policy_version": POLICY_VERSION,
        "environment": environment(),
        "input_sha256": sess.sha256,
        "session_id": m.get("session_id"),
        "created_utc": m.get("created_utc"),
        "kind": m.get("kind", "flight"),
        "flight": m.get("flight", {}),
        "mount": m.get("mount", {}),
        "device": m.get("device", {}),
        "imu": {**(m.get("imu") or {}), "decode": sess.imu_stats},
        "flags": flags,
        "validation_status": "provisional",
        "provenance_status": "unverified",
    }
    st = sess.imu_stats
    # Require explicit complete verification within every recording phase/connection.
    verified = [t for t, k, d in sess.events if k == "imu_config" and verified_config(d, m.get("imu") or {})]
    for ph in m.get("phases", []):
        if not any(ph["start_ns"] <= t <= ph["end_ns"] for t in verified):
            flags.append("imu_config_unverified")
            break
    for t, kind, _ in sess.events:
        if kind == "imu_connect":
            ph = next((p for p in m.get("phases", []) if p["start_ns"] <= t <= p["end_ns"]), None)
            if ph and not any(t <= v <= min(t + 30e9, ph["end_ns"]) for v in verified):
                flags.append("imu_config_unverified")
                break
    flags[:] = list(dict.fromkeys(flags))
    if "gyro" not in sess.streams or "accel" not in sess.streams:
        flags.append("no_imu_data")
        return _clean(res)
    if st.get("bytes") and st.get("unparsed_bytes", 0) > 1e-3 * st["bytes"]:
        flags.append("imu_corrupt_bytes")
    if st.get("gyro_range_reported_dps") is not None and st["gyro_range_reported_dps"] != st.get("gyro_range_intended_dps"):
        flags.append("imu_range_differs_from_intended")      # decoded with the range the device reported
    if not st.get("gyro_range_readbacks_consistent", True):
        flags.append("imu_range_inconsistent")              # readbacks disagree: decoded with the intended range
    if st.get("accel_range_reported_g") is not None and st["accel_range_reported_g"] != st.get("accel_range_intended_g"):
        flags.append("imu_accel_range_differs_from_intended")
    if not st.get("accel_range_readbacks_consistent", True):
        flags.append("imu_accel_range_inconsistent")
    # Each phase is one connection. A gap inside a phase means the link dropped.
    gaps = 0
    for ph in m.get("phases", []):
        g = sess.slice("gyro", ph["start_ns"], ph["end_ns"])
        if g is not None and len(g["t_ns"]) > 1:
            gaps += int((np.diff(g["t_ns"]) > 1e9).sum())
    res["imu"]["gaps_in_phases"] = gaps
    if gaps:
        flags.append("imu_link_gaps")

    # calibration, ground Earth-rate measurement, drift
    cal_pre, cal_post = calib.calibrate(sess, "cal_pre"), calib.calibrate(sess, "cal_post")
    res["calibration"] = {}
    for name, c in (("pre", cal_pre), ("post", cal_post)):
        if c is None:
            flags.append(f"no_cal_{name}")
            continue
        rec = {k: v for k, v in c.items() if k not in ("bias", "bias_sem")}
        rec["bias_dph"] = (c["bias"] * calib.RAD2DPH).tolist()
        rec["bias_sem_dph"] = (c["bias_sem"] * calib.RAD2DPH).tolist()
        loc = (m.get("privacy", {}).get("cal_locations") or {}).get("cal_" + name) or {}
        lat_cal = loc.get("lat_deg") if 0 <= loc.get("age_s", float("inf")) <= 900 else None
        # Schema 2 stored one latitude without freshness or per-calibration attribution.
        rec["latitude_status"] = "fresh" if lat_cal is not None else "unknown"
        if lat_cal is not None:
            rec["lat_deg"] = lat_cal
            rec["predicted"] = calib.ground_model_predictions(lat_cal)
        res["calibration"][name] = rec
    res["drift"] = {n: drift.drift_run(sess, n) for n in ("drift_pre", "drift_post", "bench")}
    res["reversal"] = calib.reversal_test(sess)
    res["unit_quality"] = unit_quality(res, m)
    bias_fn, prior_sigma, bias_mode = drift.bias_model(cal_pre, cal_post, vre_dph=th.vre_budget_dph,
                                                       gsens_dph=th.gsens_budget_dph)
    res["bias_model"] = {"mode": bias_mode, "prior_sigma_dph": (prior_sigma * calib.RAD2DPH).tolist()}
    if cal_pre and cal_post:
        res["bias_model"]["pre_post_change_dph"] = ((cal_post["bias"] - cal_pre["bias"]) * calib.RAD2DPH).tolist()

    flight = sess.phase("flight")
    if flight is None:
        flags.append("no_flight_phase")
        return _clean(res)
    clock = m.get("clock") or {}
    if isinstance(clock.get("utc_ms"), (int, float)) and isinstance(clock.get("elapsed_ns"), (int, float)):
        utc = clock["utc_ms"] / 1000 + (flight["start_ns"] - clock["elapsed_ns"]) / 1e9
        res["flight_started_utc"] = datetime.fromtimestamp(utc, timezone.utc).isoformat()
    # Mount epochs: deliberate turns of the IMU (and bumps) during the flight. The gyro measures each
    # turn, so later epochs are mapped back into the first epoch's frame exactly.
    gs = sess.slice(sess.gyro_stream(), flight["start_ns"], flight["end_ns"])
    gt = gs["t_ns"] / 1e9
    Gc = np.column_stack([gs["x"], gs["y"], gs["z"]]) - bias_fn(gt)
    ev = [(t / 1e9, kind) for t, kind, _ in sess.events if kind in ("index_turn", "placement_shift")
          and flight["start_ns"] <= t <= flight["end_ns"]]
    rate = (m.get("imu", {}).get("config") or {}).get("rate_hz")
    motion_gn = sess.slice('gnss', flight['start_ns'], flight['end_ns'])
    try:
        motion = maneuver_mask(None if motion_gn is None else gnss_kinematics(motion_gn, th),
                               max_turn_dps=th.max_turn_dps, max_vz_mps=th.max_vz_mps,
                               min_speed_mps=th.min_speed_mps,max_h_acc_m=th.max_h_acc_m)
    except InvalidGnssData:
        motion = maneuver_mask(None)
    epochs, exclude = mount_epochs(gt, Gc, ev, sat=gs.get("sat"), expected_period=1 / rate if rate else None,
                                  aircraft_motion=motion)
    R0 = np.array([e['R0'] for e in epochs])
    if diagnostics_directory is not None:
        np.save(diagnostics_directory/'mount-matrices.npy',R0,allow_pickle=False)
        np.savez_compressed(diagnostics_directory/'turn-input.npz',t=gt,calibrated_gyro=Gc)
    res['aircraft_motion_mask'] = motion
    if any(e.get("orientation_unresolved") for e in epochs):
        flags.append("orientation_unresolved")
    res["mount_epochs"] = [{"t0_s": e["t0_s"], "t1_s": e["t1_s"], "turn": e["turn"],
                            "orientation_unresolved": bool(e.get("orientation_unresolved"))} for e in epochs]
    if any(e["turn"] and e["turn"].get("unresolved_gap") for e in epochs):
        flags.append("imu_turn_gap")
    if any(e["turn"] and e["turn"]["kind"] == "index_turn" for e in epochs):
        flags.append("imu_turned_in_flight")
    if any(e["turn"] and e["turn"].get("saturated_samples") for e in epochs):
        flags.append("imu_turn_saturated")     # a hand turn exceeded the gyro's full scale; its angle is unreliable

    try:
        segs, kin = find_segments(sess, flight, th, exclude=exclude)
    except InvalidGnssData as exc:
        flags.append("gnss_invalid_data")
        res["invalid_data"] = str(exc)
        return _clean(res)
    res["segments"] = [{"t0_s": a, "t1_s": b, "minutes": (b - a) / 60} for a, b in segs]
    if kin is not None:
        step = max(1, len(kin["t"]) // 2000)
        res["track"] = {k: np.asarray(kin[k][::step]).tolist() for k in ("t", "lat", "lon", "h", "speed", "vz")}
        res["track"]["lat"] = np.degrees(res["track"]["lat"]).tolist()
        res["track"]["lon"] = np.degrees(res["track"]["lon"]).tolist()
    if not segs:
        flags.append("no_stable_cruise")
        return _clean(res)
    bins = make_bins(sess, segs, kin, th)
    if bins is None:
        flags.append("no_bins")
        return _clean(res)
    bins["epoch"] = epoch_of(bins["t"], epochs)
    if diagnostics_directory is not None:
        np.savez_compressed(diagnostics_directory/'pre-selection-bins.npz',**bins)
    keep = bins["epoch"] >= 0
    # After a turn whose rate was clipped, the IMU's new orientation is unknown (the accelerometer
    # can't see a turn about the vertical), so later epochs can't be mapped and are left out.
    sat_epoch = next((i for i, e in enumerate(epochs) if e["turn"] and e["turn"].get("saturated_samples")), None)
    if sat_epoch is not None:
        keep &= bins["epoch"] < sat_epoch
        res["excluded_after_saturated_turn_s"] = float(epochs[sat_epoch]["t0_s"])
    unresolved = next((i for i, e in enumerate(epochs) if e.get("orientation_unresolved")), None)
    if unresolved is not None:
        keep &= bins["epoch"] < unresolved
        res["excluded_after_unresolved_orientation_s"] = float(epochs[unresolved]["t0_s"])
    if not keep.any():
        flags.append("no_bins")
        return _clean(res)
    bins = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v) for k, v in bins.items()}
    if diagnostics_directory is not None:
        np.savez_compressed(diagnostics_directory/'orientation-qualified-bins.npz',**bins)

    # magnetometer watchdog for slow yaw slip in the mount; segments where the WMM version sees slip
    # are left out of the gyro fit (the no-declination version is a reported cross-check). The choice
    # uses only magnetometer and GPS data, never the gyro. A globe-based selection rule can still
    # shift k if what it drops correlates with the model terms, so the fit is repeated without it.
    bins_all = bins
    hi = next((c.get("mag_hard_iron_counts") for c in (cal_pre, cal_post) if c and c.get("mag_hard_iron_counts")), None)
    gn = sess.streams.get("gnss")
    year = 1970 + float(np.median(gn["utc_ms"])) / 1000 / 86400 / 365.2425 if gn is not None and len(gn["utc_ms"]) else 2026.0
    res["slip"] = slip.watchdog(bins, hi, year, th.max_slip_dph)
    res["slip"]["pre_exclusion_geometry"] = {"n_bins": len(bins["t"]), "heading_diversity": heading_diversity(bins)}
    if res["slip"].get("available"):
        if res["slip"]["exclude_segments"]:
            flags.append("mount_slip_detected")
            flags.append("magnetic_yaw_change_ambiguous")
            keep = ~np.isin(bins["seg"], res["slip"]["exclude_segments"])
            res["slip"]["excluded_bins"] = int((~keep).sum())
            res["slip"]["retained_bins"] = int(keep.sum())
            if ambiguity_mode=='exclude':
                bins = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v) for k, v in bins.items()}
                if not len(bins["t"]):
                    flags.append("no_bins")
                    return _clean(res)
            else:
                res['slip'].update(would_exclude_bins=int((~keep).sum()),excluded_bins=0,retained_bins=len(bins['t']),
                    selection_policy='experimental retained mount-yaw fit and original exclusion-path agreement')
    else:
        flags.append("slip_watchdog_unavailable")
    if ambiguity_mode=='model_and_compare':
        from .mount_yaw import boundary_keep
        keep=boundary_keep(bins,res['slip'].get('exclude_segments',[]))
        res['slip']['ambiguous_boundary_bins']=int((~keep).sum())
        bins={k:(v[keep] if isinstance(v,np.ndarray) and len(v)==len(keep) else v) for k,v in bins.items()}
        res['slip']['retained_bins']=len(bins['t'])
        if not len(bins['t']):
            flags.append('no_bins'); return _clean(res)
        fit_options.update(mount_yaw_model='piecewise',mount_yaw_segments=res['slip'].get('exclude_segments',[]))

    # forward axis from banked turns over the whole flight, in the first epoch's frame
    ge = epoch_of(gt, epochs)
    ok = ge >= 0
    if unresolved is not None:
        ok &= ge < unresolved
    G0 = np.einsum("nij,nj->ni", R0[ge[ok]], Gc[ok])
    up_ref = np.median(np.einsum("nij,nj->ni", R0[bins["epoch"]], bins["up"]), axis=0)
    reference_estimator = estimate_forward_axis
    if reference_method == 'matched':
        from .forward_reference import estimate_forward_axis as reference_estimator
    fwd0, fq = reference_estimator(gt[ok], G0, kin["t"], kin["speed"], np.degrees(kin["psi"]), up_ref)
    fit_options = dict(fit_options or {})
    injected_angle = fit_options.pop("research_forward_offset_deg", 0.)
    if injected_angle and fwd0 is not None:
        from .attitude import expm_so3, unit
        fwd0 = expm_so3(unit(up_ref)*np.radians(injected_angle)) @ fwd0
        fq["research_injected_angle_deg"] = injected_angle
    res["forward_axis"] = {"axis_b": None if fwd0 is None else fwd0.tolist(), **fq}
    vertical_only = fwd0 is None
    # each bin's forward axis in its own epoch's frame: v_epoch = R0ᵀ v_0
    fwd = None if fwd0 is None else np.einsum("nji,j->ni", R0[bins["epoch"]], fwd0)
    if fit_options.get("forward_uncertainty"):
        from .attitude import unit
        fit_options["forward_sigma_rad"] = fq.get("angle_sigma_rad")
        tangent0 = None if fwd0 is None else np.cross(unit(up_ref), fwd0)
        fit_options["forward_tangent"] = None if tangent0 is None else np.einsum("nji,j->ni", R0[bins["epoch"]], tangent0)
    if vertical_only:
        flags.append("no_heading_reference_vertical_only")

    # Temperature: if the IMU is noticeably warmer or colder in cruise than during calibration,
    # fit a per-axis bias-vs-temperature coefficient (prior from drift runs if available).
    temp_ref, temp_prior, temp_mean = None, None, None
    bat = sess.streams.get("imu_temp")
    cal_temps = []
    for ph in sess.phases("cal_"):
        b = sess.slice("imu_temp", ph["start_ns"], ph["end_ns"])
        if b is not None and np.isfinite(b["temp_c"]).any():
            cal_temps.append(np.nanmean(b["temp_c"]))
    if bat is not None and cal_temps and np.isfinite(bins["temp"]).all():
        t_ref = float(np.mean(cal_temps))
        # 90th percentile, not max: one glitchy temperature reading shouldn't switch the term on
        if np.percentile(np.abs(bins["temp"] - t_ref), 90) >= th.min_temp_delta_c:
            temp_ref = t_ref
            # only from drift runs where temperature wasn't confounded with elapsed time
            measured = [d["bias_temp_coef_dph_per_c"] for d in res["drift"].values()
                        if d and d.get("bias_temp_coef_dph_per_c") and not d.get("bias_temp_confounded")]
            if measured:
                # a drift run measured this unit's coefficient: apply it, and fit only the residual
                c = np.mean(measured, axis=0)
                temp_mean = c / calib.RAD2DPH
                temp_prior = np.maximum(0.3 * np.abs(c), 0.2) / calib.RAD2DPH
            else:
                temp_prior = th.temp_prior_dph_per_c / calib.RAD2DPH
            flags.append("temperature_term")
    res["temperature"] = {"cal_mean_c": float(np.mean(cal_temps)) if cal_temps else None,
                          "cruise_min_c": float(np.nanmin(bins["temp"])) if np.isfinite(bins["temp"]).any() else None,
                          "cruise_max_c": float(np.nanmax(bins["temp"])) if np.isfinite(bins["temp"]).any() else None,
                          "term_used": temp_ref is not None,
                          "coefficient_source": None if temp_ref is None else ("drift_run" if temp_mean is not None else "free_fit"),
                          "prior_dph_per_c": None if temp_prior is None else (np.asarray(temp_prior) * calib.RAD2DPH).tolist()}

    if diagnostics_directory is not None:
        arrays = {**bins,'mount_matrices':R0,'up_reference':up_ref}
        if fwd is not None: arrays['forward'] = fwd
        np.savez_compressed(diagnostics_directory/'fit-input.npz',**arrays)
    f = fit.fit(bins, fwd, bias_fn, prior_sigma, vertical_only=vertical_only, temp_ref=temp_ref, temp_prior=temp_prior,
                temp_mean=temp_mean, **(fit_options or {}))
    if diagnostics_directory is not None and '_rows' in f:
        y,J,idx,_,z = f['_rows']
        np.savez_compressed(diagnostics_directory/'fit-rows.npz',y=y,jacobian=J,bin_index=idx,parameters=z)
        if f.get('wind_tas') is not None:
            # Speed constraints participate in inference but are distinct from gyro rows.
            import json
            (diagnostics_directory/'wind-tas.json').write_text(json.dumps(f['wind_tas'],indent=2,allow_nan=False)+'\n')
        if f.get('mount_yaw') is not None:
            import json
            (diagnostics_directory/'mount-yaw.json').write_text(json.dumps(f['mount_yaw'],indent=2,allow_nan=False)+'\n')
    if not f["convergence"]["converged"]:
        flags.append("inference_nonconvergence")
    if temp_ref is not None and temp_mean is None:
        # A freely fitted temperature term can absorb signal. Report what k would be without it,
        # and flag the session when that moves any k by more than 1σ.
        f0 = fit.fit(bins, fwd, bias_fn, prior_sigma, vertical_only=vertical_only, **{**fit_options, "n_boot": 0})
        if not f0["convergence"]["converged"]:
            flags.append("inference_nonconvergence")
        shift = {n: (f["k"][n] - f0["k"][n]) / f["k_sd"][n] for n in fit.TERM_NAMES}
        res["temperature"]["k_without_term"] = f0["k"]
        res["temperature"]["k_shift_sigma"] = shift
        if max(abs(v) for v in shift.values()) > 1.0:
            flags.append("temperature_sensitive")
    if not f["identifiability"]["identified"]:
        flags.append("k_not_identified")       # curvature indistinguishable from bias on this flight
    ibt = f["identifiability"]["identified_by_term"]
    if not ibt["k_rot_sphere"]:
        flags.append("k_rot_not_identified")
    if not ibt["k_disc"]:
        flags.append("k_disc_not_identified")  # e.g. no change in east velocity along the route
    if f["prior_sensitivity"]["prior_dominated"]:
        flags.append("prior_dominated")        # a nuisance prior (bias, crab, temperature), not the data, is setting k
    cs = f.get("crab_sensitivity")
    if cs and cs["crab_sensitive"]:
        # k moves by more than 1σ across crab priors of 3–15°. Informational only: the sweep shows how
        # much the error bars lean on the prior, not crab bias (EVIDENCE §11), so it isn't a gate.
        flags.append("crab_sensitive")
    if cs and cs["course_groups"] == 1:
        flags.append("single_heading")
    if bins_all is not bins and ambiguity_mode=='exclude':
        fa = None if fwd0 is None else np.einsum("nji,j->ni", R0[bins_all["epoch"]], fwd0)
        all_options = dict(fit_options)
        if all_options.get("forward_uncertainty") and tangent0 is not None:
            all_options["forward_tangent"] = np.einsum("nji,j->ni", R0[bins_all["epoch"]], tangent0)
        fw = fit.fit(bins_all, fa, bias_fn, prior_sigma, vertical_only=vertical_only, temp_ref=temp_ref,
                     temp_prior=temp_prior, temp_mean=temp_mean, **all_options)
        if not fw["convergence"]["converged"]:
            flags.append("inference_nonconvergence")
        moved = {n: (f["k"][n] - fw["k"][n]) / f["k_sd"][n] for n in fit.TERM_NAMES}
        res["fit_no_wmm_exclusion"] = {"k": fw["k"], "k_sd": fw["k_sd"], "rejected": fw["rejected"],
                                       "k_shift_sigma": moved}
        if fw["rejected"] != f["rejected"] or max(abs(v) for v in moved.values()) > 1.0:
            flags.append("wmm_selection_sensitive")
    y, X, idx, cbns, theta = f["_rows"]
    res["fit"] = f
    if ambiguity_mode=='model_and_compare':
        from .mount_yaw import compare_paths
        control=None; control_error=None
        try:
            control=analyze(path,th,fit_options=exclusion_options,
                diagnostics_directory=diagnostics_directory/'excluded-path' if diagnostics_directory is not None else None)
        except (ValueError,np.linalg.LinAlgError) as exc:
            control_error=str(exc)
        # Re-run the original path, including its own preprocessing and selection sensitivity.
        baseline=(control or {}).get('fit') if res['slip'].get('available') else None
        f['magnetic_ambiguity_comparison']=compare_paths(f,baseline,flags,(control or {}).get('flags',[]))
        if control_error: f['magnetic_ambiguity_comparison']['excluded_path_error']=control_error
        res['magnetic_exclusion_path']={key:(control or {}).get(key) for key in ('fit','flags','slip','forward_axis','input_sha256')}
    res["eligibility_policy"] = f["eligibility_policy"]
    res["policy_version"] = f["eligibility_policy"]["version"]
    res["scientific_exclusions"] = scientific_exclusions(res)
    if "pairwise" in f:
        from .pairwise import flight_evidence, three_model_winner, shape_evidence
        options = fit_options or {}
        f["pairwise"] = flight_evidence(f, flags, policy=options.get("pairwise_decision_policy"),
                                       candidate_id=options.get("decision_candidate_id"), variant=options.get("decision_variant"))
        f["pairwise_three_model_winner"] = three_model_winner(f["pairwise"])
        f['shape_evidence'] = shape_evidence(f['pairwise'])
    res["fit"]["expected_k"] = models.EXPECTED_K
    res["accumulated"] = fit.accumulated(bins, cbns, y, idx, vertical_only)
    res["cruise_minutes"] = float(bins["dt"].sum() / 60)
    res["heading_diversity"] = heading_diversity(bins)
    return _clean(res)
