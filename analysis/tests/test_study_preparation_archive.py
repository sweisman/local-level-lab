# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
from lll.studies.artifacts import encoded,digest,ArchiveStore


def fixture(root,*,external=False,closed=True,changed=False):
    base=root/'data/prep-inputs';base.mkdir(parents=True)
    name='data/retained.json' if external else 'data/prep-inputs/case.json'
    path=root/name;path.write_bytes(b'{"value":1}\n')
    sha=digest(path.read_bytes())
    definition=dict(id='example',inputs={'case':name})
    target=base/'definition.json';target.write_bytes(encoded(definition))
    study=root/'data/example';study.mkdir()
    manifest=encoded(dict(inputs={'case':dict(source=name,sha256=sha)}))
    (study/'manifest.json').write_bytes(manifest)
    if closed:(study/'completion.json').write_bytes(encoded(dict(state='complete',manifest_sha256=digest(manifest))))
    if changed:path.write_bytes(b'{"value":2}\n')
    return target.relative_to(root).as_posix(),name


def test_completed_generated_preparation_is_preserved_as_verified_archive_aliases(tmp_path):
    from lll.studies.publication import archive_preparation
    definition,name=fixture(tmp_path);before={p:(tmp_path/p).read_bytes() for p in (definition,name)}
    result=archive_preparation(tmp_path,definition)
    assert result['compacted_files']==2 and result['numerical_work']==0
    for path,value in before.items():
        assert not (tmp_path/path).exists()
        assert ArchiveStore(tmp_path).read(path)==value


@pytest.mark.parametrize('settings',[dict(external=True),dict(closed=False),dict(changed=True)])
def test_preparation_compaction_never_touches_external_unclosed_or_changed_inputs(tmp_path,settings):
    from lll.studies.publication import archive_preparation
    definition,name=fixture(tmp_path,**settings)
    with pytest.raises(ValueError):archive_preparation(tmp_path,definition)
    assert (tmp_path/name).is_file() and (tmp_path/definition).is_file()
