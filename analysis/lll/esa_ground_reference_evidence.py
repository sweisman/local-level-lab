# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the permanent Nuuk development evidence without refitting or publishing raw AIR1."""
import argparse
from contextlib import closing, nullcontext
import json
import math
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy


BASE = 'docs/prediction-observed-development/'
INDEX = BASE+'esa-ground-reference-evidence-v1.json'
CURRENT_INDEX = BASE+'esa-ground-reference-evidence-v2.json'
COMBINED_INDEX = BASE+'esa-ground-reference-evidence-v3.json'
MUSEUM_INDEX = BASE+'esa-ground-reference-evidence-v4.json'
APRON_INDEX = BASE+'esa-ground-reference-evidence-v5.json'
CARRIER_INDEX = BASE+'esa-ground-reference-evidence-v6.json'
NUUK_INDEX = BASE+'esa-ground-reference-evidence-v7.json'
QAQ_INTAKE = 'esa-qaq-ground-intake.json'
QAQ_INTAKE_SHA = '0cd8b21d3015f105d750d29290016f3eac353e85d2ab65c6cab4cfaeeb82c6e8'
ERROR_BUDGET = 'esa-reference-error-budget-v1.json'
ERROR_BUDGET_SHA = '9c0678e6c6c75e5fe45ff31d0c9905669e3b0789bee926570ba7c4a13f7347a6'
INTAKE = 'esa-nuuk-ground-intake.json'
INTAKE_SHA = 'bb9ee437d5031e72fdb57908d8f535400c1899317a6b2c00c3f8ec6f1fb2ce6b'
# Filename, SHA-256, study, task, and sealed artifact name minus .json.
STUDIES = (
    ('esa-nkar-cadence-result.json', '461e5385024e7925ffb276a41898ac66743d9c1891a9e9049e6440569c544eee',
     'esa-nkar-cadence-v1', 'nkar-carrier-grid', 'nkar-carrier-cadence'),
    ('esa-nuuk-ground-phase-result.json', '2feb085e4c7d2895bb3f8a49775e83b8982f9581998b7e23dcb8443218b2f012',
     'esa-nuuk-phase-v2', 'nuuk-phase', 'nuuk-ground-phase'),
    ('esa-nuuk-between-samples-result.json', '2baf051f00af95e8ec9021bcdd84bda30fef442c61158b8e2d8b015518e64f75',
     'esa-nuuk-between-samples-v1', 'nuuk-between-samples', 'nuuk-between-samples'),
    ('esa-nuuk-between-carrier-result.json', 'cd6bfb15696dae2bb202604ccb902fc77cf16a8552912b074416aa913a076b7b',
     'esa-nuuk-between-carrier-v1', 'nuuk-between-carrier', 'nuuk-between-carrier'),
    ('esa-ground-grid-score-result.json', '00df98ad149f147af6a25e3d8fe7fb186513d2b62ec61e85b2a8cbb33425f106',
     'esa-ground-grid-score-v1', 'ground-grid-score', 'ground-grid-score'),
    ('esa-nuuk-phase-transfer-result.json', '0779e5d7362e17176ade66268f45276b2158db7989ff4a1c1dacd01b48a4d58e',
     'esa-nuuk-phase-transfer-v1', 'nuuk-phase-transfer', 'nuuk-phase-transfer'),
    ('esa-nuuk-phase-position-result.json', 'a9e3163db2a54adb59b9f65f225599e860feb6720fd856568b3808b9bf6b2528',
     'esa-nuuk-phase-position-v1', 'nuuk-phase-position', 'nuuk-phase-position'),
)
ADDITIONAL = (
    ('esa-nuuk-orbit-clock-result.json', '40b586d4e848468e41482df75353efc8d93256cf0593e8eca8a3635d7cd7261d',
     'esa-nuuk-orbit-clock-v1', 'nuuk-orbit-clock', 'nuuk-orbit-clock'),
    ('esa-carrier-score-bound-result.json', '12c0f807d4e710cf05fc3dc521ad9e05f2ba69df8e53f95bcf47dd541b6295bb',
     'esa-carrier-score-bound-v1', 'carrier-score-bound', 'carrier-score-bound'),
    ('esa-carrier-anchor-error-result.json', '173b6541028b1e5db7cc64cec2903788a1b34eb5139d93dfa6e85eb9fdffa1fc',
     'esa-carrier-anchor-error-v1', 'carrier-anchor-error', 'carrier-anchor-error'),
    ('esa-carrier-score-cadence-result.json', '3c992f6a0c5200651f89e0c773a6b56f2b94b1261a9c751495cee0c9bcde1bda',
     'esa-carrier-score-cadence-v1', 'carrier-score-cadence', 'carrier-score-cadence'),
)
COMBINED = (
    ('esa-qaq-ground-score-result.json', '98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185',
     'esa-qaq-ground-score-v1', 'qaq-ground-score', 'qaq-ground-score'),
    ('esa-qaq-phase-transfer-result.json', '50508c8bc9a6777b44b27533dee56fd977c7874e4a3f1fc46d247f8a2493d61b',
     'esa-qaq-phase-transfer-v1', 'qaq-phase-transfer', 'qaq-phase-transfer'),
    ('esa-carrier-range-remainder-result.json', '8db0d4ae89708015fa6b8026aac2da522fbbb4aabd64f0f9501ad722abc67844',
     'esa-carrier-range-remainder-v1', 'carrier-range-remainder', 'carrier-range-remainder'),
)
MUSEUM = (
    ('esa-nkar-ground-score-result.json', 'ab8fcb08bbf97d43538e0020649fce3f810bd4d488b1c52dadbc93ae5690aa75',
     'esa-nkar-ground-score-v1', 'nkar-ground-score', 'nkar-ground-score'),
    ('esa-nkar-phase-transfer-result.json', 'c43f33005a7844453ccd6c7c2d1ac094eb615f2799821b7b4564104b17c0740c',
     'esa-nkar-phase-transfer-v1', 'nkar-phase-transfer', 'nkar-phase-transfer'),
    ('esa-nkar-antenna-result-v2.json', 'cf7774271aaf6f3907383f0eadcb5b989a5e9359fa6ae3bde4ceaa32d2c724c4',
     'esa-nkar-antenna-v2', 'nkar-antenna', 'nkar-antenna'),
    ('esa-nkar-phase-windup-result.json', '4f3ef1bce94b412553e895010b5ef6bdf46eba5a5505cbf9cd2a2036203e0b57',
     'esa-nkar-phase-windup-v1', 'phase-windup', 'phase-windup'),
)
MUSEUM_BUDGET = ('esa-nkar-error-budget-v1.json',
                 '803317aa17a3e6ed98f0bbe3f8434cdfa9e0313b1ff7ac30950e0add2d820cc6')
