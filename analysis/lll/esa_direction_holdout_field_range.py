# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound shape scores between the tested gyro field retention settings."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_direction_holdout_forecast as forecast
from . import esa_direction_holdout_score as score
from .esa_direction_receiver_derivative import SHAPES, quadrature_points
from .esa_doppler_force import CENTERS, WIDTHS, rate_operator
from .esa_force_direction_transfer import FIELDS, TRAINING, _predicted_vectors
from .esa_matched_gyro_direction import DISC_WITH_FIELD, GLOBE, FieldFrame, background_axes, profile_all_pairs, support
from .force_direction_alignment import direction_pair_angles_deg
from .models import OMEGA_E
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-direction-holdout-field-range-v1'
SCOPE = 'bound both shape scores over continuous gyro field retention on eight sealed ESA 187 windows'
PLAN = forecast.selection.FOLDER+'ESA_DIRECTION_HOLDOUT_FIELD_RANGE_PLAN.md'
RESULT = forecast.selection.FOLDER+'esa-direction-holdout-field-range.json'
SCORE_SHA = 'd151cfceb38de59035ec26e53a217c4a9b3dec2fefe50a1e0143166dbdd6313e'
SCORE_MANIFEST = 'd5bf1c715aabde54ff289724fcd4e12ef108d34becd93fc6e4c65a8bb7c67dc9'
GRID = 81
SHAPE_MODELS = dict(globe=GLOBE, disc=DISC_WITH_FIELD)
RETAINED = ('full_field_removed_from_gyro', 'full_field_logged')
ENDPOINT_ATOL_DEG = 2e-10


def work_steps(width):
    endpoints = quadrature_points(width)
    grid_nodes = len(CENTERS[TRAINING:])*len(SHAPES)*4*(width-1)*GRID
    return len(forecast.METHODS)*(endpoints+grid_nodes)


TASK = dict(identity='profile-saved-direction-angle-errors', input_key='scores', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+forecast.WINDOWS*len(WIDTHS),
                bound_steps=64080+forecast.WINDOWS*sum(map(work_steps, WIDTHS))))


def combined_bounds(zero_error, profile):
    """Bound the minimum over absent field and given field with uncertain retention."""
    lower = min(zero_error, profile['continuous_lower_rms_deg'])
    upper = min(zero_error, profile['grid_best_rms_deg'])
    return dict(lower_rms_deg=lower, upper_rms_deg=upper,
                best_sampled_case='zero_field' if zero_error <= profile['grid_best_rms_deg'] else 'specified_field')


def classify(bounds):
    globe, disc = (bounds[shape] for shape in SHAPES)
    gap = [disc['lower_rms_deg']-globe['upper_rms_deg'], disc['upper_rms_deg']-globe['lower_rms_deg']]
    preference = 'globe' if gap[0] > 0. else 'disc' if gap[1] < 0. else 'overlap'
    return dict(disc_minus_globe_rms_deg=gap, preference=preference)


def check_endpoints(actual, saved):
    import numpy as np

    a, b = (np.asarray(x, float) for x in (actual, saved))
    if (a.shape != (28,) or b.shape != a.shape or not np.isfinite(a).all() or not np.isfinite(b).all()
            or not np.allclose(a, b, rtol=0., atol=ENDPOINT_ATOL_DEG)):
        raise ValueError('sealed direction prediction did not reproduce')
    return float(np.max(np.abs(a-b)))


def fraction_frames(time, coordinate, fractions):
    import numpy as np

    frames = {}
    rate = OMEGA_E*(1.+1e-14)
    for model in SHAPE_MODELS.values():
        axes = background_axes(coordinate, model)
        steps = (axes[:-1]+axes[1:])/2.
        if np.max(np.linalg.norm(steps, axis=1)) > rate:
            raise ValueError('matched field exceeds the bound used for the continuous error interval')
        frames[model] = [FieldFrame(time, steps, fraction) for fraction in fractions]
    return rate, frames


