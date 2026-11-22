# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recompute the ESA direction tables from saved public reports."""

from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import median


FOLDER = Path('docs/prediction-observed-development')
FILES = {
    'esa-direction-window-transfer-result.json': 'ebbef12c33cb84824ab289886fa41d81c40d77aeae6f628e7bfa49fe32840b0c',
    'esa-direction-angle-pairs-result.json': 'fdff86240215dd7ce70c0272be6c7e61a6071aea95dca558b7491ed0e45ef9bb',
    'esa-direction-lever-arm-result.json': 'e5b0d1ea0dd91150c0814db8195fe74d73b184812cb04448093ee60d0ac1b776',
}
KINDS = ('straight', 'turn')
FIELDS = ('zero_field', 'full_field_logged', 'full_field_removed_from_gyro')
MODES = ('nominal', 'transfer')
SHAPES = ('globe', 'disc')
SETTINGS = {(width, field) for width in (11, 25) for field in FIELDS}


def read_report(path, expected):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f'saved report hash differs: {path.name}')
    return json.loads(raw)


def _rms(samples):
    return math.sqrt(math.fsum(value*value for value in samples)/len(samples))


def _angles(values, length):
    if len(values) != length or not all(0. <= value <= 180. for value in values):
        raise ValueError('missing or invalid angles')
    return values


def _check_score(value, saved):
    if not math.isclose(value, saved, rel_tol=1e-12, abs_tol=1e-13):
        raise ValueError('recomputed angle score differs')


def _angle_comparison(observed, predicted):
    observed = _angles(observed, 28)
    g, d = (_angles(predicted[shape]['predicted_deg'], 28) for shape in SHAPES)
    g_rms = _rms([x-y for x, y in zip(observed, g, strict=True)])
    d_rms = _rms([x-y for x, y in zip(observed, d, strict=True)])
    separation = _rms([x-y for x, y in zip(g, d, strict=True)])
    tie_distance = abs(d_rms*d_rms-g_rms*g_rms)/(2.*separation) if separation else 0.
    return g_rms, d_rms, tie_distance


def angle_pair_scores(row):
    g, d, tie = _angle_comparison(row['observed_deg'], row['scores'])
    _check_score(g, row['scores']['globe']['rms_deg'])
    _check_score(d, row['scores']['disc']['rms_deg'])
    _check_score(d-g, row['disc_minus_globe_deg'])
    return g, d, tie


def _lever_arm_scores(corrected, nominal):
    angles = corrected['observed_corrected_deg']
    g, d, tie = _angle_comparison(angles, nominal['scores'])
    _check_score(g, corrected['corrected_rms_deg']['globe'])
    _check_score(d, corrected['corrected_rms_deg']['disc'])
    _check_score(d-g, corrected['corrected_disc_minus_globe_deg'])
    _check_score(nominal['disc_minus_globe_deg'], corrected['nominal_disc_minus_globe_deg'])
    change = _rms([a-b for a, b in zip(angles, nominal['observed_deg'], strict=True)])
    _check_score(change, corrected['offset_effect_rms_deg'])
    return (g, d, tie), change


def _verified_rows(report, passes_per_window):
    if (report['scientific_decision'] != 'abstain'
            or any(report[key] != 0 for key in ('new_calibration_fits', 'original_data_reads', 'protected_reads'))):
        raise ValueError('unexpected development scope')
    windows = report['windows']
    if (len({window['window'] for window in windows}) != len(windows)
            or Counter(window['kind'] for window in windows) != dict.fromkeys(KINDS, 4)):
        raise ValueError('incomplete or duplicate windows')
    charges = report['charged']
    if (charges['bound_calls'] != passes_per_window*len(windows)
            or charges['bound_steps'] != passes_per_window*sum(window['packet_count'] for window in windows)
            or any(charges[key] != 0 for key in ('native_calls', 'packet_visits'))):
        raise ValueError('saved packet accounting differs')
    rows = {}
    for window in windows:
        settings = window['settings']
        if len(settings) != len(SETTINGS) or {(s['width_reports'], s['field']) for s in settings} != SETTINGS:
            raise ValueError('incomplete or duplicate matched settings')
        for setting in settings:
            key = (window['window'], window['kind'], window['packet_count'],
                   setting['width_reports'], setting['field'])
            rows[key] = setting
    return rows