TILT_BUDGET = ('esa-phase-windup-budget.json',
               '103daedec51b2bfd5c82a94bd531572b5ec93195322a437ad69952d43f363244')


def _public(root, name, expected):
    raw = (root/BASE/name).read_bytes()
    if digest(raw) != expected:
        raise ValueError('public report hash differs: '+name)
    value = json.loads(raw)
    fits = [field for key, field in value.items() if key.startswith('new_') and key.endswith('fits')]
    if (value['scientific_decision'] != 'abstain' or value.get('protected_reads', value.get('reserved_reads')) != 0
            or not fits or any(fits) or value.get('passed', True) is not True):
        raise ValueError('the development evidence must retain its abstention and fit/read counts')
    return value


def _phase_transfer(value):
    """Recompute the published residual comparison from the public signed values."""
    import numpy as np

    from .gnss_position import GAMMA
    from .ground_phase_transfer import compare_transfer

    training, withheld = value['training_indices'], value['withheld_indices']
    a = np.asarray(value['aircraft_band_residual_m'])
    b = np.asarray(value['ground_band_residual_m'])
    scale = np.array([GAMMA, -1.])/(GAMMA-1.)
    for band, x, y in (('ionosphere_free', a@scale, b@scale), ('L1', a[:, :, 0], b[:, :, 0]), ('L2', a[:, :, 1], b[:, :, 1])):
        calculated = compare_transfer(x, y, training=training, withheld=withheld)
        expected = value['summary'][band]
        for k in ('training', 'withheld'):
            if not np.allclose([calculated[k][m] for m in expected[k]], list(expected[k].values()),
                               rtol=1e-12, atol=1e-14):
                raise ValueError('public ground range comparison differs')
        if not np.isclose(calculated['trained_gain'], expected['trained_gain'], rtol=1e-12, atol=1e-14):
            raise ValueError('public earlier ground multiplier differs')


