# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('website_build',Path(__file__).resolve().parents[1]/'build.py')
site=importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


def write(root,name,text):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)


def example(root):
    write(root,'README.md','# Home\n\n[Method](docs/method.md#how-it-works)\n\n![Logo](docs/img/logo.svg)\n')
    write(root,'docs/method.md','# Method\n\n## How it works\n\n[Home](../README.md) [More](nested/other.md) [CSV](rates.csv)\n\n\\(A\\cos\\phi\\)\n\n```mermaid\nflowchart LR\n A --> B\n```\n')
    write(root,'docs/nested/other.md','# Other\n\n[Method](../method.md)\n')
    write(root,'docs/img/logo.svg','<svg xmlns="http://www.w3.org/2000/svg"/>')


def test_archived_page_and_data_links_remain_accessible(tmp_path):
    from lll.studies.artifacts import ArchiveStore,atomic,encoded,digest
    root=tmp_path/'repo';out=tmp_path/'site';example(root)
    write(root,'docs/nested/result.json','{"answer":42}')
    write(root,'docs/nested/other.md','# Other\n\n[Data](result.json)\n')
    store=ArchiveStore(root);store.pack(['docs/nested/other.md','docs/nested/result.json']);store.compact()
    catalog=store.catalog();catalog['origin_commit']='a'*40;raw=encoded(catalog)
    atomic(store.catalog_path,raw);atomic(store.catalog_path.with_suffix('.sha256'),(digest(raw)+'\n').encode())
    report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert report['missing_pages']==[] and report['page_count']==3
    assert '/blob/'+('a'*40)+'/docs/nested/result.json' in (out/'docs/nested/other.html').read_text()


def test_recursive_pages_links_and_repo_downloads(tmp_path):
    root=tmp_path/'repo';out=tmp_path/'site';example(root)
    report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert report['page_count']==3
    homepage=(out/'index.html').read_text();method=(out/'docs/method.html').read_text()
    assert 'href="/docs/method.html#how-it-works"' in homepage
    assert 'href="/"' in method
    assert 'href="/docs/nested/other.html"' in method
    assert 'https://github.com/sweisman/local-level-lab/blob/main/docs/rates.csv' in method
    assert (out/'docs/img/logo.svg').exists()
    assert not (out/'docs/rates.csv').exists()
    assert report['missing_fragments']==[]


def test_frozen_doc_relative_links_keep_snapshot_neighbors_and_resolve_original_context(tmp_path):
    root=tmp_path/'repo';out=tmp_path/'site'
    write(root,'README.md','# Home\n\n[Snapshot](docs/study/source-freeze/docs/adapter/METHOD.md)\n')
    write(root,'docs/study/source-freeze/docs/adapter/METHOD.md',
        '# Frozen method\n\n[Neighbor](NEIGHBOR.md) [Guide](../GUIDE.md#current) [Adapter](README.md)\n')
    write(root,'docs/study/source-freeze/docs/adapter/NEIGHBOR.md','# Frozen neighbor\n')
    write(root,'docs/adapter/NEIGHBOR.md','# Current neighbor\n')
    write(root,'docs/adapter/README.md','# Adapter\n')
    write(root,'docs/GUIDE.md','# Guide\n\n## Current\n')
    report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    text=(out/'docs/study/source-freeze/docs/adapter/METHOD.html').read_text()
    assert report['missing_pages']==[] and report['missing_fragments']==[]
    assert 'href="/docs/GUIDE.html#current"' in text
    assert 'href="/docs/adapter/README.html"' in text
    assert 'href="/docs/study/source-freeze/docs/adapter/NEIGHBOR.html"' in text


