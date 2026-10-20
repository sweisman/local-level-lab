# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def module():
    path=Path(__file__).resolve().parents[2]/'docs/paper-development-dataset-v1/build_dataset.py'
    spec=importlib.util.spec_from_file_location('paper_dataset_builder',path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_frozen_snapshot_checks_copies_without_requiring_live_inputs_unchanged(tmp_path):
    w=module();root=tmp_path/'source';root.mkdir();dest=tmp_path/'snapshot'
    (root/'input.csv').write_text('sealed source');(root/'builder.py').write_text('# fixed builder')
    w.freeze(root,dest,{'input.csv':w.sha(root/'input.csv')},{'builder.py':w.sha(root/'builder.py')},{'table.csv':b'a,b\n1,2\n'},
        dict(final_paper_dataset=False))
    w.check(dest);(root/'input.csv').write_text('later live project revision')
    w.check(dest)
    with pytest.raises(ValueError):w.check(dest,live_root=root)
    assert (dest/'frozen-inputs/input.csv').read_text()=='sealed source'
    with pytest.raises(ValueError):w.freeze(root,dest,{}, {}, {}, {})


def test_snapshot_rejects_tampered_outputs_instead_of_regenerating_them(tmp_path):
    w=module();root=tmp_path/'root';root.mkdir();dest=tmp_path/'snapshot'
    w.freeze(root,dest,{}, {}, {'table.csv':b'original'},dict(final_paper_dataset=False))
    (dest/'table.csv').write_bytes(b'altered')
    with pytest.raises(ValueError):w.check(dest)
    assert (dest/'table.csv').read_bytes()==b'altered'
