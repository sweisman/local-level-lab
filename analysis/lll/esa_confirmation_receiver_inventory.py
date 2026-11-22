# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen reserved ESA receiver exports without reading protected IMU data."""

import argparse
from collections import Counter
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .esa_group_evidence import SOURCES, _groups
from .esa_ppp_acquisition import BASE_URL, LISTING_SHA256, sha256
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-confirmation-receiver-inventory-v3'
PREVIOUS = 'esa-confirmation-receiver-inventory-v2'
SCOPE = 'Receiver-only eligibility on seven reserved ESA groups; no protected IMU or model use'
DOCS = 'docs/external-imu-data/'
PLAN = DOCS+'ESA_CONFIRMATION_RECEIVER_INVENTORY_PLAN.md'
ACCOUNTING = DOCS+'ESA_CONFIRMATION_RECEIVER_INVENTORY_ACCOUNTING.md'
TIME_FORMAT = DOCS+'ESA_CONFIRMATION_RECEIVER_INVENTORY_TIME_FORMAT.md'
RESULT = DOCS+ID+'-result.json'
PREVIOUS_RESULT = DOCS+PREVIOUS+'-result.json'
PREVIOUS_SHA = '08566d7dfd94994d8c85447063cff0a452f2077d729da1acd9fa5039bf6f6c62'
REQUEST = DOCS+ID+'-qualification.json'
XML = DOCS+ID+'-tests.xml'
INPUTS = 'data/esa-confirmation-receiver-inventory-inputs/'
ACQUISITION = INPUTS+'acquisition.json'
LISTING = 'data/external-imu-survey-20261018/esa-sample/catalog/lvl1-gnss-list.txt'
TEST = 'analysis/tests/test_airquantumgrav_selection_v2.py'
TESTS = ('test_provisional_receiver_inventory_cannot_certify_full_eligibility',
         'test_full_motion_exact_duration_distance_and_quality_thresholds_pass',
         'test_receiver_worker_charges_complete_operations_before_decode',
         'test_esa_utc_hour_can_have_one_digit_and_stays_verbatim')
TARGETS = {'178a': 9_017_739, '178b': 5_751_474, '179': 18_638_557, '180': 15_811_636,
           '182': 28_871_950, '183': 15_131_602, '184': 14_129_857, '186': 14_682_088}
MAX_EPOCHS = 100_000
BLOCK_SIZE = 1024
MAX_BLOCKS = (MAX_EPOCHS+BLOCK_SIZE)//BLOCK_SIZE
WORK = ('178a', '180', '182')


def filename(recording):
    return f'{recording}_air1_ppp_2Hz_final.txt'


def expected_groups(root):
    def load(key):
        path, sha = SOURCES[key]
        raw = (root/path).read_bytes()
        if digest(raw) != sha:
            raise ValueError('the original ESA reservation and ledger are required')
        return json.loads(raw)

    _, groups = _groups(load('groups'), load('policy'))
    selected = {name.removesuffix('_rqh01.txt'): group['group_id'] for group in groups
                if group['role'] == 'protected_confirmation' for name in group['source_files']}
    if set(selected) != set(TARGETS) or len(set(selected.values())) != 7:
        raise ValueError('the eight receiver endpoints must match all seven reserved groups')
    return selected


def retain_acquisition(root):
    from .esa_ppp_acquisition import parse_target_listing

    listing = (root/LISTING).read_bytes()
    if digest(listing) != LISTING_SHA256:
        raise ValueError('the original ESA file listing is required')
    expected = {filename(recording): size for recording, size in TARGETS.items()}
    parse_target_listing(listing.decode().splitlines(), expected=expected)
    groups, records = expected_groups(root), {}
    for recording, size in TARGETS.items():
        name = filename(recording)
        final = root/INPUTS/name
        partial = final.with_suffix('.txt.part')
        path = final if final.is_file() else partial
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ValueError(f'complete declared receiver file required: {name}')
        stamp = sha256(path)
        _write_equal(root/INPUTS/(name+'.sha256'), (stamp+'\n').encode())
        if path == partial:
            partial.rename(final)
        records[recording] = dict(filename=name, url=BASE_URL+name, size_bytes=size, sha256=stamp,
                                  group_id=groups[recording])
    result = dict(listing_sha256=LISTING_SHA256, records=records, raw_imu_reads=0,
                  protected_outcome_reads=0, server_checksum_available=False)
    _write_equal(root/ACQUISITION, encoded(result))
    return dict(acquired=len(records), bytes=sum(TARGETS.values()), sha256=digest(encoded(result)))


