# SPDX-License-Identifier: AGPL-3.0-or-later
"""Serializable simulation design and enforced independent campaign partitions."""
import inspect
import itertools
import json
from pathlib import Path
import numpy as np

from . import __version__
from .inference_policy import INFERENCE_POLICY, digest
from .policy import eligibility_policies
from .runtime import numerical_environment, numerical_environment_hash
from .synth import synthesize

PARTITIONS = {"development": (0, 1_000_000), "calibration": (1_000_000, 2_000_000),
              "validation": (2_000_000, 3_000_000)}
DESIGN_VERSION = "simulation-design-2"
STREAMS = ("geometry", "nuisance", "sensor", "bootstrap", "pool", "protocol", "missingness")
INTERACTIONS = ("crab_long_drift", "correlated_thermal", "forward_crab", "turn_dropout_drift")


def seed_range(partition, start=None, count=1):
    lo, hi = PARTITIONS[partition]
    start = lo if start is None else start
    if count < 1 or start < lo or start+count > hi:
        raise ValueError(f"seed range must stay inside {partition} [{lo}, {hi})")
    return range(start, start+count)


def streams(seed, partition="development"):
    seed_range(partition, seed)
    return {name: int(np.random.SeedSequence([seed, i]).generate_state(1)[0]) for i, name in enumerate(STREAMS)}


def plain(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, dict): return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    return value


def route(rng):
    legs = [[float(rng.uniform(0, 360)), float(rng.uniform(10, 45))] for _ in range(int(rng.integers(2, 7)))]
    return dict(lat0=float(rng.uniform(-70, 70)), lon0=float(rng.uniform(-180, 180)), legs=legs,
                index_turns=[], gnss_dropouts=[])


def random_turns(rng, duration):
    return [[float(t), "z"] for t in sorted(rng.uniform(2, duration-2, int(rng.integers(0, 5))))]


def random_gaps(rng, duration):
    return [[float(rng.uniform(1, duration-4)), float(rng.uniform(10, 180)/60)]
            for _ in range(int(rng.integers(0, 4)))]


def geometry_stress_matrix():
    """Observable, deterministic domain cells; speed labels do not assert measured information."""
    cells = []
    for latitude, headings, separation, duration, speed, turns in itertools.product(
            (-65., -35., -5., 5., 35., 65.), (2, 6), ("poor", "good"), (60., 180.), (150., 270.), (0, 3, 6)):
        span = 20. if separation == "poor" else (120. if headings == 2 else 300.)
        bearings = np.linspace(10., 10.+span, headings)
        cell = {"id": f"lat{latitude:+g}-h{headings}-{separation}-t{duration:g}-v{speed:g}-turn{turns}",
                "latitude_deg": latitude, "heading_count": headings, "heading_separation": separation,
                "heading_span_deg": span, "duration_min": duration, "speed_mps": speed, "turn_count": turns,
                "simulator": {"lat0": latitude, "lon0": -30., "speed": speed,
                    "legs": [[float(b), duration/headings] for b in bearings],
                    "index_turns": [[float(t), "z"] for t in np.linspace(10., duration-10., turns)] if turns else [],
                    "gnss_dropouts": []}}
        cells.append(cell)
    return cells


def validate_turn_schedule(turns, duration, min_spacing=10., edge_margin=5.):
    if not np.isfinite([duration, min_spacing, edge_margin]).all() or duration <= 0 or min_spacing <= 0 or edge_margin < 0:
        raise ValueError("duration and spacing must be positive; edge margin must be nonnegative")
    times = [float(t) for t in turns]
    if len(times) > 6 or not all(np.isfinite(times)) or times != sorted(times):
        raise ValueError("turn schedule must contain at most six finite, sorted times")
    if times and (times[0] < edge_margin or times[-1] > duration-edge_margin or
                  any(b-a < min_spacing for a, b in zip(times, times[1:]))):
        raise ValueError("turn schedule violates spacing or edge margin")
    return [[t, "z"] for t in times]


