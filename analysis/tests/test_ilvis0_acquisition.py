# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import json
from pathlib import Path
from urllib import request
import pytest
from lll.ilvis0_acquisition import (entries_from_page, filename_from_url, download_one,
                                    load_records, append_record, SafeRedirect, ScopedToken,
                                    AuthenticationRequired, initial_selection, _owned_root)
from lll.ilvis0 import screen, SCREEN_POLICY
import csv


def test_actual_download_url_selection_not_granule_name():
    links = [{'href': u, 'rel': 'http://esipfed.org/ns/fedsearch/1.1/data#'} for u in
             ('https://host/x.013', 'https://host/x.013.xml', 's3://bucket/x.013', 'https://host/a.jps', 'https://host/x.031')]
    rows = entries_from_page([dict(id='G1', producer_granule_id='misleading.jps', time_start='2009-04-14', links=links, granule_size='1.5')])
    assert len(rows) == 1 and rows[0]['filename'] == 'x.013'
    assert rows[0]['size_bytes_exact'] is None
    assert filename_from_url('https://host/path/x.013?download=true') == 'x.013'
    assert filename_from_url('https://host/path/bad%2Fx.013') is None


def test_redirects_drop_auth_and_token_is_host_scoped():
    req = request.Request('https://urs.earthdata.nasa.gov/x', headers={'Authorization': 'secret'})
    redirect = SafeRedirect().redirect_request(req, None, 302, 'found', {}, 'https://other.example/y')
    assert redirect.get_header('Authorization') is None
    assert ScopedToken('secret').https_request(redirect).get_header('Authorization') is None
    with pytest.raises(ValueError):
        SafeRedirect().redirect_request(req, None, 302, 'found', {}, 'http://other.example/y')


class Response(io.BytesIO):
    def __init__(self, data, size=None, html=False):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data) if size is None else size), 'Content-Type': 'text/html' if html else 'application/octet-stream'}
    def geturl(self):
        return 'https://data.nsidc.earthdatacloud.nasa.gov/x.013'


class Client:
    def __init__(self, data, **kwargs):
        self.data, self.kwargs, self.calls = data, kwargs, 0
    def open(self, *args, **kwargs):
        self.calls += 1
        return Response(self.data, **self.kwargs)


def row():
    return dict(filename='x.013', url='https://data.nsidc.earthdatacloud.nasa.gov/x.013', task_id='1')


def test_download_atomic_receipt_and_verified_rerun(tmp_path):
    client = Client(b'abc')
    result = download_one(row(), tmp_path, client)
    assert result['bytes'] == 3 and client.calls == 1
    assert not (tmp_path / 'x.013.partial').exists()
    assert download_one(row(), tmp_path, client)['skipped']
    assert client.calls == 1
    (tmp_path / 'x.013').write_bytes(b'bad')
    with pytest.raises(ValueError, match='unverified'):
        download_one(row(), tmp_path, client)


def test_partial_failure_and_html_never_published(tmp_path):
    with pytest.raises(RuntimeError):
        download_one(row(), tmp_path, Client(b'ab', size=5), retries=1)
    assert (tmp_path / 'x.013.partial').exists()
    assert not (tmp_path / 'x.013').exists()
    with pytest.raises(AuthenticationRequired):
        download_one(row(), tmp_path, Client(b'login', html=True))


def test_ledger_partial_recovery_and_bad_complete_line(tmp_path):
    path = tmp_path / 'records.jsonl'
    append_record(path, dict(task_id='1', state='pending'))
    with path.open('ab') as stream:
        stream.write(b'{"task_id":')
    assert load_records(path)['1']['state'] == 'pending'
    assert len(list(tmp_path.glob('*.recovery-*'))) == 1
    with path.open('ab') as stream:
        stream.write(b'bad\n')
    with pytest.raises(json.JSONDecodeError):
        load_records(path)


def test_owned_root_refuses_unfamiliar_existing_directory(tmp_path):
    with pytest.raises(ValueError, match='ownership'):
        _owned_root(tmp_path)
    assert _owned_root(tmp_path / 'new') == tmp_path / 'new'


