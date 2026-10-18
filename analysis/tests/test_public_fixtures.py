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
