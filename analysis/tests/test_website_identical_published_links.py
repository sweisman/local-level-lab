"""Identical sealed overviews retain their original relative link context."""

import importlib.util
from pathlib import Path


def test_identical_published_overview_links_resolve_from_original_page(tmp_path):
    root = tmp_path / 'repo'
    original = root / 'docs' / 'RESULT.md'
    archived = root / 'docs' / 'published' / 'README.md'
    original.parent.mkdir(parents=True)
    archived.parent.mkdir(parents=True)
    (root / 'README.md').write_text('# Home\n\n[Result](docs/RESULT.md)\n')
    content = '# Result\n\n[Plan](PLAN.md) · [Archive](published/README.md)\n'
    original.write_text(content)
    archived.write_text(content)
    (root / 'docs' / 'PLAN.md').write_text('# Plan\n')
    (root / 'docs' / 'published' / 'evidence-receipt.json').write_text('{}')
    script = Path(__file__).resolve().parents[2] / 'website' / 'build.py'
    spec = importlib.util.spec_from_file_location('site_builder', script)
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)
    output = tmp_path / 'site'
    report = site.build(root, output, assets=site.HERE / 'assets', navigation=False)
    rendered = (output / 'docs' / 'published' / 'README.html').read_text()
    assert report['missing_pages'] == []
    assert '/docs/PLAN.html' in rendered