def _equal_values(expected, actual):
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(_equal_values(expected[k], actual[k]) for k in expected)
    if isinstance(expected, (tuple, list)):
        return len(expected) == len(actual) and all(_equal_values(x, y) for x, y in zip(expected, actual))
    if type(expected) is float:
        return math.isclose(expected, actual, rel_tol=2e-12, abs_tol=2e-13)
    return expected == actual


def _require_values(expected, actual, label):
    if not _equal_values(expected, actual):
        raise ValueError('public carrier evidence differs: '+label)


def verify_carrier_reports(products, score, anchors, cadence, transfer=None):
    """Recompute the public arithmetic without opening raw receiver records."""
    import numpy as np

    from .carrier_anchor_error import anchor_uncertainty
    from .carrier_score_cadence import project_cadence
    from .esa_nuuk_orbit_clock import summarize
    from .gnss_position import GAMMA
    from .shared_motion_carrier import signed_product_comparison

    rows = products['rows']
    support = [row['common_satellites'] for row in rows]
    for row, satellites in zip(rows, support, strict=True):
        base = [row['fixed_path_residual_m'][row['satellites'].index(prn)] for prn in satellites]
        expected = signed_product_comparison(row['common_required_m'], base, row['orbit_m'], row['clock_m'])
        _require_values({key: value.tolist() for key, value in expected.items()},
                        {key: row[key] for key in expected}, 'signed orbit and clock change')
    _require_values(summarize(rows), products['product_summary'], 'orbit and clock summary')

    cert = score['bound']
    dual = cert['dual_weights']
    count = sum(map(len, support))
    _require_values([count, count], [len(dual), cert['range_values']], 'carrier weight support')
    leverage = math.sqrt(count*math.fsum(w*w for w in dual))
    gap = score['score_gap']
    remaining = gap-cert['acceleration_rms_to_score']*score['test_acceleration_rms_mps2']
    _require_values(leverage, cert['range_rms_to_score'], 'carrier score coefficient')
    _require_values(max(0., remaining)/leverage, score['minimum_range_rms_m'], 'minimum carrier error')

    times = [score['endpoint_gps_s'][0], *(row['seconds'] for row in rows)]
    fixed = [times[0], *score['ground_anchors_gps_s'], times[-1]]
    _require_values(fixed, anchors['anchors_gps_s'], 'anchor grid')
    expected = anchor_uncertainty(anchors['signed_anchor_weights'], free_count=len(times)-len(fixed),
                                  free_weight_norm=cert['residual_weight_norm'])
    _require_values(expected, anchors['anchor_uncertainty'], 'anchor score coefficients')
    for limit, row in zip((0., .0005, .001, .0015), anchors['tolerances'], strict=True):
        available = max(0., remaining-leverage*limit)
        _require_values(dict(range_rms_m=limit, maximum_anchor_axis_error_m=available/expected['all_anchor_axis_to_score'],
                             maximum_common_axis_error_m=available/expected['common_axis_to_score']), row, 'anchor tolerance')

    observed = [(times.index(a), times.index(b)) for a, b in zip(fixed[1:-2], fixed[2:-1])]
    ground_rows = cadence['cadences']['observed_30s']['intervals']
    available = {prn for row in ground_rows for prn in row['satellites']}
    if transfer is not None:
        available = transfer['satellites']
        ground = np.asarray(transfer['ground_band_residual_m'])@ (np.array([GAMMA, -1.])/(GAMMA-1.))
        for i, row in zip(transfer['withheld_indices'], ground_rows, strict=True):
            epoch = [times[row['first']], times[row['last']]]
            _require_values(transfer['times'][i:i+2], epoch, 'ground residual time')
            subtotal = [float(ground[i, available.index(prn)]) for prn in row['satellites']]
            _require_values(subtotal, row['signed_ground_total_m'], 'ground residual support')
        _require_values(transfer['summary']['ionosphere_free']['trained_gain'], cadence['earlier_multiplier'], 'ground gain')
    grids = {'observed_30s': (observed, available),
             'ideal_30s': ([(i, i+60) for i in range(0, len(rows), 60)], None),
             'ideal_1s': ([(i, i+2) for i in range(0, len(rows), 2)], None)}
    for name, (grid, prns) in grids.items():
        projected = project_cadence(support, dual, grid, available=prns)
        saved = cadence['cadences'][name]
        _require_values(projected, saved | {'intervals': [
            {key: value for key, value in row.items() if key != 'signed_ground_total_m'}
            for row in saved['intervals']]}, name+' score projection')
    projected = [math.fsum(w*r for w, r in zip(row['aggregate_weights'], row['signed_ground_total_m'], strict=True))
                 for row in ground_rows]
    _require_values(projected, cadence['ground_score_by_interval'], 'signed ground projection')
    total = math.fsum(projected)
    _require_values(total, cadence['ground_score_equivalent'], 'total ground projection')
    _require_values(total*cadence['earlier_multiplier'], cadence['adjusted_ground_score_equivalent'], 'adjusted projection')