def profile_width(time, coordinate, rates, width, fractions, rate, frames, sealed, measured, *, sample_time=None):
    import numpy as np

    supports = list(forecast.paired_supports(time, coordinate, rates, width, sample_time=sample_time))
    ends = {model: [rows[0], rows[-1]] for model, rows in frames.items()}
    output = {}
    for method in forecast.METHODS:
        targets = _predicted_vectors(time, coordinate, rates, width, ends,
                                     coefficients=[values[method] for _, _, values in supports])
        expected = sealed[method]
        max_difference = 0.
        comparisons = {label: {} for label in measured['observed_deg'][str(width)]}
        shifts = {}
        for shape, model in SHAPE_MODELS.items():
            predicted = {}
            shifts[shape] = {}
            for field in FIELDS:
                predicted[field] = direction_pair_angles_deg(targets[field][shape][TRAINING:])
                if sample_time is None:
                    deviation = check_endpoints(predicted[field], expected[field][shape])
                    max_difference = max(max_difference, deviation)
                else:
                    shifts[shape][field] = float(np.sqrt(np.mean((predicted[field]-expected[field][shape])**2)))
            late = [support(relative, rate_operator(relative)[1], coordinate[index], values[method], time[index], model)
                    for index, relative, values in supports[TRAINING:]]
            vectors = np.asarray([[node.average(frame) for node in late] for frame in frames[model]])
            for i, field in zip((0, -1), RETAINED, strict=True):
                max_difference = max(max_difference, check_endpoints(direction_pair_angles_deg(vectors[i]),
                                                                     predicted[field]))
            for label, actual in measured['observed_deg'][str(width)].items():
                result = profile_all_pairs(actual, late, vectors, fractions, rate)
                old = measured['scores'][str(width)][method]
                absolute = {}
                for field in FIELDS:
                    error = float(np.sqrt(np.mean((predicted[field]-actual)**2)))
                    reference = old[field][label]['earlier_reference_rms_deg']
                    absolute[field] = dict(error_rms_deg=error, earlier_reference_rms_deg=reference,
                                           within_reference=error <= reference)
                zero = absolute['zero_field']['error_rms_deg']
                keys = ('grid_best_fraction', 'grid_best_rms_deg', 'continuity_allowance_deg', 'continuous_lower_rms_deg', 'grid_rms_deg')
                comparisons[label][shape] = dict(combined_bounds(zero, result),
                    specified_field={key: result[key] for key in keys}, fixed_field_errors=absolute)
        output[method] = dict(maximum_endpoint_replay_difference_deg=max_difference,
                              corrections={label: dict(classify(rows), by_shape=rows) for label, rows in comparisons.items()})
        if sample_time is not None:
            output[method]['fixed_prediction_shift_from_air1_rms_deg'] = shifts
    return output


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing field range study must stay sealed')
    for module, expected, relative, sha in ((forecast, score.FORECAST_MANIFEST, forecast.RESULT, score.FORECAST_SHA),
                                           (score, SCORE_MANIFEST, score.RESULT, SCORE_SHA)):
        raw = (root/relative).read_bytes()
        with closing(ClosedStudy(root, 'data/'+module.ID)) as study:
            if (study.completion['manifest_sha256'] != expected or not study.summary['passed']
                    or digest(raw) != sha or json.loads(raw)['manifest_sha256'] != expected):
                raise ValueError('unchanged sealed forecasts and scores required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(forecasts=forecast.RESULT, scores=score.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_direction_holdout_field_range.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact continuous field range task required')
    design = forecast.frozen_input(context, 'forecasts', score.FORECAST_SHA)
    measurements = forecast.frozen_input(context, 'scores', SCORE_SHA)
    scored = {row['query_first_index']: row for row in measurements['windows']}
    if (len(scored) != forecast.WINDOWS or measurements['forecast_sha256'] != score.FORECAST_SHA
            or any(row['status'] != 'scored' for row in scored.values())):
        raise ValueError('complete prior angle measurements required')
    fractions = np.linspace(0., 1., GRID)
    output = []
    for window, reports, times in forecast.selected_receiver_windows(design['windows'], design['source'], context):
        identity = window['query_first_index']
        measured = scored[identity]
        if (digest(encoded(reports)) != window['receiver_rows_sha256'] or times.tolist() != window['receiver_times_s']
                or any(window[key] != measured[key] for key in ('leg', 'query_last_index', 'course'))):
            raise ValueError('window receiver or measurement provenance differs')
        time, coordinate, rates = forecast.receiver_kinematics(reports, times)
        widths = {}
        for width in WIDTHS:
            context.charge(bound_calls=1, bound_steps=work_steps(width))
            if not widths:
                rate, frames = fraction_frames(time, coordinate, fractions)
            widths[str(width)] = profile_width(time, coordinate, rates, width, fractions, rate, frames,
                window['predicted_angles_deg'][str(width)], measured)
        row = dict(query_first_index=identity, leg=window['leg'], course=window['course'], widths=widths)
        context.save_bytes(f'window-{identity}.json', encoded(row))
        output.append(identity)
    context.save_bytes('index.json', encoded(dict(window_ids=output, fractions=fractions.tolist(),
        maximum_rate_rad_s=rate, forecast_sha256=score.FORECAST_SHA, score_sha256=SCORE_SHA,
        original_imu_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=len(output) == forecast.WINDOWS, windows=len(output), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('all fixed operations and window artifacts are required')
        result = study.artifact(identity, 'index.json')
        result['windows'] = [study.artifact(identity, f'window-{i}.json') for i in result.pop('window_ids')]
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['charged'] = study.summary['charged']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('field range receipt differs from sealed evidence')
    return dict(sha256=digest(raw), windows=len(result['windows']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
