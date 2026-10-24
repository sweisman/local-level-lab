# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks; no numerical libraries or study execution."""
import hashlib

import pytest


def _bind(source,**kwargs):
    from lll.studies.protocols import bind_function
    return bind_function(source,expected_sha256=hashlib.sha256(source).hexdigest(),function='run',
        import_module='builtins',import_name='str',provider=lambda value:'wide:'+value,
        provider_source_sha256='a'*64,namespace={'prefix':'p:'},**kwargs)


def test_protocol_binding_changes_only_explicit_import_and_leaves_shared_names_untouched():
    from lll.studies.protocols import bind_function
    source=b"def run(value):\n    from builtins import str, len\n    return prefix+str(value)+':'+str(len(value))\n"
    namespace={'prefix':'p:'};provider=lambda value:'wide:'+str(value)
    run,proof=bind_function(source,expected_sha256=hashlib.sha256(source).hexdigest(),function='run',
        import_module='builtins',import_name='str',provider=provider,provider_source_sha256='a'*64,namespace=namespace)
    assert run('abc')=='p:wide:abc:wide:3'
    assert namespace=={'prefix':'p:'} and str('abc')=='abc'
    assert proof['substitutions']==1 and proof['source_sha256']==hashlib.sha256(source).hexdigest()
    assert proof['provider_source_sha256']=='a'*64 and proof['import_name']=='str'
    again,_=bind_function(source,expected_sha256=proof['source_sha256'],function='run',
        import_module='builtins',import_name='str',provider=lambda v:'other:'+str(v),
        provider_source_sha256='b'*64,namespace={'prefix':'q:'})
    assert again('x')=='q:other:x:other:1' and run('abc')=='p:wide:abc:wide:3'


@pytest.mark.parametrize('source',[
    b'def other(x): return x\n',
    b'def run(x): return x\n',
    b'def run(x):\n from builtins import str\n from builtins import str\n return str(x)\n',
    b'@decorator\ndef run(x):\n from builtins import str\n return str(x)\n',
    b'def run(x):\n from builtins import str as _lll_protocol_provider\n return str(x)\n',
])
def test_protocol_binding_rejects_missing_ambiguous_or_effectful_declarations(source):
    with pytest.raises(ValueError):_bind(source)


def test_protocol_binding_rejects_unbound_source_before_execution():
    from lll.studies.protocols import bind_function
    source=b"raise AssertionError('never execute module')\ndef run(x):\n from builtins import str\n return str(x)\n"
    with pytest.raises(ValueError,match='hash'):
        bind_function(source,expected_sha256='0'*64,function='run',import_module='builtins',import_name='str',
            provider=str,provider_source_sha256='a'*64,namespace={})
    run,proof=_bind(source)
    assert run('x')=='wide:x' # Top-level source statements are not executed.
