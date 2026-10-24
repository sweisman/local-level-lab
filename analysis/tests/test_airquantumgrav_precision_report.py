# SPDX-License-Identifier: AGPL-3.0-or-later
from unittest.mock import patch

import numpy as np
import pytest


def test_precision_report_rejects_open_study_before_numerical_audit(tmp_path):
    from lll.airquantumgrav_precision_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_precision_saved_array_audit_rejects_changed_points_labels_and_costs(tmp_path):
    import io
    from lll.ilvis0_precision_value import compare
    from lll.airquantumgrav_precision_report import verify_case
    from test_ilvis0_precision_value import _stationary_problem
    p=_stationary_problem(tmp_path);points=np.zeros((2,len(p.bounds.active)));binary={}
    def native(problem,point,model,*,kernel,longitude):
        return dict(coordinates=p.gps.copy(),coordinate_difference=np.zeros_like(p.gps),residual=np.zeros(9),boundaries=0)
    with patch('lll.ilvis0_precision_value.calculate',side_effect=native):
        result=compare(p,points,source_residuals=np.zeros((2,9)),source_converged=False,model='flat_still',
            kernel_factory=lambda precision:(None,{}),reserve=lambda **v:None,save=lambda *v:None,
            save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    arrays={}
    for k,v in binary.items():
        with np.load(io.BytesIO(v),allow_pickle=False) as a:arrays[k]={n:a[n].copy() for n in a.files}
    assert verify_case(p,result,arrays,points=points,reference=np.zeros((2,9)),source_converged=False)
    import copy
    for changed in ('point','label','cost'):
        a=copy.deepcopy(arrays);r=copy.deepcopy(result)
        if changed=='point':a['double-0.npz']['point'][0]=.1
        elif changed=='label':r['source_converged']=True
        else:r['modes']['double-stable']['baseline_cost']=1.
        with pytest.raises(ValueError):verify_case(p,r,a,points=points,reference=np.zeros((2,9)),source_converged=False)
