# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only RT27 inventory with resumable source preparation."""
import csv
import datetime as datetime
import gzip
import hashlib
import io
import json
from pathlib import Path
import statistics

from lll.ilvis0_rt27_position import (audit_receiver_bytes, compare_receiver_positions,
                                      extract_primary_receiver)
from lll.studies.artifacts import atomic, encoded


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def gps_utc_offset(date):
    """GPS minus UTC seconds for the selected 2009–2017 archive dates."""
    day = datetime.date.fromisoformat(date)
    if not datetime.date(2009, 1, 1) <= day <= datetime.date(2017, 12, 31):
        raise ValueError('date outside fixed GPS/UTC offset table')
    if day >= datetime.date(2017, 1, 1):
        return 18
    if day >= datetime.date(2015, 7, 1):
        return 17
    if day >= datetime.date(2012, 7, 1):
        return 16
    return 15


def stage_record(root, stage, record, date, leap_seconds):
    """Seal one original-derived receiver stream; resume sealed records only."""
    root, stage = Path(root).resolve(), Path(stage).resolve()
    identity = record['task']
    if not identity.isalnum() or len(identity) > 40:
        raise ValueError('safe recording identity required')
    receipt = stage/'records'/f'{identity}.json'
    if receipt.is_file():
        saved = json.loads(receipt.read_text())
        if (saved['task'] != identity or saved['source_sha256'] != record['source_sha256']
                or saved['date'] != date or saved['leap_seconds'] != leap_seconds):
            raise ValueError('sealed receiver preparation differs from selection')
        compressed = (root/saved['input_path']).read_bytes()
        if (_sha(compressed) != saved['compressed_sha256']
                or _sha(gzip.decompress(compressed)) != saved['receiver_sha256']):
            raise ValueError('sealed receiver stream changed')
        return saved
    original = root/'data/ilvis0-ready'/identity/'decoded'/(record['filename']+'.gz')
    source = extract_primary_receiver(original, record['source_sha256'])
    raw = source['receiver_bytes']
    prior = original.parent/'primary-gps-stream.bin.gz'
    if prior.is_file():
        compressed = prior.read_bytes()
        if gzip.decompress(compressed) != raw:
            raise ValueError('prior receiver stream differs from checked original')
        chosen = prior
        provenance = 'existing_exact_match'
    else:
        chosen = stage/'streams'/f'{identity}.bin.gz'
        compressed = gzip.compress(raw, mtime=0)
        if chosen.is_file():
            if chosen.read_bytes() != compressed:
                raise ValueError('unsealed prior receiver extraction differs')
        else:
            atomic(chosen, compressed)
        provenance = 'new_group10001_extraction'
    saved = dict(task=identity, filename=record['filename'],
        date=date, leap_seconds=leap_seconds,
        source_sha256=record['source_sha256'], original_reads=1,
        original_bytes=source['original_bytes'], original_frames=source['original_frames'],
        receiver_packets=source['receiver_packets'], receiver_sha256=source['receiver_sha256'],
        receiver_bytes=len(raw), compressed_sha256=_sha(compressed),
        compressed_bytes=len(compressed), input_path=chosen.relative_to(root).as_posix(),
        provenance=provenance, model_fits=0, original_imu_payloads_decoded=0)
    atomic(receipt, encoded(saved))
    return saved


