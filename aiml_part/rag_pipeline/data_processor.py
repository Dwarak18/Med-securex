import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import re
import logging
from pathlib import Path
import json
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DataPreprocessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def clean_text(self, text: str) -> str:
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        text = re.sub(r'[^\w\s\-\.\,\:\;\(\)\[\]\{\}\'\"\/\\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def normalize_severity(self, severity: str) -> str:
        if pd.isna(severity):
            return "Medium"
        
        severity = severity.lower().strip()
        severity_mapping = {
            'critical': 'Critical',
            'high': 'High', 
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Low',
            'information': 'Low'
        }
        
        return severity_mapping.get(severity, 'Medium')
    
    def extract_mitre_techniques(self, text: str) -> List[str]:
        if pd.isna(text) or not isinstance(text, str):
            return []
        
        mitre_pattern = r'T\d{4}(?:\.\d{3})?'
        techniques = re.findall(mitre_pattern, text)
        return list(set(techniques))
    
    def chunk_long_text(self, text: str, max_length: int = 512, overlap: int = 50) -> List[str]:
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_length, len(text))
            
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(end - overlap, start + 1)
            
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        return self.embedding_model.encode(texts, convert_to_tensor=False)
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        embeddings = self.generate_embeddings([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def _calculate_risk_score(self, severity: str, mitre_techniques: List[str], attack_type: str) -> float:
        """Calculate a risk score based on severity, MITRE techniques, and attack type"""
        base_score = 0.0
        
        # Severity scoring
        severity_scores = {
            'Critical': 4.0,
            'High': 3.0,
            'Medium': 2.0,
            'Low': 1.0
        }
        base_score += severity_scores.get(severity, 2.0)
        
        # MITRE technique scoring
        base_score += len(mitre_techniques) * 0.5
        
        # Attack type scoring
        high_risk_attacks = ['sql_injection', 'xss', 'command_injection', 'xxe', 'deserialization']
        if any(risk_type in attack_type.lower() for risk_type in high_risk_attacks):
            base_score += 1.0
            
        # Normalize to 0-10 scale
        return min(base_score * 1.5, 10.0)

class MitreAttackProcessor(DataPreprocessor):
    def __init__(self):
        super().__init__()
        
    def process_mitre_dataset(self, csv_path: str) -> List[Dict[str, Any]]:
        try:
            # Custom parser for pipe-delimited CSV with multiline descriptions
            processed_data = []
            
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Skip empty lines and get header
            header_line = lines[0].strip()
            if '|' in header_line:
                headers = [h.strip() for h in header_line.split('|')]
            else:
                logging.error("Invalid header format in MITRE dataset")
                return []
            
            current_row = []
            in_description = False
            description_buffer = ""
            
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                
                if not line:  # Skip empty lines
                    if in_description:
                        description_buffer += "\n"
                    continue
                
                # Check if this is a new row (starts with a payload)
                if line.count('|') >= 6 and not in_description:
                    # Process previous row if exists
                    if current_row:
                        self._process_mitre_row(current_row, headers, processed_data)
                    
                    # Start new row
                    current_row = [part.strip() for part in line.split('|')]
                    if len(current_row) > 6 and current_row[6]:  # Has description
                        in_description = True
                        description_buffer = current_row[6]
                    else:
                        in_description = False
                        
                elif in_description:
                    # Continue building description
                    description_buffer += " " + line
                    if current_row and len(current_row) > 6:
                        current_row[6] = description_buffer
                    
                    # Check if this might be the end of description
                    if line.endswith('"') and line.count('"') % 2 == 1:
                        in_description = False
            
            # Process last row
            if current_row:
                self._process_mitre_row(current_row, headers, processed_data)
                
        except Exception as e:
            logging.error(f"Error processing MITRE dataset: {e}")
            return []
        
        return processed_data
    
    def _process_mitre_row(self, row_data: List[str], headers: List[str], processed_data: List[Dict[str, Any]]):
        """Process a single MITRE dataset row"""
        try:
            if len(row_data) < len(headers):
                # Pad with empty strings if row is shorter than headers
                row_data.extend([''] * (len(headers) - len(row_data)))
            
            # Create row dictionary
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row_data[i] if i < len(row_data) else ''
            
            # Process the row similar to original logic
            payload = self.clean_text(str(row_dict.get('Payload', '')))
            signature = self.clean_text(str(row_dict.get('Signature', '')))
            attack_type = self.clean_text(str(row_dict.get('AttackType', '')))
            severity = self.normalize_severity(str(row_dict.get('Severity', '')))
            mitre_id = self.clean_text(str(row_dict.get('MITRE', '')))
            label = self.clean_text(str(row_dict.get('Label', '')))
            description = self.clean_text(str(row_dict.get('Description', '')))
            
            if not payload and not description:
                return
            
            mitre_techniques = self.extract_mitre_techniques(mitre_id)
            if not mitre_techniques:
                mitre_techniques = self.extract_mitre_techniques(description)
            
            main_content = f"{payload} {description}".strip()
            chunks = self.chunk_long_text(main_content, max_length=400)
            
            for i, chunk in enumerate(chunks):
                processed_entry = {
                    'content': chunk,
                    'payload': payload,
                    'signature': signature,
                    'attack_type': attack_type,
                    'severity': severity,
                    'mitre_id': mitre_id,
                    'mitre_techniques': mitre_techniques,
                    'label': label,
                    'description': description,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'source': 'mitre_attack_dataset',
                    'row_index': len(processed_data)
                }
                processed_data.append(processed_entry)
                
        except Exception as e:
            logging.warning(f"Error processing MITRE row: {e}")

        logging.info(f"Processed {len(processed_data)} entries from MITRE ATT&CK dataset")

class PayloadProcessor(DataPreprocessor):
    def __init__(self):
        super().__init__()
        
    def process_payload_dataset(self, csv_path: str = None, datasets_dir: str = None) -> List[Dict[str, Any]]:
        """
        Process payload datasets - either single CSV or multiple CSV files from datasets directory
        """
        try:
            processed_data = []
            
            if datasets_dir:
                # Load from multiple CSV files in datasets directory
                return self.process_multiple_datasets(datasets_dir)
            elif csv_path:
                # Load from single master CSV file (legacy)
                return self.process_single_dataset(csv_path)
            else:
                logging.error("Either csv_path or datasets_dir must be provided")
                return []
                
        except Exception as e:
            logging.error(f"Error processing payload dataset: {e}")
            return []
    
    def process_multiple_datasets(self, datasets_dir: str) -> List[Dict[str, Any]]:
        """Process multiple CSV files from datasets directory"""
        processed_data = []
        datasets_path = Path(datasets_dir)
        
        if not datasets_path.exists():
            logging.error(f"Datasets directory not found: {datasets_dir}")
            return []
        
        csv_files = list(datasets_path.glob("*.csv"))
        logging.info(f"Found {len(csv_files)} CSV files in {datasets_dir}")
        
        for csv_file in csv_files:
            try:
                logging.info(f"Processing dataset: {csv_file.name}")
                
                # Try different CSV reading strategies to handle malformed CSV files
                df = None
                try:
                    # First try standard reading
                    df = pd.read_csv(csv_file, encoding='utf-8')
                except pd.errors.ParserError:
                    try:
                        # Try with error handling for bad lines
                        df = pd.read_csv(csv_file, encoding='utf-8', on_bad_lines='skip')
                        logging.warning(f"Skipped some malformed lines in {csv_file.name}")
                    except Exception:
                        try:
                            # Try with different quoting
                            df = pd.read_csv(csv_file, encoding='utf-8', quotechar='"', escapechar='\\', on_bad_lines='skip')
                            logging.warning(f"Used alternative parsing for {csv_file.name}")
                        except Exception as e:
                            logging.error(f"Failed to parse {csv_file.name}: {e}")
                            continue
                
                if df is None or df.empty:
                    logging.warning(f"Skipping {csv_file.name} - could not read or empty")
                    continue
                
                # Validate required columns
                required_columns = ['Payload', 'AttackType', 'Severity', 'MITRE', 'Label', 'Description']
                available_columns = df.columns.tolist()
                if not all(col in available_columns for col in required_columns):
                    logging.warning(f"Skipping {csv_file.name} - missing required columns. Available: {available_columns}")
                    continue
                
                # Process each row in the CSV
                for _, row in df.iterrows():
                    processed_row = self._process_new_format_row(row, csv_file.stem)
                    if processed_row:
                        processed_data.append(processed_row)
                        
            except Exception as e:
                logging.error(f"Error processing {csv_file.name}: {e}")
                continue
        
        logging.info(f"Successfully processed {len(processed_data)} total records from {len(csv_files)} files")
        return processed_data
    
    def _process_new_format_row(self, row: pd.Series, file_category: str) -> Dict[str, Any]:
        """Process a row from the new CSV format"""
        try:
            payload = str(row.get('Payload', '')).strip()
            if not payload or payload == 'nan':
                return None
            
            # Clean and normalize the data
            cleaned_payload = self.clean_text(payload)
            attack_type = str(row.get('AttackType', file_category)).strip()
            severity = self.normalize_severity(str(row.get('Severity', 'Medium')))
            mitre_techniques = self.extract_mitre_techniques(str(row.get('MITRE', '')))
            label = str(row.get('Label', 'Unknown')).strip()
            description = self.clean_text(str(row.get('Description', '')))
            
            # Create the processed record
            processed_record = {
                'payload': cleaned_payload,
                'original_payload': payload,
                'attack_type': attack_type,
                'severity': severity,
                'mitre_techniques': mitre_techniques,
                'label': label,
                'description': description,
                'file_category': file_category,
                'is_malicious': label.lower() in ['malicious', 'attack', 'threat'],
                'risk_score': self._calculate_risk_score(severity, mitre_techniques, attack_type),
                'embedding_text': f"{payload} {attack_type} {description}",
                'metadata': {
                    'source_file': file_category,
                    'attack_type': attack_type,
                    'severity': severity,
                    'mitre_techniques': mitre_techniques,
                    'label': label
                }
            }
            
            return processed_record
            
        except Exception as e:
            logging.error(f"Error processing row: {e}")
            return None
    
    def process_single_dataset(self, csv_path: str) -> List[Dict[str, Any]]:
        """Process single master CSV file (legacy method)"""
        try:
            # Custom parser for pipe-delimited CSV
            processed_data = []
            
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Skip empty lines and get header
            header_line = lines[0].strip()
            if '|' in header_line:
                headers = [h.strip() for h in header_line.split('|')]
            else:
                logging.error("Invalid header format in payload dataset")
                return []
            
            current_row = []
            in_description = False
            description_buffer = ""
            
            for i, line in enumerate(lines[1:], 1):
                line = line.strip()
                
                if not line:  # Skip empty lines
                    if in_description:
                        description_buffer += "\n"
                    continue
                
                # Check if this is a new row (starts with a payload)
                if line.count('|') >= 6 and not in_description:
                    # Process previous row if exists
                    if current_row:
                        self._process_payload_row(current_row, headers, processed_data)
                    
                    # Start new row
                    current_row = [part.strip() for part in line.split('|')]
                    if len(current_row) > 6 and current_row[6]:  # Has description
                        in_description = True
                        description_buffer = current_row[6]
                    else:
                        in_description = False
                        
                elif in_description:
                    # Continue building description
                    description_buffer += " " + line
                    if current_row and len(current_row) > 6:
                        current_row[6] = description_buffer
                    
                    # Check if this might be the end of description
                    if line.endswith('"') and line.count('"') % 2 == 1:
                        in_description = False
            
            # Process last row
            if current_row:
                self._process_payload_row(current_row, headers, processed_data)
                
        except Exception as e:
            logging.error(f"Error processing payload dataset: {e}")
            return []
        
        logging.info(f"Processed {len(processed_data)} entries from payload dataset")
        return processed_data
    
    def _process_payload_row(self, row_data: List[str], headers: List[str], processed_data: List[Dict[str, Any]]):
        """Process a single payload dataset row"""
        try:
            if len(row_data) < len(headers):
                # Pad with empty strings if row is shorter than headers
                row_data.extend([''] * (len(headers) - len(row_data)))
            
            # Create row dictionary
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row_data[i] if i < len(row_data) else ''
            
            # Process the row similar to original logic
            payload = self.clean_text(str(row_dict.get('Payload', '')))
            signature = self.clean_text(str(row_dict.get('Signature', '')))
            attack_type = self.clean_text(str(row_dict.get('AttackType', '')))
            severity = self.normalize_severity(str(row_dict.get('Severity', '')))
            mitre_id = self.clean_text(str(row_dict.get('MITRE', '')))
            label = self.clean_text(str(row_dict.get('Label', '')))
            description = self.clean_text(str(row_dict.get('Description', '')))
            
            if not payload and not description:
                return
            
            mitre_techniques = self.extract_mitre_techniques(mitre_id)
            if not mitre_techniques:
                mitre_techniques = self.extract_mitre_techniques(description)
            
            main_content = f"{payload} {description}".strip()
            chunks = self.chunk_long_text(main_content, max_length=400)
            
            for i, chunk in enumerate(chunks):
                processed_entry = {
                    'content': chunk,
                    'payload': payload,
                    'signature': signature,
                    'attack_type': attack_type,
                    'severity': severity,
                    'mitre_id': mitre_id,
                    'mitre_techniques': mitre_techniques,
                    'label': label,
                    'description': description,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'source': 'payload_dataset',
                    'row_index': len(processed_data)
                }
                processed_data.append(processed_entry)
                
        except Exception as e:
            logging.warning(f"Error processing payload row: {e}")

class CyberAgentDataProcessor(DataPreprocessor):
    def __init__(self):
        super().__init__()
        
    def extract_agent_knowledge(self, cyberagents_path: str) -> List[Dict[str, Any]]:
        knowledge_base = []
        
        agents_path = Path(cyberagents_path) / "agents"
        
        if not agents_path.exists():
            logging.warning(f"Agents path not found: {agents_path}")
            return []
        
        for py_file in agents_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                agent_name = py_file.stem
                
                docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
                comments = re.findall(r'#\s*(.*)', content)
                
                knowledge_text = f"Agent: {agent_name}\n"
                
                if docstrings:
                    knowledge_text += "Documentation:\n" + "\n".join(docstrings) + "\n"
                
                if comments:
                    relevant_comments = [c.strip() for c in comments if len(c.strip()) > 10]
                    if relevant_comments:
                        knowledge_text += "Implementation Notes:\n" + "\n".join(relevant_comments[:5])
                
                chunks = self.chunk_long_text(knowledge_text, max_length=300)
                
                for i, chunk in enumerate(chunks):
                    knowledge_entry = {
                        'content': chunk,
                        'agent_name': agent_name,
                        'source': 'cyberagents',
                        'file_path': str(py_file),
                        'chunk_id': i,
                        'total_chunks': len(chunks),
                        'type': 'agent_knowledge'
                    }
                    knowledge_base.append(knowledge_entry)
                    
            except Exception as e:
                logging.warning(f"Error processing agent file {py_file}: {e}")
                continue
        
        logging.info(f"Extracted knowledge from {len(knowledge_base)} agent chunks")
        return knowledge_base

class ComprehensiveDataProcessor:
    def __init__(self):
        self.mitre_processor = MitreAttackProcessor()
        self.payload_processor = PayloadProcessor()
        self.agent_processor = CyberAgentDataProcessor()
        
    def process_all_datasets(self, mitre_csv_path: str = None, payload_csv_path: str = None, 
                           cyberagents_path: str = None, datasets_dir: str = None) -> Dict[str, List[Dict[str, Any]]]:
        
        logging.info("Starting comprehensive data processing...")
        
        results = {
            'mitre_data': [],
            'payload_data': [],
            'agent_knowledge': []
        }
        
        # Process MITRE data if available
        if mitre_csv_path:
            try:
                results['mitre_data'] = self.mitre_processor.process_mitre_dataset(mitre_csv_path)
            except Exception as e:
                logging.error(f"Failed to process MITRE dataset: {e}")
        
        # Process payload data - prioritize datasets_dir over single CSV
        if datasets_dir:
            try:
                results['payload_data'] = self.payload_processor.process_payload_dataset(datasets_dir=datasets_dir)
                logging.info(f"Using new datasets directory: {datasets_dir}")
            except Exception as e:
                logging.error(f"Failed to process datasets directory: {e}")
        elif payload_csv_path:
            try:
                results['payload_data'] = self.payload_processor.process_payload_dataset(csv_path=payload_csv_path)
                logging.info(f"Using legacy single CSV: {payload_csv_path}")
            except Exception as e:
                logging.error(f"Failed to process payload dataset: {e}")
        else:
            logging.warning("No payload dataset source provided")
            
        # Process agent knowledge if available
        if cyberagents_path:
            try:
                results['agent_knowledge'] = self.agent_processor.extract_agent_knowledge(cyberagents_path)
            except Exception as e:
                logging.error(f"Failed to process agent knowledge: {e}")
        
        total_processed = sum(len(data) for data in results.values())
        logging.info(f"Completed processing. Total entries: {total_processed}")
        
        return results
    
    def save_processed_data(self, processed_data: Dict[str, List[Dict[str, Any]]], 
                          output_path: str) -> None:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved processed data to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save processed data: {e}")
    
    def load_processed_data(self, input_path: str) -> Dict[str, List[Dict[str, Any]]]:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Loaded processed data from {input_path}")
            return data
        except Exception as e:
            logging.error(f"Failed to load processed data: {e}")
            return {'mitre_data': [], 'payload_data': [], 'agent_knowledge': []}