def _verify_runtime(root, store, indexed, studies):
    source_count = input_count = 0
    for value, (_, _, study_id, identity, artifact) in zip(indexed, studies, strict=True):
        with closing(ClosedStudy(root, 'data/'+study_id, store=store)) as study:
            expected = study.envelope(identity)
            result = study.artifact(identity, artifact+'.json')
            if (set(study.rows) != {identity} or study.completion != value['completion']
                    or result != expected['result'] or expected['charged'] != study.tasks[identity]['limits']
                    or any(value[k] != v for k, v in result.items())):
                raise ValueError('sealed result differs from the public report: '+study_id)
            for name, sha in study.manifest['sources'].items():
                study.read('source-freeze/'+name, sha, raw=True)
                source_count += 1
            for key in study.manifest['inputs']:
                study.input(key, raw=True)
                input_count += 1
    with closing(ClosedStudy(root, 'data/esa-nuuk-phase-v2', store=store)) as corrected:
        earlier = corrected.input('previous_receipt')
    with closing(ClosedStudy(root, 'data/esa-nuuk-phase-v1', store=store)) as failed:
        if (failed.completion != earlier['completion'] or failed.completion['state'] != 'terminal'
                or failed.envelope('nuuk-phase') != earlier['failure']
                or any(earlier['failure']['charged'].values()) or earlier['failure']['result']['passed']):
            raise ValueError('the earlier accounting failure must be preserved')
    return dict(runtime_studies=len(studies), failed_prechecks=1, source_bindings=source_count, input_bindings=input_count)


