# Model Configuration Update Summary

This document describes the recent updates to support user-defined model configuration for the chunking and embedding process.

## Overview

The document processing tools now support flexible model configuration through environment variables, allowing you to choose between different model providers (HuggingFace, OpenAI) and customize tokenization and embedding settings.

## Changes Made

### 1. New Utility Module: `model_loader.py`

**Location:** `document_processor/tools/utils/model_loader.py`

This module provides three main functions:

#### `get_tokenizer(model_name, model_source)`
Loads a tokenizer based on the specified model source.
- **HuggingFace**: Uses `AutoTokenizer` from transformers
- **OpenAI**: Uses `OpenAITokenizerWrapper` with tiktoken

#### `get_embedding_model(model_name, model_source)`
Loads an embedding model based on the specified model source.
- **HuggingFace**: Uses `SentenceTransformer`
- **OpenAI**: Uses `OpenAIEmbeddingWrapper` that wraps the OpenAI API

#### `get_model_config()`
Retrieves model configuration from environment variables.

Returns:
- `tokenizer_model`: Model to use for tokenization
- `embedding_model`: Model to use for embeddings
- `model_source`: Provider (HuggingFace, OpenAI, etc.)
- `max_chunk_tokens`: Maximum tokens per chunk

### 2. Updated Tools

#### `CrawlAndProcessUrl.py`
**Changes:**
- `_chunk_document()`: Now uses `get_tokenizer()` to load tokenizer based on `MODEL_SOURCE`
- `_generate_embeddings()`: Now uses `get_embedding_model()` to load embedding model based on `MODEL_SOURCE`
- Response includes `model_source` field

#### `SearchSimilarChunks.py`
**Changes:**
- `_generate_query_embedding()`: Now uses `get_embedding_model()` to generate query embeddings based on `MODEL_SOURCE`
- Supports both HuggingFace and OpenAI embedding models for search

#### `ExtractAndChunkWebsite.py` (sage_agent)
**Changes:**
- Updated to use `get_tokenizer()` for loading tokenizer
- Respects `MODEL_SOURCE`, `TOKENIZER_MODEL`, and `MAX_CHUNK_TOKENS` from environment
- Response includes `model_source` and actual `tokenizer_model` used

### 3. OpenAI Tokenizer Wrapper

**Location:** `document_processor/tools/utils/tokenizer.py`

Provides `OpenAITokenizerWrapper` class that makes OpenAI's tiktoken compatible with the HybridChunker interface. This wrapper:
- Implements the `PreTrainedTokenizerBase` interface
- Uses tiktoken encoding (e.g., `cl100k_base`)
- Compatible with Docling's chunking process

### 4. Documentation

#### `ENV_CONFIGURATION.md`
Comprehensive guide explaining:
- All environment variables
- Configuration options for different use cases
- Example configurations
- How to set environment variables on different platforms
- Troubleshooting tips

## Environment Variables

### New/Updated Variables

| Variable | Description | Default | Example Values |
|----------|-------------|---------|----------------|
| `MODEL_SOURCE` | Model provider | `HuggingFace` | `HuggingFace`, `OpenAI` |
| `TOKENIZER_MODEL` | Tokenizer model | `sentence-transformers/all-MiniLM-L6-v2` | HF: `BAAI/bge-small-en-v1.5`<br>OpenAI: `cl100k_base` |
| `EMBEDDING_MODEL` | Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | HF: `BAAI/bge-large-en-v1.5`<br>OpenAI: `text-embedding-3-small` |
| `MAX_CHUNK_TOKENS` | Max tokens per chunk | `512` | `256`, `512`, `1024`, `8191` |

## Usage Examples

### Example 1: Using HuggingFace Models (Default)

**.env:**
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```

**Python:**
```python
from document_processor.document_processor import document_processor

