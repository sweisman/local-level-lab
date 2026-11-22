# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent generated receiver cuts for a bounded solver forecast gate."""

import numpy as np

VERSION='ilvis0-generated-solver-forecast-v1'


def split_fixture(fixture):
    times=np.asarray(fixture['gps_times'],float)
    gps=np.asarray(fixture['gps'],float)
    if (times.shape!=(24,) or gps.shape!=(24,3) or
            not np.all(np.isfinite(times)) or
            not np.all(np.diff(times)>0) or not np.all(np.isfinite(gps))):
        raise ValueError('complete finite 24-epoch independent fixture required')
    train=dict(fixture,gps_times=times[:16].copy(),gps=gps[:16].copy())
    query=dict(fixture,gps_times=times.copy(),gps=gps.copy())
    query['gps'][16:]=0.
    later=gps[16:].copy()
    return train,query,later


def compare_rows(rows):
    if not isinstance(rows,list) or len(rows)!=4 or len({r['identity'] for r in rows})!=4:
        raise ValueError('four distinct solver/start results required')
    paths=[np.asarray(row['later_path'],float) for row in rows]
    metric=np.asarray(rows[0]['metric'],float)
    if (metric.shape!=(3,) or not np.all(np.isfinite(metric)) or
            np.any(metric<=0) or any(path.shape!=(8,3) or
            not np.all(np.isfinite(path)) for path in paths) or
            any(not np.array_equal(np.asarray(row['metric'],float),metric) or
            not np.isfinite(row['training_cost']) or
            not np.isfinite(row['known_cost']) for row in rows)):
        raise ValueError('finite matched physical forecast paths required')
    spread=max(float(np.max(np.linalg.norm((a-b)*metric,axis=1)))
               for index,a in enumerate(paths) for b in paths[index+1:])
    stops=all(row['converged'] for row in rows)
    objectives=all(row['training_cost']<=row['known_cost']+.01
                   for row in rows)
    return dict(passed=bool(stops and objectives and spread<=.1),
                all_numerically_stopped=stops,
                all_objectives_within_known_reference=objectives,
                maximum_later_path_spread_m=spread,
                scientific_decision='abstain')
