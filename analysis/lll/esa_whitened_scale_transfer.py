# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the ESA covariance fit in units of the native forecast covariance."""

from contextlib import closing
import json
import math
from pathlib import Path
import sys

from .esa_component_scale_transfer import (
    COMPONENTS, ID as PARENT, LAWS, MAXIMUM, RESULT as PARENT_REPORT,
    fit_cases, make_case, read_case, score_case, task_for,
)
from .esa_repeat_turn_scoring import _lower
from .esa_scored_path_shape import BASE
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-whitened-scale-transfer-v1'
PLAN = BASE+'ESA_WHITENED_SCALE_TRANSFER_PLAN.md'
RESULT = BASE+'esa-whitened-scale-transfer-result.json'
SCOPE = 'ESA 187 paired covariance scale transfer with an exact native whitening'
PARENT_MANIFEST = '6e22991982ef26ede3beb84844906a6151088cc1f7ce47b8266da4145b4bff8f'
PARENT_REPORT_SHA = '6ce82cb07c9c46500818065a1788ccfd25acce918beac49b1b7893b650c2d80c'


def whiten(case):
    import numpy as np
    from scipy.linalg import solve_triangular

    native = _lower(case.roots['native'], len(case.error))
    error = solve_triangular(native, case.error, lower=True)
    roots = {key: solve_triangular(native, case.roots[key], lower=True)
             for key in COMPONENTS if key != 'native'}
    roots['native'] = np.eye(len(error))
    return make_case(case.index, roots, error), float(np.log(native.diagonal()).sum())


def score_preserved(original, transformed, normalization, variances):
    direct, white = (score_case(case, variances) for case in (original, transformed))
    if (not math.isclose(direct['quadratic'], white['quadratic'], rel_tol=1e-8, abs_tol=1e-8)
            or not math.isclose(direct['negative_log_score'], white['negative_log_score']+normalization,
                                rel_tol=1e-8, abs_tol=1e-8)):
        raise ValueError('native whitening changed the Gaussian score')
    return direct


def fitted_scales(cases, *, maximum):
    transformed = [whiten(case) for case in cases]
    for case, (white, normalization) in zip(cases, transformed, strict=True):
        score_preserved(case, white, normalization, dict.fromkeys(COMPONENTS, 1.))
        score_preserved(case, white, normalization, dict(native=.3, persistent=3., maneuver=2.))
    fitted = fit_cases([case for case, _ in transformed], maximum=maximum)
    final = fitted['separate']['variances']
    if final is not None:
        for case, (white, normalization) in zip(cases, transformed, strict=True):
            score_preserved(case, white, normalization, final)
    return fitted


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing whitened fits must be preserved')
    if digest((root/PARENT_REPORT).read_bytes()) != PARENT_REPORT_SHA:
        raise ValueError('the original scale fit report is required')
    with closing(ClosedStudy(root, 'data/'+PARENT)) as original:
        if original.completion['manifest_sha256'] != PARENT_MANIFEST or not original.summary['passed']:
            raise ValueError('the entire earlier scale fit study is required')
        design = original.input('design')
        keys = ['design'] + [f'observed-{index}' for pair in design['pairs'] for index in pair]
        keys += [f'forecast-{index}-{law}' for pair in design['pairs'] for index in pair for law in LAWS]
        materials = {key: original.input(key, raw=True) for key in keys}
        materials['prior'] = encoded({identity: original.artifact(identity, 'fold.json')
                                      for identity in original.rows})
    inputs = dict(plan=PLAN, prior_report=PARENT_REPORT)
    for name, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(pair, law) for pair in design['pairs'] for law in LAWS],
        workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_whitened_scale_transfer.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    def load(key):
        return json.loads(context.input_path(key).read_bytes())

    design, previous = load('design'), load('prior')[task['identity']]
    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law) or previous['pair'] != pair or previous['law'] != law):
        raise ValueError('the exact original held-out pair and setting are required')

    def read(index):
        return read_case(context, index, law, design['scores'][f'{index}-{law}'])

    training = [index for window in design['pairs'] for index in window if index not in pair]
    if training != previous['fitting_windows']:
        raise ValueError('the original disjoint fitting windows are required')
    context.charge(bound_calls=1, bound_steps=MAXIMUM)
    fitted = fitted_scales([read(index) for index in training], maximum=MAXIMUM)
    if not math.isclose(fitted['common_variance'], previous['fit']['common_variance'], rel_tol=1e-8):
        raise ValueError('common multiplier changed under whitening')
    separate, target = fitted['separate']['variances'], []
    for index, original in zip(pair, previous['target'], strict=True):
        case = read(index)
        if original['index'] != index:
            raise ValueError('the held-out window order changed')
        white, normalization = whiten(case)
        scores = {key: score_preserved(case, white, normalization, dict.fromkeys(COMPONENTS, value))
                  for key, value in (('fixed', 1.), ('common', fitted['common_variance']))}
        if separate is not None:
            scores['separate'] = score_preserved(case, white, normalization, separate)
        target.append(dict(index=index, scores=scores))
    result = dict(pair=pair, law=law, fitting_windows=training, original_fit=previous['fit'],
        fit=fitted, target=target, passed=True, scientific_decision='abstain')
    context.save_bytes('fold.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != 8:
            raise ValueError('all eight sealed whitening comparisons are required')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
            folds=[study.artifact(identity, 'fold.json') for identity in study.rows],
            independent_flight_groups=0, scientific_decision='abstain'))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('whitened scale report differs')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_whitened_scale_transfer {prepare,report}')
    command(Path.cwd())
