# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the layout and relative clock of bounded GIRAFE platform log ranges."""

from contextlib import closing
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import ssl
import stat
import sys

from . import esa_direction_holdout_clock as clock
from .esa_direction_holdout_clock_score import CLOCK_SHA
from .esa_direction_holdout_forecast import frozen_input
from .esa_ftps_bounded_read import GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES, read_esa_range
from .esa_full_parallel_gnss import BASE
from .esa_ppp_acquisition import CERTIFICATE_SHA256
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-probes-v1'
SCOPE = 'verify three bounded GIRAFE platform log ranges on opened ESA 187'
PLAN = clock.forecast.selection.FOLDER+'ESA_GIRAFE_PLATFORM_PROBE_PLAN.md'
RESULT = clock.forecast.selection.FOLDER+'esa-girafe-platform-probe-result.json'
AUDIT_RESULT = clock.forecast.selection.FOLDER+'esa-girafe-platform-layout-audit.json'
PROBE_SHA = '93b134e7961afba3c2eebee2e22d01ef60b36cf388c3c254adec62c0f71981d5'
PREFIX = BASE+'/girafe-187-platform-01-prefix.asc'
PREFIX_SHA = '222235a6de00797770460d01b2aa4e04a4e73f38900268f1d830ad3129db536e'
ROW_BYTES, BLOCK = 77, 128
OFFSETS = [ROW_BYTES*(GIRAFE_SOURCE_BYTES*i//(4*ROW_BYTES)) for i in range(1, 4)]
TASK = dict(identity='girafe-logxio01-byte-ranges', input_key='flight', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=len(OFFSETS), bound_steps=len(OFFSETS)*BLOCK*ROW_BYTES))


def inspect_block(raw, first_index, *, expected_rows):
    """Check complete records and retain the exact printed-clock phase interval."""
    if (type(first_index) is not int or first_index < 0 or len(raw) != expected_rows*ROW_BYTES
            or expected_rows < 2):
        raise ValueError('exact bounded number of full platform rows required')
    return inspect_records([raw[i:i+ROW_BYTES] for i in range(0, len(raw), ROW_BYTES)], first_index)


def printed_tick(token):
    if not re.fullmatch(rb'\d{6}\.\d{4}', token):
        raise ValueError('platform time must have six integer and four fractional places')
    return int(token.replace(b'.', b''))


def inspect_records(records, first_index):
    baseline = []
    last = None
    increments = {}
    for i, record in enumerate(records):
        fields = record[:-2].split()
        if (record[-2:] != b'\r\n' or b'\r' in record[:-2] or b'\n' in record[:-2]
                or len(record) not in (ROW_BYTES, ROW_BYTES+1) or len(fields) != 7
                or not all(math.isfinite(float(value)) for value in fields[1:])):
            raise ValueError('platform row width, delimiters or numeric layout changed')
        current = printed_tick(fields[0])
        if last is not None:
            dt = current-last
            if dt <= 0:
                raise ValueError('platform time tags must increase strictly')
            increments[str(dt)] = increments.get(str(dt), 0)+1
        baseline.append(64*current-625*(first_index+i))
        last = current
    lo, hi = min(baseline), max(baseline)
    return dict(first_row=first_index, last_row=first_index+len(records)-1, rows=len(records),
                first_tag_s=(baseline[0]+625*first_index)/640000,
                last_tag_s=last/10000, step_counts_0p1ms=increments,
                phase_min_64ths_tick=lo, phase_max_64ths_tick=hi,
                local_rounding_compatible=hi-lo <= 64)


def inspect_range_fragments(raw, start_tag_tick):
    """Keep each complete row between the two acquisition-edge fragments."""
    first, *inside, last = raw.split(b'\r\n')
    if len(first) >= ROW_BYTES-2 or len(last) >= ROW_BYTES-2 or len(inside) < 2:
        raise ValueError('expected shorter partial edges and complete interior records')
    first_tick = printed_tick(inside[0].split()[0])
    clock_index = (64*(first_tick-start_tag_tick)+312)//625
    if clock_index < 0:
        raise ValueError('interior records precede the saved prefix clock')
    records = [row+b'\r\n' for row in inside]
    summary = inspect_records(records, clock_index)
    summary['first_clock_index'] = summary.pop('first_row')
    summary['last_clock_index'] = summary.pop('last_row')
    return dict(summary, leading_partial_bytes=len(first)+2, trailing_partial_bytes=len(last),
                record_width_counts=dict(Counter(str(len(row)) for row in records)),
                field_width_counts={','.join(map(str, widths)): count for widths, count in
                    Counter(tuple(map(len, row.split())) for row in records).items()})


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing platform byte probe must stay sealed')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(flight=clock.RESULT), tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_probe.py']),
        workers=1, threads=1, maximum_wall_s=150.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def connection_files(root):
    certificate = safe_path(root, BASE+'/ftps-peer.pem')
    der = ssl.PEM_cert_to_DER_cert(certificate.read_text())
    if hashlib.sha256(der).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError('trusted ESA FTPS certificate changed')
    credential = Path.home()/'.esa-ftps.netrc'
    if stat.S_IMODE(credential.stat().st_mode) != 0o600:
        raise ValueError('private ESA credential permissions required')
    return certificate, credential


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact platform byte probe task required')
    opened = frozen_input(context, 'flight', CLOCK_SHA)
    if opened['source']['group_id'] != 'esa-99f1530c3eda4318' or opened['protected_reads'] != 0:
        raise ValueError('only the opened recording 187 may be probed')
    root = context.root.parents[1]
    prefix = safe_path(root, PREFIX).read_bytes()
    if len(prefix) != 16384 or digest(prefix) != PREFIX_SHA:
        raise ValueError('exact sealed platform prefix required')
    rows = len(prefix)//ROW_BYTES
    baseline = inspect_block(prefix[:rows*ROW_BYTES], 0, expected_rows=rows)
    certificate, credential = connection_files(root)
    results = []
    for offset in OFFSETS:
        context.charge(bound_calls=1, bound_steps=ROW_BYTES*BLOCK)
        result = dict(offset=offset, bytes_requested=ROW_BYTES*BLOCK)
        try:
            raw = read_esa_range(GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES, offset, ROW_BYTES*BLOCK, certificate, credential)
        except (OSError, ValueError) as error:
            result.update(status='read_failed', error_type=type(error).__name__)
        else:
            target = safe_path(root, f'{BASE}/girafe-platform-probe-v1/range-{offset}.asc')
            if not target.exists():
                atomic(target, raw)
            if target.read_bytes() != raw:
                raise ValueError('existing range bytes differ; preserve both receipts for review')
            result.update(sha256=digest(raw), bytes_received=len(raw))
            try:
                result.update(inspect_block(raw, offset//ROW_BYTES, expected_rows=BLOCK), status='checked')
            except ValueError:
                result.update(status='invalid_row_layout')
        results.append(result)
    valid = [baseline, *(row for row in results if row['status'] == 'checked')]
    complete = len(valid) == len(OFFSETS)+1
    width = max(r['phase_max_64ths_tick'] for r in valid)-min(r['phase_min_64ths_tick'] for r in valid)
    summary = dict(prefix=baseline, probes=results, prefix_sha256=PREFIX_SHA, source_bytes=GIRAFE_SOURCE_BYTES,
                   phase_span_64ths_tick=width, filewide_sample_lattice_supported_at_probes=complete and width <= 64,
                   platform_absolute_clock_qualified=False, protected_reads=0, scientific_decision='abstain')
    context.save_bytes('probes.json', encoded(summary))
    return dict(passed=complete and all(r['local_rounding_compatible'] for r in valid), checked_ranges=len(valid)-1,
                scientific_decision='abstain')


def report(root):
    identity = TASK['identity']
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        result = study.artifact(identity, 'probes.json')
        if study.rows[identity]['charged'] != TASK['limits'] or len(result['probes']) != len(OFFSETS):
            raise ValueError('all charged byte range attempts must be retained')
        for row in result['probes']:
            if 'sha256' in row:
                saved = safe_path(root, f"{BASE}/girafe-platform-probe-v1/range-{row['offset']}.asc")
                if digest(saved.read_bytes()) != row['sha256']:
                    raise ValueError('locally saved platform range differs')
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    dest = root/RESULT
    if not dest.exists():
        atomic(dest, raw)
    if dest.read_bytes() != raw:
        raise ValueError('saved platform range summary differs')
    return dict(sha256=digest(raw), checked_ranges=sum(r['status'] == 'checked' for r in result['probes']))


def audit_saved(root):
    receipt = (root/RESULT).read_bytes()
    original = json.loads(receipt)
    if digest(receipt) != PROBE_SHA or [row['offset'] for row in original['probes']] != OFFSETS:
        raise ValueError('exact terminal byte probe receipt required')
    prefix = original['prefix']
    start_tag_tick = round(prefix['first_tag_s']*10_000)
    results = []
    for probe in original['probes']:
        offset = probe['offset']
        path = safe_path(root, f'{BASE}/girafe-platform-probe-v1/range-{offset}.asc')
        raw = path.read_bytes()
        if digest(raw) != probe['sha256'] or len(raw) != probe['bytes_requested']:
            raise ValueError('captured range differs from its original receipt')
        results.append(dict(offset=offset, sha256=probe['sha256'], **inspect_range_fragments(raw, start_tag_tick)))
    phases = [prefix, *results]
    phase_span = max(r['phase_max_64ths_tick'] for r in phases)-min(r['phase_min_64ths_tick'] for r in phases)
    raw = encoded(dict(probes=results, parent_sha256=PROBE_SHA, phase_span_64ths_tick=phase_span,
        common_relative_clock_at_probes=phase_span <= 64, absolute_clock_qualified=False,
        code_sha256=digest(Path(__file__).read_bytes()), original_reads=0, protected_reads=0,
        scientific_decision='abstain'))
    path = root/AUDIT_RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved platform layout audit differs')
    return dict(sha256=digest(raw), rows=sum(p['rows'] for p in results), phase_span_64ths_tick=phase_span)


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report, 'audit-saved': audit_saved}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
