"""Mechanics checks for two contextual-bandit libraries on toy data.

Toy data only (NOT measured user data). Purpose: verify that both libraries
install, fit on (context, arm, reward) records shaped like our decision-point
table, and predict. Numbers here say nothing about intervention quality.

Run: python bandit_quickrun.py
Verified 2026-11-14:
- MABWiser LinTS fit on 8 toy records and returned predictions + expected
  rewards for two contexts.
- contextualbandits LinTS trained on 200 toy records; holdout best-arm rate
  was 0.34 vs 0.333 for random choice, i.e. no learning above chance under
  this tiny setup. Mechanics verified; quality not demonstrated.
"""
import numpy as np

print("=== MABWiser ===")
from mabwiser.mab import MAB, LearningPolicy

arms = ["morning_word_a", "evening_word_b", "no_send"]
decisions = [
    "morning_word_a", "evening_word_b", "no_send", "morning_word_a",
    "evening_word_b", "morning_word_a", "no_send", "evening_word_b",
]
rewards = [1, 0, 0, 1, 1, 0, 0, 1]
contexts = [[9, 1], [21, 0], [12, 1], [9, 0], [21, 1], [9, 1], [18, 0], [21, 0]]
mab = MAB(arms, LearningPolicy.LinTS())
mab.fit(decisions, rewards, contexts)
print("predictions for contexts [9,1] and [21,0]:", mab.predict([[9, 1], [21, 0]]))
print("expected rewards:", mab.predict_expectations([[9, 1], [21, 0]]))

print("=== contextualbandits ===")
from contextualbandits.online import LinTS

rng = np.random.default_rng(3)
X = rng.normal(size=(300, 4))
B = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]])
best = (X @ B.T).argmax(axis=1)
model = LinTS(nchoices=3)
a_train = rng.integers(0, 3, size=200)
r_train = (a_train == best[:200]).astype(float)
model.fit(X[:200], a_train, r_train)
pred = model.predict(X[200:])
print("holdout best-arm rate:", round(float((pred == best[200:]).mean()), 3), "(random = 0.333)")
