# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import pytest


def test_verified_python_reference_is_hash_bound_before_execution():
    from lll.studies.closed import load_python_reference
    raw=b'value=17\n';sha=hashlib.sha256(raw).hexdigest()
    module=load_python_reference(raw,name='lll._test_sealed_reference',sha256=sha)
    assert module.value==17 and module.__package__=='lll' and module.__lll_source_hash__==sha
    assert load_python_reference(raw,name=module.__name__,sha256=sha) is module
    with pytest.raises(ValueError):load_python_reference(b'raise RuntimeError("ran")',name=module.__name__,sha256=sha)
    other=b'value=18\n'
    with pytest.raises(ValueError):load_python_reference(other,name=module.__name__,sha256=hashlib.sha256(other).hexdigest())


@pytest.mark.parametrize('name',['os','lll','lll.bad-name','wrong.package'])
def test_reference_module_remains_in_explicit_analysis_package(name):
    from lll.studies.closed import load_python_reference
    raw=b'value=17\n'
    with pytest.raises(ValueError):load_python_reference(raw,name=name,sha256=hashlib.sha256(raw).hexdigest())
