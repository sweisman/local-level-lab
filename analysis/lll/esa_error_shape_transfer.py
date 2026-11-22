# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retrospective prefix-to-suffix checks of ESA forecast-error shapes."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_ERROR_SHAPE_TRANSFER_PLAN.md'
FREEZE = BASE+'esa-error-shape-transfer-freeze.json'
RESULT = BASE+'esa-error-shape-transfer-result.json'
EXPOSURE_SHA = ('4c42b5cf1c50be8e889a10734cdc9ba4aacf42b549ea57cbb2dfcadff1399e07',
                '52db5fd0ae40a538c08673438ce6f35c388da99184a72cb9d2a80fa570709389')
SELECTION_SHA = '8e65babaf0abe267b2ee8fa9a6228e31b0fcf3ea6d81b1a811d5972a3174187e'
SHORT_PREFIX, LONG_PREFIX = 90, 200
RANK_RTOL = 1e-10


def rms(values):
    import numpy as np

    return np.sqrt(np.mean(np.asarray(values)**2, axis=0)).tolist()


def fit_correction(design, observed, *, prefix):
    """Estimate coefficients on the prefix and score positions only on the suffix."""
    import numpy as np

    x, observed = (np.asarray(a, float) for a in (design, observed))
    if (x.ndim != 2 or observed.shape != (len(x), 3) or not x.shape[1] <= prefix < len(x)
            or not np.isfinite(x).all() or not np.isfinite(observed).all()):
        raise ValueError('complete physical position errors and a declared prefix required')
    scale = np.linalg.norm(x[:prefix], axis=0)
    scale[scale == 0.] = 1.
    estimates, _, rank, singular = np.linalg.lstsq(x[:prefix]/scale, observed[:prefix], rcond=RANK_RTOL)
    common = dict(prefix_rank=int(rank), prefix_singular_values=singular.tolist())
    if rank != x.shape[1]:
        return dict(common, status='unidentifiable', coefficients=None)
    coefficients = estimates/scale[:, None]
    residual = observed-x@coefficients
    return dict(common, status='scored', coefficients=coefficients.tolist(),
                prefix_rms_neu_m=rms(residual[:prefix]), later_rms_neu_m=rms(residual[prefix:]))


def compare(times, observed, *, prefix, exposure):
    import numpy as np
    from .esa_motion_error_transfer import DECAY_S
    from .maneuver_error_roots import roots

    times = np.asarray(times, float)
    ages = times[1:]-times[0]
    state = np.column_stack((np.ones(len(ages)), ages))
    acceleration = .5*ages**2
    designs = dict(state=state, steady=np.column_stack((state, acceleration)))
    if exposure is not None:
        impulse = roots(times[1:], exposure, previous_time=times[0], decay_s=DECAY_S)['maneuver']
        # The archived covariance treats shocks as independent. For an error
        # shape, sum their responses with one shared coefficient per axis.
        response = np.sum(impulse[::3, ::2], axis=1)
        designs.update(turn=np.column_stack((state, response)),
                       combined=np.column_stack((state, acceleration, response)))
    scores = {name: fit_correction(x, observed, prefix=prefix) for name, x in designs.items()}
    return dict(prefix_reports=prefix, later_reports=len(ages)-prefix,
        original_prefix_rms_neu_m=rms(observed[:prefix]), original_later_rms_neu_m=rms(observed[prefix:]),
        scores=scores, linear_solves=len(scores))


def short(study, cut, receiver, score, exposure):
    from .esa_innovation_transfer import window

    values = window(study, cut, receiver, score)
    times = study.input(f'{cut}-forecast_times')[cut-1:]
    return {law: compare(times, physical, prefix=SHORT_PREFIX, exposure=exposure)
            for law, (_, physical) in values.items()}


