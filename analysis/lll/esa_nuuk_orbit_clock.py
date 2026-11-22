# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the joint final-product update on the existing ESA 187 carrier witness."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_nuuk_between_carrier as prior
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .esa_final_orbit_replay import ORBIT, ORBIT_SHA, interpolate_orbit
from .esa_precise_gps_support import read_orbit_positions
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-nuuk-orbit-clock-v1'
SCOPE = 'Joint final orbit and clock update on the fixed Nuuk-anchored carrier replay'
PLAN = carrier.FOLDER+'ESA_NUUK_ORBIT_CLOCK_PLAN.md'
RESULT = carrier.FOLDER+'esa-nuuk-orbit-clock-result.json'
REQUEST = carrier.FOLDER+'esa-nuuk-orbit-clock-qualification.json'
XML = carrier.FOLDER+'esa-nuuk-orbit-clock-tests.xml'
TEST = 'analysis/tests/test_esa_nuuk_orbit_clock.py'
ARTIFACT = 'nuuk-orbit-clock.json'
PARENT_SHA = 'cd6bfb15696dae2bb202604ccb902fc77cf16a8552912b074416aa913a076b7b'
N = prior.PAIR_COUNT
TASK = dict(identity='nuuk-orbit-clock', input_key='orbit', payload=dict(pairs=N),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+N, bound_steps=1+99*N))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
                                    'analysis/tests/test_shared_motion_carrier.py',
                                    'analysis/tests/test_esa_final_orbit_replay.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_product_update_combines_signs_after_removing_receiver_clock',
        'test_clock_correction_keeps_common_satellites_and_cancellation_signs',
        'test_interpolation_matches_a_known_degree_seven_polynomial'), minimum_tests=7)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite final-product study')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    if digest((root/ORBIT).read_bytes()) != ORBIT_SHA:
        raise ValueError('the pinned final orbit product is required')
    with ExitStack() as stack:
        study, result = _parent(root, prior.RESULT, PARENT_SHA, prior.ID, prior.TASK, prior.ARTIFACT, stack)
        if study.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits'] or len(result['rows']) != N:
            raise ValueError('the completed carrier witness and exact accounting are required')
        values = {key: study.input(key, raw=True) for key in
                  ('rinex', 'navigation', 'clock', 'anchor', 'path', 'continuity', 'metric', 'gap')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=prior.RESULT, orbit=ORBIT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def summarize(rows):
    import numpy as np

    from .shared_motion_carrier import centre, compare_signatures

    def joined(name):
        return np.concatenate([row[name] for row in rows])

    def rms(values):
        return float(np.sqrt(np.mean(values**2)))

    required = joined('common_required_m')
    comparison = {}
    for name in ('orbit', 'clock', 'products'):
        update = joined(name+'_m')
        fit = compare_signatures(required, update)
        fit['update_rms_m'] = fit.pop('clock_rms_m')
        fit['aligned_fraction'] = float(required@update/(required@required))
        comparison[name] = fit
    fixed = np.concatenate([centre([row['fixed_path_residual_m'][row['satellites'].index(prn)]
                                    for prn in row['common_satellites']]) for row in rows])
    return dict(pairs=len(rows), values=len(required), comparison=comparison,
                broadcast_fixed_rms_m=rms(fixed), broadcast_shifted_rms_m=rms(fixed+required),
                final_fixed_rms_m=rms(joined('fixed_residual_m')),
                final_shifted_rms_m=rms(joined('shifted_residual_m')))


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the frozen final-product task is required')
    orbit = read_orbit_positions(gzip.decompress(context.input_path('orbit').read_bytes()).decode('ascii'))
    result = carrier.replay_signature(context, record_residuals=True,
                                      final_orbit_position=lambda prn, time: interpolate_orbit(orbit[prn], time))
    saved = json.loads(context.input_path('prior').read_bytes())['rows']
    fields = ('seconds', 'satellites', 'common_satellites', 'required_m', 'clock_m', 'fixed_path_residual_m')
    for first, second in zip(saved, result['rows'], strict=True):
        if any(first[field] != second[field] for field in fields):
            raise ValueError('the signed broadcast replay must reproduce before comparing products')
    result['product_summary'] = summarize(result['rows'])
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('a sealed complete final-product replay is required')
        _write_equal(root/RESULT, encoded(dict(result, parent_sha256=PARENT_SHA, orbit_sha256=ORBIT_SHA,
                                               completion=study.completion)))
    return result['product_summary']


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    result = {'request': partial(qualification, verify=False), 'prepare': prepare, 'report': report,
              'recover': partial(carrier.recover_signature, study_id=ID, task=TASK)}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
