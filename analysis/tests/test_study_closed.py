# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_closed_reader_verifies_result_bindings(tmp_path):
    from test_ilvis0_prediction_publication import closed_fixture
    from lll.studies.closed import ClosedStudy
    prefix=closed_fixture(tmp_path)
    study=ClosedStudy(tmp_path,prefix)
    assert len(study.tasks)==6
    assert study.envelope('case-0')['result']['numerical_checks_passed']
    study.close()


def test_closed_reader_rejects_active_or_changed_results(tmp_path):
    from test_ilvis0_prediction_publication import closed_fixture
    from lll.studies.closed import ClosedStudy
    with pytest.raises(ValueError,match='closed'):ClosedStudy(tmp_path,'data/active')
    prefix=closed_fixture(tmp_path)
    path=tmp_path/prefix/'results/case-0.json';path.write_bytes(path.read_bytes()+b'\n')
    study=ClosedStudy(tmp_path,prefix)
    with pytest.raises(ValueError,match='hash'):study.envelope('case-0')
    study.close()


def test_external_reference_requires_exact_hash_and_safe_path(tmp_path):
    from test_ilvis0_prediction_publication import closed_fixture
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest
    study=ClosedStudy(tmp_path,closed_fixture(tmp_path));path=tmp_path/'data/reference.json'
    path.write_bytes(b'{"value":1}\n')
    assert study.reference(dict(path='data/reference.json',sha256=digest(path.read_bytes())))=={'value':1}
    with pytest.raises(ValueError):study.reference(dict(path='data/reference.json',sha256='a'*64))
    with pytest.raises(ValueError):study.reference(dict(path='../outside',sha256='a'*64))
    study.close()
