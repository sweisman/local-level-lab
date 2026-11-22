# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze two alternate PPP training-coordinate inputs on opened ESA 187."""

import gzip
import json
import math
from pathlib import Path

from .esa_alternate_ppp_scoring import PARENT
from .esa_full_parallel_gnss import AIR1, BASE, INVENTORY, _sha
from .esa_parallel_gnss import MATCH_TOLERANCE_S, earlier_lines, match_times
from .esa_parallel_gnss_time import corrected_neu
from .esa_ppp_acquisition import TARGETS, verify_complete

VERSION='esa-alternate-training-material-v1'
SCORES='docs/prediction-observed-development/esa-alternate-ppp-scoring-result.json'
PLAN='docs/prediction-observed-development/ESA_ALTERNATE_TRAINING_MATERIAL_PLAN.md'


def aligned_coordinates(reference, adjusted_neu):
    from .models import radii
    if (len(adjusted_neu)!=3 or not all(math.isfinite(float(x)) for x in adjusted_neu)):
        raise ValueError('finite three-axis local displacement required')
    latitude=float(reference['latitude_deg'])
    longitude=float(reference['longitude_deg'])
    height=float(reference['height_m'])
    rm,rn=radii(math.radians(latitude))
    north=float(rm+height)
    east=float((rn+height)*math.cos(math.radians(latitude)))
    if north<=0 or east<=0:
        raise ValueError('positive local receiver metric required')
    output=(latitude+math.degrees(adjusted_neu[0]/north),
            longitude+math.degrees(adjusted_neu[1]/east),
            height+float(adjusted_neu[2]))
    if abs(output[0])>=90 or abs(output[1])>180:
        raise ValueError('aligned coordinates outside supported chart')
    return output


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_rolling_origin_400_model_matrix import ID
    from .studies.artifacts import digest,encoded
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    scores=json.loads((root/SCORES).read_bytes())
    inventory=json.loads((root/INVENTORY).read_bytes())
    if (scores.get('version')!='esa-alternate-ppp-forecast-scoring-v1'
            or scores.get('common_withheld_epochs')!=120
            or scores.get('protected_reads')!=0
            or inventory.get('source_file')!=AIR1):
        raise ValueError('same completed ESA receiver development sources required')
    parent=ClosedStudy(root,PARENT)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (parent.completion['manifest_sha256']!=scores['parent_manifest_sha256']
                or study.completion['manifest_sha256']!=scores['matrix_manifest_sha256']):
            raise ValueError('sealed parent or matrix manifest differs')
        all_rows=json.loads(gzip.decompress(parent.input('training',raw=True)))
        if len(all_rows)!=800:
            raise ValueError('same 800-report parent cut required')
        earlier=all_rows[:400]
        cutoff=earlier[-1]['time_s']
        air1=root/BASE/AIR1
        if _sha(air1)!=inventory['sha256'] or inventory['sha256']!=scores['raw_air1_sha256']:
            raise ValueError('air1 source hash differs')
        with air1.open() as stream:
            raw=list(records(earlier_lines(stream,last_training_s=cutoff)))
        matched=match_times(earlier,raw)
        if (len(matched)!=400 or [index for index,_ in matched]!=list(range(400))
                or any(any(source[key]!=earlier[index][key]
                           for key in ('latitude_deg','longitude_deg','height_m'))
                       for index,source in matched)):
            raise ValueError('sealed parent training positions differ from air1')
        sources=[]
        for name,size in TARGETS.items():
            path=root/BASE/name
            receipt=json.loads((root/BASE/(name+'.receipt.json')).read_bytes())
            source_sha=verify_complete(path,size,receipt)
            expected=next(row for row in scores['sources'] if row['filename']==name)
            if source_sha!=expected['sha256']:
                raise ValueError('alternate PPP source hash differs')
            with path.open() as stream:
                alternate=list(records(earlier_lines(stream,last_training_s=cutoff)))
            pairs=match_times(earlier,alternate)
            if len(pairs)!=400 or [index for index,_ in pairs]!=list(range(400)):
                raise ValueError('complete 400-epoch alternate training match required')
            modified=[]
            displacements=[]
            for index,other in pairs:
                reference=earlier[index]
                if abs(other['time_s']-reference['time_s'])>MATCH_TOLERANCE_S:
                    raise ValueError('alternate training time exceeds tolerance')
                adjusted=corrected_neu(reference,other)[1]
                latitude,longitude,height=aligned_coordinates(reference,adjusted)
                row=dict(reference,latitude_deg=latitude,
                         longitude_deg=longitude,height_m=height)
                modified.append(row)
                displacements.append(adjusted)
            sources.append(dict(filename=name,source_sha256=source_sha,
                training_rows=modified,
                training_rows_sha256=digest(encoded(modified)),
                maximum_absolute_shift_neu_m=[max(abs(row[axis]) for row in displacements)
                                              for axis in range(3)],
                rms_shift_neu_m=[math.sqrt(math.fsum(row[axis]**2 for row in displacements)/400)
                                 for axis in range(3)]))
        return dict(version=VERSION,plan_sha256=_sha(root/PLAN),
            code_sha256=_sha(Path(__file__)),source_scores_sha256=_sha(root/SCORES),
            parent_manifest_sha256=parent.completion['manifest_sha256'],
            matrix_manifest_sha256=study.completion['manifest_sha256'],
            original_air1_sha256=inventory['sha256'],training_epochs=400,
            future_receiver_positions_read=False,
            changed_fields=['latitude_deg','longitude_deg','height_m'],
            unchanged_air1_covariance_and_velocity=True,sources=sources,
            protected_group_reads=0,imu_original_reads=0,new_fits=0)
    finally:
        study.close();parent.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh alternate training material required')
    result=build(args.root)
    atomic(output,gzip.compress(encoded(result),mtime=0))
    print([(row['filename'],row['rms_shift_neu_m']) for row in result['sources']])


if __name__=='__main__': main()