def test_math_mermaid_tables_and_code_literals(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md',r'''# Home

\[
\omega_N=A\cos\phi
\]

| Axis | Rate |
|---|---|
| N | $A$ |

`$literal$`

```python
path="docs/method.md"
```

```mermaid
flowchart LR
    A --> B
```
''')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets',navigation=False)
    text=(out/'index.html').read_text()
    assert '\\omega_N=A\\cos\\phi' in text
    assert '<table>' in text and 'class="table-scroll"' in text
    assert '<code>$literal$</code>' in text
    assert '<code class="language-python">' in text
    assert 'class="language-mermaid"' in text
    assert 'docs/method.md' in text


def test_reference_html_encoded_links_and_project_basepath(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md','# Home\n\n[Method][m]\n\n[m]: docs/method.md\n\n<a href="docs/nested/other.md">Other</a>\n\n[Data](docs/a%20file.csv?raw=1)\n')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets',navigation=False,base_path='/local-level-lab')
    text=(out/'index.html').read_text()
    assert '/local-level-lab/docs/method.html' in text
    assert '/local-level-lab/docs/nested/other.html' in text
    assert 'blob/main/docs/a%20file.csv?raw=1' in text


def test_only_linked_pages_are_read_and_instructions_stay_on_github(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md','# Home\n\n[Instructions](AGENTS.md) [Directory](docs/)\n')
    write(root,'AGENTS.md','private instructions')
    write(root,'docs/unlinked.md','not linked')
    out=tmp_path/'site';report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert report['page_count']==1
    text=(out/'index.html').read_text()
    assert 'blob/main/AGENTS.md' in text
    assert 'tree/main/docs/' in text
    assert not (out/'AGENTS.html').exists()
    assert not (out/'docs/unlinked.html').exists()


def test_rejects_path_escape_and_symlink_before_read(tmp_path):
    root=tmp_path/'repo';root.mkdir();write(root,'README.md','# Home\n\n[Outside](../outside.md)\n')
    with pytest.raises(ValueError,match='outside'): site.build(root,tmp_path/'site',assets=site.HERE/'assets',navigation=False)
    write(root,'README.md','# Home\n\n[Linked](docs/linked.md)\n')
    (root/'docs').mkdir();(root/'docs/linked.md').symlink_to(tmp_path/'outside.md')
    with pytest.raises(ValueError,match='symlink'): site.build(root,tmp_path/'another',assets=site.HERE/'assets',navigation=False)


def test_build_rejects_existing_output_instead_of_deleting_it(tmp_path):
    root=tmp_path/'repo';example(root);out=tmp_path/'site';out.mkdir()
    with pytest.raises(ValueError,match='fresh'): site.build(root,out,assets=site.HERE/'assets',navigation=False)


def test_missing_pages_and_fragments_are_reported(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md','# Home\n\n[Missing](docs/missing.md) [Section](docs/method.md#gone)\n')
    report=site.build(root,tmp_path/'site',assets=site.HERE/'assets',navigation=False)
    assert len(report['missing_pages'])==1 and len(report['missing_fragments'])==1


def test_github_markdown_links_are_pages_but_artifacts_remain_external(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md','# Home\n\n[Method](https://github.com/sweisman/local-level-lab/blob/main/docs/method.md)\n\n[JSON](https://github.com/sweisman/local-level-lab/blob/main/docs/report.json)\n\n[Outside](https://example.org/reference.md)\n')
    out=tmp_path/'site';report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    text=(out/'index.html').read_text()
    assert report['page_count']==3 and 'href="/docs/method.html"' in text
    assert 'href="https://example.org/reference.md"' in text
    assert 'blob/main/docs/report.json' in text


def test_encoded_traversal_is_rejected(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    write(root,'README.md','# Home\n\n[Outside](%2e%2e/outside.md)\n')
    with pytest.raises(ValueError,match='outside'): site.build(root,tmp_path/'site',assets=site.HERE/'assets',navigation=False)


def test_linked_documentation_outside_docs_also_becomes_a_page(tmp_path):
    root=tmp_path/'repo';example(root)
    write(root,'README.md','# Home\n\n[Build guide](website/README.md)\n')
    write(root,'website/README.md','# Build guide\n\n[Home](../README.md)\n')
    out=tmp_path/'site';report=site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert report['page_count']==2 and (out/'website/README.html').exists()


def test_link_preview_describes_telemetry_and_keeps_source_attribution_in_body(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    write(root,'README.md','# Local Level Lab\n\nNASA survey recordings supply the observations.\n')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets',navigation=False)
    text=(out/'index.html').read_text()
    from html.parser import HTMLParser
    class Metadata(HTMLParser):
        values={}
        def handle_starttag(self,tag,attrs):
            if tag=='meta':
                a=dict(attrs);self.values[a.get('property',a.get('name'))]=a.get('content','')
    parser=Metadata();parser.feed(text)
    for name in ('description','og:description','twitter:description'):
        assert 'airborne lidar survey' in parser.values[name].lower()
        assert 'NASA' not in parser.values[name]
    assert parser.values['og:url']=='https://locallevellab.com/'
    assert parser.values['og:title']=='Local Level Lab — Airborne lidar survey IMU analysis'
    assert 'NASA survey recordings supply the observations.' in text


def test_navigation_opens_current_findings_stretches_and_study_index(tmp_path):
    root=tmp_path/'repo';root.mkdir();write(root,'README.md','# Home\n')
    for name in ('docs/CURRENT_STATUS.md','docs/STUDIES.md','docs/NEXT_STEPS.md','docs/METHODOLOGY.md',
                 'docs/ilvis0-current-findings-20261015/STRETCHES.md','docs/STATIONARY.md'):
        write(root,name,'# Reference\n')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets')
    text=(out/'index.html').read_text()
    assert 'href="/docs/CURRENT_STATUS.html"' in text
    assert 'href="/docs/STUDIES.html"' in text
    assert 'href="/docs/NEXT_STEPS.html"' in text
    assert 'href="/docs/ilvis0-current-findings-20261015/STRETCHES.html"' in text


@pytest.mark.parametrize('base_path', ('', '/project'))
def test_completed_study_has_context_without_rewriting_its_historical_source(tmp_path, base_path):
    root=tmp_path/'repo';root.mkdir()
    report_path='docs/ilvis0-example/README.md'
    original='# Study results\n\n12 globe / 0 flat / 41 unresolved.\n'
    write(root,'README.md','# Home\n\n[Earlier study]('+report_path+')\n')
    write(root,report_path,original)
    write(root,'docs/ilvis0-example/completion.json','{}')
    write(root,'docs/ilvis0-example/evidence-receipt.json','{}')
    write(root,'docs/CURRENT_STATUS.md','# Current findings\n\n53 globe / 0 flat / 0 unresolved.\n')
    write(root,'docs/NEXT_STEPS.md','# Next analyses\n')
    out=tmp_path/'site'
    result=site.build(root,out,assets=site.HERE/'assets',navigation=False,base_path=base_path)
    text=(out/'docs/ilvis0-example/README.html').read_text()
    assert 'class="study-context"' in text
    assert 'Individual study report' in text
    assert '12 globe / 0 flat / 41 unresolved.' in text
    assert f'href="{base_path}/docs/CURRENT_STATUS.html"' in text
    assert f'href="{base_path}/docs/NEXT_STEPS.html"' in text
    assert (root/report_path).read_text()==original
    assert result['missing_pages']==[] and result['missing_fragments']==[]
    assert 'class="study-context"' not in (out/'index.html').read_text()


def test_current_aggregate_is_not_labeled_as_an_individual_study(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    source=dict(site.NAVIGATION)['Flight stretches'];parent=str(Path(source).parent)
    write(root,'README.md','# Home\n\n[Stretches]('+source+')\n')
    write(root,source,'# Current stretches\n')
    write(root,parent+'/completion.json','{}')
    write(root,parent+'/evidence-receipt.json','{}')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert 'class="study-context"' not in (out/site.output_path(source)).read_text()


def test_uncompleted_study_does_not_get_a_completed_report_notice(tmp_path):
    root=tmp_path/'repo';root.mkdir()
    source='docs/ilvis0-preparation/README.md'
    write(root,'README.md','# Home\n\n[Plan]('+source+')\n')
    write(root,source,'# Research preparation\n')
    out=tmp_path/'site';site.build(root,out,assets=site.HERE/'assets',navigation=False)
    assert 'class="study-context"' not in (out/site.output_path(source)).read_text()
