# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only rank and scale support on sealed ESA flight tangents."""

import argparse
from contextlib import closing
import io
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_FITTED_SCALE_SUPPORT_PLAN.md'
FREEZE = BASE+'esa-fitted-scale-support-freeze.json'
RESULT = BASE+'esa-fitted-scale-support-result.json'
SOURCE_SHA = '580f297f0f8fd1b944edd2d21a53bdc248d8d1552cea3649e4894204745b62fe'
RANK_LIMITS = (1e-8, 1e-10)
REFERENCE_SD = (.0001, .001)


def support(design, roots, *, rank_rtol, reference_sd):
    """Measure covariance-term support relative to fixed native unit variance."""
    import numpy as np

    u, s, _ = np.linalg.svd(design, full_matrices=False)
    rank = int(np.count_nonzero(s > rank_rtol*s[0]))
    basis = u[:, :rank]
    result = dict(mean_rank=rank)

    def component_information(root):
        singular = np.linalg.svd(root, compute_uv=False)
        variances = (np.asarray(reference_sd)[:, None]*singular)**2
        return (0.5*np.sum((variances/(1.+variances))**2, axis=1)).tolist()

    for name, root in roots.items():
        retained = root-basis@(basis.T@root)
        original_energy = float(np.sum(root**2))
        retained_energy = float(np.sum(retained**2))
        result[name] = dict(retained_squared_loading_fraction=(
            retained_energy/original_energy if original_energy else None),
            information_before=component_information(root),
            information_after=component_information(retained))
    return result


def replay(study):
    import numpy as np
    from . import esa_conditioned_tangent as parent
    from .esa_motion_error_transfer import DECAY_S, THRESHOLD_DEG_S
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore
    from .maneuver_error_roots import roots, turn_exposure
    from .studies.artifacts import digest

    cut = parent.TRAIN
    times = np.asarray(study.input('forecast_times')[:cut])
    counts = {study.input(parent.key(model, 'training_observations'))['native_prefix_packets']
              for model in parent.MODELS}
    packet_count, = counts
    with np.load(io.BytesIO(study.input('interval', raw=True)), allow_pickle=False) as data:
        exposure = turn_exposure(data['dt'][:packet_count], data['theta'][:packet_count], times[1:],
                                 previous_time=times[0], threshold_deg_s=THRESHOLD_DEG_S)
    loadings = roots(times[1:], exposure, previous_time=times[0], decay_s=DECAY_S)
    loadings['maneuver'] = loadings['maneuver'][:, np.repeat(exposure > 0, 2)]
    results = {}
    for model in parent.MODELS:
        info = study.artifact(model, 'conditioned-tangent.json')
        f = study.input(parent.key(model, 'tangent'), raw=True)
        fit = study.input(parent.key(model, 'fit'))
        training = study.input(parent.key(model, 'training_observations'))
        op = restore(study.artifact(model, 'full-factors.npz', raw=True),
                     expected_sha256=info['snapshot_sha256'],
                     expected_configuration=info['operator_configuration'], maximum_bytes=parent.STORAGE)
        prefix = op.prefix(cut)
        tangent = json.loads(f)
        if (digest(f) != info['raw_jacobian_sha256'] or prefix.configuration != info['prefix_configuration']
                or training['times_s'] != times.tolist() or tangent['active_parameters'] != fit['active_parameters']):
            raise ValueError('exact archived training tangent and factors required')
        jacobian = prefix.whiten(np.asarray(tangent['jacobian'][:3*cut]))
        if not np.allclose(jacobian, fit['local_linearization']['jacobian'], rtol=1e-10, atol=1e-8):
            raise ValueError('design differs from the original fit')
        metric = np.tile(physical_metric(training['coordinates'][:1])[0], cut)
        whitened = {name: (prefix.whiten(np.pad(root, ((3, 0), (0, 0)))/metric[:, None])
                           if root.shape[1] else np.zeros((3*cut, 0)))
                    for name, root in loadings.items()}
        results[model] = {str(rtol): support(jacobian, whitened, rank_rtol=rtol, reference_sd=REFERENCE_SD)
                          for rtol in RANK_LIMITS}
    return dict(models=results, training_reports=cut, positive_motion_intervals=int((exposure > 0).sum()),
                total_motion_exposure=float(exposure.sum()), reference_acceleration_sd_m_s2=REFERENCE_SD)


def run(root, action):
    from . import esa_conditioned_tangent as parent
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion['manifest_sha256'] != SOURCE_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != set(parent.MODELS) or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('complete sealed calibration tangents required')
        own = Path(__file__).relative_to(root).as_posix()
        definition = encoded(dict(source=study.completion, environment=runtime_environment(),
            sources={name: digest((root/name).read_bytes()) for name in source_closure(
                root, (own, PLAN, 'analysis/tests/test_fitted_path_covariance_scales.py'))},
            models=parent.MODELS, relative_rank_limits=RANK_LIMITS, reference_sd=REFERENCE_SD,
            design_projections=6, fit_starts=0, native_calls=0, later_receiver_positions=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, definition)
            return dict(freeze_sha256=digest(definition))
        if (root/FREEZE).read_bytes() != definition:
            raise ValueError('frozen projection inputs, environment or source changed')
        payload = encoded(dict(replay(study), freeze_sha256=digest(definition), fit_starts=0,
            native_calls=0, later_receiver_positions=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, payload)
    return dict(sha256=digest(payload), archived_designs=len(parent.MODELS))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
