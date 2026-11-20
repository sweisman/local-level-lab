# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify a bounded raw RINEX window on ESA development recording 187."""

from contextlib import closing
from datetime import datetime
from decimal import Decimal
import argparse
import fcntl
import gzip
import json
from pathlib import Path
import ssl
import stat
from .esa_ftps_bounded_read import read_air1_range
from .esa_ppp_acquisition import CERTIFICATE_SHA256
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


SOURCE = 'ftps://tpm-if.eo.esa.int/lvl0/187/air1/air10706a.23o'
SIZE = 363_446_705
LISTING_SHA = '32bc29fa8507c325ee8db42d0465a2067566779eff37c92789c98ed11aa579ec'
PREFIX_SHA = '76c2817f18661effcc605e1dc618e1e63c89f62f7f899ebd6404b712bbdc0414'
MATRIX = 'data/esa-rolling-origin-400-model-matrix-20261118'
MATRIX_SHA = 'd29ecef42b37a8fffe05dbff591cf24d0720129c3792f14cd1649803a141829d'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_RINEX_WINDOW_PLAN.md'
REST_PLAN = FOLDER+'ESA_RINEX_REST_PLAN.md'
STREAM_PLAN = FOLDER+'ESA_RINEX_BOUNDED_STREAM_PLAN.md'
REPORT = FOLDER+'esa-rinex-window.json'
LOCAL = 'data/external-imu-survey-20261018/esa-sample'
GPS_EPOCH = datetime(1980, 1, 6)
WEEK = 2269
FIRST, LAST = 388214.5, 388734.5
PROBE, CHUNK = 256*1024, 1024*1024
MAX_PROBES, MAX_CHUNKS = 16, 9
OVERLAP = 128
REST_OFFSET = 51_218_772
REST_SHA = '9f8e598d7bc9fa10456adf00e29ce98cb2892cb37300adf58b9161cdeb3e1ee7'
FIRST_ATTEMPT_RANGE = '51441219-1048576.part-0'


def gps_seconds(fields):
    year, month, day, hour, minute = map(int, fields[:5])
    second = Decimal(fields[5])
    if not second.is_finite() or not 0 <= second < 60:
        raise ValueError('valid GPS observation seconds required')
    age = datetime(year, month, day, hour, minute)-GPS_EPOCH
    week, days = divmod(age.days, 7)
    if week < 0:
        raise ValueError('observation epoch predates GPS')
    return week, days*86400+age.seconds+float(second)


def read_header(raw):
    lines = raw.splitlines(keepends=True)
    first = lines[0].decode('ascii')
    if first[:9].strip() != '3.04' or first[20] != 'O' or first[60:].strip() != 'RINEX VERSION / TYPE':
        raise ValueError('expected a RINEX 3.04 observation header')
    declarations, counts, times = {}, {}, {}
    length = 0
    interval = None
    for line in lines:
        length += len(line)
        text = line.decode('ascii')
        label = text[60:].strip()
        if label == 'SYS / # / OBS TYPES':
            if text[0] != ' ':
                system = text[0]
                if system in counts:
                    raise ValueError('duplicate RINEX system declaration')
                counts[system] = int(text[3:6])
                declarations[system] = []
            declarations[system].extend(text[7:60].split())
        elif label in ('TIME OF FIRST OBS', 'TIME OF LAST OBS'):
            values = text[:60].split()
            if len(values) != 7 or values[-1] != 'GPS':
                raise ValueError('same declared GPS epoch scale required')
            times[label] = gps_seconds(values[:6])
        elif label == 'INTERVAL':
            interval = float(text[:60])
        elif label == 'END OF HEADER':
            if (set(times) != {'TIME OF FIRST OBS', 'TIME OF LAST OBS'} or interval != .5
                    or set(declarations) != {'G', 'R'} or
                    any(len(codes) != counts[k] or len(set(codes)) != counts[k]
                        for k, codes in declarations.items())):
                raise ValueError('exact AIR1 GPS/GLONASS header and cadence required')
            return raw[:length], dict(version='3.04', time_scale='GPS', interval_s=interval,
                first=times['TIME OF FIRST OBS'], last=times['TIME OF LAST OBS'],
                observation_types=declarations)
    raise ValueError('incomplete RINEX header')


def epoch_offsets(raw, *, offset):
    positions = []
    for line in raw.splitlines(keepends=True):
        if line.startswith(b'> ') and line.endswith(b'\n'):
            fields = line.decode('ascii').split()
            week, second = gps_seconds(fields[1:7])
            flag, satellites = map(int, fields[7:9])
            if positions and (week, second) <= positions[-1][1:3]:
                raise ValueError('RINEX epochs must be strictly ordered')
            positions.append((offset, week, second, flag, satellites))
        offset += len(line)
    if not positions:
        raise ValueError('no complete epoch marker in requested byte range')
    return positions


