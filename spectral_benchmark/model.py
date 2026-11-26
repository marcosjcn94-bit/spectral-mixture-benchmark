import numpy as np
from scipy.optimize import lsq_linear, minimize

WIDTH = 6
AXIS = np.arange(-60, 61)
SEPARATIONS = (0.25, 0.5, 1, 2, 4)
FRACTIONS = (0, 0.1, 0.5, 0.9, 1)
NOISE = (0, 0.01, 0.03, 0.10)
SEED = 2026


def spectra(separation):
    center = separation * WIDTH / 2
    return tuple(np.exp(-0.5 * ((AXIS - mean) / WIDTH)**2)
                 for mean in (-center, center))


def reference(first, second, observation):
    direction = first - second
    if np.array_equal(first, second):
        return None
    projection = np.dot(direction, observation - second) / np.dot(direction, direction)
    return float(np.clip(projection, 0, 1))


def fit(first, second, observation):
    if np.array_equal(first, second):
        return {}
    direction = first - second
    target = observation - second

    def objective(p):
        residual = direction * p[0] - target
        return residual @ residual

    def gradient(p):
        return np.array([2 * (direction @ (direction * p[0] - target))])

    return {
        "BVLS": lsq_linear(direction[:, None], target, bounds=(0, 1),
                           method="bvls", lsq_solver="exact", tol=1e-12, max_iter=100),
        "SLSQP": minimize(objective, [0.5], jac=gradient, bounds=[(0, 1)],
                          method="SLSQP", options={"ftol": 1e-14, "maxiter": 100}),
    }