def _transfer_scores(row):
    errors = {}
    for mode in MODES:
        for shape in SHAPES:
            score = row['scores'][shape][mode]
            if score['status'] != 'scored':
                raise ValueError('saved nominal or transferred score missing')
            angles = _angles(score['angular_errors_deg'], 16)
            early, late = angles[:8], angles[8:]
            for errors_deg, key in ((early, 'training_rms_deg'), (late, 'later_rms_deg')):
                _check_score(_rms(errors_deg), score[key])
            errors[mode, shape] = (early, late)
        _check_score(_rms(errors[mode, 'disc'][1])-_rms(errors[mode, 'globe'][1]),
                     row['disc_minus_globe_deg'][mode])
    return errors


def _summary(by_group):
    for (kind, field), scores in sorted(by_group.items()):
        globe, disc, *extra = zip(*scores, strict=True)
        gaps = [d-g for g, d in zip(globe, disc, strict=True)]
        row = dict(kind=kind, field=field, settings=len(scores), globe_lower=sum(gap > 0. for gap in gaps),
                   globe_median_deg=median(globe), disc_median_deg=median(disc),
                   disc_minus_globe_deg=[min(gaps), max(gaps)])
        if extra:
            row['minimum_rms_change_to_tie_deg'] = min(extra[0])
        yield row


def audit(folder):
    transfer, pairs, lever = (read_report(folder / name, expected) for name, expected in FILES.items())
    if (pairs['parent_manifest_sha256'] != transfer['study_manifest_sha256']
            or lever['parent_manifest_sha256'] != pairs['manifest_sha256']):
        raise ValueError('saved studies do not share the same window freeze')
    transfer_rows, pair_rows = _verified_rows(transfer, 13), _verified_rows(pairs, 1)
    lever_rows = _verified_rows(lever, 1)
    if not transfer_rows.keys() == pair_rows.keys() == lever_rows.keys():
        raise ValueError('scored windows and settings differ between studies')
    angle_groups = defaultdict(list)
    lever_groups = defaultdict(list)
    lever_changes = []
    transferred_groups = {mode: defaultdict(list) for mode in MODES}
    omitted_favor_globe = 0
    retained_ratios = ([], [])
    for key, row in transfer_rows.items():
        _, kind, _, _, field = key
        angle_groups[kind, field].append(angle_pair_scores(pair_rows[key]))
        corrected, change = _lever_arm_scores(lever_rows[key], pair_rows[key])
        lever_groups[kind, field].append(corrected)
        lever_changes.append(change)
        errors = _transfer_scores(row)
        for mode in MODES:
            g, d = (errors[mode, shape][1] for shape in SHAPES)
            transferred_groups[mode][kind, field].append((_rms(g), _rms(d)))
            for start in range(7):
                omitted_favor_globe += (
                    _rms(g[:start]+g[start+2:]) < _rms(d[:start]+d[start+2:]))
        if field == 'full_field_logged':
            for ratios, nominal, fixed in zip(
                    retained_ratios, errors['nominal', 'globe'], errors['transfer', 'globe'], strict=True):
                ratios.append(_rms(fixed)/_rms(nominal))

    earlier, later = retained_ratios
    return dict(paired_settings=len(pair_rows), angle_pairs=list(_summary(angle_groups)),
                lever_arm_angle_pairs=list(_summary(lever_groups)),
                largest_lever_arm_angle_change_rms_deg=max(lever_changes),
                window_transfer={mode: list(_summary(groups)) for mode, groups in transferred_groups.items()},
                adjacent_pair_omissions_favoring_globe=omitted_favor_globe,
                adjacent_pair_omissions_total=len(pair_rows)*len(MODES)*7,
                retained_field_globe_transfer_factor=dict(
                    earlier_increased=sum(ratio > 1. for ratio in earlier), earlier_median=median(earlier),
                    later_increased=sum(ratio > 1. for ratio in later),
                    later_range=[min(later), max(later)], later_median=median(later)))


if __name__ == '__main__':
    print(json.dumps(audit(FOLDER), indent=2))
