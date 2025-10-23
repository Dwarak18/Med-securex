# Try to import components gracefully
try:
    from .vector_db import VectorDatabase, CybersecurityVectorDB
except ImportError as e:
    import logging
    logging.warning(f"Vector DB components not available: {e}")
    VectorDatabase = None
    CybersecurityVectorDB = None

try:
    from .data_processor import (
        DataPreprocessor, 
        MitreAttackProcessor, 
        PayloadProcessor, 
        CyberAgentDataProcessor, 
        ComprehensiveDataProcessor
    )
except ImportError as e:
    import logging
    logging.warning(f"Data processor components not available: {e}")
    DataPreprocessor = None
    MitreAttackProcessor = None
    PayloadProcessor = None
    CyberAgentDataProcessor = None
    ComprehensiveDataProcessor = None

try:
    from .ingestion import (
        DataIngestionPipeline, 
        IncrementalIngestionManager, 
        BatchIngestionOptimizer
    )
except ImportError as e:
    import logging
    logging.warning(f"Ingestion components not available: {e}")
    DataIngestionPipeline = None
    IncrementalIngestionManager = None
    BatchIngestionOptimizer = None

try:
    from .retrieval import (
        AdvancedRAGRetriever, 
        RAGQueryOptimizer, 
        QueryType, 
        RetrievalResult, 
        RAGContext
    )
except ImportError as e:
    import logging
    logging.warning(f"Retrieval components not available: {e}")
    AdvancedRAGRetriever = None
    RAGQueryOptimizer = None
    QueryType = None
    RetrievalResult = None
    RAGContext = None

try:
    from .rag_agent import (
        RAGSecurityAgent, 
        ThreatAnalysisResult, 
        PayloadAnalysisResult, 
        SecurityRecommendation
    )
except ImportError as e:
    import logging
    logging.warning(f"RAG agent components not available: {e}")
    RAGSecurityAgent = None
    ThreatAnalysisResult = None
    PayloadAnalysisResult = None
    SecurityRecommendation = None

try:
    from .main_pipeline import (
        RAGPipelineOrchestrator, 
        RAGPipelineConfig, 
        create_rag_pipeline
    )
except ImportError as e:
    import logging
    logging.warning(f"Main pipeline components not available: {e}")
    RAGPipelineOrchestrator = None
    RAGPipelineConfig = None
    create_rag_pipeline = None

__version__ = "1.0.0"
__author__ = "Cybersecurity RAG Team"

__all__ = [
    'VectorDatabase',
    'CybersecurityVectorDB',
    'DataPreprocessor',
    'MitreAttackProcessor',
    'PayloadProcessor', 
    'CyberAgentDataProcessor',
    'ComprehensiveDataProcessor',
    'DataIngestionPipeline',
    'IncrementalIngestionManager',
    'BatchIngestionOptimizer',
    'AdvancedRAGRetriever',
    'RAGQueryOptimizer',
    'QueryType',
    'RetrievalResult',
    'RAGContext',
    'RAGSecurityAgent',
    'ThreatAnalysisResult',
    'PayloadAnalysisResult',
    'SecurityRecommendation',
    'RAGPipelineOrchestrator',
    'RAGPipelineConfig',
    'create_rag_pipeline'
]
