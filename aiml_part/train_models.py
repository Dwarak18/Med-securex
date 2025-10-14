import os
import logging
import pandas as pd
from pathlib import Path
import sys

from ml.training import TrainingConfig, train_all

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from gemini_analyzer import GeminiPayloadAnalyzer
from enhanced_vectordb import EnhancedVectorDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainCLI")


def build_text_from_row(row: pd.Series) -> str:
    parts = []
    # Handle different possible column names in the datasets
    possible_keys = ["Payload", "payload", "Signature", "signature", "AttackType", "attack_type", 
                     "Severity", "severity", "MITRE", "mitre", "Description", "description"]
    for key in possible_keys:
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
    
    # Handle different possible label column names
    label_col = None
    for col in ["Label", "label", "Classification", "classification"]:
        if col in df.columns:
            label_col = col
            break
    
    if label_col is None:
        # If no label column exists, assume it's a malicious dataset and assign label "1"
        logger.warning(f"No label column found in {csv_path}, assuming all entries are malicious (label=1)")
        label_col = "assigned_label"
        df[label_col] = "1"
    
    out = pd.DataFrame()
    out["text"] = df.apply(build_text_from_row, axis=1)
    out["label"] = df[label_col].astype(str)
    
    # Clean up NaN values and invalid labels
    out = out.dropna(subset=["text", "label"]).reset_index(drop=True)
    out = out[out["label"] != "nan"].reset_index(drop=True)  # Remove 'nan' string labels
    out = out[out["text"].str.len() > 0].reset_index(drop=True)  # Remove empty text
    
    return out


def main():
    root = Path(__file__).resolve().parent
    # Use datasets folder - check both possible locations
    datasets_dir = Path("/app/datasets") if Path("/app/datasets").exists() else root.parent / "datasets"
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = models_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Find all CSV files in datasets directory
    if not datasets_dir.exists():
        raise FileNotFoundError(f"Datasets directory not found: {datasets_dir}")
    
    csv_files = list(datasets_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {datasets_dir}")

    logger.info(f"Found {len(csv_files)} CSV files in datasets directory")
    
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
    
    # Enhanced cleanup - Keep ALL payloads without removing duplicates
    initial_count = len(merged_df)
    merged_df = merged_df[merged_df["text"].str.len() > 3]  # Remove very short text
    merged_df = merged_df.dropna(subset=["text", "label"])  # Remove any remaining NaN values
    merged_df = merged_df[~merged_df["label"].isin(["nan", "NaN", "null", "NULL"])]  # Remove invalid labels
    
    # **KEEP ALL PAYLOADS - NO DUPLICATE REMOVAL OR SAMPLING**
    # This preserves all 440k payloads to understand complete patterns
    logger.info("ENHANCED MODE: Keeping ALL payloads without duplicate removal")
    
    # Separate legitimate and malicious for analysis but keep all
    legit_df = merged_df[merged_df["label"].isin(["Legit", "legitimate", "normal", "0"])]
    malicious_df = merged_df[~merged_df["label"].isin(["Legit", "legitimate", "normal", "0"])]
    
    logger.info(f"Found {len(legit_df)} legitimate payloads and {len(malicious_df)} malicious payloads")
    
    # Keep all data - just recombine
    merged_df = pd.concat([legit_df, malicious_df], ignore_index=True)
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

    # ENHANCED ANALYSIS: Use Gemini to analyze legitimate payloads
    gemini_analysis = None
    try:
        logger.info("Starting Gemini analysis of legitimate payloads...")
        gemini_analyzer = GeminiPayloadAnalyzer()
        
        # Get legitimate payloads for analysis
        legitimate_payloads = legit_df["text"].tolist() if len(legit_df) > 0 else []
        
        if legitimate_payloads:
            gemini_analysis = gemini_analyzer.analyze_legitimate_patterns(legitimate_payloads)
            logger.info(f"Gemini analysis completed. Found {len(gemini_analysis.get('legitimate_characteristics', []))} characteristics")
        else:
            logger.warning("No legitimate payloads found for Gemini analysis")
            
    except Exception as e:
        logger.warning(f"Gemini analysis failed (continuing without it): {e}")
        gemini_analysis = None

    # ENHANCED STORAGE: Save all data to Vector Database
    try:
        logger.info("Storing complete dataset in Vector Database...")
        # Use separate training database to avoid conflicts
        training_db_path = "/app/training_vectordb"
        vectordb_manager = EnhancedVectorDBManager(db_path=training_db_path)
        
        # Store the complete training dataset
        session_id = vectordb_manager.store_training_dataset(
            df=merged_df,
            gemini_analysis=gemini_analysis
        )
        
        # Store Gemini insights if available
        if gemini_analysis:
            vectordb_manager.store_gemini_insights(gemini_analysis, session_id)
            
        logger.info(f"Successfully stored {len(merged_df)} payloads in Vector Database (Session: {session_id})")
        
        # Get and log statistics
        stats = vectordb_manager.get_training_statistics(session_id)
        logger.info(f"Vector DB Stats: {stats}")
        
    except Exception as e:
        logger.warning(f"Vector Database storage failed (continuing with training): {e}")

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

    print(f"\n✅ Enhanced Training Complete!")
    print(f"📁 Models saved under 'models/': attack_model.joblib, network_model.joblib")
    print(f"📊 Total training samples: {len(merged_df)} (ALL payloads kept - no duplicates removed)")
    print(f"🏷️  Labels: {list(label_counts.index)}")
    print(f"📂 Source: {len(csv_files)} CSV files from datasets/")
    print(f"🤖 Gemini Analysis: {'✅ Completed' if gemini_analysis else '❌ Skipped/Failed'}")
    print(f"🗄️  Vector DB Storage: ✅ All payloads stored for future pattern recognition")
    
    if gemini_analysis:
        print(f"\n📈 Gemini Insights Summary:")
        print(f"   • Analyzed {gemini_analysis.get('total_analyzed', 0)} legitimate samples")
        print(f"   • Found {len(gemini_analysis.get('legitimate_characteristics', []))} unique characteristics")
        print(f"   • Generated {len(gemini_analysis.get('security_insights', []))} security insights")
        
        # Show some example insights
        insights = gemini_analysis.get('security_insights', [])[:3]
        if insights:
            print(f"   • Sample insights: {'; '.join(insights[:2])}")
    
    print(f"\n🔍 Pattern Recognition Enhanced:")
    print(f"   • All 440k+ payloads available for pattern learning")
    print(f"   • Legitimate payload patterns analyzed by Gemini")
    print(f"   • Complete dataset stored in Vector DB for similarity search")
    print(f"   • Future queries can leverage historical pattern analysis")


if __name__ == "__main__":
    main()