def tasks():
    return [dict(identity=recording, input_key='acquisition', payload=dict(recording=recording),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=MAX_BLOCKS+1, bound_steps=MAX_EPOCHS+2))
            for recording in WORK]


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, ACCOUNTING, TIME_FORMAT, TEST,
             'analysis/tests/test_esa_confirmation_receiver_inventory.py',
             'analysis/tests/test_airquantumgrav_receiver.py')
    sources, environment = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('existing frozen inventory must be preserved')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    receipt = json.loads((root/ACQUISITION).read_bytes())
    if ({key: row['group_id'] for key, row in receipt['records'].items()} != expected_groups(root)
            or {key: row['size_bytes'] for key, row in receipt['records'].items()} != TARGETS):
        raise ValueError('all acquired receivers must match the frozen reservation')
    previous = (root/PREVIOUS_RESULT).read_bytes()
    if digest(previous) != PREVIOUS_SHA:
        raise ValueError('sealed receiver-format failure list required')
    with closing(ClosedStudy(root, 'data/'+PREVIOUS)) as study:
        for key, row in json.loads(previous)['records'].items():
            result = study.envelope(key)['result']
            if result != row['result'] or (key in WORK and result.get('reason') != 'documented receiver UTC text required'):
                raise ValueError('only previously unsupported UTC text is in scope')
            if key not in WORK and not result['passed']:
                raise ValueError('all other saved screens must already pass')
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, acquisition=ACQUISITION,
                  earlier=PREVIOUS_RESULT)
    for key, value in dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER)).items():
        name = INPUTS+key
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                      inputs=inputs, sources=sources, tasks=tasks(), workers=1, threads=1,
                                      maximum_wall_s=300), root).prepare(root)['limits']


def evaluate(task, context):
    from .airquantumgrav_inventory import decode
    from .airquantumgrav_selection import select_receiver_only
    from .ilvis0_control_shards import _check_continue

    recording = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks() or context.root.parent.name != 'data':
        raise ValueError('only the frozen receiver-only task can read a receiver export')
    reference = json.loads(context.input_path().read_bytes())['records'][recording]
    if reference['filename'] != filename(recording) or reference['size_bytes'] != TARGETS[recording]:
        raise ValueError('the declared receiver file and size are required')
    source = safe_path(context.root.parent.parent, INPUTS+filename(recording))
    if source.stat().st_size != TARGETS[recording]:
        raise ValueError('the frozen byte count differs from the acquired receiver')
    with source.open('rb') as stream:
        decoded = decode(stream, expected_sha256=reference['sha256'], maximum_epochs=MAX_EPOCHS, block_size=BLOCK_SIZE,
                         reserve=lambda decoder_calls: context.charge(bound_calls=1, bound_steps=decoder_calls),
                         check_continue=lambda: _check_continue(context.root, context.manifest))
    context.charge(bound_calls=1, bound_steps=1)
    result = select_receiver_only(decoded['rows'], receiver_integrity_verified=True)
    return dict(group_id=reference['group_id'], recording=recording, source=reference,
                receiver_epochs=result['total_receiver_epochs'], excluded_epochs=result['excluded_epochs'],
                receiver_candidates=result['receiver_candidates'], rejected_runs=result['rejected_runs'],
                exclusion_reasons=dict(Counter(reason for row in result['epoch_reasons'] for reason in row)),
                imu_support_verified=False, raw_imu_reads=0, protected_outcome_reads=0, new_fits=0,
                scientific_decision='abstain', passed=True)


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged receiver recovery policy required')
            if all(study.envelope(key)['status'] == 'complete' for key in WORK):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    from .studies.combined_task_evidence import inspect

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    selected = inspect(root, continuation)['selected'] if continuation.is_dir() else {}
    groups = expected_groups(root)
    records = {}
    with ExitStack() as stack:
        studies = {}
        for key in TARGETS:
            origin = selected.get(key, {}).get('origin', prefix if key in WORK else 'data/'+PREVIOUS)
            if origin not in studies:
                studies[origin] = stack.enter_context(closing(ClosedStudy(root, origin)))
            study = studies[origin]
            envelope = study.envelope(key)
            result = envelope.get('result') or {}
            if result.get('passed') and (result.get('group_id') != groups[key] or result.get('recording') != key
                                         or result.get('imu_support_verified') is not False or result.get('new_fits') != 0):
                raise ValueError('closed evidence differs from its reserved receiver role')
            records[key] = dict(group_id=groups[key], status=envelope['status'], charged=envelope['charged'],
                                origin=origin, manifest_sha256=study.completion['manifest_sha256'], result=result)
    passing = [row['result'] for row in records.values() if row['result'].get('passed')]
    ready = [row for row in passing if row['receiver_candidates']]
    result = dict(groups=len(set(groups.values())), files=len(records), screened_files=len(passing),
                  candidate_groups=len({row['group_id'] for row in ready}),
                  candidates=sum(len(row['receiver_candidates']) for row in ready), records=records,
                  confirmed_eligible=0, raw_imu_reads=0, protected_outcome_reads=0, new_fits=0,
                  scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key != 'records'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('retain', 'request', 'prepare', 'report', 'recover'))
    args = parser.parse_args()
    root = Path.cwd()
    actions = dict(retain=retain_acquisition, request=lambda path: qualification(path, False),
                   prepare=prepare, report=report, recover=recover)
    print(json.dumps(actions[args.action](root), sort_keys=True))
