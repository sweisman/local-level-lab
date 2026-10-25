# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete-block prediction scores; no fitting or confidence calibration."""
import math

COORDINATES=('latitude','longitude','height')


def _rows(values,columns):
    try:
        if not values or any(len(row)!=columns or any(type(x) not in (int,float) or not math.isfinite(x)
                for x in row) for row in values):raise ValueError('complete finite numeric rows required')
        return values
    except TypeError as exc:raise ValueError('complete finite numeric rows required') from exc


def maximum_score(errors,standard_deviations,*,maximum_epochs):
    if type(maximum_epochs) is not int or not 1<=maximum_epochs<=100000:
        raise ValueError('finite epoch allowance required')
    errors=_rows(errors,3);std=_rows(standard_deviations,3)
    if len(errors)!=len(std) or len(errors)>maximum_epochs or any(x<=0 for row in std for x in row):
        raise ValueError('aligned positive standard deviations within the epoch allowance required; no floor')
    z=[[x/s for x,s in zip(e,v)] for e,v in zip(errors,std)]
    if any(not math.isfinite(v) for row in z for v in row):raise ValueError('finite standardized errors required')
    i,j=max(((i,j) for i in range(len(z)) for j in range(3)),key=lambda ij:abs(z[ij[0]][ij[1]]))
    return dict(maximum_standardized_error=abs(z[i][j]),worst_epoch_index=i,worst_coordinate=COORDINATES[j],
        maximum_by_coordinate={name:max(abs(row[k]) for row in z) for k,name in enumerate(COORDINATES)},
        standardized_errors=z,epochs=len(z),score_definition='maximum absolute marginal-standardized coordinate error over complete later block',
        calibration_uncertainty_included=False,confidence_calibrated=False,scientific_decision='abstain')


def coordinate_score(predicted,truth,covariance,*,maximum_epochs):
    p=_rows(predicted,3);t=_rows(truth,3)
    if len(p)!=len(t) or len(covariance)!=len(p):raise ValueError('aligned complete positions and covariance required')
    if any(abs(row[0])>=math.pi/2 for row in [*p,*t]):raise ValueError('nonpolar native latitude coordinates required')
    deviations=[]
    for covariance_row in covariance:
        c=_rows(covariance_row,3)
        if len(c)!=3 or any(c[i][i]<=0 for i in range(3)):raise ValueError('positive coordinate covariance required')
        std=[math.sqrt(c[i][i]) for i in range(3)]
        r=[[c[i][j]/std[i]/std[j] for j in range(3)] for i in range(3)]
        if (any(not math.isfinite(v) for row in r for v in row)
                or any(abs(r[i][j]-r[j][i])>1e-12 for i in range(3) for j in range(3))):
            raise ValueError('symmetric finite coordinate covariance required')
        # Check the normalized correlation matrix without an ill-scaled solve.
        second=1-r[1][0]**2
        if second<=0:raise ValueError('positive-definite covariance required; no repair')
        last=1-r[2][0]**2-((r[2][1]-r[2][0]*r[1][0])/math.sqrt(second))**2
        if not math.isfinite(last) or last<=0:raise ValueError('positive-definite covariance required; no repair')
        deviations.append(std)
    errors=[[a-b for a,b in zip(x,y)] for x,y in zip(p,t)]
    for row in errors:
        if row[1]<-math.pi or row[1]>=math.pi:row[1]=(row[1]+math.pi)%(2*math.pi)-math.pi
    return dict(maximum_score(errors,deviations,maximum_epochs=maximum_epochs),
        coordinate_units=['radian','radian','metre'],longitude_wrapping='[-pi,pi)',
        covariance_scope='conditional physical-position error with calibration treated as known')
