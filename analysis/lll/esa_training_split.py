# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage a shorter ESA training fit without its receiver scoring observations."""

from dataclasses import dataclass
import gzip
import io
import json
import math


@dataclass(frozen=True)
class DevelopmentSplit:
    interval_bytes: bytes
    training_bytes: bytes
    scoring_rows: tuple
    times_s: object
    packet_count: int

    def fit_material(self):
        """The only fields that may be staged for the training worker."""
        return dict(interval=self.interval_bytes, training=self.training_bytes,
                    forecast_times=json.dumps(self.times_s.tolist()).encode())


def partition_development_input(interval_bytes, training_bytes, saved_times,
                                *, time_origin_s, training_epochs,
                                forecast_epochs, latency_s):
    """Return separate training and scoring material from sealed development data.

    Only ``interval_bytes``, ``training_bytes`` and ``times_s`` belong in the
    fitting study. The caller must hold ``scoring_rows`` outside that study
    until its fit and forecast have been sealed.
    """
    import numpy as np

    if (type(training_epochs) is not int or type(forecast_epochs) is not int or
            not 2 <= training_epochs < forecast_epochs or
            not all(math.isfinite(value) for value in
                    (time_origin_s, latency_s)) or latency_s < 0):
        raise ValueError('finite earlier-only split and latency required')
    try:
        rows = json.loads(gzip.decompress(training_bytes))
        times = np.asarray(saved_times, dtype=float)
    except (OSError, ValueError, TypeError) as error:
        raise ValueError('valid sealed receiver and time inputs required') from error
    if (not isinstance(rows, list) or forecast_epochs > len(rows) or
            times.ndim != 1 or len(times) <= forecast_epochs or
            not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0)):
        raise ValueError('complete ordered forecast and receiver support required')
    try:
        coordinates = np.asarray([[row[key] for key in
            ('time_s', 'latitude_deg', 'longitude_deg', 'height_m')]
            for row in rows], dtype=float)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('complete receiver rows required') from error
    if (coordinates.shape != (len(rows), 4) or
            not np.all(np.isfinite(coordinates)) or
            not np.allclose(coordinates[:, 0] - time_origin_s,
                            times[:len(rows)], atol=1e-6, rtol=0)):
        raise ValueError('receiver rows must match the saved time support')
    try:
        with np.load(io.BytesIO(interval_bytes), allow_pickle=False) as archive:
            arrays = {key: np.asarray(archive[key], dtype=float)
                      for key in ('theta', 'dv', 'dt')}
    except (OSError, KeyError, ValueError) as error:
        raise ValueError('complete sealed inertial increments required') from error
    dt = arrays['dt']
    if (dt.ndim != 1 or arrays['theta'].shape != (len(dt), 3) or
            arrays['dv'].shape != (len(dt), 3) or
            not all(np.all(np.isfinite(value)) for value in arrays.values()) or
            np.any(dt <= 0)):
        raise ValueError('finite ordered inertial increments required')
    endpoint = float(times[forecast_epochs - 1] + latency_s)
    elapsed = np.cumsum(dt)
    count = int(np.searchsorted(elapsed, endpoint, side='left')) + 1
    if count > len(dt) or times[0] < 0:
        raise ValueError('whole latency-bound forecast support required')
    output = io.BytesIO()
    np.savez(output, **{key: value[:count] for key, value in arrays.items()})
    return DevelopmentSplit(
        interval_bytes=output.getvalue(),
        training_bytes=gzip.compress(
            json.dumps(rows[:training_epochs], sort_keys=True,
                       separators=(',', ':')).encode(), mtime=0),
        scoring_rows=tuple(rows[training_epochs:forecast_epochs]),
        times_s=times[:forecast_epochs].copy(), packet_count=count)


def preflight_sealed_development(root):
    """Check the planned 600/200 cut against the hash-verified ESA parent."""
    from pathlib import Path
    from .esa_fixed_rate_protocol import stage_parent
    from .studies.artifacts import digest

    source = stage_parent(Path(root).resolve(), smoke=False)
    binding = json.loads(source['saved-input-binding'])
    recipe = json.loads(source['recipe'])
    forecast = json.loads(source['saved-increment-forecast'])
    if (binding['source_id'] != 'esa-99f1530c3eda4318' or
            binding['training_epochs'] != 800 or
            len(forecast['times_s']) != 1200 or
            recipe['clock'] != 'header_elapsed'):
        raise ValueError('sealed ESA development parent or timing differs')
    split = partition_development_input(
        source['interval'], source['training'], forecast['times_s'],
        time_origin_s=binding['time_origin_s'], training_epochs=600,
        forecast_epochs=800,
        latency_s=abs(float(recipe['limits'].get('time_offset', 0.))))
    if len(split.scoring_rows) != 200:
        raise ValueError('exactly 200 separate scoring rows required')
    return dict(source_id=binding['source_id'], training_epochs=600,
                prediction_epochs=200, packet_count=split.packet_count,
                maximum_evaluations_per_fit=recipe['maximum_evaluations'],
                staged_interval_sha256=digest(split.interval_bytes),
                staged_training_sha256=digest(split.training_bytes),
                scoring_rows_staged_with_fit=False,
                protected_confirmation_groups_opened=0)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight',))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    if args.action == 'preflight':
        print(json.dumps(preflight_sealed_development(args.root), sort_keys=True))


if __name__ == '__main__':
    main()
