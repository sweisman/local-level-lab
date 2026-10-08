"""Build compact inventories from completed hash-bound receiver evidence."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(directory,output):
    completion=json.loads((directory/'completion.json').read_text())
    for name,key in (('manifest.json','manifest_sha256'),('summary.json.gz','summary_sha256')):
        if sha(directory/name)!=completion[key]:
            raise ValueError('completed receiver evidence hash mismatch')
    with gzip.open(directory/'summary.json.gz','rt') as stream:
        results=json.load(stream)['results']
    rows=[]; outliers=[]
    for report in results:
        for name,digest in report['artifacts_sha256'].items():
            if Path(name).name!=name or sha(directory/name)!=digest:
                raise ValueError('receiver export hash mismatch')
        base={key:report[key] for key in ('task_id','filename','source_sha256')}
        rows.append(base | dict(decoded_epochs=report['decoded_epochs'],
            decoded_signal_measurements=report['decoded_signal_epochs'],
            median_sample_interval_s=report['sample_intervals_s']['median'],
            duration_s=report['duration_s'],gap_count=report['gaps_over_1_5_median'],
            gps_ephemeris_packets=len(report['gps_ephemerides']),
            matched_receiver_position_epochs=report['same_epoch_receiver_positions'],
            matched_sky_angle_pairs=report['sky_angle_check']['matched_gps_satellite_epochs'],
            sky_angle_outliers=report['sky_angle_check']['outlier_count'],
            receiver_boundary_failures=len(report['boundary_failures']),
            reported_angle_hdop_median=report['geometry']['hdop'].get('median'),
            reported_angle_vdop_median=report['geometry']['vdop'].get('median'),
            calibrated_covariance=False,empirical_earth_fit_attempts=0))
        for row in report['sky_angle_check']['outliers']:
            outliers.append(base | {key:value for key,value in row.items() if key not in ('signals','sv_flags')}
                            | dict(sv_flags=json.dumps(row['sv_flags'])))
    output.mkdir(exist_ok=True,parents=True)
    for name,records in (('inventory.csv',rows),('sky-angle-outliers.csv',outliers)):
        with (output/name).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]),lineterminator='\n')
            writer.writeheader(); writer.writerows(records)
    receipt=dict(generator_sha256=sha(Path(__file__)),
        source_manifest_sha256=completion['manifest_sha256'],
        source_summary_sha256=completion['summary_sha256'],
        files=len(rows),outlier_rows=len(outliers),
        artifacts_sha256={name:sha(output/name) for name in ('inventory.csv','sky-angle-outliers.csv')},
        scientific_eligibility_changes=0,empirical_earth_fit_attempts=0)
    (output/'inventory-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(f'Verified measurement export hashes; inventoried {len(rows)} files and {len(outliers)} flagged angle rows.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    export(args.directory,args.output)