def verify_qaq_reports(intake, products, score, ground, later):
    from .carrier_score_cadence import project_cadence
    from .esa_qaq_phase_transfer import transfer

    rows = products['rows']
    start, stop = score['endpoint_gps_s']
    if (intake['station'] != 'QAQ100GRL' or ground['station'] != intake['station']
            or intake['coverage_counts'] != {'matched': 121} or intake['target_epochs'] != 121
            or ground['intake_sha256'] != QAQ_INTAKE_SHA or ground['matched_intervals'] != 120
            or ground['planned_intervals'] != 120 or ground['aircraft_accuracy_established']
            or ground['score_gap'] != score['score_gap'] or later['score_gap'] != score['score_gap']
            or later['later_sha256'] != COMBINED[0][1] or len(ground['intervals']) != 120):
        raise ValueError('the original Qaqortoq development-only overlap is required')
    counts = intake['score_pair_satellite_counts']
    continuous = {r['time_s']: {int(sv[1:]) for sv in r['continued']} for r in intake['rows']}
    samples = ground['intervals']
    intervals, allowed, a_scores, g_scores, held = [], {}, [], [], []
    support = [r['common_satellites'] for r in rows]
    for i, (row, raw_count) in enumerate(zip(samples, counts, strict=True)):
        b, c = 2*i, 2*i+2
        interval = (b, c)
        _require_values([b, c, start+i, start+i+1], [row[k] for k in
                       ('first', 'last', 'start_gps_s', 'stop_gps_s')], 'Qaqortoq time pairing')
        prns = row['satellites']
        if not 5 <= len(prns) <= raw_count or not set(prns) <= continuous[row['stop_gps_s']]:
            raise ValueError('public carrier evidence differs: Qaqortoq support count')
        allowed[interval] = prns
        intervals.append(interval)
        a = [sum(rows[j]['fixed_residual_m'][support[j].index(prn)] for j in range(b, c)) for prn in prns]
        mean = math.fsum(a)/len(a)
        a = [x-mean for x in a]
        g, weights = row['ground_range_m'], row['aggregate_weights']
        _require_values(a, row['air_range_m'], 'Qaqortoq aircraft range')
        a_scores.append(math.fsum(w*x for w, x in zip(weights, a, strict=True)))
        g_scores.append(math.fsum(w*x for w, x in zip(weights, g, strict=True)))
        _require_values((a_scores[-1], g_scores[-1]), (row['aircraft_score'], row['ground_score']), 'Qaqortoq interval score')
        held.append((row['start_gps_s'], a, g))
    _require_values(stop, samples[-1]['stop_gps_s'], 'Qaqortoq last time')
    projection = project_cadence(support, score['bound']['dual_weights'], intervals, interval_satellites=allowed)
    _require_values(projection['intervals'], [{k: row[k] for k in ('first', 'last', 'satellites', 'aggregate_weights')}
                                            for row in samples], 'Qaqortoq interval weights')
    _require_values({k: val for k, val in projection.items() if k != 'intervals'},
                    {k: ground[k] for k in projection if k != 'intervals'}, 'Qaqortoq projected weights')
    air, station = math.fsum(a_scores), math.fsum(g_scores)
    _require_values([air, station, air-station], [ground[k] for k in ('aircraft_score_equivalent', 'ground_score_equivalent',
                                                                   'air_minus_ground_score_equivalent')], 'Qaqortoq total score')
    training = [(r['start_gps_s'], r['aircraft_m'], r['ground_m']) for r in later['training_rows']]
    _require_values(list(range(388215, 388550)), [r[0] for r in training], 'Qaqortoq disjoint earlier times')
    summary = transfer(training, held)
    _require_values(summary, {k: later[k] for k in summary}, 'Qaqortoq chronological range transfer')
    shift = -station*summary['trained_gain']
    _require_values([shift, air+shift], [later['later_score_shift'], later['later_score_equivalent']], 'Qaqortoq transfer score')


