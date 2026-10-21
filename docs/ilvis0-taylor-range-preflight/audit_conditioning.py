# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only ancestry audit before transferring training bounds to subdomains."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def load(root,name,receipt):
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()):raise ValueError('artifact escapes its published root')
    blob=path.read_bytes();digest=hashlib.sha256(blob).hexdigest()
    if receipt['artifacts'].get(name)!=digest:raise ValueError('published ancestry input changed: '+name)
    return json.loads(blob),digest


def main():
    parent=ROOT/'docs/ilvis0-conditioned-prediction';child=ROOT/'docs/ilvis0-coupled-prediction'
    receipts={root:json.loads((root/'evidence-receipt.json').read_text()) for root in (parent,child)}
    manifest,_=load(parent,'manifest.json',receipts[parent]);rows=[]
    for task in manifest['tasks']:
        name=task['identity'];record=manifest['inputs'][task['input_key']]
        bundle,p_hash=load(parent,record['path'],receipts[parent])
        training,t_hash=load(child,f'artifacts/{name}/training.json',receipts[child])
        future,f_hash=load(child,f'artifacts/{name}/future.json',receipts[child])
        _,projection_hash=load(parent,f'artifacts/{name}/acceleration-projection.json',receipts[parent])
        before=bundle['training']['region'];after=training['region'];old=bundle['future']
        if before['parameter_count']!=51 or after['parameter_count']!=78:raise ValueError('original complete coordinate bases required')
        inherited=Counter((tuple(row+[0.]*27),limit) for row,limit in zip(
            before['inequality_design'],before['inequality_upper'],strict=True))
        actual=Counter((tuple(row),limit) for row,limit in zip(
            after['inequality_design'],after['inequality_upper'],strict=True))
        subset=all(a<=c<=d<=b for a,b,c,d in zip(old['lower'],old['upper'],future['lower'][:51],future['upper'][:51],strict=True))
        same=all(old[key][:27]==future[key][:27] for key in ('lower','upper'))
        source=(old['reference']==future['reference']==training['reference']
            and before['center']==after['center'][:51]
            and before['coordinate_scale']==after['coordinate_scale'] and before['origin']==after['origin'])
        constraints=all(actual[row]>=count for row,count in inherited.items())
        rows.append(dict(identity=name,parent_input_sha256=p_hash,descendant_training_sha256=t_hash,
            descendant_future_sha256=f_hash,parent_projection_sha256=projection_hash,
            physical_domain_identical=same,all_51_domain_coordinates_contained=subset,
            source_center_and_frame_identical=source,parent_constraints_retained=constraints,
            parent_constraint_count=sum(inherited.values())))
    report=dict(cases=rows,case_count=len(rows),identical_physical_domains=sum(row['physical_domain_identical'] for row in rows),
        valid_subdomains=sum(all(row[key] for key in ('all_51_domain_coordinates_contained',
            'source_center_and_frame_identical','parent_constraints_retained')) for row in rows),
        native_evaluations=0,bounds=0,optimizer_starts=0,original_reads=0,scientific_decision='abstain')
    path=Path(__file__).with_name('conditioning-audit.json');path.write_text(json.dumps(report,indent=2)+'\n')
    print(f"Verified {report['valid_subdomains']}/{len(rows)} inherited regions; {report['identical_physical_domains']} physical domains are identical. No numerical bounds or fits.")


if __name__=='__main__':main()
