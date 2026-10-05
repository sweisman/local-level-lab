# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.metadata
from pathlib import Path
import tomllib

from lll import __version__
from lll_server.app import create_app


def test_single_source_versions(tmp_path):
    root = Path(__file__).resolve().parents[2]
    assert create_app(tmp_path).openapi()["info"]["version"] == __version__
    assert importlib.metadata.version("lll") == __version__
    assert importlib.metadata.version("lll-server") == __version__
    for package in ("analysis", "server"):
        metadata = tomllib.loads((root/package/"pyproject.toml").read_text())
        assert "version" in metadata["project"]["dynamic"]
        assert "version" not in metadata["project"]
    gradle = (root/"android/app/build.gradle.kts").read_text()
    assert 'rootProject.file("../analysis/lll/__init__.py")' in gradle
    assert 'versionName = Regex(' in gradle
