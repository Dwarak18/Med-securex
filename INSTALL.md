# Installation Guide

This guide will help you set up the Cybersecurity Analysis Pipeline with RAG capabilities.

## Prerequisites

- Python 3.8 or higher
- Git
- At least 4GB of RAM
- Internet connection for downloading models and dependencies

## Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd assr
```

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv cyberenv

# Activate virtual environment
# On Windows:
cyberenv\Scripts\activate
# On Linux/Mac:
source cyberenv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will install Qdrant client for vector database operations. Qdrant will automatically create a local instance if no existing server is found.

## Step 4: Set up Environment Variables

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit the `.env` file and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
MODEL_NAME=gemini-1.5-flash
```

To get a Gemini API key:
- Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create a new API key
- Copy and paste it into your `.env` file

## Step 5: Prepare Data Files

Ensure you have the required CSV files:
- `mitre_attack_structured_dataset.csv` - MITRE ATT&CK data
- `payload_dataset.csv` - Security payload data

These should be in the project root directory.

## Step 6: Test the Installation

Run the test script to verify everything is working:

```bash
python test_pipeline.py
```

## Step 7: Run the Main Application

### Option 1: Run CyberAgents Only
```bash
cd cyberagents
python main.py
```

### Option 2: Use RAG Pipeline
```python
from rag_pipeline.main_pipeline import create_rag_pipeline

# Create and initialize the pipeline
pipeline = create_rag_pipeline(
    mitre_csv_path="mitre_attack_structured_dataset.csv",
    payload_csv_path="payload_dataset.csv",
    cyberagents_path="cyberagents"
)

# Query the knowledge base
result = pipeline.query_knowledge_base("SQL injection attack")
print(result)
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure you've activated the virtual environment and installed all requirements.

2. **API Key Issues**: Verify your Gemini API key is correct and has sufficient quota.

3. **Memory Issues**: If you encounter memory issues, try reducing batch sizes in the configuration.

4. **Permission Errors**: Make sure you have write permissions in the project directory.

### Optional Dependencies

Some features require additional dependencies:
- `torch` and `torch-geometric` for advanced graph analysis
- `pyod` for anomaly detection
- `ticketutil` for JIRA integration

These are optional and the system will work without them.

## Configuration

You can customize the pipeline behavior by modifying the configuration in `rag_pipeline/main_pipeline.py`:

```python
config = RAGPipelineConfig()
config.similarity_threshold = 0.3  # Adjust similarity threshold
config.top_k_results = 10          # Number of results to return
config.max_context_length = 2000   # Maximum context length
```

## Data Ingestion

The first time you run the pipeline, it will automatically:
1. Process your CSV data files
2. Create embeddings
3. Store everything in a vector database
4. This may take several minutes depending on data size

## Next Steps

- Explore the example scripts in the project
- Check the README.md for usage examples
- Review the API documentation in each module
