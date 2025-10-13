#!/usr/bin/env python3
"""
Test script to validate that the RAG pipeline can load the new dataset structure
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add the aiml_part directory to Python path
sys.path.insert(0, '/workspaces/codespaces-blank/integration/aiml_part')

from rag_pipeline.main_pipeline import RAGPipelineOrchestrator, RAGPipelineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_data_loading():
    """Test the dataset loading process"""
    logger.info("🚀 Starting dataset loading test...")
    
    try:
        # Configure the RAG pipeline
        config = RAGPipelineConfig()
        config.vector_db_path = "/tmp/test_vectordb"
        
        # Create directory if it doesn't exist
        os.makedirs(config.vector_db_path, exist_ok=True)
        
        # Initialize pipeline
        pipeline = RAGPipelineOrchestrator(config)
        
        # Define paths
        datasets_dir = "/workspaces/codespaces-blank/integration/datasets"
        cyberagents_path = "/workspaces/codespaces-blank/integration/aiml_part/cyberagents"
        
        logger.info(f"📁 Using datasets directory: {datasets_dir}")
        logger.info(f"🤖 Using cyberagents path: {cyberagents_path}")
        
        # Check if datasets directory exists
        if not os.path.exists(datasets_dir):
            logger.error(f"❌ Datasets directory not found: {datasets_dir}")
            return False
        
        # Count CSV files
        csv_files = list(Path(datasets_dir).glob("*.csv"))
        logger.info(f"📊 Found {len(csv_files)} CSV files to process")
        
        # Initialize pipeline with datasets
        logger.info("🔄 Initializing RAG pipeline with datasets...")
        init_result = pipeline.initialize_pipeline(
            datasets_dir=datasets_dir,
            cyberagents_path=cyberagents_path if os.path.exists(cyberagents_path) else None,
            force_rebuild=True
        )
        
        if init_result['status'] == 'success':
            logger.info("✅ Pipeline initialization successful!")
            
            # Get collection info
            collection_info = pipeline.vector_db.get_collection_info()
            logger.info(f"📈 Vector database stats:")
            logger.info(f"   • Document count: {collection_info.get('document_count', 0)}")
            logger.info(f"   • Collection name: {collection_info.get('collection_name', 'N/A')}")
            
            # Test a simple query using the retriever
            logger.info("🔍 Testing a sample query...")
            try:
                test_results = pipeline.retriever.hybrid_search(
                    query="SQL injection attack",
                    top_k=3
                )
                
                if test_results:
                    logger.info(f"✅ Query test successful! Found {len(test_results)} results")
                    for i, result in enumerate(test_results[:2]):
                        logger.info(f"   Result {i+1}: {result.get('content', 'N/A')[:100]}...")
                else:
                    logger.warning("⚠️  Query test returned no results")
            except Exception as query_e:
                logger.warning(f"⚠️  Query test failed: {query_e}, but data loading was successful")
            
            return True
            
        else:
            logger.error(f"❌ Pipeline initialization failed: {init_result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logger.info("=== Dataset Loading Test ===")
    
    success = asyncio.run(test_data_loading())
    
    if success:
        logger.info("🎉 All tests passed! Dataset loading is working correctly.")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed! Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()