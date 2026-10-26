# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path


def resolver():
    path=Path(__file__).with_name('public_fixtures.py')
    assert path.exists(), 'public frozen-fixture resolver is missing'
    import importlib.util
    spec=importlib.util.spec_from_file_location('public_fixture_checks',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_only_documented_runtime_reads_are_mapped_to_public_copies(tmp_path):
    module=resolver();root=tmp_path/'checkout';root.mkdir()
    remap=module.public_read_path(root,recorded_root=Path('/site/repo/local-level-lab'))
    assert remap(root/'data/ilvis0-last-time-profile-20261018/manifest.json')==root/'docs/ilvis0-last-time-profile-20261018/manifest.json'
    assert remap('/site/repo/local-level-lab/analysis/lll/ilvis0_shape.py')==root/'analysis/lll/ilvis0_shape.py'
    assert remap('/unrelated/private/file')=='/unrelated/private/file'
    assert remap(4)==4


def test_interrupted_manifest_uses_exact_later_snapshot(tmp_path):
    module=resolver();remap=module.public_read_path(tmp_path)
    name='data/ilvis0-boundary-diagnostic-20261016/manifest.json'
    assert remap(tmp_path/name)==tmp_path/'docs/ilvis0-last-zero-boundary-20261018/source-freeze'/name


def test_historical_library_reads_use_declared_snapshot_not_current_source(tmp_path):
    root=tmp_path/'checkout';source='analysis/lll/ilvis0_estimator.py'
    current=root/source;current.parent.mkdir(parents=True);current.write_text('new version')
    freeze=root/'docs/study/source-freeze';saved=freeze/source
    saved.parent.mkdir(parents=True);saved.write_text('original version')
    remap=resolver().public_read_path(root,source_freeze=freeze)
    assert remap(root/source)==saved
    assert remap('/unrelated/private/file')=='/unrelated/private/file'


def test_write_modes_are_not_redirected(tmp_path):
    module=resolver();calls=[]
    def original(path,mode='r',*args,**kwargs):calls.append((path,mode));return 'opened'
    wrapped=module.read_adapter(original,lambda p:tmp_path/'published')
    assert wrapped(tmp_path/'runtime','rb')=='opened'
    assert calls[-1]==(tmp_path/'published','rb')
    for mode in ('wb','a','r+','xb'):
        wrapped(tmp_path/'runtime',mode)
        assert calls[-1]==(tmp_path/'runtime',mode)


def test_source_aliases_keep_original_hashes_and_paths(tmp_path):
    module=resolver();key='/site/repo/local-level-lab/analysis/lll/ilvis0_shape.py';values={key:'original-hash'}
    aliased=module.source_aliases(tmp_path,values)
    assert aliased[key]=='original-hash'
    assert aliased[str(tmp_path/'analysis/lll/ilvis0_shape.py')]=='original-hash'
    assert values=={key:'original-hash'}


def test_generated_prerequisites_always_use_named_public_copies(tmp_path):
    module = resolver()
    remap = module.generated_read_path(tmp_path)
    for runtime, public in module.GENERATED_RUNTIME_COPIES.items():
        path = tmp_path / 'data' / runtime / 'manifest.json'
        path.parent.mkdir(parents=True)
        path.write_text('local runtime must not mask missing CI fixtures')
        assert remap(path) == tmp_path / 'docs' / public / 'manifest.json'
    assert remap(tmp_path / 'data/unrelated/file') == tmp_path / 'data/unrelated/file'
    assert remap('/unrelated/private/file') == '/unrelated/private/file'
    assert remap(3) == 3


def test_production_worker_still_rejects_environment_mismatch(tmp_path, monkeypatch):
    import builtins
    import io
    import pytest
    import ilvis0_acceleration_cover_worker as worker
    monkeypatch.setattr(worker, 'DATA', tmp_path / 'new-study')
    monkeypatch.setattr(worker.base, 'environment', lambda: {'environment': 'mismatch'})
    module=resolver();root=Path(__file__).resolve().parents[2]
    with module.archived_read_path(root,tmp_path/'fixtures') as remap:
        monkeypatch.setattr(builtins,'open',module.read_adapter(builtins.open,remap))
        monkeypatch.setattr(io,'open',module.read_adapter(io.open,remap))
        with pytest.raises(ValueError, match='environment changed'):
            worker.prepare()
    assert not worker.DATA.exists()


def frozen_worker_checkout(tmp_path):
    import hashlib,json
    root=tmp_path/'checkout';public=root/'docs/example-controls'
    sources={'analysis/lll/__init__.py':b'',
        'analysis/lll/example_math.py':b'value=17\n',
        'analysis/tests/example_worker.py':
            b'from pathlib import Path\nfrom lll import example_math\nROOT=Path(__file__).resolve().parents[2]\n'}
    hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in sources.items()}
    for name,raw in sources.items():
        path=public/'source-freeze'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    raw=json.dumps(dict(sources=hashes,environment={'frozen':True})).encode()
    (public/'manifest.json').write_bytes(raw)
    (public/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={'manifest.json':hashlib.sha256(raw).hexdigest()})))
    current=root/'analysis/lll/example_math.py';current.parent.mkdir(parents=True);current.write_text('value=99\n')
    return root,public


