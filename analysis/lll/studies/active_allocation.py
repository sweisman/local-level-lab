# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fast conservative thread accounting from registered live study locks."""

import fcntl
import json
from pathlib import Path
import subprocess
import sys


def register(root, *, name, path):
    """Expose a prepared project study to the canonical status registry."""
    from .artifacts import atomic, encoded

    root = Path(root).resolve()
    target = (root/path).resolve()
    if (not isinstance(name, str) or not name or
            not isinstance(path, str) or not path.startswith('data/') or
            not target.is_relative_to(root/'data') or
            not (target/'manifest.json').is_file()):
        raise ValueError('prepared named data/ study required')
    registry = root/'analysis/study-status.json'
    lock = root/'analysis/study-status.lock'
    with lock.open('a+b') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        value = json.loads(registry.read_bytes())
        if not isinstance(value.get('studies'), list):
            raise ValueError('canonical status registry required')
        existing = [item for item in value['studies']
                    if item.get('path') == path]
        if len(existing) > 1:
            raise ValueError('duplicate registered study')
        if existing:
            return False
        value['studies'].insert(0, dict(name=name, path=path))
        atomic(registry, encoded(value))
        return True


def _held(path):
    try:
        stream = path.open('rb')
    except FileNotFoundError:
        return False
    with stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        else:
            fcntl.flock(stream, fcntl.LOCK_UN)
            return False


def active_paths(root):
    """Return registered paths with a held study or shard lease.

    Archived result ledgers are intentionally skipped here. The canonical
    targeted status command verifies each returned path before allocation.
    """
    root = Path(root).resolve()
    registry = json.loads((root/'analysis/study-status.json').read_bytes())
    entries = registry.get('studies')
    if not isinstance(entries, list):
        raise ValueError('canonical data study registry required')
    found = []
    seen = set()
    for entry in entries:
        name = entry.get('path') if isinstance(entry, dict) else None
        if not isinstance(name, str) or not name.startswith('data/'):
            raise ValueError('registered study must be inside data/')
        path = (root/name).resolve()
        if not path.is_relative_to(root/'data'):
            raise ValueError('registered study must be inside data/')
        if name in seen:
            continue
        seen.add(name)
        if not path.is_dir():
            continue
        held = _held(path/'worker.lock')
        shards = path/'shards'
        if shards.is_dir():
            held = held or any(_held(lock)
                               for lock in shards.glob('*/worker.lock'))
        if held:
            found.append(name)
    return found


def _targeted_status(root, path):
    result = subprocess.run(
        [sys.executable, str(root/'analysis/status.py'),
         '--study', path, '--json'], cwd=root,
        capture_output=True, text=True, timeout=60, check=False)
    if result.returncode not in (0, 1):
        raise ValueError('targeted canonical status check failed')
    report = json.loads(result.stdout)
    if (report.get('warnings') or len(report.get('studies', [])) != 1):
        raise ValueError('targeted canonical status warning')
    return report['studies'][0]


def other_threads(root, *, workers, status_reader=None):
    """Reserve room for a new one-thread-per-worker job, or fail closed."""
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError('one to four requested workers required')
    root = Path(root).resolve()
    read = status_reader or (lambda path: _targeted_status(root, path))
    observed = 0
    for path in active_paths(root):
        report = read(path)
        if (report.get('warnings') or report.get('state') == 'invalid' or
                type(report.get('threads')) is not int or
                not 0 <= report['threads'] <= 4):
            raise ValueError('active canonical status is ambiguous')
        observed += report['threads']
    if observed + workers > 4:
        raise ValueError('other numerical jobs exhaust the four-thread allocation')
    return observed