def stage_inventory(root, *, identity='ilvis0-rt27-position-preparation-20261110'):
    """Prepare the fixed 53-recording cohort with sealed, resumable records."""
    from .studies.artifacts import ArchiveStore

    root = Path(root).resolve()
    stage = root/'data'/identity
    archive = ArchiveStore(root)
    catalog = archive.catalog()
    cohort_name = 'docs/ilvis0-receiver-metadata/artifacts/publication/inventory.json'
    cohort_bytes = archive._read(cohort_name, catalog)
    cohort = json.loads(cohort_bytes)
    records = cohort['records']
    if (len(records) != 53 or len({r['task'] for r in records}) != 53
            or not cohort['complete'] or cohort['model_outcomes_used']):
        raise ValueError('fixed 53-recording receiver-only cohort required')
    prepared = []
    for row in sorted(records, key=lambda item:item['task']):
        name = f'data/ilvis0-ready/{row["task"]}/decoded/inspection.json'
        inspection = json.loads(archive._read(name, catalog))
        if (inspection['source_file'] != row['filename']
                or inspection['source_sha256'] != row['source_sha256']):
            raise ValueError('inspection differs from fixed source cohort')
        dates = list(inspection['gps']['dates'])
        if len(dates) != 1:
            raise ValueError('one unambiguous receiver ZDA date required')
        date = dates[0]
        prepared.append(stage_record(root, stage, row, date, gps_utc_offset(date)))
    sources = ('analysis/lll/ilvis0_rt27_study.py',
               'analysis/lll/ilvis0_rt27_position.py',
               'analysis/lll/trimble_receiver.py',
               'analysis/tests/test_ilvis0_rt27_study.py',
               'analysis/tests/test_ilvis0_rt27_position.py',
               'analysis/tests/test_trimble_enhanced_position.py',
               'docs/ilvis0-trimble-position-precision/PLAN.md')
    summary = dict(version='receiver-rt27-position-preparation-v1',
        cohort_path=cohort_name, cohort_sha256=_sha(cohort_bytes),
        source_hashes={name:_sha((root/name).read_bytes()) for name in sources},
        records=prepared, record_count=len(prepared),
        prior_streams_confirmed=sum(r['provenance']=='existing_exact_match' for r in prepared),
        new_streams_extracted=sum(r['provenance']=='new_group10001_extraction' for r in prepared),
        original_reads=len(prepared), model_fits=0, original_imu_payloads_decoded=0)
    target = stage/'summary.json'
    raw = encoded(summary)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('sealed receiver preparation summary differs')
    else:
        atomic(target, raw)
    return summary


def write_definition(root, summary, *, identity='ilvis0-rt27-position-inventory-20261110'):
    """Freeze a finite 53-task receiver-only inventory from sealed inputs."""
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    if summary['record_count'] != 53 or summary['model_fits'] != 0:
        raise ValueError('complete receiver-only preparation required')
    adapter = 'analysis/lll/ilvis0_rt27_study.py'
    seeds = [adapter, 'analysis/tests/test_ilvis0_rt27_study.py',
             'analysis/tests/test_ilvis0_rt27_position.py',
             'analysis/tests/test_trimble_enhanced_position.py',
             'docs/ilvis0-trimble-position-precision/PLAN.md']
    sources = source_closure(root, seeds)
    stage_name = 'data/ilvis0-rt27-position-preparation-20261110'
    inputs = {'preparation_summary':stage_name+'/summary.json'}
    tasks = []
    for index, record in enumerate(summary['records']):
        key = 'receiver_'+record['task']
        preparation_key = 'preparation_'+record['task']
        inputs[key] = record['input_path']
        inputs[preparation_key] = stage_name+'/records/'+record['task']+'.json'
        tasks.append(dict(identity=record['task'], index=index, shard=0,
            input_key=key, preparation_key=preparation_key,
            compressed_sha256=record['compressed_sha256'],
            receiver_sha256=record['receiver_sha256'],
            source_sha256=record['source_sha256'], date=record['date'],
            leap_seconds=record['leap_seconds'], minimum_matches=100,
            limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)))
    definition = dict(id=identity, scope='fixed 53-recording primary receiver RT27 '
        'precision inventory; no Earth-model or inertial fit', adapter=adapter,
        sources=sources, inputs=inputs, tasks=tasks,
        workers=1, threads=1, maximum_wall_s=900)
    target = root/'docs/ilvis0-trimble-position-precision/study-definition.json'
    raw = encoded(definition)
    if target.is_file():
        if target.read_bytes() != raw:
            raise ValueError('frozen study definition differs')
    else:
        atomic(target, raw)
    return definition