def verify_range_remainder(products, score, remainder):
    from fractions import Fraction

    from .carrier_range_remainder import bound_score_remainder, position_cap

    counts = [len(row['common_satellites']) for row in products['rows']]
    times = [score['endpoint_gps_s'][0], *score['ground_anchors_gps_s'], score['endpoint_gps_s'][1]]
    low, high = remainder['measured_final_satellite_radius_m']
    if (times != remainder['anchor_times_gps_s'] or remainder['range_endpoints'] != 2*sum(counts)
            or not 20e6 < low <= high < 40e6 or score['score_gap'] != remainder['score_gap']
            or remainder['parent_sha256'] != ADDITIONAL[1][1]):
        raise ValueError('public carrier evidence differs: geometric assurance domain')
    args = (score['bound']['dual_weights'], counts, remainder['metric'], remainder['max_absolute_path_height_m'])
    unit = bound_score_remainder(*args, 1)['max_score_remainder']
    cap = position_cap(times, 1., .002)
    if unit != Fraction(remainder['exact_score_bound_per_square_m']):
        raise ValueError('public carrier evidence differs: geometric coefficient')
    _require_values([float(cap), float(unit), float(unit*cap*cap)],
                    [remainder[k] for k in ('representative_axis_cap_m', 'score_bound_per_square_m',
                                            'representative_score_remainder')], 'geometric error bound')


def verify_museum(products, score, qaq, ground, transfer, antenna):
    """Recompute the matched range, chronological transfer and antenna scores."""
    from .esa_nkar_phase_transfer import compare_transfer, later_pair
    from .esa_nkar_score import compare_score

    start, stop = score['endpoint_gps_s']
    rows = ground['intervals']
    if (stop-start != 120 or start != int(start) or ground['matched_intervals'] != 120 or len(rows) != 120
            or ground['bound_sha256'] != ADDITIONAL[1][1] or ground['orbit_sha256'] != ADDITIONAL[0][1]
            or transfer['score_gap'] != score['score_gap'] or ground['score_gap'] != score['score_gap']
            or antenna['score_gap'] != score['score_gap'] or antenna['nkar_sha256'] != MUSEUM[0][1]):
        raise ValueError('the complete unchanged Nuuk Museum comparison is required')
    start, stop = int(start), int(stop)
    by_time = {row['start_gps_s']: row for row in rows}
    _require_values(list(range(start, stop)), list(by_time), 'Nuuk Museum time grid')

    def read_ground(first, last, candidates):
        row = by_time[first]
        return dict(zip(row['satellites'], row['ground_range_m'], strict=True))

    grid = {time: time for time in range(start, stop+1)}
    projected = compare_score(products['rows'], score['bound']['dual_weights'], start, grid, read_ground)
    _require_values(projected, {key: ground[key] for key in projected}, 'Nuuk Museum matched range projection')
    held = [later_pair(a, b) for a, b in zip(rows, qaq['intervals'], strict=True)]
    _require_values(held, transfer['withheld_rows'], 'Nuuk Museum shared withheld rows')
    earlier = transfer['training_rows']
    _require_values(list(range(388215, 388550)), [r['start_gps_s'] for r in earlier],
                    'Nuuk Museum separate transfer times')
    computed = compare_transfer(earlier, held, score_gap=score['score_gap'])
    _require_values(computed, {key: transfer[key] for key in computed}, 'Nuuk Museum chronological transfer')

    sums = {key: [] for key in ('air_transmitter', 'ground_transmitter', 'ground_receiver')}
    for before, after in zip(rows, antenna['matched'], strict=True):
        _require_values(
            {key: before[key] for key in ('start_gps_s', 'satellites', 'air_range_m', 'ground_range_m')},
            {key: after[key] for key in ('start_gps_s', 'satellites', 'air_range_m', 'ground_range_m')},
            'antenna receiver grid')
        _require_values(before['aggregate_weights'], after['weights'], 'antenna score weights')
        for key in sums:
            sign = -1 if key == 'air_transmitter' else 1
            sums[key].extend(sign*w*x for w, x in zip(after['weights'], after[key+'_m'], strict=True))
    corrections = {key: math.fsum(values) for key, values in sums.items()}
    signed = math.fsum(corrections.values())
    _require_values(corrections, antenna['signed_air_minus_ground_score_shifts'], 'phase centre components')
    _require_values([signed, signed/score['score_gap']],
                    [antenna['signed_total_shift'], antenna['signed_shift_per_gap']], 'phase centre shift')


