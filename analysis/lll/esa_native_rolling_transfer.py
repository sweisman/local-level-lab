# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay matched native held-out covariance scores at the two ESA forecast origins."""

import argparse
from contextlib import closing
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ID = 'esa-native-rolling-transfer-v1-20261118'
ADAPTER = 'analysis/lll/esa_native_rolling_transfer.py'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_NATIVE_ROLLING_TRANSFER_PLAN.md'
EARLIER_REPORT = FOLDER+'esa-native-rolling-transfer-earlier.json'
REPORT = FOLDER+'esa-native-rolling-transfer-result.json'
SCOPE = 'exact fixed native covariance factors for two sealed ESA origins and two IMU laws'
PARENTS = {
    200: ('data/esa-rolling-origin-200-conditioning-v1-20261116',
          'd197a774b335f855f7357ed5c0cb51497b077beb943f6f596428b5a19d24beaa', 95868),
    400: ('data/esa-rolling-origin-400-conditioning-v1-20261115',
          'c02064b4e7d59565564b857cdb66763cad4744389b9b9522a121f9d741a3f8f5', 155868),
}
LAWS = ('increment', 'point')
LATER = 120
STORAGE = 64*1024**2
LATER_SOURCE = 'data/prediction-observed-development-continuation-v1-20261113'
LATER_SOURCE_SHA = '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
LATER_ROWS_SHA = '70b3a439d302587190243e2fe38abcd9f844261504ee1f39f3786ac200f146e3'
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'saved-input-binding',
          'qualification_environment', 'source-index', 'source-pack')
PER_LAW = ('fit', 'forecast', 'error-operator', 'training-observations',
           'conditional', 'compilation')
COMPANIONS = ('analysis/lll/esa_original_whitening.py', 'analysis/lll/innovations_snapshot.py')


def matched_window(rows, training, times, *, origin):
    """Authenticate training prefix and exact timestamp support before scoring."""
    cut = len(training)
    if not cut or len(times) <= cut or len(rows) < len(times) or rows[:cut] != training:
        raise ValueError('unchanged receiver training prefix required')
    if [row['time_s']-origin for row in rows[:len(times)]] != list(times):
        raise ValueError('receiver and forecast query times differ')
    return rows[cut:len(times)]


def tasks():
    return [dict(identity=f'{cut}-{law}', input_key=f'{cut}-interval', native_kind='tangent',
                 payload=dict(cut=cut, law=law),
                 limits=dict(native_calls=packets+cut+LATER, packet_visits=packets+cut+LATER,
                             bound_calls=0, bound_steps=0))
            for cut, (_, _, packets) in PARENTS.items() for law in LAWS]


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_native_tangent_replay import frozen_source_pack
    from .esa_original_whitening import QUAL
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the already frozen native transfer study')
    checked(root, QUAL+'/request.json', sources=qualification_sources(root),
            environment=runtime_environment(), required_tests=REQUIRED_TESTS,
            minimum_tests=len(REQUIRED_TESTS))
    materials = {}
    for cut, (prefix, expected, _) in PARENTS.items():
        with closing(ClosedStudy(root, prefix)) as study:
            if (study.completion['manifest_sha256'] != expected
                    or study.completion['state'] != 'complete'
                    or set(study.tasks) != set(LAWS)
                    or any(not study.rows[law]['passed'] for law in LAWS)
                    or study.input('qualification_environment') != environment()):
                raise ValueError('exact sealed 200/120 and 400/120 conditioning parents required')
            for name in SHARED[:-2]:
                materials[f'{cut}-{name}'] = study.input(name, raw=True)
            pack, index = frozen_source_pack(study)
            materials[f'{cut}-source-pack'] = pack
            materials[f'{cut}-source-index'] = encoded(dict(source_hashes=json.loads(index)))
            for law in LAWS:
                for name in PER_LAW[:4]:
                    materials[f'{cut}-{law}-{name}'] = study.input(f'{law}-{name}', raw=True)
                materials[f'{cut}-{law}-conditional'] = study.artifact(law, 'conditional-forecast.json', raw=True)
                materials[f'{cut}-{law}-compilation'] = encoded(
                    study.artifact(law, 'compilation.json')['noise_bridge'])
    inputs = {}
    for name, payload in materials.items():
        path = base/name
        atomic(path, payload)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN, *COMPANIONS]),
                      workers=4, threads=1, maximum_wall_s=600.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import frozen_workspace
    from .innovations_snapshot import restore
    from .studies.artifacts import digest

    task = {key: value for key,value in declared.items() if key not in ('index','shard')}
    cut, law = declared['payload']['cut'], declared['payload']['law']
    if (context.manifest['scope'] != SCOPE or task not in tasks()
            or json.loads(context.input_path(f'{cut}-qualification_environment').read_bytes()) != environment()):
        raise ValueError('unchanged native transfer task and numerical environment required')
    files = {name: str(context.input_path(f'{cut}-{name}').resolve()) for name in SHARED[:5]}
    files.update({name: str(context.input_path(f'{cut}-{law}-{name}').resolve()) for name in PER_LAW})
    with frozen_workspace(context, COMPANIONS, parent_key=f'{cut}-source-index',
                          pack_key=f'{cut}-source-pack') as work:
        counts = {key: task['limits'][key] for key in ('native_calls','packet_visits')}
        with context.prepay_native(**counts):
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '_frozen', str(cut),
                            law, json.dumps(files), str(work)], cwd=work,
                           env={**os.environ, 'PYTHONPATH': str(work/'analysis')}, check=True)
        report = json.loads((work/'factor-replay.json').read_bytes())
        payload = (work/'rolling-factors.npz').read_bytes()
    if report['cut'] != cut or report['law'] != law or report['snapshot_sha256'] != digest(payload):
        raise ValueError('factor output changed identity or content')
    restore(payload, expected_sha256=report['snapshot_sha256'],
            expected_configuration=report['configuration'], maximum_bytes=STORAGE)
    context.save('factor-replay.json', report)
    context.save_bytes('rolling-factors.npz', payload)
    return dict(passed=True, cut=cut, law=law, optimizer_starts=0, scoring_positions_read=0,
                protected_reads=0, scientific_decision='abstain')


