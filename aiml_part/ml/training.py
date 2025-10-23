import os
import os
import logging
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLTraining")


@dataclass
class TrainingConfig:
    attack_csv_path: str
    network_csv_path: str
    models_dir: str = "models"
    text_column: str = "text"
    label_column: str = "label"
    test_size: float = 0.2
    random_state: int = 42


def _ensure_models_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _build_text_classifier() -> Pipeline:
    # Enhanced classifier for larger dataset
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=100000,  # Increased for better pattern capture
            ngram_range=(1, 3),   # Include trigrams for better context
            min_df=2,             # Minimum document frequency
            max_df=0.95,          # Maximum document frequency
            sublinear_tf=True     # Apply sublinear TF scaling
        )),
        ("clf", LogisticRegression(
            max_iter=500,         # Increased iterations for convergence
            C=1.0,               # Regularization strength
            class_weight='balanced'  # Handle class imbalance
        ))
    ])


def _train_and_save(csv_path: str, out_path: str, text_col: str, label_col: str, test_size: float, random_state: int) -> Optional[dict]:
    if not os.path.exists(csv_path):
        logger.warning(f"Dataset not found: {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    if text_col not in df.columns or label_col not in df.columns:
        raise ValueError(f"Dataset must contain columns '{text_col}' and '{label_col}'")

    # Sometimes stratify fails when a label has too few samples; fall back to non-stratified split
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            df[text_col].astype(str), df[label_col].astype(str), test_size=test_size, random_state=random_state, stratify=df[label_col]
        )
    except ValueError:
        logger.warning("Stratified split failed (imbalanced labels). Falling back to non-stratified split.")
        X_train, X_test, y_train, y_test = train_test_split(
            df[text_col].astype(str), df[label_col].astype(str), test_size=test_size, random_state=random_state
        )

    model = _build_text_classifier()
    logger.info(f"Training classifier on {csv_path} (train={len(X_train)}, test={len(X_test)})")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    joblib.dump(model, out_path)
    logger.info(f"Saved model -> {out_path}")

    return report


def train_all(config: TrainingConfig) -> dict:
    _ensure_models_dir(config.models_dir)

    results = {}
    attack_model_path = os.path.join(config.models_dir, "attack_model.joblib")
    network_model_path = os.path.join(config.models_dir, "network_model.joblib")

    results["attack"] = _train_and_save(
        csv_path=config.attack_csv_path,
        out_path=attack_model_path,
        text_col=config.text_column,
        label_col=config.label_column,
        test_size=config.test_size,
        random_state=config.random_state,
    )

    results["network"] = _train_and_save(
        csv_path=config.network_csv_path,
        out_path=network_model_path,
        text_col=config.text_column,
        label_col=config.label_column,
        test_size=config.test_size,
        random_state=config.random_state,
    )

    return results


