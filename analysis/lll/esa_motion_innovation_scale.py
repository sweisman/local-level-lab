# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test a causal motion-dependent covariance on the saved ESA forecast pairs."""

from contextlib import closing
from itertools import product
import json
import math
from pathlib import Path
import sys

from .esa_component_scale_transfer import COMPONENTS, LAWS, LOG_BOUNDS, read_case
from .esa_forecast_error_localization import ID as PARENT, RESULT as PARENT_REPORT
from .esa_repeat_turn_scoring import DECAY_S
from .esa_scored_path_shape import BASE
from .esa_whitened_scale_transfer import whiten
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-motion-innovation-scale-v1'
PLAN = BASE+'ESA_MOTION_INNOVATION_SCALE_PLAN.md'
RESULT = BASE+'esa-motion-innovation-scale-result.json'
SCOPE = 'ESA 187 leave-one-pair-out motion-dependent native forecast innovation scales'
PARENT_MANIFEST = 'a152833e70fdd6f02bef79b4044eb14b8f0dd455d49ebfc2a0f146581607d7c7'
PARENT_REPORT_SHA = '001cce23f97e49a6e601675eaf25d20114ed01de7f49565e7f098dc45fe85fa5'
SCALES = tuple(math.exp(i) for i in range(int(LOG_BOUNDS[0]), int(LOG_BOUNDS[1])+1))
GRID_SIZE = len(SCALES) + len(SCALES)**2
TARGET_COUNT = 2*3
TRAIN_COUNT = 6
VERIFY_COUNT = TRAIN_COUNT+2


def response(times, *, previous_time, exposure):
    import numpy as np

    times, exposure = np.asarray(times, float), np.asarray(exposure, float)
    dt = np.diff(times, prepend=previous_time)
    if (times.ndim != 1 or not len(times) or times.shape != exposure.shape
            or not np.isfinite(dt).all() or np.any(dt <= 0.)
            or not np.isfinite(exposure).all() or np.any(exposure < 0.)):
        raise ValueError('complete ordered times and nonnegative motion exposure required')
    state, values = 0., []
    for step, active in zip(dt, exposure > 0., strict=True):
        switched = -math.expm1(-step/DECAY_S)
        state += switched*(float(active)-state)
        values.append(state)
    return np.asarray(values)


class InnovationScore:
    def __init__(self, y, root, weight, normalization):
        import numpy as np
        from scipy.stats import chi2

        self.y, root, self.weight = (np.asarray(value, float) for value in (y, root, weight))
        if (self.y.ndim != 1 or not len(self.y) or root.ndim != 2
                or root.shape[0] != len(self.y) or self.weight.shape != self.y.shape
                or any(not np.isfinite(v).all() for v in (self.y, root, self.weight))
                or np.any((self.weight < 0.) | (self.weight > 1.))
                or not math.isfinite(normalization)):
            raise ValueError('finite aligned innovations, weights and roots required')
        self.root = root[:, np.any(root != 0., axis=0)]
        self.identity = np.eye(self.root.shape[1])
        self.normalization = normalization + .5*len(self.y)*math.log(2*math.pi)
        self.reference = chi2.ppf([.05/16, 1-.05/16], len(self.y))

    def score(self, base, motion):
        import numpy as np
        from scipy.linalg import solve_triangular

        variance = base+motion*self.weight
        if not np.isfinite(variance).all() or np.any(variance <= 0.):
            raise ValueError('finite positive innovation variances required')
        error = self.y/np.sqrt(variance)
        logdet = float(np.log(variance).sum())
        coeff = np.empty(0)
        if self.root.shape[1]:
            scaled = self.root/np.sqrt(variance[:, None])
            factor = np.linalg.cholesky(self.identity+scaled.T @ scaled)
            half = solve_triangular(factor, scaled.T @ error, lower=True, check_finite=False)
            coeff = solve_triangular(factor.T, half, lower=False, check_finite=False)
            error = error-scaled @ coeff
            logdet += 2.*float(np.log(factor.diagonal()).sum())
        quadratic = float(error @ error + coeff @ coeff)
        return dict(quadratic=quadratic, mean_standardized_error=quadratic/len(self.y),
                    negative_log_score=.5*(quadratic+logdet)+self.normalization,
                    within_reference=bool(self.reference[0] <= quadratic <= self.reference[1]))


