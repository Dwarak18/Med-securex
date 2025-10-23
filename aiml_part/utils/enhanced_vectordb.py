"""
Enhanced Vector Database Manager for cybersecurity payload analysis
Provides advanced vector database operations for threat intelligence and payload analysis
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import hashlib
from datetime import datetime

# Import vector database components
try:
    from rag_pipeline.vector_db import CybersecurityVectorDB
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    logging.warning("Vector database not available")

class EnhancedVectorDBManager:
    """
    Enhanced Vector Database Manager for cybersecurity operations
    Handles payload storage, similarity search, and threat intelligence
    """
    
    def __init__(self, db_path: str = "training_vectordb"):
        self.db_path = Path(db_path)
        self.vector_db = None
        self.metadata_store = {}
        
        # Initialize vector database if available
        if VECTOR_DB_AVAILABLE:
            try:
                self.vector_db = CybersecurityVectorDB(str(self.db_path))
                logging.info(f"Enhanced Vector DB initialized at {self.db_path}")
            except Exception as e:
                logging.error(f"Failed to initialize vector DB: {e}")
                self.vector_db = None
        else:
            logging.warning("Vector DB not available, using fallback mode")
    
    def store_training_dataset(self, payloads: List[Dict[str, Any]], batch_size: int = 100) -> bool:
        """
        Store training dataset with enhanced metadata
        
        Args:
            payloads: List of payload dictionaries with content and metadata
            batch_size: Batch size for processing
            
        Returns:
            bool: Success status
        """
        try:
            if not self.vector_db:
                logging.warning("Vector DB not available for storage")
                return False
            
            stored_count = 0
            for i in range(0, len(payloads), batch_size):
                batch = payloads[i:i + batch_size]
                
                for payload_data in batch:
                    content = payload_data.get('content', '')
                    metadata = payload_data.get('metadata', {})
                    
                    # Enhanced metadata with timestamp and hash
                    enhanced_metadata = {
                        'stored_at': datetime.now().isoformat(),
                        'content_hash': hashlib.sha256(content.encode()).hexdigest()[:16],
                        **metadata
                    }
                    
                    # Store in vector database
                    self.vector_db.add_documents([content], [enhanced_metadata])
                    stored_count += 1
                
                if i % (batch_size * 10) == 0:
                    logging.info(f"Stored {stored_count} payloads...")
            
            logging.info(f"Successfully stored {stored_count} payloads in vector DB")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store training dataset: {e}")
            return False
    
    def search_similar_threats(self, payload: str, top_k: int = 5, 
                             similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar threats in the vector database
        
        Args:
            payload: Input payload to search for
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar threat dictionaries
        """
        try:
            if not self.vector_db:
                logging.warning("Vector DB not available for search")
                return []
            
            # Perform similarity search
            results = self.vector_db.query(payload, n_results=top_k)
            
            similar_threats = []
            if results.get('documents') and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    distance = results['distances'][0][i] if results.get('distances') else 1.0
                    similarity = 1 - distance
                    
                    if similarity >= similarity_threshold:
                        similar_threats.append({
                            'content': doc,
                            'metadata': metadata,
                            'similarity': similarity,
                            'threat_score': similarity * metadata.get('severity_score', 0.5)
                        })
            
            return similar_threats
            
        except Exception as e:
            logging.error(f"Failed to search similar threats: {e}")
            return []
    
    def analyze_payload_patterns(self, payload: str) -> Dict[str, Any]:
        """
        Analyze payload patterns using vector similarity
        
        Args:
            payload: Input payload to analyze
            
        Returns:
            Analysis result dictionary
        """
        try:
            analysis_result = {
                'payload': payload,
                'timestamp': datetime.now().isoformat(),
                'threat_indicators': [],
                'similar_attacks': [],
                'risk_assessment': 'unknown'
            }
            
            # Search for similar threats
            similar_threats = self.search_similar_threats(payload, top_k=3)
            analysis_result['similar_attacks'] = similar_threats
            
            # Analyze threat indicators
            if similar_threats:
                max_similarity = max(threat['similarity'] for threat in similar_threats)
                avg_threat_score = sum(threat['threat_score'] for threat in similar_threats) / len(similar_threats)
                
                analysis_result['threat_indicators'] = [
                    f"Max similarity: {max_similarity:.3f}",
                    f"Average threat score: {avg_threat_score:.3f}",
                    f"Similar attacks found: {len(similar_threats)}"
                ]
                
                # Risk assessment based on similarity and threat scores
                if max_similarity > 0.8 and avg_threat_score > 0.7:
                    analysis_result['risk_assessment'] = 'high'
                elif max_similarity > 0.6 and avg_threat_score > 0.5:
                    analysis_result['risk_assessment'] = 'medium'
                else:
                    analysis_result['risk_assessment'] = 'low'
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Failed to analyze payload patterns: {e}")
            return {
                'payload': payload,
                'error': str(e),
                'risk_assessment': 'unknown'
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics and health information
        
        Returns:
            Database statistics dictionary
        """
        try:
            stats = {
                'db_path': str(self.db_path),
                'available': self.vector_db is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.vector_db:
                try:
                    collection_info = self.vector_db.get_collection_info()
                    stats.update({
                        'document_count': collection_info.get('document_count', 0),
                        'collection_name': collection_info.get('collection_name', 'unknown'),
                        'status': 'healthy'
                    })
                except Exception as e:
                    stats.update({
                        'status': 'error',
                        'error': str(e)
                    })
            else:
                stats['status'] = 'unavailable'
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get database stats: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def cleanup_old_entries(self, days_threshold: int = 30) -> int:
        """
        Clean up old entries from the database
        
        Args:
            days_threshold: Number of days to keep entries
            
        Returns:
            Number of entries cleaned up
        """
        try:
            # This would implement cleanup logic based on stored_at timestamps
            # For now, return 0 as a placeholder
            logging.info(f"Cleanup requested for entries older than {days_threshold} days")
            return 0
            
        except Exception as e:
            logging.error(f"Failed to cleanup old entries: {e}")
            return 0

# Factory function for easy instantiation
def create_enhanced_vectordb_manager(db_path: str = "training_vectordb") -> EnhancedVectorDBManager:
    """
    Factory function to create an Enhanced Vector DB Manager
    
    Args:
        db_path: Path to the vector database
        
    Returns:
        EnhancedVectorDBManager instance
    """
    return EnhancedVectorDBManager(db_path)