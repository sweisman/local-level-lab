# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the sealed earlier-only drift diagnostic and publish its limits."""

import gzip
import json
import statistics
from pathlib import Path

from lll.prediction_drift_control import evaluate as score_drift
from lll.prediction_drift_study import (
    PILOT, STUDY, checked_preparation, require_baseline)
from lll.studies.artifacts import ArchiveStore, atomic, digest, encoded
from lll.studies.closed import ClosedStudy


MODEL = {0:'globe with specified field',
         1:'globe with zero field',
         2:'stationary disc'}


def summarize_model(rows):
    """Retain all settings; compare fixed corrections within each setting."""
    qualified = [row for row in rows if row['correction'] is not None]
    output = dict(settings=len(rows), qualified=len(qualified),
                  numerical_abstentions=len(rows)-len(qualified), methods={},
                  median_horizontal_rms_m={method:statistics.median(
                      row['correction']['scores'][method]['horizontal_rms_m']
                      for row in qualified) if qualified else None
                      for method in ('original','constant','linear')})
    for method in ('constant','linear'):
        ratios = {}
        improved = {}
        worsened = {}
        for metric in ('horizontal_rms_m','three_dimensional_rms_m',
                       'height_rms_m'):
            values=[]
            better=worse=0
            for row in qualified:
                scores=row['correction']['scores']
                baseline=scores['original'][metric]
                changed=scores[method][metric]
                if baseline <= 0:
                    raise ValueError('positive original withheld error required')
                values.append(changed/baseline)
                better += changed < baseline
                worse += changed > baseline
            ratios[metric]=statistics.median(values) if values else None
            improved[metric]=better
            worsened[metric]=worse
        output['methods'][method]=dict(median_error_ratio=ratios,
                                       improved=improved, worsened=worsened)
    return output


def audit(root):
    root=Path(root).resolve()
    prepared=checked_preparation(root)
    closed=ClosedStudy(root,'data/'+STUDY)
    pilot=ClosedStudy(root,PILOT)
    try:
        if (closed.completion['state']!='complete'
                or closed.summary['completed']!=3
                or closed.summary['charged']!=dict(native_calls=0,
                    packet_visits=0,bound_calls=0,bound_steps=0)
                or set(closed.tasks)!=set(prepared['material_sha256'])):
            raise ValueError('closed zero-native three-task diagnostic required')
        all_rows=[]
        for sid in sorted(closed.tasks):
            result=closed.envelope(sid)['result']
            if (result.get('passed') is not True
                    or result.get('model_fits')!=0
                    or result.get('original_imu_reads')!=0
                    or result.get('protected_esa_reads')!=0):
                raise ValueError('complete saved-data task required')
            material=json.loads(gzip.decompress(
                closed.input('material-'+sid,raw=True)))
            saved=closed.artifact(sid,'drift-comparison.json')
            selections=[row for row in prepared['selected_settings']
                        if row['segment_id']==sid]
            if len(saved)!=12 or len(selections)!=12:
                raise ValueError('all twelve settings per recording required')
            for row,selected in zip(saved,selections):
                if any(row.get(key)!=value for key,value in selected.items()):
                    raise ValueError('frozen training-only selection changed')
                identity=selected['chosen_identity']
                if identity is None:
                    if row['correction'] is not None:
                        raise ValueError('unqualified setting gained a correction')
                else:
                    expected=score_drift(material['selected_epochs'][identity])
                    if row['correction']!=expected:
                        raise ValueError('sealed earlier-only drift calculation differs')
                    require_baseline(expected,
                        prepared['baseline_reference'][identity])
                    prior=pilot.envelope(identity)['result']['prediction']
                    require_baseline(expected,dict(
                        north_rms_m=prior['north_rms_m'],
                        east_rms_m=prior['east_rms_m'],
                        vertical_rms_m=prior['vertical_rms_m'],
                        horizontal_rms_m=prior['horizontal_rms_m']))
                all_rows.append(row)
        if (len(all_rows)!=36
                or sum(row['correction'] is not None for row in all_rows)!=28
                or sum(row['correction'] is None for row in all_rows)!=8):
            raise ValueError('complete 28/8 selected coverage required')
        by_model=[dict(model=model,label=label,
                       **summarize_model([row for row in all_rows
                                          if row['model']==model]))
                  for model,label in MODEL.items()]
        return dict(version='prediction-drift-audit-v1',
                    audit_source_sha256=digest(Path(__file__).read_bytes()),
                    study='data/'+STUDY,
                    study_manifest_sha256=closed.completion['manifest_sha256'],
                    study_summary_sha256=closed.completion['summary_sha256'],
                    pilot_manifest_sha256=prepared['pilot_manifest_sha256'],
                    pilot_summary_sha256=prepared['pilot_summary_sha256'],
                    completed_tasks=3, settings=36,
                    qualified=28, numerical_abstentions=8,
                    by_model=by_model, settings_detail=all_rows,
                    later_errors_used_for_method_choice=False,
                    training_window_s=120,
                    method_predeclared_before_this_run=True,
                    retrospective_development=True,
                    model_fits=0, original_imu_reads=0,
                    protected_esa_reads=0,
                    accuracy_or_coverage_calibrated=False,
                    scientific_decision='abstain')
    finally:
        closed.close()
        pilot.close()


