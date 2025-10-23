import os
import logging
import uuid
from typing import List, Dict, Any, Optional
import numpy as np

# Try to import ML dependencies gracefully
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"sentence_transformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    from qdrant_client.http.exceptions import ResponseHandlingException
    QDRANT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"qdrant_client not available: {e}")
    QDRANT_AVAILABLE = False
    QdrantClient = None

class VectorDatabase:
    def __init__(self, persist_directory: str = "rag_vectordb", collection_name: str = "cybersecurity_rag"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embedding model if available
        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
            logging.warning("SentenceTransformer not available, using fallback embeddings")
        
        # Initialize Qdrant client if available
        if QDRANT_AVAILABLE and QdrantClient is not None:
            # Get Qdrant connection details from environment variables
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            
            try:
                self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
                self.client.get_collections()
                logging.info(f"Connected to Qdrant instance at {qdrant_host}:{qdrant_port}")
            except Exception as e:
                logging.warning(f"Failed to connect to remote Qdrant, using local instance: {e}")
                self.client = QdrantClient(path=persist_directory)
                logging.info(f"Created local Qdrant instance at {persist_directory}")
        else:
            self.client = None
            logging.warning("Qdrant client not available, using fallback storage")
        
        # Initialize collection if Qdrant is available
        if self.client:
            try:
                self.client.get_collection(collection_name)
                logging.info(f"Loaded existing collection: {collection_name}")
            except Exception:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logging.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: Optional[List[str]] = None) -> None:
        if not self.client or not self.embedding_model:
            logging.warning("Vector database or embedding model not available, skipping document addition")
            return
            
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        embeddings = self.embedding_model.encode(documents).tolist()
        
        points = []
        for i, (doc, metadata, doc_id, embedding) in enumerate(zip(documents, metadatas, ids, embeddings)):
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "document": doc,
                    "metadata": metadata,
                    "id": doc_id
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logging.info(f"Added {len(documents)} documents to collection")
    
    def query(self, query_text: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.client or not self.embedding_model:
            logging.warning("Vector database or embedding model not available, returning empty results")
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]],
                'ids': [[]]
            }
            
        query_embedding = self.embedding_model.encode([query_text]).tolist()[0]
        
        filter_condition = None
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value)))
            filter_condition = Filter(must=conditions)
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=filter_condition
        )
        
        results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]],
            'ids': [[]]
        }
        
        for result in search_result:
            results['documents'][0].append(result.payload['document'])
            results['metadatas'][0].append(result.payload['metadata'])
            results['distances'][0].append(1 - result.score)
            results['ids'][0].append(result.payload['id'])
        
        return results
    
    def similarity_search(self, query: str, top_k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
        results = self.query(query, n_results=top_k)
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                similarity = 1 - distance
                
                if similarity >= threshold:
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity': similarity,
                        'distance': distance
                    })
        
        return sorted(formatted_results, key=lambda x: x['similarity'], reverse=True)
    
    def get_collection_info(self) -> Dict[str, Any]:
        count = 0
        if self.client:
            try:
                collection_info = self.client.get_collection(self.collection_name)
                count = collection_info.points_count
            except Exception:
                count = 0
        
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else "fallback",
            "vector_size": 384
        }
    
    def delete_collection(self) -> None:
        if not self.client:
            logging.warning("Client not available, cannot delete collection")
            return
        try:
            self.client.delete_collection(self.collection_name)
            logging.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logging.warning(f"Could not delete collection: {e}")
    
    def reset_collection(self) -> None:
        if not self.client:
            logging.warning("Client not available, cannot reset collection")
            return
        try:
            self.delete_collection()
        except Exception:
            pass
        
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        logging.info(f"Reset collection: {self.collection_name}")


class CybersecurityVectorDB(VectorDatabase):
    def __init__(self, persist_directory: str = "cybersecurity_vectordb"):
        super().__init__(persist_directory, "cybersecurity_knowledge")
    
    def add_mitre_attack_data(self, payload: str, signature: str, attack_type: str, 
                             severity: str, mitre_id: str, description: str, 
                             additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        
        combined_text = f"MITRE ATT&CK Technique: {mitre_id}\nAttack Type: {attack_type}\nSeverity: {severity}\nPayload: {payload}\nSignature: {signature}\nDescription: {description}"
        
        metadata = {
            "type": "mitre_attack",
            "mitre_id": mitre_id,
            "attack_type": attack_type,
            "severity": severity,
            "payload": payload,
            "signature": signature
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        self.add_documents([combined_text], [metadata])
    
    def add_payload_data(self, payload: str, attack_type: str, severity: str, 
                        mitre_id: str, label: str, description: str,
                        additional_metadata: Optional[Dict[str, Any]] = None) -> None:
        
        combined_text = f"Security Payload: {payload}\nMITRE: {mitre_id}\nAttack Type: {attack_type}\nSeverity: {severity}\nLabel: {label}\nDescription: {description}"
        
        metadata = {
            "type": "security_payload",
            "mitre_id": mitre_id,
            "attack_type": attack_type,
            "severity": severity,
            "payload": payload,
            "label": label
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        self.add_documents([combined_text], [metadata])
    
    def search_by_attack_type(self, attack_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.similarity_search(f"attack type {attack_type}", top_k=top_k)
    
    def search_by_mitre_id(self, mitre_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.similarity_search(f"MITRE {mitre_id}", top_k=top_k)
    
    def search_by_severity(self, severity: str, top_k: int = 5) -> List[Dict[str, Any]]:
        where_clause = {"severity": severity}
        results = self.query("cybersecurity threat", n_results=top_k, where=where_clause)
        
        modified_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                
                modified_results.append({
                    'content': doc,
                    'metadata': metadata,
                    'similarity': 1 - distance,
                    'distance': distance
                })
        
        return modified_results
    
    def get_attack_techniques_for_payload(self, payload: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return self.similarity_search(payload, top_k=top_k)