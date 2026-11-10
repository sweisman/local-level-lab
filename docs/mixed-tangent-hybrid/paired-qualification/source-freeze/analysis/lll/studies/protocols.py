# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind one explicit dependency of a trusted, source-frozen Python protocol.

Only the selected function is compiled. Its other statements remain unchanged;
the original module and process-wide imports are never patched. Source/provider
qualification remains a caller-owned prerequisite. This is not an upload sandbox.
"""
import ast
import copy
import hashlib
import re


def bind_function(source,*,expected_sha256,function,import_module,import_name,provider,provider_source_sha256,namespace):
    if not isinstance(source,bytes) or hashlib.sha256(source).hexdigest()!=expected_sha256:
        raise ValueError('exact protocol source hash required')
    if (not isinstance(function,str) or not function.isidentifier() or not isinstance(import_name,str)
            or not import_name.isidentifier() or not isinstance(import_module,str)
            or not all(s.isidentifier() for s in import_module.split('.')) or not callable(provider)
            or not isinstance(provider_source_sha256,str) or not re.fullmatch('[0-9a-f]{64}',provider_source_sha256)
            or not isinstance(namespace,dict)):
        raise ValueError('explicit function, imported dependency and bound provider required')
    tree=ast.parse(source);selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function]
    if len(selected)!=1:raise ValueError('one unambiguous top-level protocol function required')
    node=copy.deepcopy(selected[0]);reserved='_lll_protocol_provider'
    if (node.decorator_list or node.returns or getattr(node,'type_params',[])
            or any(a.annotation for a in (*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs))
            or (node.args.vararg and node.args.vararg.annotation) or (node.args.kwarg and node.args.kwarg.annotation)):
        raise ValueError('effect-free protocol declaration required')
    try:
        for value in [*node.args.defaults,*node.args.kw_defaults]:
            if value is not None:ast.literal_eval(value)
    except (ValueError,TypeError):raise ValueError('literal protocol defaults required') from None
    if reserved in namespace or any(
            (isinstance(n,ast.Name) and n.id==reserved)
            or (isinstance(n,ast.arg) and n.arg==reserved)
            or (isinstance(n,ast.alias) and (n.name==reserved or n.asname==reserved)) for n in ast.walk(node)):
        raise ValueError('reserved provider binding collides with protocol')
    before=ast.dump(node,include_attributes=False)
    class Bind(ast.NodeTransformer):
        count=0
        def visit_ImportFrom(self,n):
            if n.level or n.module!=import_module:return n
            matches=[a for a in n.names if a.name==import_name]
            if not matches:return n
            self.count+=len(matches)
            remaining=[a for a in n.names if a.name!=import_name];result=[]
            if remaining:result.append(ast.copy_location(ast.ImportFrom(module=n.module,names=remaining,level=0),n))
            result.extend(ast.copy_location(ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],
                value=ast.Name(id=reserved,ctx=ast.Load())),n) for a in matches)
            return result
    transform=Bind();node=transform.visit(node)
    if transform.count!=1:raise ValueError('exactly one explicit dependency import required')
    after=ast.dump(node,include_attributes=False);module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    local=dict(namespace);local[reserved]=provider
    exec(compile(module,'/<bound-protocol:'+expected_sha256+'>','exec'),local)
    result=local[function]
    proof=dict(version='study-function-provider-v1',source_sha256=expected_sha256,function=function,
        original_function_ast_sha256=hashlib.sha256(before.encode()).hexdigest(),
        bound_function_ast_sha256=hashlib.sha256(after.encode()).hexdigest(),import_module=import_module,
        import_name=import_name,provider_source_sha256=provider_source_sha256,substitutions=transform.count)
    return result,proof
