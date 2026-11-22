# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report all primary ESA turn forecasts from saved closure and score receipts."""

import argparse
import json
import math
from pathlib import Path

from .esa_repeat_turn_release import PREFIX, primary_starts, release
from .studies.artifacts import digest, encoded


BASE = 'docs/prediction-observed-development/'
RESULT = BASE + 'ESA_REPEAT_TURN_FORECAST_RESULT.md'
EVIDENCE = BASE + 'esa-repeat-turn-forecast-evidence/'
ADDITIONS = ('steady', 'turn', 'both')
UNAVAILABLE = {
    'primary_forecast_missing': 'Selected forecast unavailable',
    'no_converged_start': 'Neither start converged',
}


def summary(*, outcomes, primary, scores, windows):
    selections = primary_starts(outcomes)
    if selections != primary or set(scores) != {
            row['identity'] for row in selections if row['state'] == 'sealed'}:
        raise ValueError('scores must cover exactly the released primary forecasts')
    rows = []
    for selection in selections:
        index = selection['first_index']
        course = windows[index]['window']['signed_course_change_deg']
        row = dict(selection, course_change_deg=course)
        if selection['state'] == 'sealed':
            score = scores[selection['identity']]
            if (score['forecast_sha256'] != selection['forecast_sha256']
                    or score['law'] != selection['law']
                    or set(score['scores']) != {'native', *ADDITIONS}):
                raise ValueError('score does not match its released forecast or covariance choices')
            north, east, height = score['physical_rms_neu_m']
            horizontal = score['horizontal_rms_m']
            costs = {name: values['negative_log_score'] for name, values in score['scores'].items()}
            if (not all(math.isfinite(value) for value in (course, north, east, height, horizontal, *costs.values()))
                    or min(north, east, height, horizontal) < 0.
                    or not math.isclose(horizontal, math.hypot(north, east), rel_tol=1e-9, abs_tol=1e-12)):
                raise ValueError('invalid position errors or Gaussian scores in saved result')
            row.update(rms_neu_m=[north, east, height], horizontal_rms_m=horizontal,
                       rms_3d_m=math.hypot(horizontal, height), native_nll=costs['native'],
                       nll_change={name: costs[name] - costs['native'] for name in ADDITIONS})
        rows.append(row)
    return rows


def render(rows, outcomes, release_sha256, scores_sha256):
    sealed = sum(row['state'] == 'sealed' for row in rows)
    converged = sum(case['converged'] for case in outcomes.values())
    lines = [
        '# How four turns tested the ESA position forecasts', '',
        f'{converged} of {len(outcomes)} training starts converged. '
        f'{sealed} of {len(rows)} window and error-description pairs have a scored primary forecast.',
        'All four windows come from ESA development recording 187. The two error descriptions',
        'for each window use the same inertial measurement unit (IMU) readings.', '',
        'The errors below compare the forecast with 120 later GPS positions. Each row',
        'uses one path for all four covariance scores. A negative score change means the',
        'added error allowance improved the joint Gaussian score, including the penalty',
        'for wider uncertainty. Position errors are in metres. The signed course change',
        'describes the turn block selected from the receiver trajectory.', '',
        '| First receiver index | Course change | IMU error description | Primary | North | East | Height | Horizontal | 3D | Native score | Steady change | Turn change | Both change |',
        '| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for row in rows:
        prefix = [str(row['first_index']), f"{row['course_change_deg']:+.1f}°",
                  {'increment': 'Increment', 'point': 'Point rate'}[row['law']]]
        if row['state'] == 'sealed':
            fields = [str(row['identity'].rsplit('-', 1)[1]),
                      *(f'{value:.3f}' for value in (*row['rms_neu_m'], row['horizontal_rms_m'], row['rms_3d_m'])),
                      f"{row['native_nll']:.4g}", *(f"{row['nll_change'][name]:+.4g}" for name in ADDITIONS)]
        else:
            fields = [UNAVAILABLE[row['state']], *(['—'] * 9)]
        lines.append('| ' + ' | '.join(prefix + fields) + ' |')
    lines.extend([
        '', 'These results measure prediction and error scoring on one development flight.',
        'Independent flight coverage, absolute accuracy and a matched Earth-model comparison',
        'require separate studies.', '',
        f'- [Forecast release receipt](esa-repeat-turn-forecast-evidence/receiver-release.json), SHA-256 `{release_sha256}`',
        f'- [Position and covariance scores](esa-repeat-turn-forecast-evidence/receiver-scores.json), SHA-256 `{scores_sha256}`',
        '- [Method and reproduction](ESA_REPEAT_TURN_RELEASE_RESULT.md)', '',
    ])
    return '\n'.join(lines)


def publish_report(root, *, manifest_sha256):
    from .ilvis0_matched_observed_inputs import _write_equal

    run = root / PREFIX
    saved_release = (run / 'receiver-release.json').read_bytes()
    saved_scores = (run / 'receiver-scores.json').read_bytes()
    receipt, _, windows = release(root, expected_manifest_sha256=manifest_sha256)
    score_receipt = json.loads(saved_scores)
    sha = digest(saved_release)
    if (saved_release != encoded(receipt) or saved_scores != encoded(score_receipt)
            or score_receipt['release_sha256'] != sha
            or score_receipt['protected_reads'] != 0 or score_receipt['scientific_decision'] != 'abstain'):
        raise ValueError('verified closure, forecast release and matching score receipt required')
    rows = summary(outcomes=receipt['outcomes'], primary=receipt['primary'],
                   scores=score_receipt['scores'], windows=windows)
    markdown = render(rows, receipt['outcomes'], sha, digest(saved_scores))
    for name, raw in (('receiver-release.json', saved_release), ('receiver-scores.json', saved_scores)):
        _write_equal(root / EVIDENCE / name, raw)
    _write_equal(root / RESULT, markdown.encode())
    return dict(results=RESULT, comparisons=len(rows), scored=len(score_receipt['scores']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(publish_report(Path.cwd(), manifest_sha256=args.manifest_sha256), sort_keys=True))
