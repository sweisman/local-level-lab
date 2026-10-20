#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate corrected adapter-entry freeze; original zero-start failure retained."""
import ilvis0_joint_constraint_projection_worker as base

base.DATA=base.ROOT/'data/ilvis0-joint-constraint-projection-v2-20261020'
base.PUBLIC=base.ROOT/'docs/ilvis0-joint-constraint-projection-v2'
base.SOURCES=base.SOURCES+['analysis/tests/ilvis0_joint_constraint_projection_v2.py',
    'docs/ilvis0-joint-constraint-projection-v2/PLAN.md']

if __name__=='__main__':base.main()
