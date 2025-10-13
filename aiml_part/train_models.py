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
    # Use more robust CSV reading with error handling
    try:
        df = pd.read_csv(csv_path, on_bad_lines='skip', encoding='utf-8')
    except UnicodeDecodeError:
        # Try with different encodings if utf-8 fails
        try:
            df = pd.read_csv(csv_path, on_bad_lines='skip', encoding='latin-1')
        except:
            df = pd.read_csv(csv_path, on_bad_lines='skip', encoding='cp1252')
    
    if df.empty:
        return pd.DataFrame(columns=['text', 'label'])
    
    if "Label" not in df.columns:
        raise ValueError(f"Expected 'Label' column in {csv_path}")
    
    out = pd.DataFrame()
    out["text"] = df.apply(build_text_from_row, axis=1)
    out["label"] = df["Label"].astype(str)
    
    # Clean up NaN values and invalid labels
    out = out.dropna(subset=["text", "label"]).reset_index(drop=True)
    out = out[out["label"] != "nan"].reset_index(drop=True)  # Remove 'nan' string labels
    out = out[out["text"].str.len() > 0].reset_index(drop=True)  # Remove empty text
    
    return out


def main():
    root = Path(__file__).resolve().parent
    # Use attack_type_csvs folder instead of individual CSV files
    attack_csvs_dir = root.parent / "attack_type_csvs"
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = models_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Find all CSV files in attack_type_csvs directory
    if not attack_csvs_dir.exists():
        raise FileNotFoundError(f"Attack types CSV directory not found: {attack_csvs_dir}")
    
    csv_files = list(attack_csvs_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {attack_csvs_dir}")

    logger.info(f"Found {len(csv_files)} CSV files in attack_type_csvs directory")
    
    merged = []
    for csv_path in csv_files:
        logger.info(f"Loading dataset: {csv_path.name}")
        try:
            df = convert_to_text_label(str(csv_path))
            if not df.empty:
                merged.append(df)
                logger.info(f"  - Loaded {len(df)} samples from {csv_path.name}")
            else:
                logger.warning(f"  - Empty dataset: {csv_path.name}")
        except Exception as e:
            logger.error(f"  - Error loading {csv_path.name}: {e}")
            continue

    if not merged:
        raise ValueError("No valid datasets could be loaded from attack_type_csvs folder")

    merged_df = pd.concat(merged, ignore_index=True)
    logger.info(f"Total samples after merging: {len(merged_df)}")
    
    # Advanced cleanup
    initial_count = len(merged_df)
    merged_df = merged_df[merged_df["text"].str.len() > 3]  # Remove very short text
    merged_df = merged_df.dropna(subset=["text", "label"])  # Remove any remaining NaN values
    merged_df = merged_df[~merged_df["label"].isin(["nan", "NaN", "null", "NULL"])]  # Remove invalid labels
    merged_df = merged_df.drop_duplicates(subset=["text"])  # Remove duplicate texts
    merged_df = merged_df.reset_index(drop=True)
    
    logger.info(f"Samples after cleanup: {len(merged_df)} (removed {initial_count - len(merged_df)} invalid samples)")
    
    # Display label distribution
    label_counts = merged_df["label"].value_counts()
    logger.info(f"Label distribution: {dict(label_counts)}")
    
    # Ensure we have valid data for training
    if len(merged_df) < 10:
        raise ValueError("Not enough valid samples for training (minimum 10 required)")
    
    unique_labels = merged_df["label"].nunique()
    if unique_labels < 2:
        raise ValueError("Need at least 2 different labels for classification training")

    # For this project, train two classifiers from the same merged dataset
    attack_tmp = tmp_dir / "attack_text_label.csv"
    network_tmp = tmp_dir / "network_text_label.csv"
    merged_df.to_csv(attack_tmp, index=False)
    merged_df.sample(frac=1.0, random_state=42).to_csv(network_tmp, index=False)
    
    logger.info(f"Saved training datasets to tmp/ directory")

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

    print(f"\n✅ Training Complete!")
    print(f"📁 Models saved under 'models/': attack_model.joblib, network_model.joblib")
    print(f"📊 Total training samples: {len(merged_df)}")
    print(f"🏷️  Labels: {list(label_counts.index)}")
    print(f"📂 Source: {len(csv_files)} CSV files from attack_type_csvs/")


if __name__ == "__main__":
    main()


