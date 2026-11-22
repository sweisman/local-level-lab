# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit only timestamp support for receiver-selected reserved ESA slices."""

import argparse
import csv
from contextlib import ExitStack, closing
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
import io
import json
from pathlib import Path
import re

from .airquantumgrav import HEADER
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
from .esa_ppp_acquisition import sha256
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-confirmation-timing-v1'
SCOPE = 'Timestamp and record framing only on seven receiver-selected reserved ESA groups'
DOCS = 'docs/external-imu-data/'
PLAN = DOCS+'ESA_CONFIRMATION_TIMING_PLAN.md'
RESULT = DOCS+ID+'-result.json'
REQUEST = DOCS+ID+'-qualification.json'
XML = DOCS+ID+'-tests.xml'
SOURCES = DOCS+'esa-live-imu-files.csv'
INVENTORY = DOCS+'esa-confirmation-receiver-inventory-v3-result.json'
INVENTORY_SHA = '5055f518e0bce4b7121f0ca591f0694ec605ac81dc123a49d14923b51f46963b'
INPUTS = 'data/esa-confirmation-timing-inputs/'
RECEIPT = INPUTS+'timing-sources.json'
ROW_BYTES = 120
RATE = 300
TICKS = 100_000_000
DURATION = 1200
GUARD = 5
MAX_BYTES = 320_000_000
MAX_GAP = 500_000
TEST = 'analysis/tests/test_esa_confirmation_timing.py'
TESTS = ('test_timing_records_require_framing_and_keep_printed_precision',
         'test_timing_gap_at_the_requested_start_is_counted',
         'test_timing_rejects_missing_bytes_and_reversed_time',
         'test_bounded_range_is_record_aligned_and_excludes_the_header')
STAMP = re.compile(rb'[ \t]*(\d{1,6})\.(\d{8})(?=[ \t])')


def timestamp(line):
    if len(line) != ROW_BYTES or not line.endswith(b'\n') or line.count(b'\n') != 1:
        raise ValueError('exact fixed-width timestamp record required')
    match = STAMP.match(line)
    if match is None or int(match[1]) >= 604800:
        raise ValueError('printed GPS seconds-of-week required')
    return int(match[1])*TICKS+int(match[2])


