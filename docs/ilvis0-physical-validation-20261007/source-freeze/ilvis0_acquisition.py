# SPDX-License-Identifier: AGPL-3.0-or-later
"""ILVIS0 .013 catalog, verified acquisition and resumable geometry inventory.

CMR pagination/provider lookup and authentication design derived from the
NSIDC downloader supplied by the user (nsidc-download_ILVIS0.001_2026-10-07.py).

Copyright (c) 2026 Regents of the University of Colorado
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions: The above copyright notice and this
permission notice shall be included in all copies or substantial portions of
the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import argparse
import base64
import contextlib
import csv
import datetime
import fcntl
import getpass
import hashlib
import http.cookiejar
import json
import netrc
import os
from pathlib import Path
import platform
import shutil
import ssl
import tempfile
import time
from urllib import error, parse, request

from .ilvis0 import decode, screen, inventory, sha256, write_json, SCREEN_POLICY, VALIDATION_VERSION

CMR = 'https://cmr.earthdata.nasa.gov/search/'
URS = 'urs.earthdata.nasa.gov'
DATA_HOSTS = {URS, 'data.nsidc.earthdatacloud.nasa.gov', 'n5eil01u.ecs.nsidc.org'}
OWNERSHIP = 'local-level-lab-ilvis0-v1'


class AuthenticationRequired(RuntimeError):
    pass


class SafeRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if parse.urlsplit(newurl).scheme != 'https':
            raise ValueError('refusing non-TLS redirect')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            # Never carry Authorization across a redirect; host-scoped handlers re-add it.
            redirected.remove_header('Authorization')
        return redirected


class ScopedToken(request.BaseHandler):
    handler_order = 480
    def __init__(self, token):
        self.token = token

    def https_request(self, req):
        if parse.urlsplit(req.full_url).hostname in DATA_HOSTS:
            req.add_unredirected_header('Authorization', 'Bearer ' + self.token)
        return req


class ScopedBasic(ScopedToken):
    def __init__(self, login, password):
        self.value = 'Basic ' + base64.b64encode((login + ':' + password).encode()).decode('ascii')

    def https_request(self, req):
        if parse.urlsplit(req.full_url).hostname == URS:
            req.add_unredirected_header('Authorization', self.value)
        return req


def opener(auth=False, prompt=False):
    handlers = [request.HTTPSHandler(context=ssl.create_default_context()), SafeRedirect(),
                request.HTTPCookieProcessor(http.cookiejar.CookieJar())]
    if auth:
        # Only the expressly authorized Earthdata machine entry is used. No logging.
        try:
            credentials = netrc.netrc().authenticators(URS)
        except FileNotFoundError:
            credentials = None
        if not credentials and prompt:
            credentials = (input('Earthdata username (or token): '), None, getpass.getpass('Earthdata password/token: '))
        if credentials:
            login, _, password = credentials
            if login == 'token':
                handlers.append(ScopedToken(password))
            else:
                manager = request.HTTPPasswordMgrWithDefaultRealm()
                manager.add_password(None, 'https://' + URS, login, password)
                handlers.append(ScopedBasic(login, password))
                handlers.append(request.HTTPBasicAuthHandler(manager))
    return request.build_opener(*handlers)


def configure_auth():
    """User-run, hidden token prompt; create only the explicitly requested .netrc.

    Never overwrite an existing credential file or put credentials in arguments,
    reports, logs, source archives or campaign manifests.
    """
    destination = Path.home() / '.netrc'
    if destination.exists():
        raise ValueError('A .netrc already exists; leave it intact and configure its Earthdata entry locally.')
    print('Generate a user token at https://urs.earthdata.nasa.gov/profile, then paste it at the hidden prompt.')
    token = getpass.getpass('Earthdata user token (hidden): ').strip()
    if not token or any(char.isspace() for char in token):
        raise ValueError('Empty token or unexpected whitespace')
    # Exclusive creation: another process's existing file is never overwritten.
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write('machine urs.earthdata.nasa.gov login token password ' + token + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    print('Earthdata token configured in the standard private .netrc; no token was printed.')


def _json_get(client, url):
    with client.open(request.Request(url, headers={'Accept': 'application/json'}), timeout=60) as response:
        return json.load(response), response.headers


def filename_from_url(url):
    parsed = parse.urlsplit(url)
    if parsed.scheme != 'https':
        return None
    name = parse.unquote(parsed.path.rsplit('/', 1)[-1])
    if not name.lower().endswith('.013') or '/' in name or '\\' in name or name in ('.', '..'):
        return None
    return name


def entries_from_page(entries):
    selected = []
    for entry in entries:
        seen = set()
        for link in entry.get('links', []):
            url = link.get('href', '')
            name = filename_from_url(url)
            if not name or link.get('inherited') or not link.get('rel', '').endswith('/data#') or url in seen:
                continue
            seen.add(url)
            tokens = ['atm'] if '_atm_' in name.lower() else (['lvis'] if '_lvis_' in name.lower() else [])
            size = entry.get('granule_size')
            selected.append(dict(filename=name, url=url, date=entry.get('time_start', '')[:10],
                                 producer_granule_id=entry.get('producer_granule_id'),
                                 granule_id=entry.get('id'), size_mib_reported=float(size) if size else None,
                                 size_bytes_exact=None, filename_instrument_tokens=tokens,
                                 task_id=hashlib.sha256((entry.get('id', '') + '\n' + url).encode()).hexdigest()[:20]))
    return selected


def catalog(output, start='2009-04-14', end='2017-09-20', client=None):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    client = client or opener()
    data, _ = _json_get(client, CMR + 'collections.json?' + parse.urlencode({'short_name': 'ILVIS0', 'page_size': 20}))
    collections = [e for e in data['feed']['entry'] if str(e.get('version_id')) in ('1', '001')]
    if len(collections) != 1:
        raise ValueError('ambiguous ILVIS0 version 1 collection')
    collection = collections[0]
    query = {'collection_concept_id': collection['id'], 'page_size': 2000,
             'temporal': f'{start}T00:00:00Z,{end}T23:59:59Z',
             'producer_granule_id[]': '*.013', 'options[producer_granule_id][pattern]': 'true',
             'sort_key[]': ['start_date', 'producer_granule_id']}
    url = CMR + 'granules.json?' + parse.urlencode(query, doseq=True)
    rows, pages, after, visited, extensions = [], 0, None, set(), {}
    while True:
        headers = {'Accept': 'application/json'}
        if after:
            headers['CMR-Search-After'] = after
        with client.open(request.Request(url, headers=headers), timeout=60) as response:
            page = json.load(response)
            next_after = response.headers.get('CMR-Search-After')
        entries = page['feed']['entry']
        pages += 1
        for entry in entries:
            for link in entry.get('links', []):
                if link.get('rel', '').endswith('/data#'):
                    extension = Path(parse.urlsplit(link.get('href', '')).path).suffix.lower()
                    extensions[extension] = extensions.get(extension, 0) + 1
        rows.extend(entries_from_page(entries))
        if not entries or not next_after:
            break
        if next_after in visited:
            raise ValueError('CMR pagination repeated a cursor')
        visited.add(next_after)
        after = next_after
    # De-duplicate identical downloadable URLs; filename alone is not an identity.
    rows = list({row['url']: row for row in rows}.values())
    rows.sort(key=lambda row: (row['date'], row['filename'], row['task_id']))
    report = dict(version=OWNERSHIP, dataset='ILVIS0.001', collection_id=collection['id'],
                  provider=collection.get('data_center'), query=query, pages=pages,
                  observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  count=len(rows), known_reported_mib=sum(row['size_mib_reported'] or 0 for row in rows),
                  size_warning='CMR granule_size is rounded MiB, not an exact byte length',
                  downloadable_link_extensions_in_query=extensions, files=rows,
                  acquisition_sha256=sha256(Path(__file__)))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.catalog-', dir=output.parent) as temp:
        stage = Path(temp)
        write_json(stage / 'catalog.json', report)
        with (stage / 'catalog.csv').open('x', newline='') as stream:
            fields = ['task_id', 'filename', 'date', 'url', 'size_mib_reported', 'size_bytes_exact',
                      'producer_granule_id', 'granule_id', 'filename_instrument_tokens']
            writer = csv.DictWriter(stream, fields)
            writer.writeheader()
            writer.writerows(rows)
        stage.rename(output)
    return report


def _atomic_json(path, value):
    temp = Path(str(path) + '.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def download_one(row, directory, client, retries=3):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if filename_from_url(row['url']) != row['filename']:
        raise ValueError('catalog filename/URL mismatch')
    destination = directory / row['filename']
    receipt = directory / (row['filename'] + '.receipt.json')
    partial = directory / (row['filename'] + '.partial')
    if not destination.exists() and receipt.exists() and partial.exists():
        recovered = json.loads(receipt.read_text())
        if (recovered['url'] == row['url'] and partial.stat().st_size == recovered['bytes']
                and sha256(partial) == recovered['sha256']):
            partial.replace(destination)
    if destination.exists() and receipt.exists():
        record = json.loads(receipt.read_text())
        if (record['url'] == row['url'] and destination.stat().st_size == record['bytes']
                and sha256(destination) == record['sha256']):
            return dict(record, skipped=True)
    if destination.exists():
        raise ValueError('existing unverified file; refusing overwrite')
    for attempt in range(retries):
        try:
            with client.open(row['url'], timeout=60) as response:
                if parse.urlsplit(response.geturl()).hostname == URS or 'text/html' in response.headers.get('Content-Type', ''):
                    raise AuthenticationRequired('Earthdata login required; no downloaded HTML accepted')
                expected = response.headers.get('Content-Length')
                digest, size = hashlib.sha256(), 0
                with partial.open('wb') as stream:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        stream.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                if not size or (expected is not None and size != int(expected)):
                    raise IOError('incomplete download')
            # Scientific framing is checked by decode, not assumed from HTTP success.
            record = dict(url=row['url'], bytes=size, sha256=digest.hexdigest(), task_id=row['task_id'])
            _atomic_json(receipt, record)
            partial.replace(destination)
            return record
        except error.HTTPError as exc:
            if exc.code in (401, 403):
                raise AuthenticationRequired('Earthdata authorization rejected') from None
            if exc.code not in (408, 429, 500, 502, 503, 504):
                raise RuntimeError(f'download HTTP {exc.code}') from None
        except AuthenticationRequired:
            raise
        except (OSError, error.URLError, IOError):
            pass
        if attempt + 1 < retries:
            time.sleep(min(2 ** attempt, 4))
    raise RuntimeError('download failed after individual retries; partial preserved')


def append_record(path, record):
    with Path(path).open('a') as stream:
        stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def load_records(path):
    records = {}
    if not Path(path).exists():
        return records
    # A partial final append is quarantined before repair; complete bad lines fail.
    with Path(path).open('rb+') as stream:
        offset = 0
        for line in stream:
            if not line.endswith(b'\n'):
                recovery = Path(str(path) + '.recovery-' + str(time.time_ns()))
                recovery.write_bytes(line)
                stream.truncate(offset)
                os.fsync(stream.fileno())
                break
            row = json.loads(line)
            records[row['task_id']] = row
            offset += len(line)
    return records


def initial_selection(rows, limit=6):
    """One known sample, explicit stream tokens, then deterministic date diversity."""
    selected = []
    reference = [r for r in rows if r['filename'] == 'ILVIS0_gyro_54935_atm_applanix_14Apr09.013']
    selected.extend(reference[:1])
    for token in ('atm', 'lvis', None):
        candidates = [r for r in rows if r not in selected and
                      ((token in r['filename_instrument_tokens']) if token else not r['filename_instrument_tokens'])]
        if candidates:
            selected.append(candidates[-1])
    while len(selected) < min(limit, len(rows)):
        dates = [datetime.date.fromisoformat(r['date']).toordinal() for r in selected]
        remaining = [r for r in rows if r not in selected]
        chosen = max(remaining, key=lambda r: min(abs(datetime.date.fromisoformat(r['date']).toordinal() - d) for d in dates))
        selected.append(chosen)
    return selected[:limit]


def _owned_root(root):
    root = Path(root)
    marker = root / 'ownership.json'
    if not root.exists():
        root.mkdir(parents=True)
        _atomic_json(marker, {'owner': OWNERSHIP})
    if not marker.exists() or json.loads(marker.read_text()).get('owner') != OWNERSHIP:
        raise ValueError('refusing existing directory without pipeline ownership marker')
    return root


def finalize_cleanup(directory, record):
    """Only pipeline-owned, fixed artifact names. Idempotent after interruptions."""
    decoded = directory / 'decoded'
    if record['state'] != 'retained':
        for artifact in ('imu-physical.csv.gz', 'navigation.csv', 'primary-gps-stream.bin.gz', 'gps-sentences.csv', 'gps-fixes.csv'):
            (decoded / artifact).unlink(missing_ok=True)
        if not record.get('quarantine_exemplar'):
            (decoded / (record['filename'] + '.gz')).unlink(missing_ok=True)
    (directory / record['filename']).unlink(missing_ok=True)


def batch(catalog_path, root, full=False, prompt=False, reference=None, client=None, input_dir=None, local_only=False):
    """Single-file-at-a-time worker; all entries tracked, failures never hidden."""
    root = _owned_root(root)
    with (root / 'run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('another ILVIS0 worker owns the corpus') from None
        manifest = dict(catalog_sha256=sha256(catalog_path), acquisition_sha256=sha256(Path(__file__)),
                        decoder_sha256=sha256(Path(__file__).with_name('ilvis0.py')),
                        parser_sha256=sha256(Path(__file__).with_name('applanix.py')),
                        python=platform.python_version(), numpy=__import__('numpy').__version__,
                        numerical_threads={key: os.environ.get(key) for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS')},
                        validation_version=VALIDATION_VERSION,
                        screen_policy=SCREEN_POLICY)
        freeze = root / 'manifest.json'
        if freeze.exists() and json.loads(freeze.read_text()) != manifest:
            raise ValueError('corpus source/configuration/catalog mismatch; use a separate owned corpus')
        if not freeze.exists():
            _atomic_json(freeze, manifest)
        rows = json.loads(Path(catalog_path).read_text())['files']
        ledger = root / 'records.jsonl'
        records = load_records(ledger)
        for row in rows:
            if row['task_id'] not in records:
                record = dict(task_id=row['task_id'], state='pending', **{k: row[k] for k in ('filename', 'date', 'url')})
                append_record(ledger, record)
                records[row['task_id']] = record
        _atomic_json(root / 'inventory.json', dict(catalog_count=len(rows), files=list(records.values())))
        accepted_dates = {r['date'] for r in records.values() if r.get('physical_accepted')}
        if full and len(accepted_dates) < 2:
            raise ValueError('full acquisition requires independently accepted .013 files on at least two dates; run initial batch first')
        selected = rows if full else initial_selection(rows)
        client = client or (None if local_only else opener(auth=True, prompt=prompt))
        config_exemplars = {r['configuration'] for r in records.values() if r.get('quarantine_exemplar')}
        for row in selected:
            # A running worker must never silently mix a source/configuration edit.
            if sha256(Path(__file__)) != manifest['acquisition_sha256'] or any(
                    sha256(Path(__file__).with_name(name + '.py')) != manifest[key]
                    for name, key in (('ilvis0', 'decoder_sha256'), ('applanix', 'parser_sha256'))):
                _atomic_json(root / 'status.json', dict(state='stopped_source_change'))
                raise RuntimeError('source changed during acquisition; corpus stopped')
            task = row['task_id']
            previous = records[task]
            if previous['state'] in ('retained', 'discarded_no_level', 'unresolved', 'invalid_input'):
                if previous.get('cleanup_pending'):
                    finalize_cleanup(root / task, previous)
                    previous['cleanup_pending'] = False
                    append_record(ledger, previous)
                continue
            directory = root / task
            directory.mkdir(exist_ok=True)
            _atomic_json(root / 'status.json', dict(state='running', task_id=task, filename=row['filename'], pid=os.getpid()))
            record = dict(task_id=task, filename=row['filename'], date=row['date'], url=row['url'])
            try:
                source = directory / row['filename']
                supplied = None
                if reference is not None and row['filename'] == Path(reference).name:
                    supplied = Path(reference)
                elif input_dir is not None:
                    # Check catalog filenames only. Never enumerate unrelated Downloads.
                    candidate = Path(input_dir) / row['filename']
                    if candidate.is_symlink():
                        raise ValueError('refusing symlink for a supplied input')
                    if candidate.is_file():
                        if sum(other['filename'] == row['filename'] for other in rows) != 1:
                            raise ValueError('ambiguous catalog filename for local import')
                        supplied = candidate
                if supplied is not None and not source.exists():
                    # Copy explicitly supplied input; never delete the user's original.
                    shutil.copyfile(supplied, source)
                    receipt = dict(task_id=task, url=row['url'], bytes=source.stat().st_size,
                                   sha256=sha256(source), acquisition='catalog_selected_local_input')
                    _atomic_json(directory / (row['filename'] + '.receipt.json'), receipt)
                if local_only and not source.exists():
                    record['state'] = 'pending_local_input'
                    append_record(ledger, record)
                    records[task] = record
                    continue
                receipt = download_one(row, directory, client)
                record.update(source_sha256=receipt['sha256'], source_bytes=receipt['bytes'])
                write_json(directory / 'framing-inventory.json', inventory(source))
                decoded = directory / 'decoded'
                if decoded.exists():
                    report = json.loads((decoded / 'inspection.json').read_text())
                    if report['source_sha256'] != receipt['sha256']:
                        raise ValueError('decoded source hash mismatch')
                else:
                    report = decode(source, decoded)
                screening = json.loads((decoded / 'screen.json').read_text()) if (decoded / 'screen.json').exists() else screen(decoded)
                configuration = json.dumps([report['versions'], report['imu']['types'], report['imu']['rate_codes']], sort_keys=True)
                record.update(source_sha256=receipt['sha256'], source_bytes=receipt['bytes'], configuration=configuration,
                              physical_accepted=report['validation']['accepted'], screen_state=screening['state'],
                              windows=screening['windows'], earth_model_eligible=False)
                if screening['state'] == 'retain':
                    record['state'] = 'retained'
                else:
                    record['state'] = 'discarded_no_level' if screening['state'] == 'no_level_window' else 'unresolved'
                    # Latest user policy: keep ALL unresolved originals, not only exemplars.
                    exemplar = screening['state'] == 'unresolved'
                    record['quarantine_exemplar'] = exemplar
                    if exemplar:
                        config_exemplars.add(configuration)
                # Retained originals live compressed; no redundant uncompressed copy.
                append_record(ledger, dict(record, cleanup_pending=True))
                finalize_cleanup(directory, record)
                record['cleanup_pending'] = False
            except AuthenticationRequired:
                record['state'] = 'authentication_required'
                append_record(ledger, record)
                records[task] = record
                _atomic_json(root / 'inventory.json', dict(catalog_count=len(rows), files=list(records.values())))
                _atomic_json(root / 'status.json', dict(state='paused_authentication', task_id=task))
                return dict(state='paused_authentication', task_id=task)
            except ValueError as exc:
                record.update(state='invalid_input', error=str(exc))
                # Unknown layouts are not evidence that a flight lacked level motion.
                if 'unsupported' in str(exc):
                    record['state'] = 'unresolved'
                # Latest retention policy preserves uncertain configurations for review.
                quarantine_id = 'invalid:' + str(exc).split(' at ')[0]
                exemplar = True
                record.update(configuration=quarantine_id, quarantine_exemplar=exemplar)
                if exemplar:
                    config_exemplars.add(quarantine_id)
                    # Compression without reinterpretation; user's originals never removed.
                    source = directory / row['filename']
                    if source.exists():
                        import gzip
                        with source.open('rb') as src, (directory / (row['filename'] + '.quarantine.gz')).open('wb') as raw:
                            with gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as dst:
                                shutil.copyfileobj(src, dst, 1024 * 1024)
                        append_record(ledger, dict(record, cleanup_pending=True))
                        finalize_cleanup(directory, record)
                        record['cleanup_pending'] = False
                else:
                    append_record(ledger, dict(record, cleanup_pending=True))
                    finalize_cleanup(directory, record)
                    record['cleanup_pending'] = False
            except (OSError, RuntimeError) as exc:
                record.update(state='failed', error=type(exc).__name__)
            append_record(ledger, record)
            records[task] = record
            _atomic_json(root / 'inventory.json', dict(catalog_count=len(rows),
                                                     files=sorted(records.values(), key=lambda r: (r['date'], r['task_id']))))
        state_counts = {}
        for record in records.values():
            state_counts[record['state']] = state_counts.get(record['state'], 0) + 1
        summary = dict(state='complete_selected_batch', catalog_count=len(rows), selected_count=len(selected),
                       states=state_counts, source_environment_frozen=True,
                       earth_shape_status='blocked: unresolved independent processing/orientation; no Earth-model fit run')
        _atomic_json(root / 'status.json', summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('configure-auth', help='User-run hidden token prompt; exclusively create standard private .netrc')
    p = sub.add_parser('catalog')
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--start', default='2009-04-14')
    p.add_argument('--end', default='2017-09-20')
    p.add_argument('--quiet', action='store_true', help='write full catalog but print totals only')
    p = sub.add_parser('download')
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--filename', required=True)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--prompt', action='store_true')
    p = sub.add_parser('batch')
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--output', type=Path, default=Path('data/ilvis0'))
    p.add_argument('--reference', type=Path)
    p.add_argument('--input-dir', type=Path, help='Read exact catalog filenames only; never scan the directory')
    p.add_argument('--local-only', action='store_true', help='Import available catalog files without network/authentication')
    p.add_argument('--full', action='store_true')
    p.add_argument('--prompt', action='store_true')
    args = parser.parse_args()
    if args.command == 'configure-auth':
        configure_auth()
    elif args.command == 'catalog':
        result = catalog(args.output, args.start, args.end)
        if not args.quiet:
            for row in result['files']:
                print(f"{row['date']} {row['filename']} {row['size_mib_reported']} MiB {row['url']}")
        print(json.dumps(dict(count=result['count'], known_reported_mib=result['known_reported_mib'])))
    elif args.command == 'download':
        rows = [r for r in json.loads(args.catalog.read_text())['files'] if r['filename'] == args.filename]
        if len(rows) != 1:
            raise ValueError('filename is absent or ambiguous; use catalog identity')
        result = download_one(rows[0], args.output, opener(auth=True, prompt=args.prompt))
        print(json.dumps(dict(bytes=result['bytes'], sha256=result['sha256'], skipped=result.get('skipped', False))))
    else:
        print(json.dumps(batch(args.catalog, args.output, args.full, args.prompt, args.reference,
                               input_dir=args.input_dir, local_only=args.local_only)))


if __name__ == '__main__':
    main()
