# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

import truthgen
import pytest


@pytest.fixture(autouse=True)
def published_worker_fixtures(request,monkeypatch):
    """Use sealed public metadata for the six local-runtime integration tests."""
    from pathlib import Path
    names={'test_ilvis0_final_pair_v2_worker.py','test_ilvis0_last_field_worker.py',
           'test_ilvis0_last_free_time_worker.py','test_ilvis0_last_zero_boundary_worker.py',
           'test_ilvis0_saved_context.py','test_ilvis0_scaled_pair_worker.py'}
    root=Path(__file__).resolve().parents[2]
    if request.path.name not in names or (root/'data/ilvis0-last-time-profile-20261018/manifest.json').exists():return
    import builtins
    import io
    from public_fixtures import public_read_path,read_adapter
    remap=public_read_path(root)
    monkeypatch.setattr(builtins,'open',read_adapter(builtins.open,remap))
    monkeypatch.setattr(io,'open',read_adapter(io.open,remap))
    if request.path.name=='test_ilvis0_last_free_time_worker.py':
        # This frozen assertion checks source membership using the checkout root.
        # Add aliases only after the original source/hash validator has run.
        from public_fixtures import source_aliases
        original_worker=request.module.worker
        def worker():
            module=original_worker();original_build=module.build_executor
            def build():
                executor=original_build();sources=executor.sources
                executor.sources=lambda:source_aliases(root,sources())
                return executor
            module.build_executor=build;return module
        monkeypatch.setattr(request.module,'worker',worker)


def geometric_truth(world):
    """ω_in for synth, from the independent geometric generator rather than lll.models. The
    sampled track is interpolated, so the generator can differentiate the local frame along it."""
    def fn(t, lat, lon, h):
        t, lat, lon, h = (np.atleast_1d(np.asarray(x, float)) for x in (t, lat, lon, h))
        if len(t) == 1:   # a stationary point (ground calibration)
            def traj(tt):
                tt = np.atleast_1d(tt)
                return np.full(tt.shape, lat[0]), np.full(tt.shape, lon[0]), np.full(tt.shape, h[0])
        else:
            def traj(tt):
                return np.interp(tt, t, lat), np.interp(tt, t, lon), np.interp(tt, t, h)
        w, _ = truthgen.truth(world, traj, t)
        return w
    return fn
