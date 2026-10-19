# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent planted calibration fixtures, not aircraft simulations."""
import numpy as np


LIMITS=np.array([.15,.15,.15,.25,.25,.25,.05])
STARTS=(np.zeros(7),np.array([.8,-.8,.8,.8,-.8,.8,.8]),np.array([-.8,.8,-.8,-.8,.8,-.8,-.8]))
FIXTURES=('interior','near_boundary','exact_boundary','constant_degenerate')


def fixture(name):
    if name not in FIXTURES:raise ValueError('unsupported known-answer fixture')
    if name=='constant_degenerate':
        force=np.tile([0.,0.,-9.81],(121,1));return force.copy(),force,np.zeros(7)
    rng=np.random.default_rng(29451)
    force=rng.normal(size=(121,3))*2.+[0.,0.,-8.]
    planted=dict(interior=np.array([.05,-.07,.02,.05,-.04,.08,.01]),
        near_boundary=LIMITS*np.array([.99,-.99,.98,.99,-.98,.99,.98]),
        exact_boundary=LIMITS*np.array([1.,-1.,1.,1.,-1.,1.,1.]))[name]
    body=[]
    for value in force:
        rotation,_=np.linalg.qr(rng.normal(size=(3,3)))
        rotation[:,0]*=np.linalg.det(rotation)
        ideal=rotation.T@(value-np.array([0.,0.,planted[6]]))
        body.append(ideal*(1.+planted[:3])+planted[3:6])
    return np.array(body),force,planted
