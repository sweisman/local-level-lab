# SPDX-License-Identifier: AGPL-3.0-or-later
"""Experimental partial model evidence and pooling on pair-normalized observable coordinates."""
from collections import defaultdict
import json

import numpy as np
from scipy.stats import chi2, t as tdist

from . import models, __version__
from .inference_policy import digest
from .policy import MODEL_PAIRS, scientific_exclusions, decision_stratum, eligibility_policies
from .runtime import numerical_environment, numerical_environment_hash, check_environment

POOL_METHOD = "pair-normalized-reml-hk-1"
PROFILE_POOL_METHOD = 'pair-line-profile-reml-hk-1'


def pair_stratum(row, comparison, mode="flight"):
    entry = (row.get('pairwise') or row.get('pairwise_profile') or {}).get(comparison,{})
    if mode == 'flight' and entry.get('method') == 'pair-line-profile-1':
        return json.dumps([row.get('candidate_id'),row.get('variant'),comparison,entry['method']],separators=(',',':'))
    if mode == "flight": return decision_stratum(row)
    return json.dumps([row.get("candidate_id"), row.get("variant"), entry.get('method',POOL_METHOD), comparison,
                       row["pairwise"][comparison].get("n_units")], separators=(",", ":"))


def check_pairwise_policy(policy, mode):
    if policy.get("version") not in ("pairwise-empirical-1",'pairwise-empirical-2') or policy.get("mode") != mode:
        raise ValueError("pairwise policy requires calibration for this decision mode")
    methods=set(policy.get('statistic_methods',[]))
    allowed={'observable-coordinate-1','pair-line-profile-1'} if mode=='flight' else {POOL_METHOD,PROFILE_POOL_METHOD}
    if not methods <= allowed or (policy.get('version')=='pairwise-empirical-2' and not methods):
        raise ValueError('unknown or missing pairwise statistic method')
    if digest({k: v for k, v in policy.items() if k != "policy_hash"}) != policy.get("policy_hash"):
        raise ValueError("pairwise policy hash mismatch")
    if policy.get("eligibility_policies") != eligibility_policies():
        raise ValueError("pairwise eligibility policy mismatch")
    check_environment(policy.get("numerical_environment"))
    if policy.get("numerical_environment_hash") != numerical_environment_hash():
        raise ValueError("pairwise numerical environment hash mismatch")
    if policy.get("analysis_version") != __version__:
        raise ValueError("pairwise software version differs")
    if policy.get("implementation_hash") is not None:
        from .research_design import implementation_hash
        if policy["implementation_hash"] != implementation_hash():
            raise ValueError("pairwise implementation changed after calibration")


def decide(entry, comparison, thresholds=None, alpha=.0027):
    """Two endpoint tests; one rejected and the other retained is required for a preference."""
    a, b = MODEL_PAIRS[comparison]
    p = entry.get("p_diagnostic") or {}
    if not entry.get("eligible") or not entry.get("statistics"):
        rejected = {a: None, b: None}
    elif thresholds is not None:
        rejected = {model: entry["statistics"][model] > thresholds[model] for model in (a, b)}
    else:
        # Simultaneous diagnostic comparisons across the six pair/model endpoints.
        rejected = {model: p[model] < alpha/(2*len(MODEL_PAIRS)) for model in (a, b)}
    preferred = a if rejected[a] is False and rejected[b] is True else b if rejected[b] is False and rejected[a] is True else None
    entry.update(rejected_by_model=rejected, status="decision" if preferred else "abstain", preferred_model=preferred,
                 calibrated=thresholds is not None, applied_thresholds=thresholds)
    return entry


def three_model_winner(pairs):
    winners = [model for model in models.MODELS if all(
        pairs.get(name, {}).get("status") == "decision" and pairs[name].get("preferred_model") == model
        for name, endpoints in MODEL_PAIRS.items() if model in endpoints)]
    return winners[0] if len(winners) == 1 else None


