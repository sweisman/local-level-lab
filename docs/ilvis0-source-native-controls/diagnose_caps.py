from pathlib import Path
from fractions import Fraction as F
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.ilvis0_sharded_native import read
from lll.ilvis0_transform_native import make_reference
from lll.ilvis0_initial_source_bridge import certify
from lll.ilvis0_exact_scale import sqrt_upper

def norm(values):return F(sqrt_upper(sum((v*v for v in values),F(0))))
root=Path(__file__).parent
manifest=json.loads((root/'manifest.json').read_text());rows=[]
for task in manifest['tasks']:
    if task['payload']['kind']!='broad':continue
    path=root/manifest['inputs'][task['input_key']]['path'];case=read(path)
    config={k:np.asarray(v) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in case['configuration'].items()}
    lo=np.asarray(case['lower']);hi=np.asarray(case['upper']);z=np.asarray(case['center'])
    reference=make_reference(config,case['theta'],case['dv'],case['dt'],lower=lo,upper=hi,center=z)
    old=certify(reference,lo,hi);r=reference.parent;a=reference.acceleration
    limits=[F(float(v)) for v in r.limits];center=[F(float(v)) for v in z]
    p=[l*v for l,v in zip(limits,center,strict=True)]
    lower=[l*min(F(float(v)),c) for l,v,c in zip(limits,lo,center,strict=True)]
    upper=[l*max(F(float(v)),c) for l,v,c in zip(limits,hi,center,strict=True)]
    widths=[max(abs(F(float(v))-c),abs(F(float(w))-c)) for v,w,c in zip(lo,hi,center,strict=True)]
    dt=F(a.period);raw=[F(float(v)) for v in a.raw_delta_v]
    f0=[(raw[i]-p[12+i]*dt)/(1+p[18+i])/dt for i in range(3)]
    changes=[];remainders=[]
    for i in range(3):
        db=limits[12+i]*widths[12+i];dg=limits[18+i]*widths[18+i]
        corners=[(raw[i]-b*dt)/(1+g)/dt for b in (lower[12+i],upper[12+i])
            for g in (lower[18+i],upper[18+i])]
        changes.append(max(abs(v-f0[i]) for v in corners))
        den=1+p[18+i];minimum=1+lower[18+i]
        remainders.append(abs(raw[i]-p[12+i]*dt)*dg*dg/(den**2*minimum*dt)+db*dg/(den*minimum))
    matrix=[[F(float(v)) for v in row] for row in r.initial_r]
    gram=[[sum((matrix[k][i]*matrix[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
    ni=F(sqrt_upper(min(sum((gram[i][i] for i in range(3)),F(0)),max(sum(abs(v) for v in row) for row in gram))))
    angle=norm(limits[i]*widths[i] for i in range(3))
    corrected=ni*(angle**2*norm(f0)/2+min(F(2),angle)*norm(changes)+norm(remainders))
    rows.append(dict(identity=task['identity'],input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        center=z.tolist(),lower=lo.tolist(),upper=hi.tolist(),original_cap=a.remainder,
        symmetric_proof=float(F(old['nonlinear_remainder'])),actual_box_proof=float(corrected),
        actual_box_fits=corrected<=F(a.remainder)))
report=dict(scope='six analytic reference/cap comparisons; no trajectories, bounds or optimizer starts',
    cases=rows,all_actual_box_fits=all(r['actual_box_fits'] for r in rows))
Path(__file__).with_name('CAP_DIAGNOSIS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
print(json.dumps([{k:r[k] for k in ('identity','original_cap','symmetric_proof','actual_box_proof','actual_box_fits')} for r in rows]))
