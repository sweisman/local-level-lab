# SPDX-License-Identifier: AGPL-3.0-or-later
"""Truth-free comparison of methods with nearly tied training starts."""

import math


def compare_start_sets(reference, candidate, *, relative_cost_tolerance,
                       forecast_tolerance_m):
    """Check start-choice stability without selecting from withheld observations.

    The caller must supply one common binding for the training input and the
    exact forecast time grid. This is a method check, not a scientific decision.
    """
    if (type(relative_cost_tolerance) not in (int, float)
            or not math.isfinite(relative_cost_tolerance)
            or not 0 < relative_cost_tolerance < 1
            or type(forecast_tolerance_m) not in (int, float)
            or not math.isfinite(forecast_tolerance_m)
            or forecast_tolerance_m <= 0):
        raise ValueError('positive finite tolerances required')
    if not reference or not candidate:
        raise ValueError('nonempty matched start sets required')

    def checked(rows):
        selected = {}
        for row in rows:
            if not isinstance(row, dict) or type(row.get('start')) is not int or row['start'] < 0:
                raise ValueError('nonnegative integer start required')
            start = row['start']
            if start in selected:
                raise ValueError('duplicate start')
            cost = row.get('training_cost')
            if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                raise ValueError('finite nonnegative training cost required')
            forecast = row.get('forecast')
            if (not isinstance(forecast, list) or not forecast or any(
                    not isinstance(point, list) or len(point) != 3 or any(
                        type(value) not in (int, float) or not math.isfinite(value)
                        for value in point) for point in forecast)):
                raise ValueError('finite three-coordinate forecast required')
            if not isinstance(row.get('binding'), str) or not row['binding']:
                raise ValueError('common input and forecast-grid binding required')
            if type(row.get('passed')) is not bool:
                raise ValueError('explicit fit qualification required')
            selected[start] = row
        return selected

    ref, cand = checked(reference), checked(candidate)
    if set(ref) != set(cand):
        raise ValueError('matched start identities required')
    if len({row['binding'] for row in (*ref.values(), *cand.values())}) != 1:
        raise ValueError('same input and forecast-grid binding required')
    if len({len(row['forecast']) for row in (*ref.values(), *cand.values())}) != 1:
        raise ValueError('same forecast grid required')

    ref_primary = min(ref, key=lambda start: (ref[start]['training_cost'], start))
    cand_primary = min(cand, key=lambda start: (cand[start]['training_cost'], start))

    def close(a, b):
        return abs(a-b) <= relative_cost_tolerance*max(abs(a), abs(b))

    ref_min, cand_min = ref[ref_primary]['training_cost'], cand[cand_primary]['training_cost']
    ref_ties = [start for start in sorted(ref) if close(ref[start]['training_cost'], ref_min)]
    cand_ties = [start for start in sorted(cand) if close(cand[start]['training_cost'], cand_min)]
    cost_agreement = all(close(ref[start]['training_cost'], cand[start]['training_cost'])
                         for start in ref)
    cross_maximum = max(
        math.dist(a, b)
        for i in ref_ties for j in cand_ties
        for a, b in zip(ref[i]['forecast'], cand[j]['forecast'], strict=True))
    all_fits_pass = all(row['passed'] for row in (*ref.values(), *cand.values()))
    selection_stable = ref_primary in cand_ties and cand_primary in ref_ties
    return dict(equivalent=bool(all_fits_pass and selection_stable and cost_agreement
                                and cross_maximum <= forecast_tolerance_m),
                all_fits_pass=all_fits_pass,
                reference_primary=ref_primary,
                candidate_primary=cand_primary,
                reference_near_ties=ref_ties,
                candidate_near_ties=cand_ties,
                selection_stable=selection_stable,
                same_start_costs_agree=cost_agreement,
                cross_start_maximum_m=cross_maximum,
                relative_cost_tolerance=relative_cost_tolerance,
                forecast_tolerance_m=forecast_tolerance_m,
                forecast_epochs=len(ref[ref_primary]['forecast']))
