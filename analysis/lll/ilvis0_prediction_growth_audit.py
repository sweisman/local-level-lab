# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay training-to-withheld RMS growth from the sealed NASA pilot."""
import argparse
import json
import math
import statistics

from lll.studies.closed import ClosedStudy


PARENT = 'docs/ilvis0-retrospective-prediction-pilot-v2'
MANIFEST_SHA256 = 'f9499a0eee0c3f9c9f997b88e1fd2e6fb9e032ff7572a5a52cd3a719bd930dbb'
SUMMARY_SHA256 = '293d8de4cc3ed0efd6dc86d6807b9609195bd366742a7ede6ad3ec44e97e392d'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
AXES = ('north_rms_m', 'east_rms_m', 'vertical_rms_m')
ERROR_AXES = ('north', 'east', 'up')


def primary_results(results):
    """Choose each group's numerical primary using earlier cost only."""
    groups = {}
    for identity, result in results:
        if result.get('converged') is not True or result.get('passed') is not True:
            continue
        if result['model'] not in MODELS:
            raise ValueError('unexpected physical model')
        key = tuple(result[name] for name in
                    ('segment_id', 'clock', 'profile', 'model'))
        cost = result['training_cost']
        if not isinstance(cost, (int, float)) or not math.isfinite(cost):
            raise ValueError('finite earlier training cost required')
        groups.setdefault(key, []).append((cost, identity, result))
    return [min(values) for values in groups.values()]


def ratios(scores):
    output = {}
    for axis in AXES:
        earlier = scores['training'][axis]
        later = scores['prediction'][axis]
        if (not all(isinstance(value, (int, float)) and math.isfinite(value)
                    for value in (earlier, later)) or earlier <= 0 or later < 0):
            raise ValueError('finite positive earlier RMS and nonnegative later RMS required')
        output[axis] = later/earlier
    return output


def horizon_quarters(epochs):
    """RMS in four consecutive withheld blocks, with no training leakage."""
    if len(epochs) < 4:
        raise ValueError('at least four withheld epochs required')
    prediction_started = False
    prediction = []
    for index, row in enumerate(epochs):
        if row['epoch'] != index or (index and row['time_s'] <= epochs[index-1]['time_s']):
            raise ValueError('consecutive epochs and increasing times required')
        role = row['role']
        if role == 'prediction':
            prediction_started = True
            prediction.append(row)
        elif role != 'training' or prediction_started:
            raise ValueError('training prefix followed by withheld epochs required')
    if len(prediction) < 4:
        raise ValueError('at least four withheld epochs required')
    result = []
    for quarter in range(4):
        block = prediction[len(prediction)*quarter//4:len(prediction)*(quarter+1)//4]
        item = {'epochs': len(block)}
        for axis in ERROR_AXES:
            values = [row[axis+'_direct_error_m'] for row in block]
            if any(not isinstance(value, (int, float)) or not math.isfinite(value)
                   for value in values):
                raise ValueError('finite saved errors required')
            item[axis+'_rms_m'] = math.sqrt(statistics.fmean(value*value for value in values))
        result.append(item)
    return result


def build(root='.'):
    study = ClosedStudy(root, PARENT)
    try:
        if (study.completion['state'] != 'terminal' or
                study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['summary_sha256'] != SUMMARY_SHA256 or
                len(study.tasks) != 72 or len(study.rows) != 72):
            raise ValueError('exact sealed 72-start NASA development pilot required')
        selected = primary_results(
            (identity, study.envelope(identity)['result'])
            for identity in study.tasks)
        if len(selected) != 28:
            raise ValueError('unchanged 28 numerical primaries required')
        rows = []
        for cost, identity, result in selected:
            values = ratios(study.artifact(identity, 'scores.json'))
            rows.append(dict(identity=identity, model=result['model'],
                             training_cost=cost,
                             accuracy_screen_passed=result['accuracy_screen']['passed'],
                             withheld_to_training_rms=values,
                             horizon_quarters=horizon_quarters(
                                 study.artifact(identity, 'epochs.json'))))
        summary = {}
        for model in MODELS:
            subset = [row for row in rows if row['model'] == model]
            summary[model] = dict(settings=len(subset),
                                  median_ratio={axis: statistics.median(
                                      row['withheld_to_training_rms'][axis]
                                      for row in subset) for axis in AXES},
                                  median_horizon_quarter_rms_m={axis: [
                                      statistics.median(row['horizon_quarters'][quarter][axis+'_rms_m']
                                                        for row in subset)
                                      for quarter in range(4)] for axis in ERROR_AXES})
        if [summary[model]['settings'] for model in MODELS] != [9, 9, 10]:
            raise ValueError('unchanged candidate coverage required')
        return dict(verified=True, parent=PARENT,
                    manifest_sha256=MANIFEST_SHA256,
                    summary_sha256=SUMMARY_SHA256, primaries=28,
                    summary=summary, rows=rows, new_fits=0,
                    protected_reads=0, scientific_decision='abstain')
    finally:
        study.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    report = build(args.root)
    print(json.dumps(report['summary'], indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