def straight(study, receiver):
    import numpy as np
    from . import esa_maneuver_pairs as held
    from .esa_changing_drift_transfer import _coordinates
    from .esa_native_rolling_transfer import matched_window
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric

    rows = json.loads(gzip.decompress(receiver.input('scoring', raw=True)))
    training = json.loads(gzip.decompress(study.input('training', raw=True)))
    origin = study.input('saved-input-binding')['time_origin_s']
    times = study.input('weighted-forecast')['times_s']
    actual = matched_window(rows, training, times, origin=origin)
    forecast = study.artifact(held.TASK, 'conditional-forecast.json')
    if (len(training) != held.CUT or len(actual) != held.LATER or forecast['training_epochs'] != held.CUT
            or forecast['prediction_epochs'] != held.LATER or forecast['later_receiver_values_used'] is not False):
        raise ValueError('exact saved 800/400 forecast and receiver boundary required')
    delta = _coordinates(actual)-np.asarray(forecast['conditional_receiver_mean'])
    delta[:, 1] = longitude_residual(delta[:, 1])
    delta *= physical_metric(_coordinates(training[-1:]))[0]
    return compare(times[held.CUT-1:], delta, prefix=LONG_PREFIX, exposure=None)


def run(root, action):
    from . import esa_innovation_transfer as sealed
    from . import esa_maneuver_pairs as held
    from . import esa_motion_error_transfer as motion
    from . import esa_native_rolling_transfer as source
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, 'data/'+source.ID)) as rolling, closing(
            ClosedStudy(root, held.STUDY, store=rolling.store)) as no_turn:
        if (rolling.completion['manifest_sha256'] != sealed.SOURCE_SHA or rolling.completion['state'] != 'complete'
                or set(rolling.rows) != {r['identity'] for r in source.tasks()} or any(not row['passed'] for row in rolling.rows.values())
                or no_turn.completion['manifest_sha256'] != held.MANIFEST or no_turn.completion['state'] != 'complete'
                or no_turn.rows[held.TASK]['passed'] is not True):
            raise ValueError('sealed short and straight forecasts required')
        selection = (root/held.SELECTION).read_bytes()
        if digest(selection) != SELECTION_SHA or json.loads(selection)['selected']['turn_centres']:
            raise ValueError('original no-turn selection required')
        sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_error_shape_transfer.py')
        freeze = encoded(dict(rolling=rolling.completion, straight=no_turn.completion, straight_selection_sha256=SELECTION_SHA,
            environment=runtime_environment(), sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
            exposure_hashes=EXPOSURE_SHA, score_hashes=(sealed.EARLY_SCORE_SHA, sealed.LATE_SCORE_SHA),
            short_prefix=SHORT_PREFIX, straight_prefix=LONG_PREFIX, rank_rtol=RANK_RTOL, maximum_linear_solves=18,
            trajectory_fits=0, native_calls=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('frozen shape-transfer inputs or definition changed')
        exposures = [(root/path).read_bytes() for path in (motion.EARLY, motion.RESULT)]
        scores = [(root/path).read_bytes() for path in (source.EARLIER_REPORT, source.REPORT)]
        if (tuple(map(digest, exposures)) != EXPOSURE_SHA
                or tuple(map(digest, scores)) != (sealed.EARLY_SCORE_SHA, sealed.LATE_SCORE_SHA)):
            raise ValueError('sealed motion histories or original scores differ')
        early_receiver = json.loads(gzip.decompress(rolling.input('400-training', raw=True)))
        earlier = short(rolling, 200, early_receiver, json.loads(scores[0]), json.loads(exposures[0])['exposures'])
        with closing(ClosedStudy(root, source.LATER_SOURCE, store=rolling.store)) as receiver:
            if (receiver.completion['manifest_sha256'] != source.LATER_SOURCE_SHA
                    or receiver.manifest['inputs']['scoring']['sha256'] != held.SCORING_SHA):
                raise ValueError('exact opened receiver source required')
            late_receiver = json.loads(gzip.decompress(receiver.input('training', raw=True)))
            later = short(rolling, 400, late_receiver, json.loads(scores[1]), json.loads(exposures[1])['exposures'])
            quiet = straight(no_turn, receiver)
        count = sum(row['linear_solves'] for row in (*earlier.values(), *later.values(), quiet))
        if count != 18:
            raise ValueError('frozen linear solve count differs')
        payload = encoded(dict(freeze_sha256=digest(freeze), earlier_short=earlier, later_short=later, straight_long=quiet,
            linear_solves=count, trajectory_fits=0, native_calls=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, payload)
    return dict(sha256=digest(payload), linear_solves=count, forecast_windows=3)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
