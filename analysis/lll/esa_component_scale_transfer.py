# SPDX-License-Identifier: AGPL-3.0-or-later
"""Leave each saved ESA turn/steady pair out of a forecast covariance fit."""

from contextlib import closing
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys

from .esa_repeat_turn_release import receiver_positions
from .esa_scored_path_shape import BASE, checked_receipts
from .esa_straight_control_windows import RESULT as SELECTION, SELECTION_SHA
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-component-scale-transfer-v1'
PLAN = BASE+'ESA_COMPONENT_SCALE_TRANSFER_PLAN.md'
RESULT = BASE+'esa-component-scale-transfer-result.json'
SCOPE = 'ESA 187 paired cross-window transfer of forecast covariance scales'
LOG_BOUNDS = (-5., 5.)
MAXIMUM = 100
LAWS = ('increment', 'point')
COMPONENTS = ('native', 'persistent', 'maneuver')
REPORTS = 120


@dataclass(frozen=True)
class Case:
    index: int
    roots: dict
    error: object
    component_covariance: object


def make_case(index, roots, error):
    import numpy as np

    error = np.asarray(error, dtype=float).reshape(-1)
    if set(roots) != set(COMPONENTS) or not len(error) or not np.isfinite(error).all():
        raise ValueError('complete forecast errors and covariance roots required')
    roots = {name: np.asarray(roots[name], dtype=float) for name in COMPONENTS}
    if any(root.ndim != 2 or root.shape[0] != len(error) or not np.isfinite(root).all()
           for root in roots.values()):
        raise ValueError('each covariance root must align with the complete window')
    cov = np.array([root @ root.T for root in roots.values()])
    return Case(index, roots, error, cov)


def score_case(case, variances):
    import numpy as np

    from .esa_repeat_turn_scoring import gaussian
    from scipy.stats import chi2

    covariance = np.einsum('i,ijk->jk', [variances[name] for name in COMPONENTS],
                           case.component_covariance)
    result = {key: float(values[0]) for key, values in gaussian(
        np.linalg.cholesky(covariance), case.error[None, :]).items()}
    lower, upper = chi2.ppf([.05/16, 1-.05/16], len(case.error))
    return result | dict(within_reference=bool(lower <= result['quadratic'] <= upper))


def fit_cases(training, *, maximum):
    from .covariance_scale_fit import fit

    fixed = dict.fromkeys(COMPONENTS, 1.)
    energy = math.fsum(score_case(case, fixed)['quadratic'] for case in training)
    dimensions = sum(len(case.error) for case in training)
    common = min(math.exp(LOG_BOUNDS[1]), max(math.exp(LOG_BOUNDS[0]), energy/dimensions))
    separate = fit(((case.roots, case.error[None, :]) for case in training),
                   log_bounds=LOG_BOUNDS, max_evaluations=maximum)
    return dict(common_variance=common, separate=separate)


def evaluate_fold(training, target, *, maximum):
    all_indices = [case.index for case in (*training, *target)]
    if not training or not target or len(set(all_indices)) != len(all_indices):
        raise ValueError('disjoint nonempty training and target windows required')
    fitted = fit_cases(training, maximum=maximum)
    arms = dict(fixed=dict.fromkeys(COMPONENTS, 1.),
                common=dict.fromkeys(COMPONENTS, fitted['common_variance']))
    if fitted['separate']['variances'] is not None:
        arms['separate'] = fitted['separate']['variances']
    return dict(fitting_windows=[case.index for case in training], fit=fitted,
                target=[dict(index=case.index, scores={name: score_case(case, v) for name, v in arms.items()})
                        for case in target])


