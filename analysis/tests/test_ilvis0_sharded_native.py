# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict compatibility checks do not silently forgive changed scientific output."""
import unittest
from types import SimpleNamespace
import numpy as np
from lll import ilvis0_sharded_native as adapter
from lll.ilvis0_acceleration_control_case import evaluate_case


class CompatibilityTests(unittest.TestCase):
    def test_float_bits_preserve_signed_zero(self):
        adapter.compare_native(dict(point=[0.],prediction=[1.],jacobian=[[2.]],warning=0),
                               dict(point=[0.],prediction=[1.],jacobian=[[2.]],warning=0))
        with self.assertRaisesRegex(ValueError,'bitwise'):
            adapter.compare_native(dict(point=[-0.],prediction=[1.],jacobian=[[2.]],warning=0),
                                   dict(point=[0.],prediction=[1.],jacobian=[[2.]],warning=0))

    def test_shapes_warning_and_last_bit_must_match(self):
        baseline=dict(point=[0.],prediction=[1.],jacobian=[[2.]],warning=0)
        for changed in (dict(baseline,warning=1),dict(baseline,jacobian=[2.]),
                        dict(baseline,prediction=[np.nextafter(1.,2.)])):
            with self.assertRaises(ValueError):adapter.compare_native(changed,baseline)

    def test_bound_comparison_checks_all_nested_metadata(self):
        reference=dict(center=[0.,1.],reference=dict(binding='a',bounds=[2.]))
        adapter.compare_bound(reference,reference)
        with self.assertRaises(ValueError):
            adapter.compare_bound(dict(reference,reference=dict(binding='b',bounds=[2.])),reference)

    def test_normalization_preserves_numbers_and_rejects_nonfinite(self):
        self.assertEqual(adapter.plain(dict(a=np.array([1.,2.]),b=np.bool_(True))),dict(a=[1.,2.],b=True))
        with self.assertRaises(ValueError):adapter.compare_bound(dict(x=float('nan')),dict(x=float('nan')))

    def test_callback_acceptance_checks_all_physical_tangent_columns(self):
        initial=np.array([.5,0.,100.]);jac=np.arange(81.).reshape(3,27)*1e-9;seen=[]
        case=dict(center=[0.]*27,lower=[-.01]*27,upper=[.01]*27,dt=[.005],configuration=dict(initial_c=initial))
        def native(point):return initial+jac@point,jac
        def bound(point,left,right):
            seen.append(np.array(point));reference=SimpleNamespace(report=lambda:{},reference=SimpleNamespace(report=lambda:{}))
            report=SimpleNamespace(center=initial+jac@point,design=lambda matrix,ref:np.c_[matrix,np.zeros((3,15))],report=lambda:{})
            return report,reference
        result=evaluate_case(dict(identity='tangent',kind='tangent'),case,native=native,bound=bound)
        self.assertTrue(result['passed']);self.assertEqual(len(seen),55);self.assertEqual(result['tangent_columns'],27)
        bad=jac.copy();bad[2,26]+=1.
        result=evaluate_case(dict(identity='bad',kind='tangent'),case,native=lambda p:(initial+jac@p,bad),bound=bound)
        self.assertFalse(result['passed'])


if __name__=='__main__':unittest.main()
