# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only checks can run without numerical imports."""
import importlib
import itertools
import unittest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_weighted_report') is not None,'weighted saved-result reporter missing'
    return importlib.import_module('lll.airquantumgrav_weighted_report')


def fixture():
    r=dict(models=['r','s','f'],latitudes_deg=[-55.,55.],profiles=[False,True],starts=2,policies=['short','long'])
    rows=[dict(spec=dict(zip(('model','latitude_deg','profile','start','policy_id'),values)),
        complete=True,result=dict(passed=True,converged=True))
        for values in itertools.product(r['models'],r['latitudes_deg'],r['profiles'],range(2),r['policies'])]
    return r,rows


class TestWeightedMatrix(unittest.TestCase):
    def test_all_required_settings_must_pass(self):
        r,rows=fixture();report=library().matrix_summary(rows,r)
        self.assertTrue(report['qualified']);self.assertEqual(report['passing'],48)
        rows[0]['result']['passed']=False
        self.assertFalse(library().matrix_summary(rows,r)['qualified'])

    def test_missing_or_duplicate_settings_cannot_qualify(self):
        r,rows=fixture()
        with self.assertRaises(ValueError):library().matrix_summary(rows[:-1],r)
        with self.assertRaises(ValueError):library().matrix_summary(rows[:-1]+[rows[0]],r)

    def test_completion_and_accuracy_are_separate(self):
        r,rows=fixture();rows[0]['complete']=False;rows[0]['result']['passed']=False
        report=library().matrix_summary(rows,r)
        self.assertFalse(report['qualified']);self.assertEqual(report['complete'],47)
        self.assertEqual(report['passing'],47)