def inspect_window(raw, *, offset, first, last, observation_types):
    markers = epoch_offsets(raw, offset=offset)
    matches = [(row, following) for row, following in zip(markers, markers[1:])
               if first <= row[2] <= last]
    expected = [first+.5*i for i in range(round((last-first)*2)+1)]
    if [row[2] for row, _ in matches] != expected:
        raise ValueError('ensure complete consecutive half-second epochs through both endpoints')
    dual, tracked = [], set()
    gps = observation_types['G']
    first_band = [i for i, code in enumerate(gps) if code.startswith('C1') and 'L'+code[1:] in gps]
    second_band = [i for i, code in enumerate(gps) if code.startswith('C2') and 'L'+code[1:] in gps]
    pairs = [[(i, gps.index('L'+gps[i][1:])) for i in band] for band in (first_band, second_band)]
    for row, following in matches:
        begin, week, _, flag, count = row
        satellites = raw[begin-offset:following[0]-offset].splitlines()[1:]
        names = {line[:3] for line in satellites}
        if week != WEEK or flag != 0 or count < 1 or len(satellites) != count or len(names) != count:
            raise ValueError('complete normal observation epoch with unique satellites required')
        visible = 0
        for line in satellites:
            kind = line[:1].decode('ascii')
            if kind not in observation_types or len(line) < 3 or not line[1:3].isdigit():
                raise ValueError('unexpected RINEX satellite record in complete epoch')
            if len(line) > 3+16*len(observation_types[kind]):
                raise ValueError('too many RINEX fields in observation epoch')
            tracked.add(kind)
            if kind == 'G':
                measured = [line[3+16*i:17+16*i].strip() for i in range(len(gps))]
                visible += all(any(measured[i] and measured[j] for i, j in band) for band in pairs)
        dual.append(visible)
    begin, end = matches[0][0][0], matches[-1][1][0]
    return raw[begin-offset:end-offset], dict(epochs=len(matches), systems=sorted(tracked),
        minimum_dual_band_gps_satellites=min(dual), maximum_dual_band_gps_satellites=max(dual),
        byte_start=begin, byte_end_exclusive=end)


def _range(directory, offset, count, cert, credentials):
    if not 0 <= offset < offset+count <= SIZE or not 0 < count <= CHUNK:
        raise ValueError('bounded source byte range required')
    tag = f'{offset}-{count}'
    path, seal = directory/(tag+'.bin'), directory/(tag+'.json')
    if not seal.exists():
        request = directory/(tag+'.attempts')
        attempts = request.read_text().splitlines() if request.exists() else []
        if len(attempts) >= 3:
            raise ValueError('finite transfer retry allowance exhausted for '+tag)
        chunk = directory/(tag+f'.part-{len(attempts)}')
        with request.open('a') as ledger:
            ledger.write(chunk.name+'\n')
        data = read_air1_range(offset, count, cert, credentials)
        atomic(chunk, data)
        chunk.replace(path)
        atomic(seal, encoded(dict(offset=offset, bytes=count, sha256=digest(data))))
    data = path.read_bytes()
    receipt = dict(offset=offset, bytes=count, sha256=digest(data))
    if len(data) != count or json.loads(seal.read_bytes()) != receipt:
        raise ValueError('changed cached byte range: '+tag)
    return data, receipt


def _find_start(header, get):
    lo, hi = 0, SIZE-PROBE
    first, last = header['first'][1], header['last'][1]
    offset = round((SIZE-PROBE)*(FIRST-first)/(last-first))
    for _ in range(MAX_PROBES):
        data, _ = get(offset, PROBE)
        rows = epoch_offsets(data, offset=offset)
        if any(row[1] != WEEK for row in rows):
            raise ValueError('unexpected GPS week in source range')
        for row in rows:
            if row[2] == FIRST:
                return row[0]
        if rows[0][2] > FIRST:
            hi = offset-1
        elif rows[-1][2] < FIRST:
            lo = offset+PROBE//2
        else:
            raise ValueError('target epoch absent between verified markers')
        if not 0 <= lo <= hi:
            break
        offset = (lo+hi)//2
    raise ValueError('starting epoch not found within the finite probe allowance')


