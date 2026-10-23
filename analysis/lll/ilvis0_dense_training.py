# SPDX-License-Identifier: AGPL-3.0-or-later
"""Connect fixed dense training rows to their complete declared error premise.

This assembles existing row arithmetic and provenance guards. Supplied native
bounds, error laws, physical calibration domains and empirical coverage still
need their separate qualification. No later observations enter this API.
"""
from copy import deepcopy
from .ilvis0_prediction_lineage import Origin,_family,register


def transfer_center(report,native_center,*,coordinate_scale,maximum_center_error_m):
    """Translate a supplied bound, charging its exact center difference.

    This is triangle-inequality arithmetic on an already justified expression.
    It does not prove the input enclosure, derivatives or whole-program rounding.
    The original report remains unchanged and its exact hash is retained.
    """
    import math
    from fractions import Fraction as F
    from .ilvis0_saved_prediction_audit import endpoint
    from .studies.artifacts import digest,encoded
    def vector(values):
        if not isinstance(values,(list,tuple)) or len(values)!=3:
            raise ValueError('three finite binary coordinate values required')
        result=[]
        for value in values:
            if type(value) not in (int,float):raise ValueError('finite binary coordinate required')
            try:binary=float(value)
            except OverflowError as error:raise ValueError('unrepresentable coordinate') from error
            if not math.isfinite(binary) or F(binary)!=F(value):raise ValueError('exact finite binary coordinate required')
            result.append(binary)
        return result
    if 'center_transfer' in report:raise ValueError('report already has a center transfer')
    old=vector(report['center']);new=vector(native_center)
    radius=vector(report['unshared_remainder']);scale=vector(coordinate_scale)
    if (any(v<0 for v in radius) or any(v<=0 for v in scale)
            or type(maximum_center_error_m) not in (int,float)
            or not math.isfinite(maximum_center_error_m) or maximum_center_error_m<0):
        raise ValueError('nonnegative radii, positive scales and finite explicit tolerance required')
    difference=[abs(F(a)-F(b)) for a,b in zip(old,new,strict=True)]
    metres=[v*F(s) for v,s in zip(difference,scale,strict=True)]
    if any(v>F(maximum_center_error_m) for v in metres):raise ValueError('center discrepancy exceeds the frozen allowance')
    result=deepcopy(report);result['center']=new
    result['unshared_remainder']=[endpoint(F(v)+d,True) for v,d in zip(radius,difference,strict=True)]
    result['center_transfer']=dict(method='exact-additive-coordinate-translation-v1',
        original_report_sha256=digest(encoded(report)),original_center=old,coordinate_scale=scale,
        exact_added_coordinate_radius=list(map(str,difference)),center_error_m=[endpoint(v,True) for v in metres],
        maximum_center_error_m=maximum_center_error_m,whole_program_roundoff_qualified=False)
    return result


def _parent_constraints(training,reports,origins):
    known={}
    for origin in origins:
        if not isinstance(origin,Origin) or origin.input_binding in known:
            raise ValueError('unique typed parent origins required')
        known[origin.input_binding]=origin
    used=set()
    for report in reports:
        premise=report['conditioning'];version=premise['version']
        if version=='ilvis0-verified-training-acceleration-v1':
            key=premise['input_binding']
            if key not in known:raise ValueError('unknown training premise; old conditioning cannot be relabeled')
            used.add(key)
        elif version!='ilvis0-physical-directional-acceleration-v1':
            raise ValueError('supported physical root or typed parent required')
    design=[];upper=[]
    for key in sorted(used):
        design.extend(map(list,known[key].design));upper.extend(known[key].upper_bounds)
    region=training['region']
    if (region.get('inequality_design',[])!=design or region.get('inequality_upper',[])!=upper
            or any(k in region for k in ('target_lower','target_upper','noise_allowance_m','observation_allowance_m'))):
        raise ValueError('existing training constraints must come from the typed parent origins')
    return design,upper


def build(training,reports,*,reference,errors,origins=()):
    """Assemble a fresh 51-column conditioning bundle without legacy rows.

    Each data-conditioned input must name a typed parent, and its constraints
    must already be present exactly. Fixed weights depend only on timestamps.
    The bundle hash includes the full 453-row allowance premise, not just its
    twelve current radii or a covariance identity. No support solve, bound
    integration, future observation or fitted model selection occurs here.
    """
    origins=tuple(origins);parent_design,parent_upper=_parent_constraints(training,reports,origins)
    from .ilvis0_summary_error_controls import fixed_weights
    from .ilvis0_declared_training_rows import projected_training_rows
    times=training['times_s'];weights=fixed_weights(times,training_end_s=290.)[0].tolist()
    family_id,premise_id=_family(errors,weights,times)
    rows=projected_training_rows(training,reports,weights=weights,
        observation_allowance_m=errors['allowances']['radius_m'][:12],source_binding=training['source_binding'])
    region=training['region'];source=training['source_binding']
    names=('parameter_count','lower','upper','center','coordinate_scale','arithmetic_allowance','design')
    problem={key:deepcopy(region[key]) for key in names}
    problem.update(binding=source['reference_binding'],source_id=source['source_id'],future_truth_used=False,
        inequality_design=parent_design+rows['design'],inequality_upper=parent_upper+rows['upper'])
    bundle=dict(training=dict(region=problem,projected_training_id=rows['projected_training_id'],
        error_family_id=family_id,error_premise_id=premise_id),reference=deepcopy(reference),
        lower=list(region['lower']),upper=list(region['upper']))
    origin=register(training,reports,rows,errors,bundle,origins=origins)
    return dict(bundle=bundle,rows=rows,origin=origin,physical_parameter_count=27,parameter_count=51,
        future_observations_used=False,prediction_method_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
