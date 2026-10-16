"""Rendering saved evidence must not put its receipt inside itself."""
import importlib.util
import json
from pathlib import Path
import sys


def test_repeated_render_has_no_self_hash(tmp_path, monkeypatch):
    directory = Path(__file__).resolve().parents[2] / 'docs/ilvis0-boundary-review-20261016'
    monkeypatch.syspath_prepend(str(directory))
    # Avoid colliding with another report's generic module name in a full suite.
    monkeypatch.delitem(sys.modules, 'build_report', raising=False)
    spec = importlib.util.spec_from_file_location('boundary_review_renderer', directory / 'render_report.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    monkeypatch.delitem(sys.modules, 'build_report', raising=False)
    runtime = tmp_path / 'runtime'
    public = tmp_path / 'public'
    runtime.mkdir()
    public.mkdir()
    for name in ('manifest.json', 'review.json', 'completion.json'):
        (runtime / name).write_text('{}')
    (public / 'evidence-example.json').write_text('{}')
    monkeypatch.setattr(renderer, 'HERE', public)
    monkeypatch.setattr(renderer, 'OUTPUT', runtime)
    review = dict(comparisons=[], dispositions={}, attempts=[])
    renderer.render(review)
    first = (public / 'evidence-receipt.json').read_bytes()
    renderer.render(review)
    assert (public / 'evidence-receipt.json').read_bytes() == first
    receipt = json.loads(first)
    assert 'evidence-receipt.json' not in receipt['artifacts']
    assert 'evidence-example.json' in receipt['artifacts']
    for name, digest in receipt['artifacts'].items():
        assert renderer.sha(public / name) == digest
