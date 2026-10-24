# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import pytest


def library():return importlib.import_module('lll.ilvis0_forecast_publication')


def test_primary_choice_ignores_later_error_and_keeps_first_start_ties():
    rows=[dict(start=1,passed=True,converged=True,training_cost=2.,prediction=dict(horizontal_rms_m=0.)),
          dict(start=0,passed=True,converged=True,training_cost=1.,prediction=dict(horizontal_rms_m=1000.))]
    assert library().primary(rows)['start']==0
    rows[0]['training_cost']=1.
    assert library().primary(rows)['start']==0
    rows[1]['converged']=False
    assert library().primary(rows)['start']==1
    rows[0]['passed']=False
    assert library().primary(rows) is None


@pytest.mark.parametrize('cost',[float('nan'),float('inf'),-1.])
def test_primary_rejects_invalid_training_cost(cost):
    with pytest.raises(ValueError):library().primary([dict(start=0,passed=True,converged=True,training_cost=cost)])


def test_incomplete_pilot_keeps_every_missing_comparison(monkeypatch):
    from types import SimpleNamespace
    from lll import ilvis0_prediction_observed as observed
    from lll.studies import closed
    tasks=observed.tasks([dict(segment_id=str(i),native_packets=1000,training_epochs=60,receiver_epochs=90) for i in range(3)])
    study=SimpleNamespace(tasks={t['identity']:t for t in tasks},rows={},
        summary=dict(charged=dict(native_calls=0),elapsed_s=1.),
        completion=dict(manifest_sha256='a',summary_sha256='b'),close=lambda:None,input=lambda key:[])
    monkeypatch.setattr(closed,'ClosedStudy',lambda root,prefix:study)
    result=library().inspect('.','unused')
    assert result['completed']==0 and len(result['primaries'])==36
    assert all(v['primary'] is None for v in result['primaries'])


def saved_fixture(monkeypatch):
    import gzip
    import json
    from types import SimpleNamespace
    from lll import ilvis0_prediction_observed as observed
    from lll.ilvis0_saved_prediction import summarize
    from lll.studies import closed
    layouts=[dict(segment_id=str(i),native_packets=1000,training_epochs=6,receiver_epochs=9) for i in range(3)]
    tasks=observed.tasks(layouts);task=tasks[0];identity=task['identity'];times=list(map(float,range(1,10)))
    rows=[dict(epoch=i,time_s=t,role='training' if i<6 else 'prediction',
        north_direct_error_m=1.,east_direct_error_m=2.,up_direct_error_m=3.) for i,t in enumerate(times)]
    scores=summarize(rows,training_epochs=6,prediction_epochs=3)
    limits=observed.recipe()['accuracy_limits'];checks={k:scores['prediction'][k]<=v for k,v in limits.items()}
    result=dict(passed=True,converged=True,model='sphere_rotating',training_cost=1.,evaluations=2,
        training=scores['training'],prediction=scores['prediction'],
        accuracy_screen=dict(passed=all(checks.values()),checks=checks,limits=limits,
            calibrated_goodness_of_fit=False,scientific_decision='abstain'))
    fit=dict(converged=True,evaluations=2,residual_sum_squares=1.,active_parameters=list(range(26)))
    forecast=dict(coordinates=[[1/6378137.,2/6378137.,3.] for _ in times],times=times,
        training_epochs=6,active_parameters=list(range(26)),continuous_propagation_without_gps_reset=True,
        prediction_receiver_positions_used=False)
    material=dict(layout=layouts[0],times=times,training_gps=[[0.,0.,0.] for _ in range(6)])
    inputs={'recipe':observed.recipe(),'layouts.json':layouts,'0-measurements':gzip.compress(json.dumps(material).encode()),
        '0-scoring':dict(prediction_gps=[[0.,0.,0.] for _ in range(3)])}
    artifacts={'fit.json':fit,'forecast.json':forecast,'epochs.json':rows,'scores.json':scores}
    envelope=dict(result=result,charged=dict(native_calls=3),artifacts={})
    study=SimpleNamespace(tasks={t['identity']:t for t in tasks},rows={identity:True},
        summary=dict(charged=dict(native_calls=3),elapsed_s=1.),
        completion=dict(manifest_sha256='a',summary_sha256='b'),close=lambda:None,
        input=lambda key,**kwargs:inputs[key],envelope=lambda identity:envelope,
        artifact=lambda identity,name:artifacts[name])
    monkeypatch.setattr(closed,'ClosedStudy',lambda root,prefix:study)
    return result,fit,rows


def test_saved_audit_reconciles_forecast_positions_and_every_reported_comparison(monkeypatch):
    saved_fixture(monkeypatch);result=library().inspect('.','fixture')
    assert result['completed']==result['converged']==1
    assert len(result['primaries'])==36 and sum(v['primary'] is not None for v in result['primaries'])==1
    assert result['numerical_work']==0 and result['scientific_decision']=='abstain'


@pytest.mark.parametrize('fault',['cost','accuracy','numerical_label','epoch'])
def test_saved_audit_rejects_inconsistent_cost_labels_or_physical_errors(monkeypatch,fault):
    result,fit,rows=saved_fixture(monkeypatch)
    if fault=='cost':result['training_cost']=0.
    elif fault=='accuracy':result['accuracy_screen']['passed']=False
    elif fault=='numerical_label':result['passed']=False
    else:rows[-1]['up_direct_error_m']=1000.
    with pytest.raises(ValueError):library().inspect('.','fixture')
