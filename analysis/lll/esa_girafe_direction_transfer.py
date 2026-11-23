# SPDX-License-Identifier: AGPL-3.0-or-later
"""Transfer a horizontal quartz alignment across earlier ESA 187 supports."""

import argparse
from contextlib import ExitStack, closing
from itertools import islice
import json
from pathlib import Path

from . import esa_carrier_phase_continuous as carrier
from . import esa_girafe_horizontal_witness as parent
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-girafe-direction-transfer-v1'
SCOPE = 'Earlier-only ESA 187 horizontal quartz alignment and internal directional transfer'
FOLDER = parent.axis.FOLDER
PLAN = FOLDER+'ESA_GIRAFE_DIRECTION_TRANSFER_PLAN.md'
REQUEST = FOLDER+'esa-girafe-direction-transfer-qualification.json'
XML = FOLDER+'esa-girafe-direction-transfer-tests.xml'
RESULT = FOLDER+'esa-girafe-direction-transfer-result.json'
ARTIFACT = 'direction-transfer.json'
CARRIER_SHA = '68f6cfad45e74571296d2029ef72a9d0bd32f163db57b61727f835f307f4d090'
START, WIDTH, SUPPORTS, TRAINING = 388215, 24, 16, 10
STOP = START+WIDTH*SUPPORTS
SAMPLES = WIDTH*SUPPORTS*10+8
STEPS = 16*48*len(parent.MODELS)+SAMPLES*len(parent.OFFSETS)
TASK = dict(identity='direction-transfer', input_key='girafe', payload=dict(supports=SUPPORTS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+SUPPORTS,
                        bound_steps=parent.axis.MAX_ROWS+SUPPORTS*STEPS))
TESTS = ('test_esa_girafe_direction_transfer.py', 'test_esa_girafe_horizontal_witness.py',
         'test_esa_girafe.py', 'test_esa_force_position_derivative.py')
REQUIRED = ('test_alignment_recovers_offset_and_either_orthogonal_handedness[1.0]',
            'test_alignment_recovers_offset_and_either_orthogonal_handedness[-1.0]',
            'test_direction_transfer_exposes_rank_loss_and_does_not_fix_held_error',
            'test_position_kernel_recovers_constant_acceleration_and_preserves_mass')


def residual(fit, source, target):
    return source@fit['transform']+fit['offset_mps2']-target


def align(source, target):
    """Fit an orthogonal two-axis transform and a constant horizontal offset."""
    import numpy as np

    source, target = (np.asarray(value, float) for value in (source, target))
    if (source.shape != target.shape or source.ndim != 2 or source.shape[1] != 2
            or len(source) < 3 or not all(np.isfinite(value).all() for value in (source, target))):
        raise ValueError('matched finite horizontal vectors are required')
    x = source-source.mean(axis=0)
    y = target-target.mean(axis=0)
    left, sv, right = np.linalg.svd(x.T@y)
    transform = left@right
    return dict(transform=transform.tolist(), offset_mps2=(target.mean(axis=0)-source.mean(axis=0)@transform).tolist(),
                determinant=float(np.linalg.det(transform)), cross_singular_values=sv.tolist(),
                source_singular_values=np.linalg.svd(x, compute_uv=False).tolist())