def frozen_replay(cut, law, inputs, work):
    from dataclasses import replace
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_noisy_inputs import error_law
    from lll.esa_conditional_forecast_v2_study import fixed_receiver_mean
    from lll.esa_conditional_forecast_v3_study import replay_training_prefix
    from lll.esa_original_whitening import load_original_noise
    from lll.ilvis0_exploratory import ConditionalBounds
    from lll.ilvis0_native_error_training import build_training_operator
    from lll.ilvis0_training_forecast import initialize_training
    from lll.innovations_snapshot import capture
    from lll.studies.artifacts import digest, encoded

    deadline = time.monotonic()+540.

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, forecast, old, earlier, recipe, reference, binding = (read(name) for name in
        ('fit','forecast','error-operator','training-observations','recipe','conditional','saved-input-binding'))
    _, _, packets = PARENTS[cut]
    times = np.asarray(read('forecast_times'))
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    with np.load(inputs['interval'], allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta','dv','dt')}
    if (len(rows) != cut or len(times) != cut+LATER or len(arrays['dt']) != packets
            or reference['law'] != law or reference['training_epochs'] != cut
            or forecast['frozen_error_model'] != 'sphere_rotating'
            or binding['source_id'] != 'esa-99f1530c3eda4318'
            or reference['later_receiver_values_used'] is not False
            or forecast['prediction_receiver_positions_used'] is not False
            or not fit['converged'] or len(fit['active_parameters']) != 26):
        raise ValueError('exact fixed earlier-only forecasts required')
    count = earlier['native_prefix_packets']
    prefix = {name: val[:count] for name,val in arrays.items()}
    gps = np.asarray(earlier['coordinates'])
    model = 'sphere_rotating'
    initial, gravity = initialize_training(times[:cut], gps, **prefix, model=model,
        maximum_interval_s=recipe['maximum_interval_s'], clock=recipe['clock'])
    weight = build(rows, policy_id='reported-short-v1')
    origin = binding['time_origin_s']
    spec = replace(weight.spec, drift_origin_s=weight.spec.drift_origin_s-origin)
    if (not np.array_equal(weight.times-origin, times[:cut])
            or reference['training_operator_configuration'] != old['operator_configuration']):
        raise ValueError('original training timing and weight identity required')
    transforms = np.concatenate((weight.transforms, np.repeat(weight.transforms[-1:], LATER, axis=0)))
    kernel, _ = load_original_noise(work, read('compilation'))
    calls = 0

    def reserve(*, native_calls, packet_steps):
        nonlocal calls
        calls += 1
        if native_calls != 1 or packet_steps != 1 or calls > packets+cut+LATER or time.monotonic() >= deadline:
            raise ValueError('declared native covariance replay allowance exhausted')

    operator, descriptor = build_training_operator(**arrays, times=times, initial=initial,
        bounds=ConditionalBounds(recipe['limits'], fit_earth_removal=False),
        model=model, gravity_mps2=gravity, disc_radius_m=6371000.,
        noise=error_law(recipe['noise_by_law'][law]), receiver_spec=spec,
        receiver_transforms=transforms, noise_kernel=kernel,
        gravity_anchor_height_m=float(gps[0,2]), maximum_packets=packets,
        maximum_queries=cut+LATER, maximum_bytes=recipe.get('maximum_covariance_bytes', STORAGE),
        anchor_policy=recipe['covariance_anchor_policy'], reserve=reserve)
    if (descriptor != reference['operator_descriptor']
            or operator.configuration != reference['full_operator_configuration']):
        raise ValueError('original full native covariance identity changed')
    replay_training_prefix(operator, forecast, training_epochs=cut,
        expected_cost=fit['residual_sum_squares'], expected_logdet=old['error_log_determinant'])
    replay = fixed_receiver_mean(operator, forecast, training_epochs=cut)
    for name, prior in [('mean','conditional_receiver_mean'), ('mean_adjustment','mean_adjustment'),
                        ('covariance','conditional_receiver_covariance')]:
        if not np.array_equal(replay[name], reference[prior]):
            raise ValueError('archived conditional result differs: '+name)
    payload = capture(operator)
    (work/'rolling-factors.npz').write_bytes(payload)
    (work/'factor-replay.json').write_bytes(encoded(dict(cut=cut, law=law,
        snapshot_sha256=digest(payload), configuration=operator.configuration,
        calls=calls, scoring_positions_read=0, original_fits_repeated=0, protected_reads=0)))


def score_phase(root, cut):
    import numpy as np
    from .esa_changing_drift_transfer import _coordinates
    from .esa_joint_path_score import joint_score
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_precision_value import longitude_residual
    from .innovations_snapshot import restore
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    phase = EARLIER_REPORT if cut == 200 else REPORT
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (study.completion['state'] != 'complete' or
                set(study.tasks) != {task['identity'] for task in tasks()}
                or any(not row['passed'] for row in study.rows.values())
                or study.manifest['sources'][ADAPTER] != digest((root/ADAPTER).read_bytes())):
            raise ValueError('all four sealed covariance replays required')
        if cut == 200:
            rows = json.loads(gzip.decompress(study.input('400-training', raw=True)))
            earlier = None
        else:
            raw = (root/EARLIER_REPORT).read_bytes()
            earlier = json.loads(raw)
            if (earlier['study_completion'] != study.completion or earlier['cut'] != 200
                    or earlier['later_origin_seen'] is not False):
                raise ValueError('earlier scoring must be sealed before opening the late window')
            with closing(ClosedStudy(root, LATER_SOURCE, store=study.store)) as source:
                if source.completion['manifest_sha256'] != LATER_SOURCE_SHA:
                    raise ValueError('original later scoring source changed')
                rows = json.loads(gzip.decompress(source.input('training', raw=True)))
        training = json.loads(gzip.decompress(study.input(f'{cut}-training', raw=True)))
        times = study.input(f'{cut}-forecast_times')
        origin = study.input(f'{cut}-saved-input-binding')['time_origin_s']
        held = matched_window(rows, training, times, origin=origin)
        held_sha = digest(encoded(held))
        if len(held) != LATER or (cut == 400 and held_sha != LATER_ROWS_SHA):
            raise ValueError('original held-out 120 reports required')
        actual = _coordinates(held)
        scores = {}
        for law in LAWS:
            identity = f'{cut}-{law}'
            original = study.input(identity+'-conditional')
            receipt = study.artifact(identity, 'factor-replay.json')
            operator = restore(study.artifact(identity, 'rolling-factors.npz', raw=True),
                expected_sha256=receipt['snapshot_sha256'],
                expected_configuration=original['full_operator_configuration'], maximum_bytes=STORAGE)
            residual = actual - np.asarray(original['conditional_receiver_mean'])
            residual[:,1] = longitude_residual(residual[:,1])
            report = joint_score(operator, cut, residual, horizons=(LATER,))[str(LATER)]
            scores[law] = dict(**report, mean_squared_standardized_error=
                               report['squared_standardized_error']/(3*LATER))
        result = dict(study_completion=study.completion, cut=cut, scores=scores, held_receiver_sha256=held_sha,
                      later_origin_seen=cut==400, scoring_epochs=LATER, fits=0, native_calls=0,
                      original_reads=0, protected_reads=0, scientific_decision='abstain')
        if earlier is not None:
            result['earlier_sha256'] = digest(raw)
            result['later_over_earlier'] = {law: scores[law]['squared_standardized_error']/
                earlier['scores'][law]['squared_standardized_error'] for law in LAWS}
    _write_equal(root/phase, encoded(result))
    return dict(report=phase, scores=sorted(scores), sha256=digest(encoded(result)))


if __name__ == '__main__':
    if len(sys.argv) == 6 and sys.argv[1] == '_frozen':
        frozen_replay(int(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4]), Path(sys.argv[5]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare','score-earlier','score-later'))
        action = parser.parse_args().action
        root = Path.cwd()
        result = prepare(root) if action == 'prepare' else score_phase(root, 200 if action == 'score-earlier' else 400)
        print(json.dumps(result, sort_keys=True))