def range_spec(source_size, first, support):
    if source_size < 3*ROW_BYTES or source_size % ROW_BYTES:
        raise ValueError('fixed-width source size required')
    lower, upper = support
    if not first <= lower < upper < 604800*TICKS:
        raise ValueError('receiver slice must occur after the original first timestamp')
    first_row = max(1, 1+(lower-first)*RATE//TICKS-GUARD*RATE)
    last_row = min(source_size//ROW_BYTES-1, 1+((upper-first)*RATE+TICKS-1)//TICKS+GUARD*RATE)
    if last_row <= first_row:
        raise ValueError('source has no usable aligned range for the planned time')
    return first_row*ROW_BYTES, (last_row+1)*ROW_BYTES-1


def audit_stream(stream, expected_bytes, support, *, check_continue=lambda: None):
    """Check every timestamp in a bounded range without parsing sensor columns."""
    if expected_bytes < 2*ROW_BYTES or expected_bytes % ROW_BYTES:
        raise ValueError('whole-record byte count required')
    digest_state = hashlib.sha256()
    first = previous = minimum = maximum = None
    lower, upper = support
    count = inside = gaps = 0
    for line in stream:
        if count % 4096 == 0:
            check_continue()
        count += 1
        if count*ROW_BYTES > expected_bytes:
            raise ValueError('range exceeds its bounded byte count')
        stamp = timestamp(line)
        digest_state.update(line)
        inside += lower <= stamp <= upper
        if first is None:
            first = stamp
        elif stamp <= previous:
            raise ValueError('strictly increasing GPS timestamps required')
        elif stamp >= lower and previous <= upper:
            interval = stamp-previous
            minimum = interval if minimum is None else min(minimum, interval)
            maximum = interval if maximum is None else max(maximum, interval)
            gaps += interval > MAX_GAP
        previous = stamp
    if count*ROW_BYTES != expected_bytes:
        raise ValueError('the complete expected byte count is required')
    brackets = first <= lower < upper <= previous
    return dict(range_records=count, slice_records=inside, first_ticks=first, last_ticks=previous,
                slice_min_dt_ticks=minimum, slice_max_dt_ticks=maximum, slice_gap_count=gaps,
                ticks_per_second=TICKS, brackets_slice=brackets, timing_supported=brackets and gaps == 0,
                range_sha256=digest_state.hexdigest())


def selections(root):
    raw = (root/INVENTORY).read_bytes()
    if digest(raw) != INVENTORY_SHA:
        raise ValueError('the original receiver-only window report is required')
    rows = json.loads(raw)['records']
    catalogue = {r['filename']: r for r in csv.DictReader(io.StringIO((root/SOURCES).read_text()))}
    earliest = {}
    for recording, row in rows.items():
        group = row['group_id']
        for window in row['result']['receiver_candidates']:
            key = window['gps_week'], window['first_time_s'], recording
            if group not in earliest or key < earliest[group][0]:
                earliest[group] = key, window
    if len(earliest) != 7:
        raise ValueError('one receiver-selected window in each of the seven reserved groups required')
    result = {}
    for group, ((week, start, recording), window) in earliest.items():
        file = recording+'_rqh01.txt'
        entry = catalogue[file]
        directory = recording.rstrip('ab')
        url = f'ftps://tpm-if.eo.esa.int/lvl0/{directory}/rqh01/{file}'
        if entry['url'] != url or entry['downloaded'] != 'False':
            raise ValueError('only a catalogued reserved timestamp source may be examined')
        if (date.fromisoformat(entry['date'])-date(1980, 1, 6)).days//7 != week:
            raise ValueError('receiver GPS week and the catalogued file date disagree')
        cutoff = Decimal(str(start))+DURATION
        if cutoff > Decimal(str(window['last_time_s'])):
            raise ValueError('the earliest receiver window does not cover the planned slice')
        lower = int((Decimal(str(start))*TICKS).to_integral_value(rounding=ROUND_FLOOR))
        upper = int((cutoff*TICKS).to_integral_value(rounding=ROUND_CEILING))
        result[recording] = dict(group_id=group, source_file=file, source_size=int(entry['size_bytes']), url=url,
                                 gps_week=week, slice_ticks=[lower, upper])
    return result


def ranges(root, retain=False):
    result = selections(root)
    for recording, row in result.items():
        probe = (root/INPUTS/(recording+'-probe.part')).read_bytes()
        header = probe[:ROW_BYTES]
        if len(probe) != 2*ROW_BYTES or not header.endswith(b'\n') or header.decode('ascii').split() != HEADER.split():
            raise ValueError('the exact two-record probe and documented iMAR header are required')
        first = timestamp(probe[ROW_BYTES:])
        begin, end = range_spec(row['source_size'], first, row['slice_ticks'])
        row.update(first_ticks=first, probe_sha256=digest(probe), start_byte=begin, end_byte=end, bytes=end-begin+1)
    if sum(row['bytes']+2*ROW_BYTES for row in result.values()) > MAX_BYTES:
        raise ValueError('the aggregate transfer ceiling would be exceeded')
    if retain:
        for recording, row in result.items():
            original = root/INPUTS/(recording+'-range.part')
            if original.is_symlink() or original.stat().st_size != row['bytes']:
                raise ValueError(f'{recording}: expected exact byte range before freezing')
            row['sha256'] = sha256(original)
        _write_equal(root/RECEIPT, encoded(result))
        return dict(sources=len(result), bytes=sum(row['bytes'] for row in result.values()))
    return result


def tasks(receipt):
    return [dict(identity=recording, input_key='receipt', payload=dict(recording=recording),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=row['bytes']//ROW_BYTES))
            for recording, row in sorted(receipt.items())]


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, TEST)
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
        raise ValueError('retain the original timing-study allowance')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    ranges(root, retain=True)
    receipt = json.loads((root/RECEIPT).read_bytes())
    inputs = dict(plan=PLAN, inventory=INVENTORY, catalog=SOURCES, receipt=RECEIPT, qualification=REQUEST,
                  qualification_tests=XML)
    for name, value in dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER)).items():
        path = INPUTS+name
        _write_equal(root/path, value)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=tasks(receipt), workers=1, threads=1, maximum_wall_s=180)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    from .ilvis0_control_shards import _check_continue

    receipt = json.loads(context.input_path().read_bytes())
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks(receipt) or context.root.parent.name != 'data':
        raise ValueError('only the frozen timestamp range may be opened')
    recording = task['identity']
    reference = receipt[recording]
    original = safe_path(context.root.parent.parent, INPUTS+recording+'-range.part')
    if original.stat().st_size != reference['bytes']:
        raise ValueError('frozen range size was changed')
    context.charge(bound_calls=1, bound_steps=reference['bytes']//ROW_BYTES)
    with original.open('rb') as stream:
        result = audit_stream(stream, reference['bytes'], reference['slice_ticks'],
                              check_continue=lambda: _check_continue(context.root, context.manifest))
    if result['range_sha256'] != reference['sha256']:
        raise ValueError('frozen range hash was changed')
    return dict(result, source=reference, sensor_value_columns_decoded=0, new_fits=0,
                protected_outcome_reads=0, scientific_decision='abstain', passed=True)


def _origins(root):
    from .studies.combined_task_evidence import inspect

    path = 'data/'+ID
    successor = root/(path+'-recovery')
    return inspect(root, successor)['selected'] if successor.is_dir() else {}


def report(root):
    selected = _origins(root)
    prefix = 'data/'+ID
    rows = {}
    with ExitStack() as stack:
        base = stack.enter_context(closing(ClosedStudy(root, prefix)))
        stores = {prefix: base}
        receipt = base.input('receipt')
        for recording, source in receipt.items():
            origin = selected.get(recording, {}).get('origin', prefix)
            if origin not in stores:
                stores[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=base.store)))
            study = stores[origin]
            envelope = study.envelope(recording)
            result = envelope.get('result') or {}
            if result.get('passed') and (result['range_sha256'] != source['sha256'] or result['source'] != source):
                raise ValueError('timing result differs from its source binding')
            rows[recording] = dict(source=source, result=result, charged=envelope['charged'], origin=origin,
                                   manifest_sha256=study.completion['manifest_sha256'])
    outcome = dict(groups=len(rows), timing_supported=sum(r['result'].get('timing_supported', False) for r in rows.values()),
                   records=rows, new_fits=0, protected_outcome_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(outcome))
    return {key: value for key, value in outcome.items() if key != 'records'}


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    successor = root/(prefix+'-recovery')
    if not successor.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged saved timing recovery policy required')
            if all(study.envelope(key)['status'] == 'complete' for key in study.input('receipt')):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, successor, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, successor)


if __name__ == '__main__':
    commands = dict(select=selections, ranges=ranges, request=lambda root: qualification(root, False),
                    prepare=prepare, report=report, recover=recover)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=commands)
    args = parser.parse_args()
    print(json.dumps(commands[args.action](Path.cwd()), sort_keys=True))
