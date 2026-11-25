"""Mechanics check: fit an HMM to a small series shaped like our state log.

The series is a hand-made sample (NOT measured user data): daily pairs of
(minutes_since_last_stimulus, responded) for one person, generated from three
regimes so the fit has something to find. Purpose is only to verify that
hmmlearn installs, fits, returns a transition matrix, and decodes states.

Run: python hmm_quickfit.py
Verified 2026-11-14: transition matrix and a 36-step decoded state sequence
were printed (hmmlearn, GaussianHMM, diag covariance).
"""
import numpy as np
from hmmlearn.hmm import GaussianHMM

rng = np.random.default_rng(7)
regimes = np.repeat([0, 1, 2, 1, 0, 2], 6)
means = {0: (240.0, 0.15), 1: (90.0, 0.45), 2: (30.0, 0.75)}
X = np.array(
    [[rng.normal(means[s][0], 25), rng.binomial(1, means[s][1])] for s in regimes],
    dtype=float,
)
model = GaussianHMM(n_components=3, covariance_type="diag", n_iter=200, random_state=7).fit(X)
print("transition matrix:")
print(np.round(model.transmat_, 2))
print("decoded states:", model.predict(X).tolist())
