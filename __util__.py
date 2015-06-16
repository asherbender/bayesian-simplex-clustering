import numpy as np


def isconv(tol, val):
    if len(val) < 2:
        return False
    return max(2.0*abs(val[-1]-val[-2]), np.spacing(1.0-tol)) <= tol*(abs(val[-1]) + abs(val[-2]))


def unique(seq):
    order = np.argsort(seq)
    ind, = np.where(np.diff(seq[order]) > 0)
    ind = np.concatenate([np.array([0]), ind+1, np.array([np.size(seq)])])
    for i, j in zip(ind[:-1], ind[1:]):
        yield seq[order[i]], order[i:j]