def forecast_cases(root):
    reports = checked_receipts(root)
    metadata = reports['turn'][0]['receiver_metadata']
    windows, forecasts = {}, {}
    raw = (root/SELECTION).read_bytes()
    if digest(raw) != SELECTION_SHA:
        raise ValueError('the original matching of steady windows and turns is required')
    pairs = [(entry['turn_first_index'], entry['control']['first_index'])
             for entry in json.loads(raw)['contrasts']]
    for regime, input_key in (('turn', 'input-preflight'), ('steady', 'bundle')):
        receipt, saved, prefix = reports[regime]
        with closing(ClosedStudy(root, prefix+'runtime')) as archive:
            if (archive.completion['manifest_sha256'] != receipt['manifest_sha256']
                    or archive.completion['state'] != 'complete' or archive.summary['completed'] != 16
                    or receipt['receiver_metadata'] != metadata):
                raise ValueError('the two original complete archives are required')
            selected = {row['window']['first_index']: row for row in archive.input(input_key)['windows']}
            if len(selected) != 4 or windows.keys() & selected.keys():
                raise ValueError('the checked report supports must be disjoint')
            windows.update(selected)
            for case in receipt['primary']:
                identity, index, law = case['identity'], case['first_index'], case['law']
                payload = archive.artifact(identity, 'sealed-receiver-forecast.json', raw=True)
                forecast = json.loads(payload)
                if (case['state'] != 'sealed' or digest(payload) != case['forecast_sha256']
                        or forecast['law'] != law
                        or forecast['training_sha256'] != selected[index]['training_receiver_sha256']
                        or forecast['times_s'] != selected[index]['query_times_s'][-REPORTS:]
                        or saved['scores'][identity]['forecast_sha256'] != case['forecast_sha256']):
                    raise ValueError('the original primary forecast seal and score are required')
                forecasts[index, law] = (payload, saved['scores'][identity]['scores'])
    indices = [index for pair in pairs for index in pair]
    if (len(set(indices)) != 8 or len(pairs) != 4 or set(indices) != windows.keys()
            or set(forecasts) != {(index, law) for index in indices for law in LAWS}):
        raise ValueError('four complete nonoverlapping matched pairs are required')
    observations = receiver_positions(root, windows, expected_metadata=metadata)
    return pairs, forecasts, observations


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=MAXIMUM))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing scale transfer evidence must be preserved')
    pairs, forecasts, observations = forecast_cases(root)
    inputs = dict(plan=PLAN, selection=SELECTION)
    materials = {f'forecast-{index}-{law}': raw for (index, law), (raw, _) in forecasts.items()}
    materials.update({f'observed-{index}': encoded(pair) for index, pair in observations.items()})
    materials['design'] = encoded(dict(pairs=pairs, scores={
        f'{index}-{law}': scores for (index, law), (_, scores) in forecasts.items()}))
    for name, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(pair, law) for pair in pairs for law in LAWS],
        workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_component_scale_transfer.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def read_case(context, index, law, previous):
    import numpy as np

    from .esa_repeat_turn_scoring import DECAY_S, NATIVE_VARIANCE, STEADY_SD, TURN_SD
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .maneuver_error_roots import roots

    forecast = json.loads(context.input_path(f'forecast-{index}-{law}').read_bytes())
    times, actual = json.loads(context.input_path(f'observed-{index}').read_bytes())
    if forecast['law'] != law or times != forecast['times_s'] or len(times) != REPORTS:
        raise ValueError('the original law and 120 common scoring times required')
    error = np.asarray(actual) - np.asarray(forecast['mean_geodetic'])
    error[:, 1] = longitude_residual(error[:, 1])
    error *= physical_metric([forecast['anchor_geodetic']])[0]
    components = roots(times, forecast['angular_exposure'],
                       previous_time=forecast['previous_time'], decay_s=DECAY_S)
    case = make_case(index, dict(
        native=np.asarray(forecast['native_root_neu_m'])*math.sqrt(NATIVE_VARIANCE[law]),
        persistent=components['persistent']*STEADY_SD,
        maneuver=components['maneuver']*TURN_SD), error)
    reproduced = score_case(case, dict.fromkeys(COMPONENTS, 1.))
    if any(not math.isclose(reproduced[name], previous['both'][name], rel_tol=1e-8, abs_tol=1e-8)
           for name in ('quadratic', 'negative_log_score')):
        raise ValueError('the original joint covariance score did not reproduce')
    return case


def evaluate(task, context):
    design = json.loads(context.input_path('design').read_bytes())
    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or law not in LAWS or pair not in design['pairs']
            or declared != task_for(pair, law)):
        raise ValueError('the exact frozen held-out pair is required')
    cases = {i: read_case(context, i, law, design['scores'][f'{i}-{law}'])
             for entry in design['pairs'] for i in entry}
    context.charge(bound_calls=1, bound_steps=MAXIMUM)
    fold = evaluate_fold([case for index, case in cases.items() if index not in pair],
                         [cases[index] for index in pair], maximum=MAXIMUM)
    result = dict(fold, pair=pair, law=law, passed=True, scientific_decision='abstain')
    context.save_bytes('fold.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != 8:
            raise ValueError('all eight matched scoring tasks must finish')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
            folds=[study.artifact(identity, 'fold.json') for identity in study.rows],
            independent_flight_groups=0, scientific_decision='abstain'))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('scale transfer report differs')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_component_scale_transfer {prepare,report}')
    command(Path.cwd())