# Uses environment configuration automatically
result = document_processor.run(
    url="https://example.com/document.pdf",
    collection_name="my_collection"
)
```

### Example 2: Using OpenAI Models

**.env:**
```bash
MODEL_SOURCE=OpenAI
TOKENIZER_MODEL=cl100k_base
EMBEDDING_MODEL=text-embedding-3-small
MAX_CHUNK_TOKENS=8191
OPENAI_API_KEY=sk-...
```

**Python:**
```python
from document_processor.tools.CrawlAndProcessUrl import CrawlAndProcessUrl

# Uses OpenAI for both tokenization and embeddings
tool = CrawlAndProcessUrl(
    url="https://example.com/document.pdf",
    collection_name="my_collection"
)
result = tool.run()
```

### Example 3: Tool-Specific Override

**.env:**
```bash
MODEL_SOURCE=HuggingFace
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```

**Python:**
```python
from document_processor.tools.CrawlAndProcessUrl import CrawlAndProcessUrl

# Override embedding model for this specific tool call
tool = CrawlAndProcessUrl(
    url="https://example.com/document.pdf",
    embedding_model="BAAI/bge-large-en-v1.5",  # Override
    max_tokens=256  # Override
)
result = tool.run()
```

## Benefits

1. **Flexibility**: Choose between free local models (HuggingFace) or cloud-based models (OpenAI)
2. **Cost Control**: Use free models for development, paid models for production
3. **Quality Control**: Switch to larger/better models when quality is critical
4. **Performance Optimization**: Adjust chunk size and model size based on your needs
5. **Easy Migration**: Change providers without modifying code

## Migration Guide

If you have existing code using the old implementation:

### Before (Hard-coded Models)
```python
# Old code - models were hard-coded
tool = CrawlAndProcessUrl(url="https://example.com")
# Always used sentence-transformers/all-MiniLM-L6-v2
```

### After (Configurable Models)
```python
# New code - models from environment
# Add to .env:
# MODEL_SOURCE=HuggingFace
# EMBEDDING_MODEL=BAAI/bge-large-en-v1.5

tool = CrawlAndProcessUrl(url="https://example.com")
# Uses BAAI/bge-large-en-v1.5 from environment
```

No code changes required! Just set environment variables.

## Testing

To verify your configuration:

```python
from document_processor.tools.utils.model_loader import get_model_config

# Check current configuration
tokenizer_model, embedding_model, model_source, max_chunk_tokens = get_model_config()

print(f"Model Source: {model_source}")
print(f"Tokenizer Model: {tokenizer_model}")
print(f"Embedding Model: {embedding_model}")
print(f"Max Chunk Tokens: {max_chunk_tokens}")
```

## Troubleshooting

### Issue: "Unknown MODEL_SOURCE" Warning
**Solution:** Set `MODEL_SOURCE` to either `HuggingFace` or `OpenAI` (case-insensitive)

### Issue: OpenAI Embedding Errors
**Solution:** 
1. Verify `OPENAI_API_KEY` is set
2. Check model name is valid (e.g., `text-embedding-3-small`)
3. Ensure you have sufficient API credits

### Issue: HuggingFace Model Download Fails
**Solution:**
1. Check internet connection
2. Verify model name exists on HuggingFace Hub
3. Check disk space for model downloads

## Future Enhancements

Potential future additions:
- Support for more model sources (Cohere, Anthropic, etc.)
- Automatic model selection based on task
- Model caching and optimization
- Batch processing optimizations
- Custom model configurations per collection

## Related Files

- `document_processor/tools/utils/model_loader.py` - Model loading utilities
- `document_processor/tools/utils/tokenizer.py` - OpenAI tokenizer wrapper
- `document_processor/tools/CrawlAndProcessUrl.py` - Updated tool
- `document_processor/tools/SearchSimilarChunks.py` - Updated search tool
- `sage_agent/tools/ExtractAndChunkWebsite.py` - Updated chunking tool
- `ENV_CONFIGURATION.md` - Environment variable guide

