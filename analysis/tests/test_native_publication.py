# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only tests; also runnable with --noconftest while jobs compute."""
import json
import pytest


def fixture(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards
    from lll.studies.artifacts import digest
    data=tmp_path/'data/study';public=tmp_path/'docs/study'
    data.mkdir(parents=True);public.mkdir(parents=True)
    (public/'README.md').write_text('Generated publication\n')
    (public/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={
        'README.md':digest((public/'README.md').read_bytes())})))
    paths=['shards/000/kernels/native.cpp','shards/000/kernels/native.so'];entries=[]
    for name,content in zip(paths,(b'// generated fixture\n',b'generated binary fixture')):
        path=data/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        entries.append(dict(path=name,sha256=digest(content)))
    monkeypatch.setattr(ilvis0_control_shards,'verify_completion',lambda path:{'state':'complete'})
    return data,public,entries


def test_native_publication_adds_only_explicit_closed_cache_files(tmp_path,monkeypatch):
    from pathlib import Path
    from lll.studies.native_publication import include_native_caches
    from lll.studies.artifacts import digest
    data,public,entries=fixture(tmp_path,monkeypatch)
    def forbidden(*args,**kwargs):raise AssertionError('explicit cache publication must not enumerate files')
    monkeypatch.setattr(Path,'iterdir',forbidden)
    result=include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert result['files']==2 and result['numerical_work']==0
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for entry in entries:
        assert receipt['artifacts'][entry['path']]==entry['sha256']
        assert digest((public/entry['path']).read_bytes())==entry['sha256']


def test_native_publication_validates_all_hashes_before_copying(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch);entries[-1]['sha256']='0'*64
    before=(public/'evidence-receipt.json').read_bytes()
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert not (public/entries[0]['path']).exists()
    assert (public/'evidence-receipt.json').read_bytes()==before


def test_native_publication_refuses_active_study(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch)
    def active(path):raise ValueError('not complete')
    monkeypatch.setattr(ilvis0_control_shards,'verify_completion',active)
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert not (public/'shards').exists()


@pytest.mark.parametrize('bad',['../other.so','artifacts/native.so','shards/000/kernels/unrelated.csv'])
def test_native_publication_rejects_paths_outside_declared_kernel_assets(tmp_path,monkeypatch,bad):
    from lll.studies.native_publication import include_native_caches
    data,public,_=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,
        entries=[dict(path=bad,sha256='0'*64)],maximum_bytes=1000)


def test_native_publication_never_overwrites_a_different_asset(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch);path=public/entries[0]['path']
    path.parent.mkdir(parents=True);path.write_bytes(b'different')
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert path.read_bytes()==b'different'


def test_native_publication_enforces_the_finite_byte_allowance(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1)
    assert not (public/'shards').exists()


def test_native_publication_rerun_is_identical_without_recomputing(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch)
    include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    receipt=(public/'evidence-receipt.json').read_bytes()
    include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert (public/'evidence-receipt.json').read_bytes()==receipt


def test_native_publication_rejects_duplicate_entries(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries+[entries[0]],maximum_bytes=1000)
    assert not (public/'shards').exists()


def test_native_publication_rejects_symlink_sources(tmp_path,monkeypatch):
    from lll.studies.native_publication import include_native_caches
    data,public,entries=fixture(tmp_path,monkeypatch)
    path=data/entries[0]['path'];content=path.read_bytes();path.unlink()
    other=data/'generated-source.cpp';other.write_bytes(content);path.symlink_to(other)
    with pytest.raises(ValueError):include_native_caches(tmp_path,data,public,entries=entries,maximum_bytes=1000)
    assert not (public/'shards').exists()


def test_native_publication_imports_no_numerical_library():
    import subprocess
    import sys
    result=subprocess.run([sys.executable,'-c',
        'import sys; import lll.studies.native_publication; assert "numpy" not in sys.modules; assert "scipy" not in sys.modules'],
        capture_output=True,text=True)
    assert result.returncode==0,result.stderr