def reference_sample_check(root):
    """Independent same-receiver decoding check on the fixed development file."""
    root = Path(root).resolve()
    name = ('data/ilvis0-ready/a0534d9c30195543709c/decoded/'
            'primary-gps-stream.bin.gz')
    compressed = (root/name).read_bytes()
    raw = gzip.decompress(compressed)
    result = audit_receiver_bytes(raw)
    match = compare_receiver_positions(result['positions'], result['gga_fixes'],
                                       leap_seconds=17)
    if (result['position_count'] != 2294 or match['matched_epochs'] != 459
            or any(match['maximum_abs_'+axis+'_m'] > 0.05
                   for axis in ('north','east','up'))):
        raise ValueError('reference receiver decoding did not reproduce')
    return dict(source_path=name, compressed_sha256=_sha(compressed),
        receiver_sha256=_sha(raw), checked_packets=result['checked_packet_count'],
        position_count=result['position_count'], gga_matches=match['matched_epochs'],
        maximum_abs_neu_m=[match['maximum_abs_'+axis+'_m']
                           for axis in ('north','east','up')],
        boundary_prefix_bytes=result['prefix_bytes'],
        boundary_tail_bytes=result['tail_bytes'],
        scientific_decision='abstain', independent_accuracy_established=False)


CSV_FIELDS = ('first_stream_offset', 'gps_week', 'gps_milliseconds',
              'latitude_deg', 'longitude_deg', 'ellipsoid_height_m',
              'velocity_north_mps', 'velocity_east_mps', 'velocity_up_mps',
              'reported_sigma_north_m', 'reported_sigma_east_m',
              'reported_sigma_up_m', 'reported_rms_m', 'hdop', 'vdop', 'tdop',
              'position_solution_mode', 'position_augmentation_type',
              'position_processing_type', 'satellites_tracked', 'satellites_used')


def evaluate(task, context):
    """One frozen receiver stream; no inertial or Earth-model data are read."""
    if 'preparation_key' in task:
        preparation = json.loads(context.input_path(task['preparation_key']).read_text())
        if (preparation['task'] != task['identity']
                or preparation['source_sha256'] != task['source_sha256']
                or preparation['receiver_sha256'] != task['receiver_sha256']
                or preparation['compressed_sha256'] != task['compressed_sha256']
                or preparation['date'] != task['date']
                or preparation['leap_seconds'] != task['leap_seconds']
                or preparation['model_fits'] != 0
                or preparation['original_imu_payloads_decoded'] != 0):
            raise ValueError('frozen receiver preparation receipt differs')
    compressed = context.input_path(task['input_key']).read_bytes()
    if _sha(compressed) != task['compressed_sha256']:
        raise ValueError('frozen receiver input hash changed')
    raw = gzip.decompress(compressed)
    if _sha(raw) != task['receiver_sha256']:
        raise ValueError('frozen extracted receiver stream hash changed')
    try:
        result = audit_receiver_bytes(raw)
        gga = compare_receiver_positions(result['positions'], result['gga_fixes'],
                                         leap_seconds=task['leap_seconds'])
        if gga['matched_epochs'] < task['minimum_matches']:
            raise ValueError('insufficient same-receiver GGA matches')
        if any(gga['maximum_abs_'+axis+'_m'] > 0.05
               for axis in ('north','east','up')):
            raise ValueError('enhanced position and GGA differ beyond 0.05 m')
    except ValueError as error:
        artifact = context.save('summary.json', dict(task=task['identity'],
            reason=str(error), receiver_sha256=task['receiver_sha256'],
            scientific_decision='abstain', receiver_covariance_established=False,
            model_fits=0, original_imu_reads=0))
        return dict(passed=False, reason=str(error), result_artifact=artifact,
                    scientific_decision='abstain', model_fits=0, original_imu_reads=0)
    positions = result.pop('positions')
    fixes = result.pop('gga_fixes')
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows({name:row[name] for name in CSV_FIELDS} for row in positions)
    positions_artifact = context.save_bytes('positions.csv.gz',
                                           gzip.compress(output.getvalue().encode(), mtime=0))
    sigma = {axis:dict(min=min(values), median=statistics.median(values),
                       max=max(values)) for axis in ('north','east','up')
             for values in [[row['reported_sigma_'+axis+'_m'] for row in positions]]}
    result.update(task=task['identity'], date=task['date'],
        source_sha256=task['source_sha256'], compressed_sha256=task['compressed_sha256'],
        gga_count=len(fixes), gga_match=gga, reported_sigma_m=sigma,
        positions_artifact=positions_artifact, scientific_decision='abstain',
        model_fits=0, original_imu_reads=0)
    artifact = context.save('summary.json', result)
    return dict(passed=True, scientific_decision='abstain', result_artifact=artifact,
                positions_artifact=positions_artifact, position_count=len(positions),
                gga_matches=gga['matched_epochs'], model_fits=0, original_imu_reads=0)