def publish(root):
    root=Path(root).resolve()
    report=audit(root)
    destination=root/'docs/prediction-drift-control'
    atomic(destination/'verified-report.json',encoded(report))
    lines=['# Can earlier residuals predict the later drift?','',
        'This saved-data development check kept the original 36 settings and '
        'their training-cost-selected starts. Twenty-eight had a qualified '
        'start; eight remained numerical abstentions. No Earth-model fit, '
        'original IMU read or protected ESA recording was added.','',
        'The only new correction used the final two minutes of earlier '
        'receiver residuals. Its mean and straight-line trend were fixed '
        'before looking at the later score. The original model predictions '
        'and their accuracy labels remain unchanged.','',
        '| Candidate | Qualified / 12 | Constant: median later horizontal '
        'RMS ratio | Linear: median later horizontal RMS ratio | '
        'Linear improved / worsened |',
        '|---|---:|---:|---:|---:|']
    for row in report['by_model']:
        constant=row['methods']['constant']
        linear=row['methods']['linear']
        metric='horizontal_rms_m'
        lines.append(f"| {row['label']} | {row['qualified']} / 12 | "
            f"{constant['median_error_ratio'][metric]:.3f} | "
            f"{linear['median_error_ratio'][metric]:.3f} | "
            f"{linear['improved'][metric]} / {linear['worsened'][metric]} |")
    absolute=[]
    for row in report['by_model']:
        values=row['median_horizontal_rms_m']
        absolute.append(f"{row['label']}: {values['original']:.2f} to "
                        f"{values['linear']:.2f} m")
    lines.extend(['',
        'A ratio below one means the empirical correction reduced that '
        'setting’s withheld error; above one means it made it worse. The '
        'median horizontal RMS before and after the linear correction is '
        + '; '.join(absolute) + '. The '
        'verified report also gives height and three-dimensional errors and '
        'every individual setting. The three recordings are retrospective '
        'development data. A correction can absorb physical-model mismatch '
        'or shared receiver error, so lower corrected error is not evidence '
        'for an Earth model. The earlier residuals were themselves left after '
        'the original training fit. This check tests predictability of one simple '
        'drift rule, not a calibrated uncertainty law.','',
        'The finite study, source and environment hashes, original scores, '
        'all abstentions and recovery qualification are in the sealed '
        'study evidence. Reproduce this report with '
        '`~/venv/bin/python -m lll.prediction_drift_audit`.',''] )
    atomic(destination/'README.md','\n'.join(lines).encode())
    return report


def verify_publication(root):
    root=Path(root).resolve()
    prefix='docs/prediction-drift-control/recorded-study'
    receipt=json.loads((root/prefix/'evidence-receipt.json').read_bytes())
    store=ArchiveStore(root)
    try:
        catalog=store.catalog()
        archived=0
        for relative,expected in receipt['artifacts'].items():
            name=prefix+'/'+relative
            if digest(store._read(name,catalog))!=expected:
                raise ValueError('published evidence differs: '+name)
            archived+=name in catalog['paths']
        return dict(verified_artifacts=len(receipt['artifacts']),
                    archived_artifacts=archived)
    finally:
        store.close()


if __name__=='__main__':
    report=publish(Path(__file__).resolve().parents[2])
    print(json.dumps(dict(completed_tasks=report['completed_tasks'],
                          qualified=report['qualified'],
                          numerical_abstentions=report[
                              'numerical_abstentions']),sort_keys=True))
