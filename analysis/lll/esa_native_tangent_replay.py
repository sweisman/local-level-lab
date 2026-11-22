# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay one sealed ESA forecast and retain its full calibration derivatives."""

import argparse
from contextlib import closing
import gzip
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


ID = 'esa-native-tangent-replay-v1-20261118'
AUTHORITATIVE = 'data/esa-rolling-origin-400-model-matrix-20261118'
PARENT_SHA = 'd29ecef42b37a8fffe05dbff591cf24d0720129c3792f14cd1649803a141829d'
CASE = 'sphere_rotating-1-increment-0'
MODEL = 'sphere_rotating'
SCOPE = 'no-refit preflight of the exact 400/120 ESA native calibration tangent'
ADAPTER = 'analysis/lll/esa_native_tangent_replay.py'
PLAN = 'docs/prediction-observed-development/ESA_NATIVE_TANGENT_REPLAY_PLAN.md'
PACKETS = 155868
TRAIN, PREDICT = 400, 120
KEYS = ('interval', 'training', 'forecast_times', 'recipe', 'fit', 'forecast',
        'training_observations', 'compiler', 'environment', 'parent', 'frozen_python_native')


def checked_jacobian(prediction, saved):
    import numpy as np
    if (any(not np.array_equal(prediction[key], saved[key])
            for key in ('coordinates', 'training_coordinate_difference'))
            or any(prediction[key] != saved[key] for key in
                   ('active_parameters', 'training_epochs', 'prediction_epochs'))
            or any(report['prediction_receiver_positions_used'] is not False
                   or report['continuous_propagation_without_gps_reset'] is not True
                   for report in (prediction, saved))):
        raise ValueError('exact sealed forecast and earlier residual replay required')
    jac = np.asarray(prediction['jacobian'], dtype=float)
    n = saved['training_epochs'] + saved['prediction_epochs']
    if (jac.shape != (3*n, len(saved['active_parameters']))
            or not np.all(np.isfinite(jac))):
        raise ValueError('complete finite calibration derivative required')
    return jac


def task():
    return dict(identity='fixed-forecast-tangent', input_key='interval', native_kind='tangent',
                payload=dict(parent_case=CASE, model=MODEL),
                limits=dict(native_calls=1, packet_visits=PACKETS*(TRAIN+PREDICT),
                            bound_calls=0, bound_steps=0))