def verify_windup(score, ground, phase):
    """Recompute phase adjustments without original carrier files or attitude products."""
    if (phase['score_gap'] != score['score_gap'] or phase['antenna_sha256'] != MUSEUM[2][1]
            or len(phase['air']) != 240 or len(phase['per_pair_minima_deg']) != 240
            or len(phase['matched']) != 120 or len(ground['intervals']) != 120):
        raise ValueError('public wind-up evidence requires the original complete grid')
    air, station, before, after = [], [], [], []
    for row, fixed in zip(phase['matched'], ground['intervals'], strict=True):
        _require_values([fixed['start_gps_s'], fixed['satellites']],
                        [row['start_gps_s'], row['satellites']], 'wind-up time and satellites')
        for a, g, da, dg, w in zip(fixed['air_range_m'], fixed['ground_range_m'],
                row['air'], row['ground'], fixed['aggregate_weights'], strict=True):
            air.append(-w*da)
            station.append(w*dg)
            before.append(a-g)
            after.append(a-g-da+dg)
    _require_values(len(air), phase['matched_values'], 'wind-up matched range count')
    shifts = dict(air=math.fsum(air), ground=math.fsum(station))
    _require_values(shifts, phase['signed_shifts'], 'wind-up score components')
    full = -math.fsum(w*x for w, x in zip(score['bound']['dual_weights'],
                                        (v for row in phase['air'] for v in row), strict=True))
    rms = [math.sqrt(math.fsum(v*v for v in values)/len(values)) for values in (before, after)]
    _require_values([math.fsum(shifts.values()), full, min(phase['per_pair_minima_deg']), *rms],
                    [phase['signed_total_shift'], phase['signed_full_air_shift'], phase['minimum_air_elevation_deg'],
                     phase['rms_m']['uncorrected'], phase['rms_m']['corrected']], 'wind-up score and range summaries')


