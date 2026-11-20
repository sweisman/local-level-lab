# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, resumable FTPS acquisition of two parallel PPP exports on ESA 187."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import ssl
import stat
import subprocess
import time


TARGETS = {
    '187_mosaic03_ppp_5Hz_final.txt': 54_289_492,
    '187_pwrpak7_ppp_1Hz_final.txt': 10_770_706,
}
LISTING_SHA256 = '31a243814ab7ecd57f79617ae174c21040bcfaadf782cf13680cee2ed85251f1'
CERTIFICATE_SHA256 = '6338eec248edb8b99174b41ce90c8153028f939935e5e1b27070c4a4dd806d4c'
BASE_URL = 'ftps://tpm-if.eo.esa.int/lvl1/gnss/'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def parse_target_listing(lines):
    found = {}
    for line in lines:
        fields = line.split(maxsplit=8)
        if len(fields) != 9 or not fields[0].startswith('-'):
            raise ValueError('regular-file ESA GNSS listing required')
        name = fields[8]
        if name not in TARGETS:
            continue
        if name in found:
            raise ValueError('unique target names required')
        size = int(fields[4])
        if size != TARGETS[name]:
            raise ValueError('target size differs from frozen listing')
        found[name] = size
    if found != TARGETS:
        raise ValueError('both frozen target names required')
    return found


def verify_complete(path, expected_size, receipt):
    path = Path(path)
    if path.stat().st_size != expected_size or receipt.get('size_bytes') != expected_size:
        raise ValueError('completed target size differs')
    digest = sha256(path)
    if digest != receipt.get('sha256'):
        raise ValueError('completed target hash differs')
    return digest


def _save(path, value):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
    os.replace(temporary, path)


def _environment(base):
    listing = base / 'catalog/lvl1-gnss-list.txt'
    if sha256(listing) != LISTING_SHA256:
        raise ValueError('saved ESA GNSS listing hash differs')
    parse_target_listing(listing.read_text().splitlines())
    certificate = base / 'ftps-peer.pem'
    der = ssl.PEM_cert_to_DER_cert(certificate.read_text())
    if hashlib.sha256(der).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError('explicitly trusted FTPS certificate changed')
    credentials = Path.home() / '.esa-ftps.netrc'
    if stat.S_IMODE(credentials.stat().st_mode) != 0o600:
        raise ValueError('private ESA credential permissions required')
    return certificate, credentials


def acquire_one(base, name, certificate, credentials):
    if name not in TARGETS:
        raise ValueError('only the two frozen ESA-187 GNSS targets are allowed')
    size = TARGETS[name]
    target = base / name
    partial = base / (name+'.part')
    receipt_path = base / (name+'.receipt.json')
    status_path = base / (name+'.status.json')
    lock_path = base / (name+'.lock')
    with lock_path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if target.exists():
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                verify_complete(target, size, receipt)
                return dict(name=name, state='already_verified', sha256=receipt['sha256'])
            if target.stat().st_size != size:
                raise ValueError('existing original size differs; preserve for review')
            digest = sha256(target)
            receipt = dict(name=name, state='complete', size_bytes=size,
                           sha256=digest, listing_sha256=LISTING_SHA256,
                           recovered_complete_file_without_receipt=True,
                           server_checksum_available=False)
            _save(receipt_path, receipt)
            _save(status_path, receipt)
            return dict(name=name, state='receipt_recovered', sha256=digest)
        if partial.exists() and partial.stat().st_size > size:
            raise ValueError('partial target exceeds frozen byte size')
        started = time.time()
        url = BASE_URL + name
        _save(status_path, dict(name=name, state='downloading',
                                url=url, expected_size_bytes=size,
                                partial_file=partial.name,
                                started_unix_s=started))
        command = ['curl', '--fail', '--silent', '--show-error',
                   '--connect-timeout', '20', '--max-time', '900',
                   '--retry', '2', '--retry-delay', '5', '--retry-all-errors',
                   '--continue-at', '-', '--max-filesize', str(size),
                   '--proto', '=ftps', '--cacert', str(certificate),
                   '--netrc-file', str(credentials), url, '-o', str(partial)]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL,
                                   check=False)
        received = partial.stat().st_size if partial.exists() else 0
        if completed.returncode or received != size:
            failure = dict(name=name, state='incomplete',
                           curl_returncode=completed.returncode,
                           received_bytes=received, expected_size_bytes=size,
                           elapsed_s=time.time()-started,
                           partial_preserved=True)
            _save(status_path, failure)
            return failure
        digest = sha256(partial)
        os.replace(partial, target)
        receipt = dict(name=name, state='complete', url=url,
                       size_bytes=size, sha256=digest,
                       listing_sha256=LISTING_SHA256,
                       certificate_sha256=CERTIFICATE_SHA256,
                       server_checksum_available=False,
                       elapsed_s=time.time()-started,
                       source_sha256=sha256(Path(__file__)))
        _save(receipt_path, receipt)
        _save(status_path, receipt)
        return dict(name=name, state='complete', sha256=digest)


def acquire(root):
    base = Path(root).resolve() / 'data/external-imu-survey-20261018/esa-sample'
    certificate, credentials = _environment(base)
    return [acquire_one(base, name, certificate, credentials) for name in TARGETS]


if __name__ == '__main__':
    results = acquire('.')
    print(json.dumps(results, sort_keys=True))
