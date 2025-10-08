import os
import logging
import pandas as pd
from pathlib import Path

from ml.training import TrainingConfig, train_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainCLI")


def build_text_from_row(row: pd.Series) -> str:
    parts = []
    for key in ["Payload", "Signature", "AttackType", "Severity", "MITRE", "Description"]:
        if key in row and pd.notna(row[key]):
            parts.append(str(row[key]))
    return " | ".join(parts)


def convert_to_text_label(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if "Label" not in df.columns:
        raise ValueError(f"Expected 'Label' column in {csv_path}")
    out = pd.DataFrame()
    out["text"] = df.apply(build_text_from_row, axis=1)
    out["label"] = df["Label"].astype(str)
    out = out.dropna(subset=["text", "label"]).reset_index(drop=True)
    return out


def main():
    root = Path(__file__).resolve().parent
    payload_csv = root / "payload_dataset.csv"
    mitre_csv = root / "mitre_attack_structured_dataset.csv"
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = models_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    datasets = []
    if payload_csv.exists():
        datasets.append(str(payload_csv))
    if mitre_csv.exists():
        datasets.append(str(mitre_csv))

    if not datasets:
        raise FileNotFoundError("No datasets found. Expected payload_dataset.csv and/or mitre_attack_structured_dataset.csv in project root.")

    merged = []
    for path in datasets:
        logger.info(f"Loading dataset: {path}")
        df = convert_to_text_label(path)
        merged.append(df)

    merged_df = pd.concat(merged, ignore_index=True)
    # Simple cleanup
    merged_df = merged_df[merged_df["text"].str.len() > 3]

    # For this project, train two classifiers from the same merged dataset
    attack_tmp = tmp_dir / "attack_text_label.csv"
    network_tmp = tmp_dir / "network_text_label.csv"
    merged_df.to_csv(attack_tmp, index=False)
    merged_df.sample(frac=1.0, random_state=42).to_csv(network_tmp, index=False)

    config = TrainingConfig(
        attack_csv_path=str(attack_tmp),
        network_csv_path=str(network_tmp),
        models_dir=str(models_dir),
        text_column="text",
        label_column="label",
    )

    results = train_all(config)
    logger.info("Training complete.")
    for k, v in results.items():
        if v is None:
            logger.info(f"Model {k}: skipped (dataset missing)")
        else:
            logger.info(f"Model {k}: trained. Classes: {list(v.keys()) if isinstance(v, dict) else 'ok'}")

    print("\nModels saved under 'models/'. Files: attack_model.joblib, network_model.joblib")


if __name__ == "__main__":
    main()


