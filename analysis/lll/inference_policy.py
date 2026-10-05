# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned inference settings. Historical tuning is development evidence only."""
import hashlib
import json

INFERENCE_POLICY = {
    "version": "inference-2",
    "k_sys_floor": {"k_rot_sphere": 0.02, "k_curv": 0.0, "k_disc": 0.0},
    "floor_provenance": "Historical 30-seed hardware-fault study; development, not holdout coverage",
    "crab_knot_seconds": 300.0,
    "crab_rate_sigma_dph": 1.0,
    "variance_shrinkage_bins": 20.0,
    "sigma_floor_rad_s": 1e-9,
    "forward_hac_lags": 10,
    "bias_knot_seconds": 900.0,
    "bias_rw_sigma_dph_sqrth": 3.0,
    "bias_drift_provenance": "Unvalidated research random-walk scale; not fitted to the rejection fixture or hardware",
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def provenance(settings):
    return {"version": INFERENCE_POLICY["version"], "policy_hash": digest(INFERENCE_POLICY),
            "settings": settings, "configuration_hash": digest({"policy": INFERENCE_POLICY, "settings": settings})}