def metrics(errors):
    import numpy as np

    squares = errors**2
    return dict(vector_rms_mps2=float(np.sqrt(np.mean(np.sum(squares, axis=1)))),
                north_rms_mps2=float(np.sqrt(np.mean(squares[:, 0]))),
                east_rms_mps2=float(np.sqrt(np.mean(squares[:, 1]))))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    *(f'analysis/tests/{test}' for test in TESTS)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED, minimum_tests=13)
    return sources, environment


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite direction transfer study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    receipt = (root/carrier.RESULT).read_bytes()
    if digest(receipt) != CARRIER_SHA:
        raise ValueError('the exact continuous carrier replay is required')
    with closing(ClosedStudy(root, 'data/'+carrier.ID)) as study:
        result = study.envelope(carrier.TASK['identity'])
        if (study.completion['manifest_sha256'] != json.loads(receipt)['study_manifest_sha256']
                or result['charged'] != carrier.TASK['limits'] or not result['result']['passed']):
            raise ValueError('complete carrier replay accounting required')
        track = study.artifact(carrier.TASK['identity'], 'carrier-path.json')['positions']
    earlier = [dict(seconds=r['seconds'], position=r['position']) for r in track if START <= r['seconds'] <= STOP]
    if [r['seconds'] for r in earlier] != [START+.5*i for i in range(2*WIDTH*SUPPORTS+1)]:
        raise ValueError('the fixed earlier half-second position grid is required')
    girafe = parent.axis.girafe.BASE/parent.axis.SOURCE
    parent.axis.girafe.verify_file(root/girafe, parent.axis.SOURCE)
    values = dict(path=encoded(earlier), recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML,
                  carrier=carrier.RESULT, girafe=girafe.as_posix())
    for key, raw in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
        maximum_wall_s=RECOVER['maximum_wall_s']), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_girafe_force_overlap import sample_edges

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the fixed earlier direction transfer task is required')
    context.charge(bound_calls=1, bound_steps=parent.axis.MAX_ROWS)
    path = json.loads(context.input_path('path').read_bytes())
    times = np.asarray([r['seconds'] for r in path])
    positions = np.asarray([r['position'] for r in path])
    samples = []
    with context.input_path('girafe').open('rb') as stream:
        for sample in islice(parent.axis.girafe.read_rows(stream), parent.axis.MAX_ROWS):
            time = parent.axis.girafe.utc_seconds_to_gps(sample.utc_seconds)
            if time > STOP+.3:
                break
            if time >= START-.3:
                samples.append((time, sample.xyz_mps2[:2]))
        else:
            raise ValueError('the approved quartz scan did not reach the earlier endpoint')
    obs_times, force = zip(*samples, strict=True)
    if len(force) > SAMPLES or not np.allclose(np.diff(obs_times), .1, rtol=0., atol=1e-8):
        raise ValueError('the approved continuous 10 Hz quartz sample grid is required')
    axes, edges = np.asarray(force), sample_edges(obs_times)

    def support(i):
        context.charge(bound_calls=1, bound_steps=STEPS)
        center = START+WIDTH*i+WIDTH/2
        sl = slice(2*WIDTH*i, 2*WIDTH*(i+1)+1)
        knots = times[sl]-center
        derivative, kernel = parent.acceleration_kernel(knots)
        predicted = {}
        for model in parent.MODELS:
            values, weights = parent.supported_horizontal_force(knots, kernel, positions[sl], derivative, model)
            predicted[model] = (weights@values).tolist()
        measured = {str(offset): (parent.sample_weights(edges+offset-center, knots, kernel)@axes).tolist()
                    for offset in parent.OFFSETS}
        return dict(center_gps_s=center, predicted=predicted, measured=measured)

    def arrays(rows, model, offset):
        return (np.asarray([r['measured'][str(offset)] for r in rows]),
                np.asarray([r['predicted'][model] for r in rows]))

    training = [support(i) for i in range(TRAINING)]
    selected = {}
    for model in parent.MODELS:
        fits = []
        for offset in parent.OFFSETS:
            x, y = arrays(training, model, offset)
            fit = align(x, y)
            fits.append(dict(fit, offset_s=offset, training=metrics(residual(fit, x, y))))
        best = min(fits, key=lambda row: row['training']['vector_rms_mps2'])
        selected[model] = dict(best=best, alternatives=fits)
    context.save('earlier-alignment.json', selected)
    held = [support(i) for i in range(TRAINING, SUPPORTS)]

    results = {}
    for model, choice in selected.items():
        best = choice['best']
        x, y = arrays(held, model, best['offset_s'])
        errors = residual(best, x, y)
        alternate = align(x, y)
        results[model] = dict(selected=choice, check=metrics(errors), signed_check_mps2=errors.tolist(),
            internal_alignment=alternate, internal_fit=metrics(residual(alternate, x, y)),
            transform_difference=float(np.linalg.norm(
                np.asarray(best['transform'])-np.asarray(alternate['transform']), ord=2)))
    result = dict(passed=True, training=training, check=held, results=results, raw_samples=len(force),
                  new_fits=0, protected_reads=0, aircraft_error_cap_established=False, scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def main():
    from .studies.closed import ClosedStudy

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'prepare':
        result = prepare(root)
    elif args.action == 'recover':
        from .esa_shared_motion_carrier import recover_signature

        result = recover_signature(root, study_id=ID, task=TASK)
    else:
        prefix, identity = 'data/'+ID, TASK['identity']
        with ExitStack() as stack:
            study = stack.enter_context(closing(ClosedStudy(root, prefix)))
            continuation = root/(prefix+'-recovery')
            if continuation.is_dir():
                from .studies.combined_task_evidence import inspect

                origin = inspect(root, continuation)['selected'][identity]['origin']
                if origin != prefix:
                    study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
            envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
            if (envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']
                    or study.artifact(identity, 'earlier-alignment.json') != {
                        model: values['selected'] for model, values in result['results'].items()}):
                raise ValueError('the complete charged transfer and earlier choices are required')
            _write_equal(root/RESULT, encoded(dict(result, completion=study.completion, carrier_sha256=CARRIER_SHA)))
        result = {key: results['check'] for key, results in result['results'].items()}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
