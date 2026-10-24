# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import sys
import tempfile
import unittest


class TestClosed(unittest.TestCase):
    def test_resolution_report_rejects_open_before_numerical_imports(self):
        m=importlib.import_module('lll.airquantumgrav_resolution_report');before='numpy' in sys.modules
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises((ValueError,FileNotFoundError)):m.inspect(root,'data/not-closed')
        self.assertEqual('numpy' in sys.modules,before)


def test_resolution_report_rejects_changed_saved_parameters_and_missing_columns():
    import copy
    import io
    import numpy as np
    import pytest
    from lll.airquantumgrav_resolution_report import verify_sweeps
    from lll.stopping_resolution import probe
    from test_stopping_resolution import fixture
    fit,evaluate=fixture();saved={};binary={}
    probe(fit,evaluate=evaluate,physical_step=lambda d:d.reshape(-1,3),packet_count=600,epoch_count=27,
        reserve=lambda **v:None,save=lambda k,v:saved.__setitem__(k,v),save_bytes=lambda k,v:binary.__setitem__(k,v),check_continue=lambda:None)
    arrays=[]
    for row in saved['probe.json']['sweeps']:
        with np.load(io.BytesIO(binary[row['artifact']]),allow_pickle=False) as a:arrays.append({k:a[k].copy() for k in a.files})
    result=verify_sweeps(fit,saved['probe.json'],arrays,physical_step=lambda d:d.reshape(-1,3))
    assert result['native_calls']==10 and not result['labels_changed']
    for bad in ('point','jacobian','physical','metric'):
        values=copy.deepcopy(arrays);output=copy.deepcopy(saved['probe.json'])
        if bad=='point':values[0]['point'][0]+=.001
        elif bad=='jacobian':values[0]['jacobian']=values[0]['jacobian'][:,:-1]
        elif bad=='physical':values[2]['position_delta_neu_m'][0,0]+=.1
        else:output['sweeps'][2]['cost']+=1.
        with pytest.raises(ValueError):verify_sweeps(fit,output,values,physical_step=lambda d:d.reshape(-1,3))
