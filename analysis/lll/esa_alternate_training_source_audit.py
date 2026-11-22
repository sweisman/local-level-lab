# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prove alternate ESA fit inputs differ only in training positions."""

import gzip
import json
from pathlib import Path

from .esa_alternate_training_refit import MATERIAL
from .esa_full_parallel_gnss import _sha

VERSION='esa-alternate-training-source-audit-v1'
POSITION={'latitude_deg','longitude_deg','height_m'}


def compare_rows(original,alternate):
    if len(original)!=400 or len(alternate)!=400:
        raise ValueError('exact 400-row matched training inputs required')
    changed=0
    for old,new in zip(original,alternate,strict=True):
        if (set(old)!=set(new) or
                {k:v for k,v in old.items() if k not in POSITION}
                !={k:v for k,v in new.items() if k not in POSITION}):
            raise ValueError('non-position training field changed')
        if any(old[key]!=new[key] for key in POSITION):
            changed+=1
    if changed!=400:
        raise ValueError('all matched positions must change for this control')
    return changed


def build(root):
    from .esa_rolling_origin_400_model_matrix import ID
    from .studies.artifacts import digest,encoded
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    raw=(root/MATERIAL).read_bytes()
    material=json.loads(gzip.decompress(raw))
    if (material.get('version')!='esa-alternate-training-material-v1'
            or material.get('training_epochs')!=400
            or material.get('future_receiver_positions_read') is not False
            or len(material.get('sources',[]))!=2):
        raise ValueError('unchanged two-source training material required')
    original=ClosedStudy(root,'data/'+ID)
    try:
        if material['matrix_manifest_sha256']!=original.completion['manifest_sha256']:
            raise ValueError('original matrix manifest differs')
        source=original.input('training',raw=True)
        baseline=json.loads(gzip.decompress(source))
        sources=[]
        for row in material['sources']:
            if digest(encoded(row['training_rows']))!=row['training_rows_sha256']:
                raise ValueError('material training-row hash differs')
            sources.append(dict(filename=row['filename'],
                                rows_changed_only_in_position=
                                compare_rows(baseline,row['training_rows'])))
        return dict(version=VERSION,code_sha256=_sha(Path(__file__)),
                    material_sha256=digest(raw),
                    original_training_sha256=digest(source),
                    original_manifest_sha256=original.completion['manifest_sha256'],
                    sources=sources,original_reads=0,later_positions_read=False,
                    protected_group_reads=0,new_fits=0)
    finally:
        original.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh source audit required')
    result=build(args.root)
    atomic(output,encoded(result))
    print([(row['filename'],row['rows_changed_only_in_position'])
           for row in result['sources']])


if __name__=='__main__': main()