def test_worker_runs_its_verified_library_and_restores_module_namespace(tmp_path):
    import sys,lll
    module=resolver();root,public=frozen_worker_checkout(tmp_path);original=lll
    with module.qualified_worker(root,public,'example_worker',tmp_path/'isolated') as worker:
        assert worker.example_math.value==17
        assert worker.ROOT==tmp_path/'isolated'
        assert Path(worker.example_math.__file__).is_relative_to(worker.ROOT)
        assert sys.modules['lll'] is not original
    assert sys.modules['lll'] is original
    assert (root/'analysis/lll/example_math.py').read_text()=='value=99\n'
    assert 'example_worker' not in sys.modules


def test_worker_isolation_rejects_a_changed_frozen_dependency(tmp_path):
    import pytest
    module=resolver();root,public=frozen_worker_checkout(tmp_path)
    (public/'source-freeze/analysis/lll/example_math.py').write_text('value=99\n')
    with pytest.raises(ValueError,match='frozen source'):
        with module.qualified_worker(root,public,'example_worker',tmp_path/'isolated'):pass


def test_reference_helper_convention_does_not_allow_executable_entrypoints(tmp_path):
    module=resolver();path=tmp_path/'helper_reference.py'
    path.write_text('from pathlib import Path\ndef original():\n    return 17\n')
    assert module.reference_fixture(path)
    path.write_text('if __name__=="__main__":\n    run_study()\n')
    assert not module.reference_fixture(path)
    path.write_text('run_study()\n')
    assert not module.reference_fixture(path)


def test_archived_fixture_reads_restore_only_the_requested_public_alias(tmp_path):
    from lll.studies.artifacts import ArchiveStore
    module=resolver();root=tmp_path/'checkout';name='docs/example/source-freeze/analysis/core.py'
    path=root/name;path.parent.mkdir(parents=True);path.write_bytes(b'value=17\n')
    store=ArchiveStore(root);store.pack([name]);store.compact(names=[name]);store.close()
    with module.archived_read_path(root,tmp_path/'cache') as remap:
        cached=Path(remap(path));assert cached.read_bytes()==b'value=17\n'
        assert not path.exists()
        private=root/'data/unrelated/private.txt';assert remap(private)==private
        assert remap('/unrelated/private.txt')=='/unrelated/private.txt'


def test_worker_snapshot_restores_hash_bound_prerequisite_sources(tmp_path):
    import hashlib,json
    module=resolver();root,public=frozen_worker_checkout(tmp_path)
    prerequisite=root/'docs/prerequisite';source='analysis/lll/auxiliary_math.py';raw=b'value=23\n'
    path=prerequisite/'source-freeze'/source;path.parent.mkdir(parents=True);path.write_bytes(raw)
    manifest=json.dumps(dict(sources={source:hashlib.sha256(raw).hexdigest()})).encode()
    (prerequisite/'manifest.json').write_bytes(manifest)
    (prerequisite/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={'manifest.json':hashlib.sha256(manifest).hexdigest()})))
    name='docs/prerequisite/manifest.json';path=public/'source-freeze'/name
    path.parent.mkdir(parents=True);path.write_bytes(manifest)
    own=json.loads((public/'manifest.json').read_bytes());own['sources'][name]=hashlib.sha256(manifest).hexdigest()
    raw=json.dumps(own).encode();(public/'manifest.json').write_bytes(raw)
    (public/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={'manifest.json':hashlib.sha256(raw).hexdigest()})))
    with module.qualified_worker(root,public,'example_worker',tmp_path/'isolated') as worker:
        assert (worker.ROOT/source).read_bytes()==b'value=23\n'