def frozen_source_pack(study):
    from .studies.artifacts import encoded
    paths = {name: sha for name, sha in study.manifest['sources'].items()
             if name.startswith('analysis/lll/') and
             Path(name).suffix in ('.py', '.c', '.cpp', '.h', '.hpp')}
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
        from zipfile import ZipInfo
        for name, sha in sorted(paths.items()):
            archive.writestr(ZipInfo(name), study.read('source-freeze/'+name, sha, raw=True),
                             compress_type=ZIP_DEFLATED)
    return buffer.getvalue(), encoded(paths)


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen replay')
    with closing(ClosedStudy(root, AUTHORITATIVE)) as study:
        if (study.completion['manifest_sha256'] != PARENT_SHA
                or study.completion['state'] != 'terminal'
                or study.summary['completed'] != 24 or study.summary['total'] != 24
                or not study.rows[CASE]['passed']):
            raise ValueError('exact closed parent with a passing source fit required')
        if study.input('qualification_environment') != require_guarded_environment(environment()):
            raise ValueError('original numerical environment required')
        materials = {key: study.input(key, raw=True) for key in
                     ('interval', 'training', 'forecast_times', 'recipe')}
        for name, artifact in [('fit', 'fit.json'), ('forecast', 'forecast.json'),
                               ('training_observations', 'training-observations.json')]:
            materials[name] = study.artifact(CASE, artifact, raw=True)
        pack, source_index = frozen_source_pack(study)
        materials.update(compiler=encoded(study.artifact(CASE, 'compilation.json')['tangent']),
                         environment=study.input('qualification_environment', raw=True),
                         parent=encoded(dict(manifest_sha256=PARENT_SHA, case=CASE,
                             source_hashes=json.loads(source_index))),
                         frozen_python_native=pack)
    inputs = {}
    for name in KEYS:
        path = base/name
        atomic(path, materials[name])
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=[task()], inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN]), workers=1, threads=1,
                      maximum_wall_s=120.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .studies.artifacts import digest, safe_path
    if (context.manifest['scope'] != SCOPE or set(context.manifest['inputs']) != set(KEYS)
            or {k: v for k, v in declared.items() if k not in ('index', 'shard')} != task()
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('exact frozen replay task and environment required')
    parent = json.loads(context.input_path('parent').read_bytes())
    if parent['manifest_sha256'] != PARENT_SHA or parent['case'] != CASE:
        raise ValueError('exact sealed development parent required')
    with TemporaryDirectory(prefix='lll-esa-tangent-') as work:
        work = Path(work)
        with ZipFile(context.input_path('frozen_python_native')) as source:
            if sorted(source.namelist()) != sorted(parent['source_hashes']):
                raise ValueError('frozen source inventory differs')
            for name, sha in parent['source_hashes'].items():
                raw = source.read(name)
                if digest(raw) != sha:
                    raise ValueError('frozen replay source differs: '+name)
                dest = safe_path(work, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
        output = work/'result.json'
        arguments = json.dumps({key: str(context.input_path(key).resolve()) for key in KEYS})
        context.charge(native_calls=1, packet_visits=PACKETS*(TRAIN+PREDICT))
        subprocess.run([sys.executable, str(Path(__file__).resolve()), '_frozen',
                        arguments, str(output)], cwd=work, check=True,
                       env={**os.environ, 'PYTHONPATH': str(work/'analysis')})
        raw = output.read_bytes()
    report = json.loads(raw)
    context.save_bytes('full-tangent.json', raw)
    return dict(passed=True, exact_forecast=True, jacobian_shape=report['jacobian_shape'],
                fit_starts=0, later_receiver_positions_read=0, protected_reads=0,
                scientific_decision='abstain')


def frozen_replay(inputs, output, *, model=MODEL):
    import numpy as np
    from lll.ilvis0_forecast import native_forecast
    from lll.ilvis0_training_forecast import training_problem
    from lll.ilvis0_wide_tangent import load, problem
    from lll.studies.artifacts import digest, encoded

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    with np.load(inputs['interval'], allow_pickle=False) as data:
        arrays = {key: data[key] for key in ('theta', 'dv', 'dt')}
    times = np.asarray(read('forecast_times'), dtype=float)
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    earlier, recipe, fit, saved = (read(name) for name in
                                   ('training_observations', 'recipe', 'fit', 'forecast'))
    if (len(rows) != TRAIN or times.shape != (TRAIN+PREDICT,)
            or len(arrays['dt']) != PACKETS or not fit['converged']
            or times.tolist() != saved['times_s'] or fit['active_parameters'] != saved['active_parameters']
            or fit['normalized_parameters'] != saved['normalized_parameters']
            or len(saved['active_parameters']) != 27 or saved['frozen_error_model'] != model):
        raise ValueError('exact earlier-only 400/120 material and passing 27-column source required')
    gps = np.array([[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']),
                     row['height_m']] for row in rows])
    count = int(np.searchsorted(np.cumsum(arrays['dt']),
                times[TRAIN-1]+recipe['limits']['time_offset'], side='left'))+1
    prefix = {name: data[:count] for name, data in arrays.items()}
    if (gps.tolist() != earlier['coordinates'] or times[:TRAIN].tolist() != earlier['times_s']
            or count != earlier['native_prefix_packets']
            or any(digest(data.astype('<f8').tobytes()) != earlier['training_prefix_sha256'][name]
                   for name, data in prefix.items())):
        raise ValueError('exact training coordinates and IMU prefix required')
    expected = read('compiler')
    tangent, manifest = load(output.parent/'kernel', gravity_anchor_height_m=gps[0, 2],
                             expected_source_sha256=expected['original_source_sha256'])
    if manifest != expected:
        raise ValueError('original native compilation receipt required')
    # The covariance is only a constructor requirement. Native propagation
    # reads the training geometry and increments and never whitens residuals.
    base = training_problem(times[:TRAIN], gps, **prefix, covariance=np.eye(3*TRAIN),
                            model=model, limits=recipe['limits'], profile=True,
                            clock=recipe['clock'], maximum_interval_s=recipe['maximum_interval_s'],
                            kernel=None, tangent_kernel=tangent)
    expected_charge = dict(native_calls=1, packet_visits=PACKETS*(TRAIN+PREDICT))
    sweeps = []

    def reserve(**work):
        if sweeps or work != expected_charge:
            raise ValueError('one matching prepaid tangent sweep required')
        sweeps.append(work)

    forecast = native_forecast(problem(base, kernel=tangent), fit['normalized_parameters'],
                               model, **arrays, times=times,
                               maximum_interval_s=recipe['maximum_interval_s'],
                               reserve=reserve, retain_training_difference=True)
    jacobian = checked_jacobian(forecast, saved)
    output.write_bytes(encoded(dict(jacobian=jacobian.tolist(), jacobian_shape=list(jacobian.shape),
        active_parameters=saved['active_parameters'], normalized_parameters=fit['normalized_parameters'],
        training_epochs=TRAIN, prediction_epochs=PREDICT, forecast_queries_s=times.tolist(),
        source_forecast_sha256=digest(Path(inputs['forecast']).read_bytes()),
        compiler=manifest, native_charge=sweeps[0], weighting_applied=False)))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