def context_files(path, vertical=0, gps=True):
    path.mkdir()
    with (path / 'navigation.csv').open('w', newline='') as stream:
        fields = ['time1_s', 'time_types', 'alignment_status', 'velocity_north_mps', 'velocity_east_mps', 'speed_mps', 'velocity_down_mps', 'roll_deg']
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        for t in range(130):
            writer.writerow(dict(time1_s=t, time_types=2, alignment_status=0, velocity_north_mps=100, velocity_east_mps=0,
                                 speed_mps=100, velocity_down_mps=vertical, roll_deg=0))
    with (path / 'gps-fixes.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, ['time1_s'])
        writer.writeheader()
        if gps:
            writer.writerows(dict(time1_s=t) for t in range(130))
    import gzip
    with gzip.open(path / 'imu-physical.csv.gz', 'wt') as stream:
        stream.write('time1_s,raw_dtheta_x\n20,1\n')


def test_geometry_selection_does_not_need_gyro_and_unresolved_is_distinct(tmp_path):
    context_files(tmp_path / 'level')
    result = screen(tmp_path / 'level')
    assert result['state'] == 'retain' and result['windows'][0]['duration_s'] >= 60
    assert not result['earth_model_eligible']
    context_files(tmp_path / 'climb', vertical=4)
    assert screen(tmp_path / 'climb')['state'] == 'no_level_window'
    context_files(tmp_path / 'missing', gps=False)
    assert screen(tmp_path / 'missing')['state'] == 'unresolved'


def test_incomplete_gps_cannot_establish_no_level_flight(tmp_path):
    context_files(tmp_path / 'incomplete', vertical=4)
    with (tmp_path / 'incomplete' / 'gps-fixes.csv').open('w') as stream:
        stream.write('time1_s\n' + ''.join(str(t) + '\n' for t in range(65)))
    result = screen(tmp_path / 'incomplete')
    assert result['valid_context_samples'] >= 60
    assert result['state'] == 'unresolved'


def test_cmr_pagination_and_catalog_snapshot(tmp_path):
    from lll.ilvis0_acquisition import catalog
    class Pages:
        def __init__(self):
            self.calls = []
        def open(self, req, timeout=60):
            self.calls.append(req)
            if 'collections.json' in req.full_url:
                payload = dict(feed=dict(entry=[dict(id='C1', version_id='1', data_center='NSIDC_CPRD')]))
                after = None
            elif req.get_header('Cmr-search-after') is None:
                payload = dict(feed=dict(entry=[dict(id='G1', producer_granule_id='x', time_start='2009-04-14',
                    links=[dict(href='https://host/x.013', rel='http://esipfed.org/ns/fedsearch/1.1/data#')])]))
                after = 'cursor1'
            else:
                payload = dict(feed=dict(entry=[]))
                after = None
            response = Response(json.dumps(payload).encode())
            if after:
                response.headers['CMR-Search-After'] = after
            return response
    client = Pages()
    report = catalog(tmp_path / 'catalog', client=client)
    assert report['count'] == 1 and report['pages'] == 2
    assert len(client.calls) == 3
    assert (tmp_path / 'catalog' / 'catalog.csv').exists()


def test_crash_between_receipt_and_publish_recovers_without_network(tmp_path):
    from lll.ilvis0 import sha256
    partial = tmp_path / 'x.013.partial'
    partial.write_bytes(b'abc')
    (tmp_path / 'x.013.receipt.json').write_text(json.dumps(dict(url=row()['url'], bytes=3, sha256=sha256(partial))))
    client = Client(b'ignored')
    assert download_one(row(), tmp_path, client)['skipped']
    assert client.calls == 0 and (tmp_path / 'x.013').read_bytes() == b'abc'


def test_batch_retention_cleanup_and_idempotent_resume(tmp_path, monkeypatch):
    import lll.ilvis0_acquisition as acq
    from test_applanix import packet
    def fake_decode(source, destination):
        context_files(destination, vertical=4)
        report = dict(source_sha256=acq.sha256(source), validation=dict(accepted=True),
                      versions={'test': 1}, imu=dict(types={'8': 1}, rate_codes={'2': 1}))
        (destination / 'inspection.json').write_text(json.dumps(report))
        (destination / 'validation.json').write_text('{"accepted":true}')
        (destination / 'primary-gps-stream.bin.gz').write_bytes(b'')
        (destination / 'gps-sentences.csv').write_text('')
        (destination / (source.name + '.gz')).write_bytes(b'original')
        return report
    monkeypatch.setattr(acq, 'decode', fake_decode)
    item = dict(row(), date='2009-04-14', filename_instrument_tokens=[])
    catalog_file = tmp_path / 'catalog.json'
    catalog_file.write_text(json.dumps(dict(files=[item])))
    client = Client(packet(4, bytes(56)))
    root = tmp_path / 'owned'
    assert acq.batch(catalog_file, root, client=client)['states']['discarded_no_level'] == 1
    assert not (root / '1' / 'x.013').exists()
    assert not (root / '1' / 'decoded' / 'imu-physical.csv.gz').exists()
    assert (root / '1' / 'decoded' / 'screen.json').exists()
    assert (root / '1' / 'decoded' / 'inspection.json').exists()
    calls = client.calls
    acq.batch(catalog_file, root, client=client)
    assert client.calls == calls
    assert len(json.loads((root / 'inventory.json').read_text())['files']) == 1


def test_local_import_waits_without_auth_or_unrelated_directory_scan(tmp_path, monkeypatch):
    import lll.ilvis0_acquisition as acq
    item = dict(row(), date='2009-04-14', filename_instrument_tokens=[])
    catalog_file = tmp_path / 'catalog.json'
    catalog_file.write_text(json.dumps(dict(files=[item])))
    def forbidden(*args, **kwargs):
        raise AssertionError('local-only import must not access auth or network')
    monkeypatch.setattr(acq, 'opener', forbidden)
    inputs = tmp_path / 'inputs'
    inputs.mkdir()
    (inputs / 'unrelated').write_text('private')
    result = acq.batch(catalog_file, tmp_path / 'owned', input_dir=inputs, local_only=True)
    assert result['states']['pending_local_input'] == 1
    assert (inputs / 'unrelated').read_text() == 'private'


def test_configure_auth_exclusive_private_file_and_no_secret_output(tmp_path, monkeypatch, capsys):
    import lll.ilvis0_acquisition as acq
    import stat
    monkeypatch.setattr(acq.Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(acq.getpass, 'getpass', lambda *args: 'secret-test-token')
    acq.configure_auth()
    assert 'secret-test-token' not in capsys.readouterr().out
    assert stat.S_IMODE((tmp_path / '.netrc').stat().st_mode) == 0o600
    original = (tmp_path / '.netrc').read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        acq.configure_auth()
    assert (tmp_path / '.netrc').read_bytes() == original