def fit_grid(training, *, reserve=lambda: None):
    if not training:
        raise ValueError('at least one fitting window is required')

    def loss(scales):
        reserve()
        return (math.fsum(item.score(*scales)['negative_log_score'] for item in training), *scales)

    native = min(loss((base, 0.)) for base in SCALES)
    motion = min(loss(pair) for pair in product(SCALES, repeat=2)) if any(
        item.weight.any() for item in training) else None
    return dict(constant=native[1:], motion=motion[1:] if motion else None,
                training_score_constant=native[0], training_score_motion=motion[0] if motion else None)


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=GRID_SIZE+TARGET_COUNT+VERIFY_COUNT,
                            bound_steps=TRAIN_COUNT*GRID_SIZE+TARGET_COUNT+2*VERIFY_COUNT))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('the existing motion scale study must be preserved')
    if digest((root/PARENT_REPORT).read_bytes()) != PARENT_REPORT_SHA:
        raise ValueError('exact saved localization report required')
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('exact saved localization study required')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        keys = ['design', *(f'observed-{index}' for index in windows)]
        keys.extend(f'forecast-{index}-{law}' for index in windows for law in LAWS)
        materials = {key: parent.input(key, raw=True) for key in keys}
    inputs = dict(plan=PLAN, prior=PARENT_REPORT)
    for key, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+key
        atomic(root/path, raw)
        inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(pair, law) for pair in design['pairs'] for law in LAWS],
        workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_motion_innovation_scale.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def scorer(context, index, law, previous):
    import numpy as np

    context.charge(bound_calls=1, bound_steps=2)
    case = read_case(context, index, law, previous)
    forecast = json.loads(context.input_path(f'forecast-{index}-{law}').read_bytes())
    weight = response(forecast['times_s'], previous_time=forecast['previous_time'],
                      exposure=forecast['angular_exposure'])
    white, logdet = whiten(case)
    root = np.column_stack([white.roots[key] for key in COMPONENTS[1:]])
    score = InnovationScore(white.error, root, np.repeat(weight, 3), logdet)
    original = score.score(1., 0.)
    if any(not math.isclose(original[key], previous['both'][key], rel_tol=1e-8, abs_tol=1e-8)
           for key in ('quadratic', 'negative_log_score')):
        raise ValueError('fixed covariance score did not reproduce')
    return score


def evaluate(task, context):
    pair, law = (task['payload'][key] for key in ('pair', 'law'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact saved motion covariance fold required')

    def read(index):
        return scorer(context, index, law, design['scores'][f'{index}-{law}'])

    fitting = [index for other in design['pairs'] for index in other if index not in pair]
    if len(fitting) != TRAIN_COUNT or len(set((*fitting, *pair))) != 8:
        raise ValueError('six training and two distinct later scoring windows required')
    fitted = fit_grid([read(index) for index in fitting], reserve=lambda: context.charge(
        bound_calls=1, bound_steps=TRAIN_COUNT))
    arms = dict(fixed=(1., 0.), constant=fitted['constant'])
    if fitted['motion'] is not None:
        arms['motion'] = fitted['motion']
    scores = []
    for index in pair:
        evidence = read(index)
        row = {}
        for name, scales in arms.items():
            context.charge(bound_calls=1, bound_steps=1)
            row[name] = evidence.score(*scales)
        scores.append(dict(index=index, scores=row))
    result = dict(law=law, pair=pair, fitting=fitting, fitted=fitted, target=scores,
                  passed=True, scientific_decision='abstain')
    context.save_bytes('motion-scale.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != 8:
            raise ValueError('every sealed motion-scale fold is required')
        rows = [study.artifact(identity, 'motion-scale.json') for identity in study.rows]
        grids = sum(GRID_SIZE if row['fitted']['motion'] else len(SCALES) for row in rows)
        scored = sum(len(target['scores']) for row in rows for target in row['target'])
        checked = len(rows)*VERIFY_COUNT
        charged = study.summary['charged']
        if (charged['bound_calls'] != grids+scored+checked
                or charged['bound_steps'] != TRAIN_COUNT*grids+scored+2*checked):
            raise ValueError('likelihood count differs from the sealed work ledger')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
                           folds=rows, charged=charged, scientific_decision='abstain'))
    destination = root/RESULT
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('saved report differs from verified scale results')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_motion_innovation_scale {prepare,report}')
    command(Path.cwd())