def trajectory(spec):
    kind = spec["kind"]
    if kind == "linear": return lambda t: spec["rate_dph"]*np.asarray(t)/3600
    if kind == "smooth": return lambda t: spec["amplitude_deg"]*np.sin(2*np.pi*np.asarray(t)/spec["period_s"])
    if kind == "transition":
        return lambda t: spec["amplitude_deg"]*(1-np.cos(np.pi*np.clip((np.asarray(t)-spec["start_s"])/spec["duration_s"], 0, 1)))/2
    raise ValueError("unknown crab trajectory")


def scenario(name, rng=None, duration_min=90., protocol_rng=None, missingness_rng=None):
    opts, analysis = {}, {}
    crab = {"kind": "linear", "rate_dph": 0.}
    if name.startswith("drift"):
        crab["rate_dph"] = float(name[5:])
    elif name == "smooth": crab = dict(kind="smooth", amplitude_deg=5., period_s=7200.)
    elif name == "transition": crab = dict(kind="transition", amplitude_deg=10., start_s=2400., duration_s=300.)
    elif name == "anisotropic": opts["gyro_noise_cov"] = np.diag([1., 4., 9.]).tolist()
    elif name == "correlated": opts["gyro_noise_cov"] = [[1., .7, .2], [.7, 2., .4], [.2, .4, 1.]]
    elif name == "equator": opts.update(lat0=0., legs=[[10, 30], [100, 30], [190, 30]])
    elif name == "high_latitude": opts.update(lat0=65., legs=[[90, 30], [180, 30], [270, 30]])
    elif name == "dateline": opts.update(lat0=20., lon0=179., legs=[[90, 45], [180, 45]])
    elif name == "turn_dropout":
        t = min(40., duration_min/2)
        opts.update(index_turns=[[t, "z"]], link_dropouts=[[t+.02, 3.]])
    elif name == "thermal": opts.update(flight_temp_rise_c=12., temp_coef_dph_per_c=[1., -.5, 2.], temp_lag_s=180.)
    elif name == "long_drift": opts.update(long_drift_dph=[3., -2., 4.], long_drift_period_s=5400.)
    elif name == "bias_step": opts["bias_jumps"] = [[duration_min*.5, [2., -1., 3.]]]
    elif name == "bias_ramp": opts["drift_dph_per_h"] = [3., -2., 4.]
    elif name == "bias_rw_high": opts["rw_dph_sqrth"] = 3.
    elif name == "bias_settling": opts.update(bias_settling_dph=[12., -9., 6.], bias_settling_tau_s=7200.)
    elif name == "bias_very_long": opts.update(long_drift_dph=[4., -3., 2.], long_drift_period_s=8*3600.)
    elif name == "bias_mixed": opts.update(rw_dph_sqrth=1.5, drift_dph_per_h=[2., -1., 2.],
                                            bias_jumps=[[duration_min*.6, [1., -.5, 1.]]])
    elif name == "wind": opts.update(wind_ne_mps=[12., -8.], wind_rate_ne_mps_per_h=[3., -2.])
    elif name in INTERACTIONS:
        names = {"crab_long_drift": ("drift+1", "long_drift"), "correlated_thermal": ("correlated", "thermal"),
                 "forward_crab": ("drift+1",), "turn_dropout_drift": ("turn_dropout", "long_drift")}[name]
        for sub in names:
            o, c, a = scenario(sub, rng, duration_min)
            opts.update(o); analysis.update(a)
            if sub.startswith("drift"): crab = c
        if name == "forward_crab": analysis["research_forward_offset_deg"] = 3.
    elif name == "fuzz":
        rng = np.random.default_rng(0) if rng is None else rng
        crab["rate_dph"] = float(rng.uniform(-5, 5))
        A = rng.normal(size=(3, 3)); C = A @ A.T
        C /= np.sqrt(np.outer(np.diag(C), np.diag(C)))
        sd = rng.uniform(1, 3, 3)
        opts.update(gyro_noise_cov=(C*np.outer(sd, sd)).tolist(), flight_temp_rise_c=float(rng.uniform(0, 12)),
                    temp_coef_dph_per_c=rng.uniform(-2, 2, 3).tolist(), temp_lag_s=float(rng.uniform(0, 180)),
                    long_drift_dph=rng.uniform(-4, 4, 3).tolist(), long_drift_period_s=float(rng.uniform(3600, 10800)))
        analysis["research_forward_offset_deg"] = float(rng.uniform(-3, 3))
        protocol_rng = np.random.default_rng(1) if protocol_rng is None else protocol_rng
        missingness_rng = np.random.default_rng(2) if missingness_rng is None else missingness_rng
        if missingness_rng.random() < .5:
            t = float(protocol_rng.uniform(2, duration_min-2))
            opts.update(index_turns=[[t, "z"]], link_dropouts=[[t+.02, float(missingness_rng.uniform(.5, 3))]])
    elif name != "hardware": raise ValueError(f"unknown scenario {name}")
    return opts, crab, analysis


