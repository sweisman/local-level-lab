# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score frozen full ESA paths over fixed post-cut error shapes."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path


SOURCE = 'data/esa-conditioned-tangent-v1-20261118'
SOURCE_SHA = '580f297f0f8fd1b944edd2d21a53bdc248d8d1552cea3649e4894204745b62fe'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_NATIVE_FUTURE_ERROR_PLAN.md'
FREEZE = FOLDER+'esa-native-future-error-freeze.json'
REPORT = FOLDER+'esa-native-future-error-result.json'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
CUT, LATER = 400, 120
MAX_ADDED_STD_M = 100.
LEVELS_M = (0., .025, .1, .5, 1., 5., 20., MAX_ADDED_STD_M)


def conditional_root(operator, metre_scale):
    """Materialize only the later conditional covariance root."""
    import numpy as np

    if operator.epoch_count != CUT+LATER or operator.observation_dimension != 3:
        raise ValueError('exact 120-query conditional support required')
    innovations = np.zeros((3*(CUT+LATER), 3*LATER))
    innovations[3*CUT:] = np.eye(3*LATER)
    root = operator.unwhiten(innovations)[3*CUT:]
    return np.tile(metre_scale, LATER)[:, None]*root


def _evaluate(study, observed, scale, times):
    import numpy as np
    from .future_error_sensitivity import added_error_roots, resolve, spectrum
    from .ilvis0_precision_value import longitude_residual
    from .innovations_snapshot import restore

    roots = added_error_roots(times[CUT:], previous_time=times[CUT-1])
    panels = {}
    for model in MODELS:
        forecast = study.artifact(model, 'conditioned-tangent.json')
        if (forecast['times_s'] != list(times[CUT:]) or forecast['later_receiver_positions_read']
                or forecast['protected_reads']):
            raise ValueError('sealed earlier-only forecast and exact scoring times required')
        factors = restore(study.artifact(model, 'full-factors.npz', raw=True),
            expected_sha256=forecast['snapshot_sha256'],
            expected_configuration=forecast['operator_configuration'], maximum_bytes=64*1024**2)
        residual = observed-np.asarray(forecast['conditioned_mean'])
        residual[:, 1] = longitude_residual(residual[:, 1])
        error = (residual*scale).ravel()
        root = conditional_root(factors, scale)
        by_shape = {}
        for name, physical in roots.items():
            model_spectrum = spectrum(root, error, physical)
            at_levels = {str(level): model_spectrum.score(level) for level in LEVELS_M}
            answer = resolve(model_spectrum, target=float(3*LATER), maximum_std=MAX_ADDED_STD_M)
            by_shape[name] = dict(**answer, scores=at_levels,
                                  added_covariance_rank=int(np.count_nonzero(model_spectrum.eigenvalues)))
        panels[model] = dict(physical_rms_m=float(np.sqrt(np.mean(np.sum(
                 error.reshape(-1,3)**2, axis=1)))),
                 baseline_score=by_shape['white']['scores']['0.0']['quadratic'],
                 baseline_conditional_logdet_m=float(2*np.log(np.diag(root)).sum()),
                 shapes=by_shape)
    return panels


def run(root, action):
    import numpy as np
    from . import esa_changing_drift_transfer as prior
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_solver_position import physical_metric
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, SOURCE)) as study, closing(
            ClosedStudy(root, prior.PARENT, store=study.store)) as receiver:
        prior_result = json.loads((root/prior.RESULT).read_bytes())
        prior_freeze = (root/prior.FREEZE).read_bytes()
        if (study.completion['manifest_sha256'] != SOURCE_SHA
                or study.completion['state'] != 'complete'
                or any(not study.rows[model]['passed'] for model in MODELS)
                or json.loads(prior_freeze)['parents'][1] != receiver.completion
                or prior_result['freeze_sha256'] != digest(prior_freeze)
                or prior_result['protected_reads'] != 0):
            raise ValueError('complete conditioned development and original receiver scoring evidence required')
        own = Path(__file__).relative_to(root).as_posix()
        configuration = encoded(dict(
            sources={name: digest((root/name).read_bytes()) for name in source_closure(
                root, (own, PLAN, 'analysis/tests/test_future_error_sensitivity.py'))},
            conditioned_study=study.completion, receiver_study=receiver.completion,
            later_receiver_sha256=prior_result['later_receiver_sha256'],
            earlier_support=CUT, later_epochs=LATER, env=runtime_environment(),
            levels=LEVELS_M, dimensions=3*LATER, maximum_std_m=MAX_ADDED_STD_M,
            spectra=9, bisections_per_spectrum=50, fits=0, native_calls=0,
            new_original_file_reads=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, configuration)
            return dict(freeze_sha256=digest(configuration))
        if (root/FREEZE).read_bytes() != configuration:
            raise ValueError('frozen scoring inputs, code or environment changed')
        rows = json.loads(gzip.decompress(receiver.input('training', raw=True)))[:CUT+LATER]
        if (len(rows) != CUT+LATER or digest(encoded(rows[CUT:])) != prior_result['later_receiver_sha256']
                or rows[:CUT] != json.loads(gzip.decompress(study.input('training', raw=True)))):
            raise ValueError('exact originally scored receiver rows required')
        times = study.input('forecast_times')
        origin = study.input(MODELS[0]+'-training_observations')['time_origin_gps_sow_s']
        if not np.array_equal(np.asarray([r['time_s'] for r in rows])-origin, times):
            raise ValueError('frozen forecast epochs and previously used reports do not align')
        coordinates = prior._coordinates(rows)
        scale = physical_metric(coordinates[CUT-1:CUT])[0]
        panels = _evaluate(study, coordinates[CUT:], scale, times)
    report = encoded(dict(freeze_sha256=digest(configuration), cases=panels, recording=187,
        considered_receiver_rows=LATER, covariance_scale_updated_from_scoring=False,
        newest_observed_files_opened=0, native_calls=0, fits=0, protected_reads=0,
        reference='unit-mean-squared-standardized-error-working-scale',
        scientific_decision='abstain'))
    _write_equal(root/REPORT, report)
    return dict(sha256=digest(report), models=len(panels), fits=0, protected_reads=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze','replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
