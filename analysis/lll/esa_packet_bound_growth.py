# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check four original query times on both sealed recorded packet prefixes."""

import argparse
from contextlib import closing
import io
import json
from pathlib import Path

from .esa_packet_bound_profile import BASE, PARENT as PREFLIGHT, PARENT_SHA, MODELS
from .esa_shape_prefix_preflight import evaluate_prepared
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-packet-bound-growth-v1'
SCOPE = 'Growth of the ESA 187 zero-field unshared packet bound at four original query times'
PLAN = BASE+'ESA_PACKET_BOUND_GROWTH_PLAN.md'
RESULT = BASE+'esa-packet-bound-growth-result.json'
REQUEST = BASE+'esa-packet-bound-growth-qualification.json'
REPORT = BASE+'esa-packet-bound-growth-tests.xml'
TEST = 'analysis/tests/test_esa_packet_bound_growth.py'
TESTS = ('test_extension_keeps_query_triplets_and_clock_support',
         'test_extension_rejects_changed_prefix_and_missing_clock_support')
INDICES = (0, 1, 4, 9)
PACKETS = 3200
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=6400)
TARGET_M = .0403


def extend_prefix(arrays, times, path, jac, limits, original):
    import numpy as np

    rows = list(INDICES)
    q = np.asarray(times)[rows]
    positions = np.asarray(path)[rows]
    tangent = np.asarray(jac).reshape(len(times), 3, 27)[rows].reshape(-1, 27)
    if (set(arrays) != {'dt', 'theta', 'dv'} or any(len(array) != len(arrays['dt']) for array in arrays.values())
            or any(not np.array_equal(original[name], array[:len(original[name])]) for name, array in arrays.items())
            or not np.array_equal(q[:2], original['times']) or not np.array_equal(positions[:2], original['positions'])
            or not np.array_equal(tangent[:6], original['jacobian'])):
        raise ValueError('the original verified prefix must be preserved')
    lower, upper = original['lower'], original['upper']
    edge = float(q[-1]+limits[25]*upper[25])
    available = len(arrays['dt'])
    count = int(np.searchsorted(np.cumsum(arrays['dt'][:PACKETS]), edge, side='right'))+2
    if (not len(original['dt']) < count <= min(available, PACKETS)
            or q[0]+limits[25]*lower[25] < 0.):
        raise ValueError('all four queries need complete bounded clock support')
    payload = {key: value[:count] for key, value in arrays.items()}
    payload.update(times=q, positions=positions, jacobian=tangent, lower=lower,
                   upper=upper, center=original['center'])
    return payload, edge


def task_for(model):
    return dict(identity=model, input_key=model, payload=dict(query_indices=list(INDICES), model=model), limits=LIMITS)


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
        'analysis/lll/ilvis0_source_prefix_reference.cpp', 'analysis/lll/ilvis0_source_prefix_intervals.cpp'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    import numpy as np

    from .esa_calibration_contrast import ID as PARENT
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the existing growth study and allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=550)))
    with closing(ClosedStudy(root, PREFLIGHT)) as prefix, closing(ClosedStudy(root, 'data/'+PARENT, store=prefix.store)) as original:
        if (prefix.completion['manifest_sha256'] != PARENT_SHA or not prefix.summary['passed']
                or prefix.manifest['environment'] != env):
            raise ValueError('exact matched short bounds under the same environment required')
        arithmetic = {'ilvis0_dyadic_source.py', 'ilvis0_native_prefix.py', 'ilvis0_batched_transport.py'}
        for name, sha in prefix.manifest['sources'].items():
            path = Path(name)
            if ((path.suffix in ('.cpp', '.hpp', '.h', '.c') or path.name in arithmetic)
                    and digest((root/name).read_bytes()) != sha):
                raise ValueError('unchanged interval arithmetic required')
        interval = original.input('interval', raw=True)
        times = original.input('forecast_times')
        with np.load(io.BytesIO(interval), allow_pickle=False) as data:
            arrays = {key: data[key] for key in ('dt', 'theta', 'dv')}
        for model in MODELS:
            metadata = prefix.input(model+'-metadata')
            forecast_raw = original.input(model+'-forecast', raw=True)
            forecast = json.loads(forecast_raw)
            tangent = original.artifact(model, 'full-tangent.json')
            if (metadata['parent'] != original.completion or digest(interval) != metadata['parent_interval_sha256']
                    or digest(forecast_raw) != metadata['forecast_sha256']
                    or tangent['source_forecast_sha256'] != metadata['forecast_sha256']
                    or tangent['forecast_queries_s'] != times or tangent['weighting_applied'] is not False
                    or forecast['times_s'] != times or forecast['prediction_receiver_positions_used'] is not False):
                raise ValueError('exact original predicted positions, timings and numerical derivatives required')
            with np.load(io.BytesIO(prefix.input(model, raw=True)), allow_pickle=False) as data:
                saved = {key: data[key] for key in data.files}
            if (saved['center'].tolist() != tangent['normalized_parameters']
                    or saved['center'].tolist() != forecast['normalized_parameters']):
                raise ValueError('the original physical parameter region must remain unchanged')
            values, edge = extend_prefix(arrays, times, forecast['coordinates'], tangent['jacobian'],
                                         metadata['configuration']['limits'], saved)
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **values)
            metadata.update(packet_count=len(values['dt']), cut_upper_s=edge, query_indices=list(INDICES),
                            original_prefix=prefix.completion)
            staged.update({model: buffer.getvalue(), model+'-metadata': encoded(metadata)})
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=[task_for(model) for model in MODELS], workers=2, threads=1, maximum_wall_s=550.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    model = task['identity']
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or model not in MODELS or declared != task_for(model):
        raise ValueError('the exact longer prefix and finite allowance are required')
    result = evaluate_prepared(task, context, packet_limit=PACKETS, step_limit=LIMITS['bound_steps'],
                               seconds=480., save_queries=True)
    if len(result['remainder_m']) != len(INDICES):
        raise ValueError('all four original query reports required')
    result['target_met'] = [max(row) <= TARGET_M for row in result['remainder_m']]
    context.save('growth.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        rows = {}
        for model in MODELS:
            record = study.envelope(model)
            checks = []
            for index in range(len(INDICES)):
                artifact = f'query-{index:02d}.json'
                if f'artifacts/{model}/{artifact}' in record['artifacts']:
                    item = study.artifact(model, artifact)
                    checks.append(dict(query=INDICES[index], time_s=item['bound']['time_s'],
                        center_error_m=item['center_error_m'], remainder_m=item['remainder_m']))
            result = record['result']
            if result['passed'] and (record['charged'] != LIMITS or len(checks) != len(INDICES)
                    or result != study.artifact(model, 'growth.json')
                    or [row['remainder_m'] for row in checks] != result['remainder_m']):
                raise ValueError('checked sequence differs from the sealed growth result')
            rows[model] = dict(result=result, status=record['status'], charged=record['charged'], checks=checks)
        output = dict(rows=rows, completion=study.completion, target_m=TARGET_M)
    _write_equal(root/RESULT, encoded(output))
    return {model: (len(row['checks']), row['result'].get('target_met')) for model, row in rows.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
