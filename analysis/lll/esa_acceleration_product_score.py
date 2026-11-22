# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use the force and accelerometer bias products in the saved ESA bound."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_direct_training_score import GAMMAS, MODELS, STARTS, STEPS, tasks as direct_tasks


ID = 'esa-acceleration-product-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_ACCELERATION_PRODUCT_SCORE_PLAN.md'
SCOPE = 'Bias and force product constraints on the saved ESA 187 shape score'
DIRECT_SHA = '0d04e716da1d285444f4f1631faea8b481faaf0a093adb4ba85d25cb3a0b787d'
ALLOWANCE = 3e-10
SETUP_STEPS = 11


def tasks():
    count = len(GAMMAS)*len(STARTS)
    return [dict(task, limits=dict(task['limits'], bound_calls=count+1,
                                  bound_steps=count*STEPS+SETUP_STEPS))
            for task in direct_tasks()]


def evaluate(task, context):
    import numpy as np
    from .esa_direct_training_score import compare, feasible_box_and_cuts
    from .esa_force_score import force_transform
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_acceleration_products import build, lift
    from .ilvis0_calibration_consistency import build as consistency_cuts
    from .ilvis0_reference_acceleration import AccelerationTerms

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact acceleration product task required')

    def read(suffix):
        return json.loads(context.input_path(model+suffix).read_bytes())

    residual, raw, design, lower, upper, earlier, target, settings = load_projection_inputs(context, model)
    context.charge(bound_calls=1, bound_steps=SETUP_STEPS)
    force, sample = read('-force'), read('-first-sample')
    transform = force_transform(force)
    acceleration = AccelerationTerms(transform.reference, sample['dv'], sample['dt'],
                                    force['configuration']['gravity'], outward_initial_force=True)
    cuts = read('-cuts')
    consistency = consistency_cuts(acceleration, transform)
    if acceleration.report()!=sample['acceleration'] or consistency.report()!=cuts['consistency']:
        raise ValueError('original acceleration convention and consistency rows required')

    added = build(acceleration, transform, consistency, lower, upper, allowance=ALLOWANCE)
    static = [row+[0.]*9 for name in ('coupling', 'consistency', 'orientation')
              for row in cuts[name]['design']] + added['design']
    limits = cuts['translated_upper']+added['limits']
    center = tuple(map(F, force['center']+[0.]*24))
    linked = [row for row in read('-witnesses')['rows'] if row['variant']=='linked_shared']
    if len(linked)!=10:
        raise ValueError('all sealed linked calibration checks required')
    checked = []
    for row in linked:
        point = [F(v)-c for v,c in zip(row['physical_point']+row['shared'], center, strict=True)]
        lifted = lift(added, point)
        if not feasible_box_and_cuts(lifted, added['lower'], added['upper'], static, limits):
            raise ValueError('acceleration product cuts exclude an archived linked point')
        if row['loss_passed']:
            checked.append((row['score_lower'], lifted))
    score, anchor = max(checked)
    context.save('product-cuts.json', dict(cuts=added, linked_points_checked=len(linked)))
    extra = np.zeros((len(residual),9))
    projection = (residual, np.c_[raw, extra], np.c_[design, extra],
                  np.asarray(added['lower']), np.asarray(added['upper']), earlier, target+((F(0), F(0)),)*9, settings)
    result = compare(context, projection, static, limits, anchor, score, read('-direct'),
                     artifact='product-support.json')
    return dict(result, linked_points_checked=len(linked), additional_constraints=len(added['design']))


def prepare(root):
    from .esa_coupled_training_score import ID as COUPLED
    from .esa_direct_training_score import ID as DIRECT, PARENT_SHA
    from .studies.artifacts import atomic
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing acceleration product freeze')
    staged = {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, 'data/'+DIRECT)))
        coupled = stack.enter_context(closing(ClosedStudy(root, 'data/'+COUPLED, store=parent.store)))
        for study, expected in ((parent, DIRECT_SHA), (coupled, PARENT_SHA)):
            if study.completion['manifest_sha256'] != expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
        staged['later-operator.npz'] = parent.input('later-operator', raw=True)
        for model in MODELS:
            for suffix, extension in (('', '.npz'), ('-weights', '.npz'), ('-settings', '.json'),
                                      ('-force', '.json'), ('-witnesses', '.json'), ('-cuts', '.json')):
                staged[model+suffix+extension] = parent.input(model+suffix, raw=True)
            staged[model+'-first-sample.json'] = coupled.input(model+'-first-sample', raw=True)
            staged[model+'-direct.json'] = parent.artifact(model, 'direct-support.json', raw=True)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path, payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter,
        sources=source_closure(root, [adapter, PLAN]), inputs=inputs, tasks=tasks(), scope=SCOPE,
        workers=2, threads=1, maximum_wall_s=110.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
