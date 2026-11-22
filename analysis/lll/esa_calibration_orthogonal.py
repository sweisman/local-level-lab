# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seek a shape contrast with exact support bounds for both calibrations."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
import math
from pathlib import Path

from .calibration_orthogonal import annihilate_quadratics, box_lower
from .esa_linked_monotone_study import BASE
from .esa_linked_training_support import TRAIN, LATER, training_inputs
from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-calibration-orthogonal-v1'
SCOPE = 'Saved ESA zero-field forecasts contrasted outside combined calibration directions'
PLAN = BASE+'ESA_CALIBRATION_ORTHOGONAL_PLAN.md'
RESULT = BASE+'esa-calibration-orthogonal-result.json'
REQUEST = BASE+'esa-calibration-orthogonal-qualification-v2.json'
REPORT = BASE+'esa-calibration-orthogonal-tests-v2.xml'
TEST = 'analysis/tests/test_esa_calibration_orthogonal.py'
TESTS = ('test_nine_moments_vanish_exactly_and_earlier_taps_do_not_change',
         'test_exact_full_box_lower_does_not_drop_a_small_nonzero_coefficient')
MODELS = ('sphere_still', 'flat_still')
NAMES = ('smooth only', 'half calibration span', 'full calibration span')
WALL_S = 180
RECOVER = dict(RECOVERY_POLICY, maximum_wall_s=WALL_S)
TASK = dict(identity='two-forecast-contrast', input_key='nominal', payload=dict(choices=list(NAMES)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=7, bound_steps=13))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from . import esa_changing_drift_transfer as full
    from .esa_joint_path_score import _ranges
    from .esa_linked_graph_cuts import ID as GRAPH
    from .esa_linked_physical_replay import SCALAR_SHA
    from .ilvis0_control_shards import runtime_environment
    from .matched_shape_metric import REFERENCE, REFERENCE_SHA
    from .shape_remainder_witness import ID as WITNESS
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the existing finite comparison')
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ArchiveStore(root)) as store:
        reference = store.read(REFERENCE)
        if digest(reference) != REFERENCE_SHA:
            raise ValueError('the original matched shape comparison is required')
        plan = next(row for row in json.loads(reference)['settings'] if row['complete'] and row['imu_law'] == 'increment')
        ranges = _ranges({name: store.read(name) for name in (full.SEAL, full.RANGES, full.FREEZE)}, full)
        wanted = {plan['selected'][model] for model in MODELS}
        centers = {row['identity']: row['ranges']['fixed_3cm']['center_m']
                   for row in ranges['rows'] if row['identity'] in wanted}
        with (closing(ClosedStudy(root, 'data/'+GRAPH, store=store)) as graph,
              closing(ClosedStudy(root, 'data/'+WITNESS, store=store)) as witness):
            shape = witness.input('shape-direction')
            if (witness.completion['manifest_sha256'] != SCALAR_SHA or not witness.summary['passed']
                    or not graph.summary['passed']
                    or witness.input('later-operator', raw=True) != graph.input('later-operator', raw=True)
                    or set(centers) != wanted):
                raise ValueError('verified conditional forecast means and operator required')
            keys = ['later-operator', *(model+suffix for model in MODELS for suffix in ('', '-weights', '-settings'))]
            staged = {key: graph.input(key, raw=True) for key in keys}
            staged.update(shape=encoded(shape), times=witness.input('forecast_times', raw=True), nominal=encoded(
                {model: centers[plan['selected'][model]] for model in MODELS}))
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER), reference=reference)
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=REPORT)
    for name, raw in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, raw)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def candidates(operator, times, difference, designs):
    import numpy as np

    phase = 2.*(times[TRAIN:]-times[TRAIN])/(times[-1]-times[TRAIN])-1.
    smooth = np.kron(np.polynomial.legendre.legvander(phase, 2), np.eye(3))
    embedded = np.pad(np.column_stack((difference, smooth)), ((3*TRAIN, 0), (0, 0)))
    target = operator.whiten(embedded)[3*TRAIN:]
    basis, factor = np.linalg.qr(target[:, 1:], mode='reduced')
    if np.linalg.matrix_rank(factor) != 9:
        raise ValueError('all nine smooth directions are required')

    def remove_smooth(vector):
        return vector-basis@(basis.T@vector)

    nominal = remove_smooth(target[:, 0])
    design = remove_smooth(operator.whiten(np.column_stack(designs))[3*TRAIN:])
    lengths = np.linalg.norm(design, axis=0)
    scaled = np.divide(design, lengths, out=np.zeros_like(design), where=lengths > 0.)
    vectors, singular, _ = np.linalg.svd(scaled, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0]*max(scaled.shape)*np.finfo(float).eps))
    return nominal, vectors, rank, singular


