"""Logistic regression, random forest and gradient-boosted tree baselines.

These three models expect a complete matrix, so on their own they can only run in
the feature intersection. :class:`ImputedXGBoost` extends the boosted-tree model
to the feature union by filling structurally absent sensors, which is one of the
union strategies evaluated in the paper.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np

# torch has to be imported before xgboost. Both ship their own copy of the OpenMP
# runtime, and on macOS loading xgboost's copy first makes subsequent torch CPU
# operations segfault. Importing it here fixes the order for every entry point,
# since this is the only module that pulls in xgboost.
import torch  # noqa: F401
from hyperopt import hp
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ..data import FeatureSpace, Split
from .base import ReceptivityModel, Validation


class LogisticRegressionModel(ReceptivityModel):
    """L1/L2 regularised linear baseline on standardised features."""

    name: ClassVar[str] = "lr"
    feature_space: ClassVar[FeatureSpace] = FeatureSpace.INTERSECTION
    validation: ClassVar[Validation] = Validation.CV5

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "C": hp.loguniform("C", np.log(1e-4), np.log(1e2)),
            "penalty": hp.choice("penalty", ["l1", "l2"]),
        }

    def fit(self, split: Split) -> "LogisticRegressionModel":
        self._scaler = StandardScaler().fit(split.X_source)
        self._model = LogisticRegression(
            C=self.params.get("C", 1.0),
            penalty=self.params.get("penalty", "l2"),
            solver="liblinear",
            max_iter=1000,
            random_state=self.seed,
        )
        self._model.fit(
            self._scaler.transform(split.X_source),
            split.y_source,
            sample_weight=split.study_size_weights(),
        )
        return self

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(self._scaler.transform(X))[:, 1]


class RandomForestModel(ReceptivityModel):
    """Bagged decision trees; no scaling needed, so features are passed as-is."""

    name: ClassVar[str] = "rf"
    feature_space: ClassVar[FeatureSpace] = FeatureSpace.INTERSECTION
    validation: ClassVar[Validation] = Validation.CV5

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "n_estimators": hp.quniform("n_estimators", 50, 300, 10),
            "max_depth": hp.quniform("max_depth", 3, 20, 1),
            "min_samples_split": hp.quniform("min_samples_split", 2, 20, 1),
            "min_samples_leaf": hp.quniform("min_samples_leaf", 1, 10, 1),
            "max_features": hp.choice("max_features", ["sqrt", "log2", None]),
        }

    def fit(self, split: Split) -> "RandomForestModel":
        self._model = RandomForestClassifier(
            n_estimators=int(self.params.get("n_estimators", 100)),
            max_depth=int(self.params.get("max_depth", 10)),
            min_samples_split=int(self.params.get("min_samples_split", 2)),
            min_samples_leaf=int(self.params.get("min_samples_leaf", 1)),
            max_features=self.params.get("max_features", "sqrt"),
            n_jobs=self.params.get("n_jobs", 4),
            random_state=self.seed,
        )
        self._model.fit(
            split.X_source, split.y_source, sample_weight=split.study_size_weights()
        )
        return self

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)[:, 1]


class XGBoostModel(ReceptivityModel):
    """Gradient-boosted trees on the feature intersection."""

    name: ClassVar[str] = "xgb"
    feature_space: ClassVar[FeatureSpace] = FeatureSpace.INTERSECTION
    validation: ClassVar[Validation] = Validation.CV5

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "max_depth": hp.quniform("max_depth", 3, 10, 1),
            "learning_rate": hp.loguniform("learning_rate", np.log(0.01), np.log(0.3)),
            "n_estimators": hp.quniform("n_estimators", 50, 300, 10),
            "gamma": hp.uniform("gamma", 0, 0.5),
            "min_child_weight": hp.quniform("min_child_weight", 1, 10, 1),
            "subsample": hp.uniform("subsample", 0.6, 1.0),
            "colsample_bytree": hp.uniform("colsample_bytree", 0.6, 1.0),
            "reg_alpha": hp.loguniform("reg_alpha", np.log(1e-10), np.log(1)),
            "reg_lambda": hp.loguniform("reg_lambda", np.log(1e-10), np.log(1)),
        }

    def _build(self) -> XGBClassifier:
        return XGBClassifier(
            max_depth=int(self.params.get("max_depth", 6)),
            learning_rate=self.params.get("learning_rate", 0.1),
            n_estimators=int(self.params.get("n_estimators", 200)),
            gamma=self.params.get("gamma", 0.0),
            min_child_weight=int(self.params.get("min_child_weight", 1)),
            subsample=self.params.get("subsample", 1.0),
            colsample_bytree=self.params.get("colsample_bytree", 1.0),
            reg_alpha=self.params.get("reg_alpha", 0.0),
            reg_lambda=self.params.get("reg_lambda", 1.0),
            objective="binary:logistic",
            eval_metric="auc",
            tree_method=self.params.get("tree_method", "hist"),
            device=self.params.get("device", "cpu"),
            verbosity=0,
            random_state=self.seed,
        )

    def fit(self, split: Split) -> "XGBoostModel":
        self._model = self._build()
        self._model.fit(
            split.X_source, split.y_source, sample_weight=split.study_size_weights()
        )
        return self

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)[:, 1]


class ImputedXGBoost(XGBoostModel):
    """Boosted trees over the source feature union, with missing sensors filled in.

    Imputer and scaler are fitted on the source pool alone and then applied to the
    target, so no target statistic reaches training. Class imbalance is handled by
    ``scale_pos_weight`` instead of per-study weights: the union strategies balance
    classes rather than study sizes.
    """

    feature_space: ClassVar[FeatureSpace] = FeatureSpace.SOURCE_UNION
    imputation: ClassVar[str] = "median"

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "n_estimators": hp.choice("n_estimators", [100, 200, 300]),
            "max_depth": hp.choice("max_depth", [3, 4, 6]),
            "learning_rate": hp.choice("learning_rate", [0.01, 0.1, 0.2]),
        }

    def _make_imputer(self):
        if self.imputation == "median":
            return SimpleImputer(strategy="median")
        if self.imputation == "knn":
            return KNNImputer(
                n_neighbors=5, weights="distance", metric="nan_euclidean"
            )
        raise ValueError(f"Unknown imputation strategy: {self.imputation}")

    def fit(self, split: Split) -> "ImputedXGBoost":
        X = split.X_source.astype(np.float64, copy=True)

        # A column absent from every source study carries no information for the
        # imputer to work with, and scikit-learn would drop it, changing the
        # matrix width between fit and transform. Anchoring it at zero keeps the
        # column count stable.
        self._empty_columns = np.isnan(X).all(axis=0)
        X[:, self._empty_columns] = 0.0

        self._imputer = self._make_imputer().fit(X)
        X = self._imputer.transform(X)
        self._scaler = StandardScaler().fit(X)

        positives = float((split.y_source == 1).sum())
        negatives = float((split.y_source == 0).sum())
        self.params["scale_pos_weight"] = negatives / max(1.0, positives)

        self._model = self._build()
        self._model.fit(self._scaler.transform(X), split.y_source)
        return self

    def _build(self) -> XGBClassifier:
        model = super()._build()
        model.set_params(scale_pos_weight=self.params.get("scale_pos_weight", 1.0))
        return model

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        X = X.astype(np.float64, copy=True)
        X[:, self._empty_columns] = 0.0
        X = self._scaler.transform(self._imputer.transform(X))
        return self._model.predict_proba(X)[:, 1]


class MedianImputedXGBoost(ImputedXGBoost):
    """Feature union with per-feature median fill (the strongest union strategy)."""

    name: ClassVar[str] = "xgb-median"
    imputation: ClassVar[str] = "median"


class KNNImputedXGBoost(ImputedXGBoost):
    """Feature union with k-nearest-neighbour fill (k=5, inverse-distance weights).

    Neighbour search dominates the runtime on the larger studies, so candidates are
    scored on a single holdout rather than five folds; refitting the imputer five
    times per candidate is not affordable across 441 configurations.
    """

    name: ClassVar[str] = "xgb-knn"
    imputation: ClassVar[str] = "knn"
    validation: ClassVar[Validation] = Validation.HOLDOUT
    max_evals: ClassVar[int] = 10
