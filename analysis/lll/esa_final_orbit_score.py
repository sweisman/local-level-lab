# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare unchanged ESA forecasts against the orbit-only GPS variation."""

from contextlib import closing
import json
import math
from pathlib import Path

from .airquantumgrav_geographic_report import error_metrics
from .esa_alternate_ppp_scoring import MODELS, rank_setting, score_errors
from .esa_final_orbit_replay import BLOCK, COUNT, ID, _baseline_rows, _task
from .esa_fit_adjusted_forecast_report import position_errors_neu
from .esa_rinex_code_comparison import FOLDER, MATRIX, MATRIX_SHA, PPP
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ORBIT_MANIFEST_SHA = 'b800cb851ba27924e5f3ec48be96e2af516e2c5710a5e92f0e6487c7e31ff191'
ORIGINAL_COMPARISON = FOLDER + 'esa-rinex-code-comparison-result.json'
ORIGINAL_SHA = 'b7484e969b6dfbafc9ec99b67ad5ccc43600bde1b4ede8d081915a393a0fad44'
PPP_SHA = '52b592c5c572fb224e3224cee422b65e4ade2ca5babbd058a126de47dc881337'
RESULT = FOLDER + 'esa-final-orbit-score-result.json'
TRAIN, LATER = 400, 120
COORDINATES = ('latitude_rad', 'longitude_rad', 'ellipsoid_height_m')


def _load(root, name, expected):
    raw = (root / name).read_bytes()
    if digest(raw) != expected:
        raise ValueError('sealed prior comparison differs: ' + name)
    return json.loads(raw)


def _coordinates(rows):
    return [[row[key] for key in COORDINATES] for row in rows]


def score_forecast_paths(root, store, paths, previous, *, comparison_key):
    """Rescore sealed forecasts and reproduce the full-set broadcast control."""
    import numpy as np

    settings = _load(root, PPP, PPP_SHA)['settings']
    rows = []
    with closing(ClosedStudy(root, MATRIX, store=store)) as matrix:
        if matrix.completion['manifest_sha256'] != MATRIX_SHA:
            raise ValueError('unexpected forecast study')
        for setting, reference in zip(settings, previous['forecast_comparisons'], strict=True):
            profile, law = setting['profile'], setting['law']
            if (profile, law) != (reference['profile'], reference['law']):
                raise ValueError('forecast setting mismatch')
            comparisons = {name: {} for name in paths}
            for model in MODELS:
                start = setting['primary_start'][model]
                raw = matrix.artifact(f'{model}-{int(profile)}-{law}-{start}', 'forecast.json', raw=True)
                forecast = json.loads(raw)
                if (digest(raw) != setting['forecast_sha256'][model]
                        or forecast['prediction_receiver_positions_used'] is not False
                        or forecast['training_epochs'] != TRAIN or forecast['prediction_epochs'] != LATER):
                    raise ValueError('expected sealed earlier-only fit and forecast')
                for name, path in paths.items():
                    errors = position_errors_neu(forecast['coordinates'][TRAIN:], path)
                    comparisons[name][model] = score_errors(errors, np.zeros((LATER, 3)), range(LATER))
            if comparisons['broadcast'] != reference['by_code']['dual_frequency']['scores']:
                raise ValueError('original broadcast scores did not reproduce')
            rows.append(dict(profile=profile, law=law, **{comparison_key: {name: dict(
                scores=scores, ranking=rank_setting(scores)) for name, scores in comparisons.items()}}))
    return rows


def build(root):
    import numpy as np

    previous = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']
    indices = previous['matched_code_indices']
    if len(indices) != TRAIN + LATER or indices != sorted(set(indices)):
        raise ValueError('original ordered GPS matches required')
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as orbit:
            if (orbit.completion['manifest_sha256'] != ORBIT_MANIFEST_SHA
                    or orbit.completion['state'] != 'complete'
                    or not orbit.summary['passed'] or orbit.summary['charged']['bound_calls'] != COUNT):
                raise ValueError('completed matched orbit run required')
            baseline = _baseline_rows(orbit.input('baseline', raw=True))
            epochs = [row for start in range(0, COUNT, BLOCK) for row in
                      json.loads(orbit.artifact(_task(start)['identity'], 'orbit-epochs.json', raw=True))]
            if (len(epochs) != COUNT or any(
                    not row['passed'] or row['gps_week_seconds'] != ref['gps_week_seconds']
                    or row['satellites'] != ref['dual_frequency']['used_satellites']
                    for row, ref in zip(epochs, baseline, strict=True))):
                raise ValueError('unchanged satellite sets and full epoch coverage required')
            orbit_summary_hash = orbit.completion['summary_sha256']
        later = indices[TRAIN:]
        paths = dict(
            broadcast=_coordinates([baseline[i]['dual_frequency'] for i in later]),
            final_orbit=_coordinates([epochs[i] for i in later]),
        )
        rows = score_forecast_paths(root, store, paths, previous, comparison_key='by_orbit')
    effects = [row['final_minus_broadcast_neu_m'] for row in epochs]
    return dict(
        observed_recording='187', epochs=len(epochs), later_epochs=LATER,
        orbit_manifest_sha256=ORBIT_MANIFEST_SHA, orbit_summary_sha256=orbit_summary_hash,
        broadcast_comparison_sha256=ORIGINAL_SHA, prior_forecast_binding_sha256=PPP_SHA,
        all_effects=error_metrics(effects), later_effects=error_metrics([effects[i] for i in later]),
        orbit_evaluations=sum(row['orbit_range_evaluations'] for row in epochs),
        maximum_satellite_displacement_m=max(max(row['satellite_displacements_m']) for row in epochs),
        median_broadcast_range_rms_m=float(np.median([row['broadcast_rms_m'] for row in epochs])),
        median_final_orbit_range_rms_m=float(np.median([row['final_orbit_rms_m'] for row in epochs])),
        signed_changes_neu_m=effects, forecast_comparisons=rows,
        new_inertial_fits=0, new_forecast_propagations=0, protected_reads=0,
        absolute_receiver_accuracy_established=False, scientific_decision='abstain',
    )


if __name__ == '__main__':
    root = Path.cwd()
    result = build(root)
    raw = encoded(result)
    path = root / RESULT
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('existing result differs from the matched replay')
    else:
        atomic(path, raw)
    print(encoded(dict(epochs=result['epochs'], later_effects=result['later_effects'],
                       result_sha256=digest(raw))).decode(), end='')