def verify(root, *, runtime=False, version=1):
    if version not in (1, 2, 3, 4, 5, 6, 7):
        raise ValueError('unknown evidence index version')
    intake = _public(root, INTAKE, INTAKE_SHA)
    if (intake['recording'] != 187 or intake['match_status'] != {'matched': 17}
            or digest((root/intake['excerpt']).read_bytes()) != intake['excerpt_sha256']):
        raise ValueError('the verified permanent station excerpt and times are required')
    studies = STUDIES if version == 1 else STUDIES+ADDITIONAL
    if version >= 3:
        studies += COMBINED
    if version >= 4:
        studies += MUSEUM
    indexed = [_public(root, name, sha) for name, sha, *_ in studies]
    transfer = indexed[len(STUDIES)-2]
    _phase_transfer(transfer)
    if version >= 2:
        extra = indexed[len(STUDIES):len(STUDIES)+len(ADDITIONAL)]
        verify_carrier_reports(*extra, transfer=transfer)
    value = dict(version=f'esa-ground-reference-evidence-v{version}', development_flight_groups=1,
                 recording=187, reserved_groups_opened=0, ground_station='NUUK00GRL', ground_epochs=17,
                 high_rate_ground_coverage_verified=False, aircraft_error_coverage_qualified=False,
                 intake=dict(path=BASE+INTAKE, sha256=INTAKE_SHA),
                 studies=[dict(path=BASE+name, sha256=sha, study=study_id, completion=row['completion'])
                          for row, (name, sha, study_id, _, _) in zip(indexed, studies, strict=True)])
    if version >= 3:
        from .esa_reference_error_budget import evidence

        products, score, _, _ = extra
        offset = len(STUDIES)+len(ADDITIONAL)
        qaq, later, remainder = indexed[offset:offset+len(COMBINED)]
        reference = _public(root, QAQ_INTAKE, QAQ_INTAKE_SHA)
        verify_qaq_reports(reference, products, score, qaq, later)
        verify_range_remainder(products, score, remainder)
        budget = (root/BASE/ERROR_BUDGET).read_bytes()
        if digest(budget) != ERROR_BUDGET_SHA or budget != encoded(evidence(root)):
            raise ValueError('the public joint error budget differs')
        value.update(distant_high_rate_ground_coverage_verified=True,
                     distant_ground_intake=dict(path=BASE+QAQ_INTAKE, sha256=QAQ_INTAKE_SHA, station='QAQ100GRL'),
                     joint_error_budget=dict(path=BASE+ERROR_BUDGET, sha256=ERROR_BUDGET_SHA, decision='abstain'))
    if version >= 4:
        from .esa_nkar_error_budget import evidence as museum_budget
        from .esa_phase_windup_budget import evidence as tilt_budget

        ground, transfer, antenna, phase = indexed[-len(MUSEUM):]
        verify_museum(products, score, qaq, ground, transfer, antenna)
        verify_windup(score, ground, phase)
        _require_values(museum_budget(root), _public(root, *MUSEUM_BUDGET), 'Nuuk Museum error budget')
        tilt = _public(root, *TILT_BUDGET)
        recalculated = tilt_budget(root)
        fields = ('results', 'covered_example_score_allowance', 'equal_covered_example_allowance_tilt_deg')
        _require_values([recalculated[key] for key in fields], [tilt[key] for key in fields], 'wind-up tilt budget')
        value.update(nuuk_museum_high_rate_ground_coverage_verified=True,
                     nuuk_museum_error_budget=dict(path=BASE+MUSEUM_BUDGET[0], sha256=MUSEUM_BUDGET[1], decision='abstain'),
                     ideal_tilt_budget=dict(path=BASE+TILT_BUDGET[0], sha256=TILT_BUDGET[1]))
    public_reports = 1+len(studies)+2*(version >= 3)+2*(version >= 4)
    with (closing(ArchiveStore(root)) if runtime else nullcontext()) as store:
        status = _verify_runtime(root, store, indexed, studies) if runtime else {}
        if version >= 5:
            from .esa_apron_evidence import evidence as apron_evidence

            apron, checks = apron_evidence(root, store=store)
            value['apron'] = apron
            status.update(checks)
            public_reports += 1+len(apron['studies'])+len(apron['technical_stops'])
            if runtime:
                status['apron_runtime_studies'] = len(apron['studies'])
                status['apron_technical_stops'] = len(apron['technical_stops'])
        if version >= 6:
            from .esa_airborne_carrier_evidence import evidence as carrier_evidence

            carrier, checks = carrier_evidence(root, store=store)
            value['airborne_carrier'] = carrier
            status.update(checks)
            public_reports += 1+len(carrier['studies'])
            if runtime:
                status['airborne_carrier_runtime_studies'] = len(carrier['studies'])
        if version >= 7:
            from .esa_nuuk_evidence import evidence as nuuk_evidence

            nuuk, checks = nuuk_evidence(root, store=store)
            value['nuuk_comparison'] = nuuk
            status.update(checks)
            public_reports += len(nuuk['studies'])
            if runtime:
                status['nuuk_runtime_studies'] = len(nuuk['studies'])
    if version >= 2:
        status['verified_carrier_reports'] = len(ADDITIONAL)
    if version >= 3:
        status['verified_distant_reference_and_budget'] = True
    if version >= 4:
        status['verified_nuuk_museum_and_antenna_reports'] = True
    return value, dict(status, public_reports=public_reports, verified_transfer=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check', 'check-runtime'))
    parser.add_argument('--version', type=int, choices=(1, 2, 3, 4, 5, 6, 7), default=1)
    args = parser.parse_args()
    root = Path.cwd()
    value, status = verify(root, runtime=args.action != 'check', version=args.version)
    index = (INDEX, CURRENT_INDEX, COMBINED_INDEX, MUSEUM_INDEX, APRON_INDEX, CARRIER_INDEX, NUUK_INDEX)[args.version-1]
    if args.action == 'release':
        _write_equal(root/index, encoded(value))
    elif (root/index).read_bytes() != encoded(value):
        raise ValueError('the public reference evidence index differs')
    print(json.dumps(status, sort_keys=True))