def flight_evidence(fit, flags=(), policy=None, candidate_id=None, variant=None):
    if policy is not None: check_pairwise_policy(policy, "flight")
    pairs = {}
    constraints = np.asarray((fit.get("identifiability") or {}).get("estimable_combinations", []), float)
    covariance = np.asarray(fit.get("k_cov"), float)
    k = np.asarray([fit.get("k", {}).get(name, np.nan) for name in ("k_rot_sphere", "k_curv", "k_disc")])
    for name, (a, b) in MODEL_PAIRS.items():
        reasons = scientific_exclusions({"fit": fit, "flags": flags}, name)
        profile = (fit.get('pairwise_profile') or {}).get(name)
        if profile is not None:
            entry = {**profile,'exclusions':list(dict.fromkeys(reasons+profile['exclusions']))}
            thresholds = None
            if policy is not None:
                if profile['method'] not in policy.get('statistic_methods',[]):
                    raise ValueError('pairwise statistic method differs from calibrated policy')
                cell = pair_stratum({'candidate_id':candidate_id,'variant':variant,'pairwise':{name:entry}},name)
                thresholds = policy['thresholds'].get(cell,{}).get(name)
                if thresholds is None: entry['exclusions'].append('uncalibrated pairwise stratum')
                entry['decision_policy_hash'] = policy['policy_hash']
            entry['eligible'] = not entry['exclusions']
            pairs[name] = decide(entry,name,thresholds)
            continue
        entry = {"eligible": not reasons, "exclusions": reasons, "statistics": None,
                 'method':'observable-coordinate-1',
                 "coordinate": "first model=1, second model=0", "estimate": None, "sd": None}
        if policy is not None and policy.get('statistic_methods') and entry['method'] not in policy['statistic_methods']:
            raise ValueError('pairwise statistic method differs from calibrated policy')
        if fit.get("design_only"):
            entry["exclusions"].append("design-only evaluation")
        if (constraints.ndim == 2 and constraints.shape[1:] == (3,) and covariance.shape == (3, 3)
                and np.isfinite(constraints).all() and np.isfinite(covariance).all() and np.isfinite(k).all()):
            direction = np.asarray(models.EXPECTED_K[a])-np.asarray(models.EXPECTED_K[b])
            observable = constraints.T @ (constraints @ direction)
            separation = float(observable @ direction)
            if separation > 1e-20:
                coordinate = observable/separation
                estimate = float(coordinate @ (k-np.asarray(models.EXPECTED_K[b])))
                variance = float(coordinate @ covariance @ coordinate)
                if np.isfinite(variance) and variance > 0:
                    statistics = {a: (estimate-1.)**2/variance, b: estimate**2/variance}
                    entry.update(estimate=estimate, sd=float(np.sqrt(variance)), projection=coordinate.tolist(),
                                 statistics=statistics, p_diagnostic={model: float(chi2.sf(value, 1)) for model, value in statistics.items()})
        if entry["statistics"] is None: entry["exclusions"].append("observable pair coordinate unavailable")
        thresholds = None
        if policy is not None:
            cell = decision_stratum({"candidate_id": candidate_id, "variant": variant, "model_test_rank": fit.get("model_test_rank")})
            thresholds = policy["thresholds"].get(cell, {}).get(name)
            if thresholds is None: entry["exclusions"].append("uncalibrated pairwise stratum")
            entry["decision_policy_hash"] = policy["policy_hash"]
        entry["eligible"] = not entry["exclusions"]
        pairs[name] = decide(entry, name, thresholds)
    return pairs


def pool_evidence(items, candidate_id, variant, policy=None):
    """items: (unit ID, per-pair evidence); repetitions pool within units before pooling units."""
    from .collate import random_effects
    if policy is not None: check_pairwise_policy(policy, "pool")
    items=list(items)
    methods = {entry.get('method','observable-coordinate-1') for _, evidence in items
               for entry in evidence.values() if entry.get('eligible')}
    if len(methods)>1: raise ValueError('cannot pool incompatible pairwise coordinate methods')
    pool_method=PROFILE_POOL_METHOD if 'pair-line-profile-1' in methods else POOL_METHOD
    if policy is not None and pool_method==PROFILE_POOL_METHOD and pool_method not in policy.get('statistic_methods',[]):
        raise ValueError('pairwise pool method differs from calibrated policy')
    pairs = {}
    for name, (a, b) in MODEL_PAIRS.items():
        units = defaultdict(list)
        for unit, evidence in items:
            entry = evidence.get(name) or {}
            if unit and entry.get("eligible") and entry.get("sd", 0) is not None and entry.get("sd", 0) > 0:
                if np.isfinite(entry["estimate"]) and np.isfinite(entry["sd"]): units[str(unit)].append(entry)
        within = {unit: random_effects([e["estimate"] for e in entries], [e["sd"] for e in entries]) for unit, entries in units.items()}
        pooled = random_effects([entry["mu"] for entry in within.values()], [entry["se"] for entry in within.values()])
        entry = {"eligible": len(within) >= 3, "exclusions": [] if len(within) >= 3 else ["fewer than three informative units"],
                 "statistics": None, "n_units": len(within), "n_sessions": sum(map(len, units.values())),
                 "units": within, "method": pool_method, "estimate": None, "sd": None, "df": len(within)-1}
        if pooled and pooled["se"] > 0:
            statistics = {a: ((pooled["mu"]-1.)/pooled["se"])**2, b: (pooled["mu"]/pooled["se"])**2}
            entry.update(estimate=pooled["mu"], sd=pooled["se"], statistics=statistics, ci95=pooled["ci95"],
                         p_diagnostic={model: float(2*tdist.sf(np.sqrt(value), pooled["df"])) if pooled["df"] > 0 else None
                                       for model, value in statistics.items()})
        thresholds = None
        if policy is not None:
            cell = pair_stratum({"candidate_id": candidate_id, "variant": variant, "pairwise": {name: entry}}, name, "pool")
            thresholds = policy["thresholds"].get(cell, {}).get(name)
            if thresholds is None:
                entry["exclusions"].append("uncalibrated pairwise pool stratum")
                entry["eligible"] = False
            entry["decision_policy_hash"] = policy["policy_hash"]
        pairs[name] = decide(entry, name, thresholds)
    return {"status": "experimental", "method": POOL_METHOD, "candidate_id": candidate_id,
            "variant": variant, "pairwise": pairs, "three_model_winner": three_model_winner(pairs),
            "validated_for_primary_claims": False}