def _query_times(root):
    with closing(ClosedStudy(root, MATRIX)) as study:
        if (study.completion['manifest_sha256'] != MATRIX_SHA
                or study.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('unchanged ESA development study required')
        times = study.input('forecast_times')
        training = json.loads(gzip.decompress(study.input('training', raw=True)))
    if len(times) != 520 or len(training) != 400:
        raise ValueError('unchanged 400/120 report split required')
    epoch = training[0]['time_s']-times[0]
    queries = [epoch+t for t in times]
    if (any(abs(row['time_s']-t) > 1e-8 for row, t in zip(training, queries))
            or any(not FIRST <= q <= LAST for q in queries)):
        raise ValueError('inconsistent saved query times and raw GPS support')
    return queries


def prepare(root, prefix, rest_probe):
    base = root/LOCAL
    listing = (base/'catalog/lvl0-187-air1-list.txt').read_bytes()
    cert = base/'ftps-peer.pem'
    credentials = Path.home()/'.esa-ftps.netrc'
    if (digest(listing) != LISTING_SHA or digest(ssl.PEM_cert_to_DER_cert(cert.read_text())) != CERTIFICATE_SHA256
            or stat.S_IMODE(credentials.stat().st_mode) != 0o600):
        raise ValueError('sealed ESA source and private authentication required')
    raw_prefix = prefix.read_bytes()
    if len(raw_prefix) != PROBE or digest(raw_prefix) != PREFIX_SHA:
        raise ValueError('exact verified prefix required')
    raw_header, header = read_header(raw_prefix)
    raw_probe = rest_probe.read_bytes()
    if len(raw_probe) != PROBE or digest(raw_probe) != REST_SHA:
        raise ValueError('exact verified FTP restart probe required')
    queries = _query_times(root)
    match = [round(q*2)/2 for q in queries]
    difference = max(abs(q-t) for q, t in zip(queries, match, strict=True))
    if len(set(match)) != len(queries) or difference > .001:
        raise ValueError('one recorded RINEX epoch within one millisecond of every query required')
    work = base/'rinex-400-120-stream'
    work.mkdir(exist_ok=True)
    reads = []
    with (work/'acquire.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original_sample = (base/'rinex-400-120-rest'/FIRST_ATTEMPT_RANGE).read_bytes()
        if len(original_sample) != CHUNK:
            raise ValueError('full preceding probe bytes required')
        worker_files = [Path(__file__), Path(__file__).with_name('esa_ftps_bounded_read.py')]
        freeze = encoded(dict(source=SOURCE, source_bytes=SIZE, prefix_sha256=PREFIX_SHA,
            plan_sha256=digest((root/PLAN).read_bytes()), rest_plan_sha256=digest((root/REST_PLAN).read_bytes()),
            stream_plan_sha256=digest((root/STREAM_PLAN).read_bytes()),
            initial_freeze_sha256=digest((base/'rinex-400-120/freeze.json').read_bytes()),
            restart_freeze_sha256=digest((base/'rinex-400-120-rest/freeze.json').read_bytes()),
            preceding_range_sha256=digest(original_sample), rest_probe_sha256=REST_SHA,
            sources={p.name: digest(p.read_bytes()) for p in worker_files},
            query_sha256=digest(encoded(queries)), first=FIRST, last=LAST,
            probes=MAX_PROBES, chunks=MAX_CHUNKS))
        frozen = work/'freeze.json'
        if frozen.exists() and frozen.read_bytes() != freeze:
            raise ValueError('existing byte extraction uses a different freeze')
        atomic(frozen, freeze)
        atomic(work/'prefix.bin', raw_prefix)
        atomic(work/'restart-probe.bin', raw_probe)

        def get(offset, count):
            if (offset, count) == (REST_OFFSET, PROBE):
                raw, receipt = raw_probe, dict(offset=offset, bytes=count, sha256=REST_SHA)
            else:
                raw, receipt = _range(work, offset, count, cert, credentials)
            reads.append(receipt)
            return raw, receipt

        start = _find_start(header, get)
        chunks = []
        for i in range(MAX_CHUNKS):
            data, _ = get(start+i*(CHUNK-OVERLAP), CHUNK)
            if not i and data[:OVERLAP] != raw_probe[start-REST_OFFSET:start-REST_OFFSET+OVERLAP]:
                raise ValueError('first byte range differs from the verified restart probe')
            if not i and data != original_sample:
                raise ValueError('first byte range differs from the preceding transport')
            if i and chunks[-1][-OVERLAP:] != data[:OVERLAP]:
                raise ValueError('adjacent byte ranges disagree at their overlap')
            chunks.append(data[OVERLAP:] if i else data)
            raw = b''.join(chunks)
            if epoch_offsets(raw, offset=start)[-1][2] > LAST:
                break
        retained, info = inspect_window(raw, offset=start, first=FIRST, last=LAST,
                                        observation_types=header['observation_types'])
        payload = raw_header+retained
        atomic(work/'air10706a-400-120-excerpt.23o.gz', gzip.compress(payload, mtime=0))
        report = dict(source=SOURCE, source_bytes=SIZE, source_size_listing_sha256=LISTING_SHA,
            prefix_bytes=PROBE, prefix_sha256=PREFIX_SHA, header=header, retained=info,
            raw_excerpt_bytes=len(payload), raw_excerpt_sha256=digest(payload),
            maximum_query_epoch_delta_s=difference, matched_query_epochs=len(queries),
            query_sha256=digest(encoded(queries)), matrix_manifest_sha256=MATRIX_SHA,
            reads=reads, freeze_sha256=digest(freeze), positions_solved=0, fit_starts=0,
            rest_probe_sha256=REST_SHA, overlap_bytes=OVERLAP, scientific_decision='abstain')
        output = root/REPORT
        content = encoded(report)
        if output.exists() and output.read_bytes() != content:
            raise ValueError('existing receiver preflight report differs')
        atomic(output, content)
        print(encoded(info).decode().strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, required=True)
    parser.add_argument('--rest-probe', type=Path, required=True)
    args = parser.parse_args()
    prepare(Path.cwd(), args.prefix, args.rest_probe)
