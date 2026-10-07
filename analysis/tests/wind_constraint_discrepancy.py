# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit research covariance for the existing physical wind speed allowance."""
import numpy as np
from lll.wind_tas import WIND_TAS_POLICY

POLICY=dict(version='registered-wind-constraint-discrepancy-1',
    source='Existing WIND_TAS_POLICY ground_constraint_sigma_mps, retained as independent model discrepancy in addition to propagated measurement errors',
    sigma_mps=WIND_TAS_POLICY['ground_constraint_sigma_mps'],
    normalized_auxiliary_variance=1.,correlation='Independent auxiliary bins; no gyro/model-discrepancy cross terms',
    covariance_components='Full shared-input measurement covariance plus explicit auxiliary model covariance',
    production_enabled=False,decisions_enabled=False)


def discrepancy_covariance(n_rows,n_gyro,crab_model):
    if n_gyro<=0 or n_gyro>n_rows or n_gyro%3:raise ValueError('valid gyro and total row counts required')
    auxiliary=n_rows-n_gyro
    if crab_model=='wind' and auxiliary:raise ValueError('broad wind has no speed auxiliary')
    if crab_model=='wind_tas' and auxiliary!=n_gyro//3:raise ValueError('one speed constraint per gyro bin required')
    if crab_model not in ('wind','wind_tas'):raise ValueError('recognized wind candidate required')
    result=np.zeros((n_rows,n_rows))
    # The auxiliary residual is already divided by the registered m/s allowance.
    result[n_gyro:,n_gyro:]=np.eye(auxiliary)
    return result


def add_discrepancy(covariance,n_gyro,crab_model):
    covariance=np.asarray(covariance,float)
    if covariance.ndim!=2 or covariance.shape[0]!=covariance.shape[1]:raise ValueError('square covariance required')
    return covariance+discrepancy_covariance(len(covariance),n_gyro,crab_model)
