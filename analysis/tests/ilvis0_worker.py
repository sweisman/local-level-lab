# SPDX-License-Identifier: AGPL-3.0-or-later
"""Detached ILVIS0 acquisition worker. No simulation or Earth-model fitting.

Run with the existing venv. --session-cookie uses a hidden local terminal prompt;
credentials stay in process memory. Otherwise use the configured Earthdata .netrc.
"""
import argparse
import datetime
import fcntl
import getpass
import hashlib
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]


def compact_completed(root, records, append):
    """Drop redundant expanded tables only after originals and level rows survive."""
    for task, record in records.items():
        directory = root / task / 'decoded'
        if record['state'] != 'retained' or record.get('cleanup_pending'):
            continue
        level = directory / 'level-imu.csv.gz'
        original = directory / (record['filename'] + '.gz')
        full = directory / 'imu-physical.csv.gz'
        if not level.is_file() or not original.is_file() or not full.is_file():
            continue
        append(root / 'storage.jsonl', dict(task_id=task, artifact=full.name,
               state='redundant_full_table_removed', source_sha256=record['source_sha256'],
               retained=['compressed_original', 'level-imu.csv.gz', 'navigation.csv', 'gps-fixes.csv']))
        full.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=REPO / 'docs/ilvis0-physical-validation-20261007/catalog/catalog.json')
    parser.add_argument('--output', type=Path, default=REPO / 'data/ilvis0-ready')
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--session-cookie', action='store_true')
    args = parser.parse_args()
    root = args.output.resolve()
    if not (root / 'ownership.json').exists():
        raise ValueError('Initialize a marked corpus using the batch command first')
    # A live acquisition worker takes precedence, including legacy launchers.
    with (root / 'run.lock').open('a') as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('An ILVIS0 worker is already running; inspect status instead.')
    token = None
    if args.session_cookie:
        cookies = SimpleCookie()
        cookies.load(getpass.getpass('Earthdata session cookie (hidden): '))
        if 'edlToken' not in cookies:
            raise ValueError('No edlToken in supplied session cookie')
        token = cookies['edlToken'].value
    # Fork before numerical imports; secret is inherited in memory, never argv/files.
    if args.detach:
        pid = os.fork()
        if pid:
            print(json.dumps(dict(state='launched', pid=pid, corpus=str(root))))
            return
        os.setsid()
        log = os.open(root / 'worker.log', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        null = os.open('/dev/null', os.O_RDONLY)
        os.dup2(null, 0)
        os.dup2(log, 1)
        os.dup2(log, 2)
        os.close(null)
        os.close(log)
    for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ.setdefault(key, '2')
    sys.path.insert(0, str(REPO / 'analysis'))
    from urllib import request, parse
    from lll.ilvis0_acquisition import opener, batch, ScopedToken, URS, load_records, append_record, _atomic_json
    class SessionCookie(request.BaseHandler):
        handler_order = 480
        def https_request(self, req):
            if parse.urlsplit(req.full_url).hostname in {URS, 'data.nsidc.earthdatacloud.nasa.gov'}:
                req.add_unredirected_header('Cookie', 'edlToken=' + token)
            return req
    client = opener(auth=token is None)
    if token:
        client.add_handler(ScopedToken(token))
        client.add_handler(SessionCookie())
    _atomic_json(root / 'launch.json', dict(pid=os.getpid(), phase='full_catalog_screening' if args.full else 'compatibility_trial',
        auth='in_memory_session' if token else 'standard_earthdata_netrc',
        worker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    try:
        result = batch(args.catalog, root, full=args.full, reference=args.reference, client=client)
        if result['state'] == 'complete_selected_batch':
            compact_completed(root, load_records(root / 'records.jsonl'), append_record)
        print(json.dumps(result), flush=True)
    except Exception as exc:
        # Log exception kind only; transport exceptions can contain sensitive URLs.
        _atomic_json(root / 'status.json', dict(state='stopped_error', error=type(exc).__name__))
        print(json.dumps(dict(state='stopped_error', error=type(exc).__name__)), flush=True)


if __name__ == '__main__':
    main()