def protocol_geometry(value):
    """Normalize a frozen geometry/turn protocol; nuisance parameters are specified separately."""
    keys = {"lat0", "lon0", "speed", "legs", "turn_schedule"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("protocol requires exactly lat0, lon0, speed, legs and turn_schedule")
    lat, lon, speed = (float(value[k]) for k in ("lat0", "lon0", "speed"))
    legs = [[float(a), float(b)] for a, b in value["legs"]]
    if (not np.isfinite([lat, lon, speed]).all() or not -90 < lat < 90 or not -180 <= lon <= 180
            or speed <= 0 or not legs or not np.isfinite(legs).all()
            or any(not 0 <= bearing < 360 or duration <= 0 for bearing, duration in legs)):
        raise ValueError("invalid protocol trajectory")
    turns = validate_turn_schedule(value["turn_schedule"], sum(l[1] for l in legs))
    return dict(lat0=lat, lon0=lon, speed=speed, legs=legs, turn_schedule=[t[0] for t in turns])


def realize(seed, scenario_name, *, partition="development", geometry="seeded", variant="spp",
            same_side_up_turns=False, hardware=None, turn_schedule=None, turn_min_spacing=10., turn_edge_margin=5.,
            geometry_cell=None, protocol=None):
    seeds = streams(seed, partition)
    # Resolve simulator defaults as well: replay does not silently acquire new defaults.
    opts = {k: plain(p.default) for k, p in inspect.signature(synthesize).parameters.items()
            if p.default is not inspect.Parameter.empty and k not in ("truth", "seed", "omega_in_fn", "crab_trajectory")}
    opts.update(fs=20., variant=variant, legs=[[10., 30.], [100., 30.], [190., 30.]])
    if geometry == "seeded": opts.update(route(np.random.default_rng(seeds["geometry"])))
    elif geometry == "stress":
        cells = {cell["id"]: cell for cell in geometry_stress_matrix()}
        if geometry_cell not in cells: raise ValueError("stress geometry requires a known geometry cell")
        if same_side_up_turns or turn_schedule is not None:
            raise ValueError("stress cells preregister their own turn schedules")
        opts.update(cells[geometry_cell]["simulator"])
    elif geometry != "fixed": raise ValueError("geometry must be fixed, seeded or stress")
    if protocol is not None:
        if geometry != "fixed" or same_side_up_turns or turn_schedule is not None:
            raise ValueError("protocol requires fixed geometry and its own turn schedule")
        protocol = protocol_geometry(protocol)
        opts.update({k: v for k, v in protocol.items() if k != "turn_schedule"})
        opts["index_turns"] = [[t, "z"] for t in protocol["turn_schedule"]]
        geometry_cell = "protocol-"+digest(protocol)
    duration = sum(l[1] for l in opts["legs"])
    if geometry == "seeded":
        opts["index_turns"] = random_turns(np.random.default_rng(seeds["protocol"]), duration)
        opts["gnss_dropouts"] = random_gaps(np.random.default_rng(seeds["missingness"]), duration)
    options, crab, analysis = scenario(scenario_name, np.random.default_rng(seeds["nuisance"]), duration,
                                     np.random.default_rng(seeds["protocol"]), np.random.default_rng(seeds["missingness"]))
    if scenario_name == "hardware":
        if hardware is None: raise ValueError("hardware fixture must be provided")
        options.update(plain(hardware))
    if (geometry == "stress" or protocol is not None) and any(key in options for key in ("lat0", "lon0", "legs", "speed", "index_turns")):
        raise ValueError("scenario overrides preregistered geometry; use a nuisance-only scenario")
    opts.update(options)
    duration = sum(l[1] for l in opts["legs"])
    # Dedicated geometry fixtures have their own duration. Regenerate only event times that
    # came from the random route, not the explicit interaction/dropout schedule.
    opts["gnss_dropouts"] = [g for g in opts["gnss_dropouts"] if g[0]+g[1] < duration]
    opts["index_turns"] = [t for t in opts["index_turns"] if t[0] < duration-1]
    if same_side_up_turns and not options.get("index_turns"):
        opts["index_turns"] = [[duration*f, "z"] for f in (2/9, 5/9, 8/9)]
    if turn_schedule is not None:
        opts["index_turns"] = validate_turn_schedule(turn_schedule, duration, turn_min_spacing, turn_edge_margin)
    return plain(dict(design_version=DESIGN_VERSION, seed=seed, partition=partition, streams=seeds,
                      geometry=geometry, scenario=scenario_name, simulator=opts, crab_trajectory=crab,
                      geometry_cell=geometry_cell,
                      analysis_options=analysis))


def simulator_options(design):
    return {**design["simulator"], "seed": design["streams"]["sensor"], "crab_trajectory": trajectory(design["crab_trajectory"])}


def freeze_manifest(config):
    content = {"design_version": DESIGN_VERSION, "analysis_version": __version__,
               "numerical_environment": numerical_environment(), "numerical_environment_hash": numerical_environment_hash(),
               "eligibility_policies": eligibility_policies(),
               "inference_policy_hash": digest(INFERENCE_POLICY), "implementation_hash": implementation_hash(), "config": config}
    return {**content, "manifest_hash": digest(content)}


def implementation_hash():
    """Explicit project sources only; no workspace enumeration or git dependency."""
    root = Path(__file__).resolve().parents[2]
    paths = ("analysis/lll/fit.py", "analysis/lll/inference.py", "analysis/lll/attitude.py",
             "analysis/lll/analyze.py", "analysis/lll/policy.py", "analysis/lll/inference_policy.py",
             "analysis/lll/synth.py", "analysis/lll/research_design.py", "analysis/lll/research_calibration.py",
             "analysis/lll/collate.py", "analysis/tests/research.py", "analysis/tests/optimize_turns.py",
             "analysis/tests/truthgen.py")
    paths += ("analysis/lll/calib.py", "analysis/lll/drift.py", "analysis/lll/models.py",
              "analysis/lll/runtime.py",
              "analysis/lll/rank_sweep.py",
              "analysis/lll/pairwise.py",
              "analysis/lll/pairwise_calibration.py",
              "analysis/lll/cli.py",
              "analysis/lll/slip.py", "analysis/lll/format.py", "analysis/lll/segments.py",
              "analysis/tests/conftest.py", "analysis/tests/test_analysis.py")
    return digest({p: (root/p).read_text() for p in paths})


def validate_manifest(manifest, config):
    if manifest != freeze_manifest(config):
        raise ValueError("campaign configuration differs from frozen manifest")
    return manifest["manifest_hash"]
