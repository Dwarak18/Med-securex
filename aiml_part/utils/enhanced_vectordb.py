import os
import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Import the existing vector database class
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag_pipeline'))
try:
    from rag_pipeline.vector_db import CybersecurityVectorDB
except ImportError:
    # Fallback to direct import
    sys.path.append('/app/rag_pipeline')
    from vector_db import CybersecurityVectorDB

logger = logging.getLogger(__name__)

class EnhancedVectorDBManager:
    """
    Enhanced vector database manager for storing and retrieving 
    analyzed payload data including Gemini insights.
    """
    
    def __init__(self, db_path: str = "/app/cybersecurity_vectordb"):
        self.db_path = db_path
        self.vector_db = CybersecurityVectorDB(persist_directory=db_path)
        self.metadata_file = Path(db_path) / "training_metadata.json"
        logger.info(f"Enhanced VectorDB Manager initialized with path: {db_path}")
    
    def store_training_dataset(self, 
                             df: pd.DataFrame,
                             gemini_analysis: Optional[Dict[str, Any]] = None,
                             training_session_id: Optional[str] = None) -> str:
        """
        Store complete training dataset with analysis in vector database.
        
        Args:
            df: DataFrame containing payload data with text and labels
            gemini_analysis: Optional Gemini analysis results
            training_session_id: Optional session identifier
            
        Returns:
            Session ID for the stored data
        """
        if training_session_id is None:
            training_session_id = f"training_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Storing training dataset with {len(df)} samples (Session: {training_session_id})")
        
        # Prepare documents and metadata for vector storage
        documents = []
        metadatas = []
        
        for idx, row in df.iterrows():
            # Create document text
            document_text = row['text']
            documents.append(document_text)
            
            # Create metadata
            metadata = {
                'session_id': training_session_id,
                'record_id': idx,
                'label': row['label'],
                'data_type': 'training_payload',
                'timestamp': datetime.now().isoformat(),
                'text_length': len(document_text),
                'is_malicious': row['label'].lower() in ['malicious', '1', 'attack'],
                'source': 'training_dataset'
            }
            
            # Add any additional columns as metadata
            for col in df.columns:
                if col not in ['text', 'label']:
                    metadata[f'original_{col}'] = str(row[col])
            
            metadatas.append(metadata)
        
        # Store in vector database
        try:
            self.vector_db.add_documents(
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully stored {len(documents)} training samples in vector database")
        except Exception as e:
            logger.error(f"Error storing training data in vector database: {e}")
            raise
        
        # Store session metadata
        session_metadata = {
            'session_id': training_session_id,
            'timestamp': datetime.now().isoformat(),
            'total_samples': len(df),
            'label_distribution': df['label'].value_counts().to_dict(),
            'gemini_analysis': gemini_analysis,
            'vector_db_path': self.db_path
        }
        
        self._save_session_metadata(session_metadata)
        
        return training_session_id
    
    def store_gemini_insights(self, 
                            gemini_analysis: Dict[str, Any],
                            session_id: str) -> bool:
        """
        Store Gemini analysis insights as separate documents for retrieval.
        
        Args:
            gemini_analysis: Gemini analysis results
            session_id: Training session identifier
            
        Returns:
            Success status
        """
        try:
            # Store pattern insights as documents
            insights_documents = []
            insights_metadata = []
            
            # Store legitimate characteristics
            if 'legitimate_characteristics' in gemini_analysis:
                for i, characteristic in enumerate(gemini_analysis['legitimate_characteristics']):
                    insights_documents.append(f"Legitimate payload characteristic: {characteristic}")
                    insights_metadata.append({
                        'session_id': session_id,
                        'data_type': 'gemini_insight',
                        'insight_type': 'legitimate_characteristic',
                        'insight_id': f"legit_char_{i}",
                        'timestamp': datetime.now().isoformat(),
                        'source': 'gemini_analysis'
                    })
            
            # Store security insights
            if 'security_insights' in gemini_analysis:
                for i, insight in enumerate(gemini_analysis['security_insights']):
                    insights_documents.append(f"Security insight: {insight}")
                    insights_metadata.append({
                        'session_id': session_id,
                        'data_type': 'gemini_insight',
                        'insight_type': 'security_insight',
                        'insight_id': f"sec_insight_{i}",
                        'timestamp': datetime.now().isoformat(),
                        'source': 'gemini_analysis'
                    })
            
            # Store pattern summaries
            for pattern_type, distribution in gemini_analysis.get('pattern_type_distribution', {}).items():
                insights_documents.append(f"Pattern type analysis: {pattern_type} appears {distribution} times in legitimate traffic")
                insights_metadata.append({
                    'session_id': session_id,
                    'data_type': 'gemini_insight',
                    'insight_type': 'pattern_distribution',
                    'pattern_type': pattern_type,
                    'frequency': distribution,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'gemini_analysis'
                })
            
            # Store insights in vector database
            if insights_documents:
                self.vector_db.add_documents(
                    documents=insights_documents,
                    metadatas=insights_metadata
                )
                logger.info(f"Stored {len(insights_documents)} Gemini insights in vector database")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing Gemini insights: {e}")
            return False
    
    def retrieve_similar_payloads(self, 
                                query_payload: str, 
                                top_k: int = 10,
                                include_analysis: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve similar payloads from vector database.
        
        Args:
            query_payload: Payload to find similar examples for
            top_k: Number of similar payloads to retrieve
            include_analysis: Whether to include Gemini analysis data
            
        Returns:
            List of similar payload results with metadata
        """
        try:
            # Search for similar training payloads
            results = self.vector_db.similarity_search(
                query=query_payload,
                top_k=top_k
            )
            
            enhanced_results = []
            for result in results:
                enhanced_result = {
                    'document': result.get('content', ''),
                    'score': result.get('similarity', 0.0),
                    'metadata': result.get('metadata', {}),
                    'is_malicious': result.get('metadata', {}).get('is_malicious', False),
                    'label': result.get('metadata', {}).get('label', 'Unknown')
                }
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error retrieving similar payloads: {e}")
            return []
    
    def get_training_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get training statistics from vector database.
        
        Args:
            session_id: Optional specific session to get stats for
            
        Returns:
            Dictionary containing training statistics
        """
        try:
            # This is a simplified approach - in a real implementation,
            # you'd want to implement proper aggregation queries
            results = self.vector_db.similarity_search(
                query="training statistics",
                top_k=1000  # Get many results for statistics
            )
            
            stats = {
                'total_training_samples': len(results),
                'sessions': set(),
                'labels': {},
                'malicious_count': 0,
                'legitimate_count': 0
            }
            
            for result in results:
                metadata = result.get('metadata', {})
                
                # Collect session IDs
                if 'session_id' in metadata:
                    stats['sessions'].add(metadata['session_id'])
                
                # Count labels
                label = metadata.get('label', 'Unknown')
                stats['labels'][label] = stats['labels'].get(label, 0) + 1
                
                # Count malicious vs legitimate
                if metadata.get('is_malicious', False):
                    stats['malicious_count'] += 1
                else:
                    stats['legitimate_count'] += 1
            
            stats['sessions'] = list(stats['sessions'])
            stats['total_sessions'] = len(stats['sessions'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting training statistics: {e}")
            return {'error': str(e)}
    
    def _save_session_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Save session metadata to file."""
        try:
            # Load existing metadata
            existing_metadata = []
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    existing_metadata = json.load(f)
            
            # Add new metadata
            existing_metadata.append(metadata)
            
            # Save back to file
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump(existing_metadata, f, indent=2)
            
            logger.info(f"Saved session metadata for {metadata['session_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session metadata: {e}")
            return False
    
    def get_session_metadata(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get session metadata from file."""
        try:
            if not self.metadata_file.exists():
                return []
            
            with open(self.metadata_file, 'r') as f:
                all_metadata = json.load(f)
            
            if session_id:
                return [m for m in all_metadata if m.get('session_id') == session_id]
            else:
                return all_metadata
                
        except Exception as e:
            logger.error(f"Error loading session metadata: {e}")
            return []