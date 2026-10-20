# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import importlib.util
from lll import ilvis0_joint_constraint_projection as projection


def test_adapter_loads_through_frozen_standalone_worker_entry():
    spec=importlib.util.spec_from_file_location('standalone_projection_adapter',projection.__file__)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate)


def test_all_42_coordinates_and_physical_auxiliary_coupling_remain():
    matrix=np.zeros((4,42));matrix[0,0]=matrix[0,27]=1.;matrix[1,0]=-1.;matrix[2,27]=-1.;matrix[3,41]=1.
    calls=[]
    result=projection.project(-np.ones(42),np.ones(42),matrix,[.25,0.,0.,.1],before_proposal=lambda:calls.append(1))
    assert len(result)==42 and len(calls)==84
    for index in (0,27):assert result[index]['lower']==0. and result[index]['upper']==.25
    assert result[41]['upper']==.1
    assert result[26]['lower']==-1. and result[26]['upper']==1.
