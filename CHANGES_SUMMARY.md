# Summary of Changes: Model Configuration Update

This document summarizes all changes made to support user-defined model configuration for chunking and embedding processes.

## Overview

Updated the document processing tools to support flexible model configuration through environment variables. Users can now choose between HuggingFace (free, local) and OpenAI (paid, API) models for tokenization and embeddings.

## Files Created

### 1. `document_processor/tools/utils/__init__.py`
- Module initialization file for utility functions

### 2. `document_processor/tools/utils/model_loader.py` ⭐ NEW
**Purpose:** Central utility module for loading models based on configuration

**Key Functions:**
- `get_tokenizer(model_name, model_source)` - Load tokenizer based on source
- `get_embedding_model(model_name, model_source)` - Load embedding model based on source
- `get_model_config()` - Retrieve configuration from environment variables

**Supported Sources:**
- HuggingFace: Uses `AutoTokenizer` and `SentenceTransformer`
- OpenAI: Uses `OpenAITokenizerWrapper` and OpenAI API

### 3. `document_processor/tools/utils/tokenizer.py` ⭐ NEW
**Purpose:** OpenAI tokenizer wrapper for compatibility with HybridChunker

**Key Class:**
- `OpenAITokenizerWrapper` - Makes tiktoken compatible with Docling's chunking interface

### 4. `ENV_CONFIGURATION.md` ⭐ NEW
**Purpose:** Comprehensive guide for environment variable configuration

**Contents:**
- Detailed explanation of all model configuration variables
- Example configurations for different use cases
- How to set environment variables on different platforms
- Troubleshooting guide

### 5. `docs/MODEL_CONFIGURATION.md` ⭐ NEW
**Purpose:** Technical documentation of the model configuration system

**Contents:**
- Overview of changes
- Detailed description of new utilities
- Usage examples
- Migration guide
- Testing instructions

### 6. `test_model_config.py` ⭐ NEW
**Purpose:** Test script to verify model configuration works correctly

**Tests:**
- Configuration loading from environment
- HuggingFace tokenizer loading
- OpenAI tokenizer loading
- HuggingFace embedding model loading
- OpenAI embedding model loading (optional)

## Files Modified

### 1. `document_processor/tools/CrawlAndProcessUrl.py`
**Changes:**

#### `_chunk_document()` method:
- **Before:** Hardcoded to use `AutoTokenizer.from_pretrained(model_name)`
- **After:** Uses `get_tokenizer()` to load tokenizer based on `MODEL_SOURCE`
- Respects `MAX_CHUNK_TOKENS` from environment

#### `_generate_embeddings()` method:
- **Before:** Hardcoded to use `SentenceTransformer(model_name)`
- **After:** Uses `get_embedding_model()` to load model based on `MODEL_SOURCE`
- Supports both HuggingFace and OpenAI embedding models

#### `_process_url()` method:
- Added `model_source` to response JSON
- Returns actual model configuration used

### 2. `document_processor/tools/SearchSimilarChunks.py`
**Changes:**

#### `_generate_query_embedding()` method:
- **Before:** Hardcoded to use `SentenceTransformer(model_name)`
- **After:** Uses `get_embedding_model()` to load model based on `MODEL_SOURCE`
- Properly handles both numpy arrays and lists for embedding output

### 3. `sage_agent/tools/ExtractAndChunkWebsite.py`
**Changes:**

#### Field definition:
- `tokenizer_model` field default changed from `default_factory` to `default=None`
- Now uses environment variable when not provided

#### Chunking section (Step 8-10):
- **Before:** Used tokenizer model string directly with `HybridChunker`
- **After:** 
  - Imports model loader utilities
  - Loads tokenizer based on `MODEL_SOURCE`
  - Creates `HybridChunker` with tokenizer instance
  - Respects all environment variables

#### Summary output:
- Added `model_source` field to summary
- Uses actual `tokenizer_model_to_use` and `max_tokens_to_use`

#### Return value:
- Added `tokenizer_model`, `model_source`, and `max_tokens` to response

### 4. `README.md`
**Changes:**

#### Features section:
- Added "🎛️ Flexible Model Configuration: Choose between HuggingFace (free) or OpenAI (paid) models"

#### Environment Variables section:
- Expanded to include all new model configuration variables
- Added `MODEL_SOURCE`, `TOKENIZER_MODEL`, `EMBEDDING_MODEL`, `MAX_CHUNK_TOKENS`
- Included examples for both HuggingFace and OpenAI configurations
- Added link to `ENV_CONFIGURATION.md` for detailed information

## Environment Variables

### New/Updated Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODEL_SOURCE` | String | `HuggingFace` | Model provider (HuggingFace, OpenAI) |
| `TOKENIZER_MODEL` | String | `sentence-transformers/all-MiniLM-L6-v2` | Model for tokenization |
| `EMBEDDING_MODEL` | String | `sentence-transformers/all-MiniLM-L6-v2` | Model for embeddings |
| `MAX_CHUNK_TOKENS` | Integer | `512` | Maximum tokens per chunk |

### Existing Variables (Unchanged)
- `OPENAI_API_KEY`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

## Usage Examples

### HuggingFace Configuration (Free, Local)

**.env:**
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```

**Result:**
- Models download and run locally
- No API costs
- No rate limits

### OpenAI Configuration (Paid, API)

**.env:**
```bash
MODEL_SOURCE=OpenAI
TOKENIZER_MODEL=cl100k_base
EMBEDDING_MODEL=text-embedding-3-small
MAX_CHUNK_TOKENS=8191
OPENAI_API_KEY=sk-...
```

**Result:**
- Uses OpenAI API for embeddings
- Costs ~$0.02 per 1M tokens
- High quality embeddings

## Backward Compatibility

✅ **Fully backward compatible!**

- If environment variables are not set, defaults to original behavior
- Existing code continues to work without changes
- Tool-specific overrides still supported

**Migration:** Simply add the new environment variables to your `.env` file. No code changes required.

## Testing

Run the test script to verify your configuration:

```bash
python test_model_config.py
```

Expected output:
- ✓ Configuration loaded successfully
- ✓ HuggingFace tokenizer works
- ✓ OpenAI tokenizer works
- ✓ HuggingFace embeddings work
- ✓ OpenAI embeddings work (if API key provided)

## Benefits

1. **Cost Control**: Choose between free local models or paid cloud models
2. **Quality Control**: Use larger models when quality is critical
3. **Flexibility**: Switch providers without code changes
4. **Performance**: Optimize based on your compute resources
5. **Easy Configuration**: All settings in one place (.env file)

## Documentation

- **ENV_CONFIGURATION.md**: User guide for environment variables
- **docs/MODEL_CONFIGURATION.md**: Technical documentation
- **README.md**: Updated quick start guide
- **test_model_config.py**: Test script with examples

## Next Steps

1. ✅ Set your preferred configuration in `.env`
2. ✅ Run `python test_model_config.py` to verify
3. ✅ Test with your actual documents
4. ✅ Deploy to production

## Support

For issues or questions:
1. Check **ENV_CONFIGURATION.md** for configuration help
2. Review **docs/MODEL_CONFIGURATION.md** for technical details
3. Run **test_model_config.py** to diagnose issues
4. Check error messages for specific guidance

---

**Summary:** The chunking process now supports user-defined models through environment variables. Users can choose between HuggingFace (free) or OpenAI (paid) models for both tokenization and embeddings, with easy configuration through the `.env` file.

