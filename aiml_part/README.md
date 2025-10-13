High-level overview
Purpose: A cyber-defense assistant combining classic ML models (attack/network detection) with a RAG pipeline over cybersecurity knowledge, wrapped in a multi-agent orchestration layer.
Major parts:
RAG pipeline: rag_pipeline/ for data processing, ingestion, retrieval, and an agent that answers domain questions using a vector DB.
ML models: ml/, train_models.py, and models/ for training and serving attack/network models.
Cyber agents: cyberagents/agents/ plus an orchestrator coordinating attack, investigation, and network agents.
Vector DBs: Qdrant-style SQLite-backed stores under cybersecurity_vectordb/, test_* dirs.

End-to-end workflow
Install dependencies
Use requirements.txt (and see INSTALL.md for environment/setup notes).
Train ML models (optional if using prebuilt)
Entry: train_models.py → uses ml/training.py.
Inputs: datasets like mitre_attack_structured_dataset.csv, payload_dataset.csv (and any internal splits).
Outputs: models/attack_model.joblib, models/network_model.joblib (+ temporary label maps in models/tmp/).
Prepare the knowledge base (RAG ingestion)
Entry: rag_pipeline/ingestion.py or rag_pipeline/main_pipeline.py.
Steps:
rag_pipeline/data_processor.py cleans/normalizes sources (e.g., MITRE ATT&CK CSV, payloads).
Embeddings are computed and written to a local vector store via rag_pipeline/vector_db.py.
Storage: vector DB artifacts in cybersecurity_vectordb/ (and test stores in test_vectordb/, test_qdrant_*).

Retrieve and reason (RAG runtime)
rag_pipeline/retrieval.py fetches semantically relevant chunks from the vector DB.
rag_pipeline/rag_agent.py composes answers using retrieved context.
Multi-agent cyber orchestration
Entry: cyberagents/main.py (project runtime).
Components:
cyberagents/agents/attack_agent.py: focuses on attack pattern detection/response.
cyberagents/agents/network_agent.py: network-centric analysis/actions.
cyberagents/agents/investigation_agent.py: enrichment, triage, and hypothesis building.
cyberagents/agents/orchestrator.py: coordinates agents, routes tasks, aggregates results.

Integrations:
Loads configuration from cyberagents/config.py.
Uses utils/logger.py for structured logs (e.g., rag_pipeline.log).
Calls ML models from models/*.joblib and enriches context via the RAG agent.
Testing and debugging
test_pipeline.py validates ingestion/retrieval flow and vector DB connectivity.
Dedicated debug/test vector DBs in debug_test_db/, test_pipeline-related stores in test_vectordb/, test_qdrant_*.

Typical run paths
Train models: train_models.py (produces models/*.joblib).
Build/refresh KB and vector index: rag_pipeline/main_pipeline.py (calls data processing + ingestion).
Run the cyber assistant: cyberagents/main.py (orchestrates agents, calls ML and RAG).
Data and artifacts
Datasets: mitre_attack_structured_dataset.csv, payload_dataset.csv.
Models: models/attack_model.joblib, models/network_model.joblib.
Vector DB: cybersecurity_vectordb/ and test stores (test_vectordb/, test_qdrant_*).
Logs: rag_pipeline.log.
