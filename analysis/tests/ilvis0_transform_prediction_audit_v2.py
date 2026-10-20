# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate saved-only freeze after the preserved zero-start import failure."""
import ilvis0_transform_prediction_audit as base

base.DATA=base.ROOT/'data/ilvis0-transform-prediction-audit-v2-20261020'
base.PUBLIC=base.ROOT/'docs/ilvis0-transform-prediction-audit-v2'
base.SOURCES=[n.replace('docs/ilvis0-transform-prediction-audit/PLAN.md',
    'docs/ilvis0-transform-prediction-audit-v2/PLAN.md') for n in base.SOURCES]
base.SOURCES.append('analysis/tests/ilvis0_transform_prediction_audit_v2.py')

if __name__=='__main__':base.main()