def evaluate(task, context):
    import numpy as np

    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the original two-model calibration contrast is required')

    def raw(name):
        return context.input_path(name).read_bytes()

    shape, times, centers = map(lambda key: json.loads(raw(key)), ('shape', 'times', 'nominal'))
    operator = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    if len(times) != TRAIN+LATER:
        raise ValueError('the original two time windows are required')
    context.charge(bound_calls=1, bound_steps=1)
    metric = np.tile(shape['metric'], TRAIN+LATER)
    designs, boxes = [], []
    for model in MODELS:
        _, design, _, lower, upper, _, settings = training_inputs(raw, model)
        if any(shape[key] != settings['shape'][key] for key in ('metric', 'direction', 'nominal', 'factors_sha256')):
            raise ValueError('the original shape weighting must remain fixed')
        designs.append(design)
        boxes.append((lower, upper))
    vectors = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    if any(len(vector) != 3*LATER for vector in vectors):
        raise ValueError('both later means must cover the same 120 epochs')
    difference = [F(b)-F(a) for a, b in zip(*vectors, strict=True)]
    nominal, basis, rank, singular = candidates(operator, np.asarray(times), np.array(list(map(float, difference))),
                                                [design*metric[:, None] for design in designs])
    if not math.isclose(float(np.linalg.norm(nominal)), shape['nominal'], rel_tol=1e-9):
        raise ValueError('the original nominal contrast did not reproduce')
    results = {}
    for name, retained in zip(NAMES, (0, rank//2, rank), strict=True):
        context.charge(bound_calls=1, bound_steps=2)
        residual = nominal-basis[:, :retained]@(basis[:, :retained].T@nominal)
        norm = float(np.linalg.norm(residual))
        if not norm > np.finfo(float).eps*np.linalg.norm(nominal):
            context.charge(bound_calls=1, bound_steps=2)
            results[name] = dict(available=False, removed_rank=retained)
            continue
        direction = np.r_[np.zeros(3*TRAIN), residual/norm]
        lower, upper = adjoint_intervals(operator, direction)
        tap = annihilate_quadratics([(F(a)+F(b))/2 for a, b in zip(lower, upper, strict=True)], times[TRAIN:])
        context.charge(bound_calls=1, bound_steps=2)
        dot = sum(weight*value for weight, value in zip(tap[3*TRAIN:], difference, strict=True))
        weights = [F(m)*w for m, w in zip(metric, tap, strict=True)]
        changes = {}
        for model, design, (lo, hi), sign in zip(MODELS, designs, boxes, (-1, 1), strict=True):
            effects = [sum(w*F(float(val)) for w, val in zip(weights, column, strict=True) if val)
                       for column in design.T]
            changes[model] = box_lower([sign*value for value in effects], lo, hi)
        margin = dot+sum(changes.values())
        threshold = margin/(2*sum(map(abs, tap))) if margin > 0 else F(0)
        results[name] = dict(available=True, removed_rank=retained, nominal_exact=str(dot),
                             margin_exact=str(margin), margin_lower=endpoint(margin, False),
                             max_position_remainder_m=endpoint(threshold, False),
                             calibration_floor_exact={key: str(value) for key, value in changes.items()},
                             weights_exact=list(map(str, tap)), moments_exact_zero=9)
    body = dict(rank=rank, directions=results, singular_values=singular.tolist(), original=shape['nominal'])
    context.save('orthogonal-contrast.json', body)
    return dict(passed=True, available=sum(row['available'] for row in results.values()),
                scientific_decision='abstain', new_fits=0, protected_reads=0)


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery allowance required')
            identity = TASK['identity']
            if identity in original.rows and original.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    recovery = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        study = original
        if recovery.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, recovery)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        envelope = study.envelope(identity)
        body = study.artifact(identity, 'orthogonal-contrast.json')
        if envelope['status'] != 'complete' or envelope['charged'] != TASK['limits'] or set(body['directions']) != set(NAMES):
            raise ValueError('all declared results and work charges are required')
        result = dict(body, completion=study.completion)
    _write_equal(root/RESULT, encoded(result))
    return dict(rank=result['rank'], directions={name: (
        [row['margin_lower'], row['max_position_remainder_m']] if row['available'] else None)
        for name, row in result['directions'].items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
