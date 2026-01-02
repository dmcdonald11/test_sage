# Environment Variable Configuration Guide

This guide explains how to configure the model settings for the document processing tools using environment variables.

## Required Environment Variables

### OpenAI API Key
```bash
OPENAI_API_KEY=your_openai_api_key_here
```
Required for OpenAI models and agents.

### Model Configuration

#### MODEL_SOURCE
Determines which model provider to use for tokenization and embeddings.

**Options:**
- `HuggingFace` - Use HuggingFace models (free, runs locally)
- `OpenAI` - Use OpenAI API models (paid, requires API key)

**Default:** `HuggingFace`

```bash
MODEL_SOURCE=HuggingFace
```

#### TOKENIZER_MODEL
The model to use for tokenization during chunking.

**For HuggingFace:**
- Use any HuggingFace model ID
- Examples: `sentence-transformers/all-MiniLM-L6-v2`, `BAAI/bge-small-en-v1.5`

**For OpenAI:**
- Use tiktoken encoding name
- Examples: `cl100k_base`, `p50k_base`, `r50k_base`

**Default:** `sentence-transformers/all-MiniLM-L6-v2`

```bash
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

#### EMBEDDING_MODEL
The model to use for generating embeddings.

**For HuggingFace:**
- Use any sentence-transformers model
- Examples: 
  - `sentence-transformers/all-MiniLM-L6-v2` (fast, 384 dimensions)
  - `BAAI/bge-small-en-v1.5` (balanced, 384 dimensions)
  - `BAAI/bge-large-en-v1.5` (high quality, 1024 dimensions)

**For OpenAI:**
- Use OpenAI embedding model names
- Examples:
  - `text-embedding-3-small` (1536 dimensions, $0.02 per 1M tokens)
  - `text-embedding-3-large` (3072 dimensions, $0.13 per 1M tokens)
  - `text-embedding-ada-002` (1536 dimensions, legacy)

**Default:** `sentence-transformers/all-MiniLM-L6-v2`

```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

#### MAX_CHUNK_TOKENS
Maximum number of tokens per chunk.

**Recommended values:**
- `256-512` - For smaller models and faster processing
- `512-1024` - For larger models with better context
- Consider your embedding model's max input length

**Default:** `512`

```bash
MAX_CHUNK_TOKENS=512
```

### PostgreSQL Configuration

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vector_store
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password
```

### PDF Processing Configuration

#### IMAGE_MODEL
The OpenAI model to use for image analysis and annotation.

**Examples:**
- `gpt-4o-mini` (recommended, fast and cost-effective)
- `gpt-4o` (higher quality, more expensive)
- `gpt-4-vision-preview` (legacy)

**Default:** `gpt-4o-mini`

```bash
IMAGE_MODEL=gpt-4o-mini
```

#### ANNOTATE_IMAGES
Whether to enable AI-powered image annotation by default.

**Options:**
- `true` - Enable image annotation
- `false` - Disable image annotation

**Default:** `false`

```bash
ANNOTATE_IMAGES=true
```

#### IMAGE_SCALE
Scale factor for generated images when annotation is enabled.

**Options:**
- `1` - Lower quality, faster processing
- `2` - Balanced quality and speed (recommended)
- `3` - Higher quality, slower processing

**Default:** `2`

```bash
IMAGE_SCALE=2
```

#### SAVE_IMAGES_AS_FILES
Whether to save images as separate external files by default.

**Options:**
- `true` - Save images in `images/` subfolder
- `false` - Embed images inline in markdown

**Default:** `false`

```bash
SAVE_IMAGES_AS_FILES=true
```

#### MD_OUTPUT_FOLDER
Specifies the output folder where converted markdown files are saved.

**Default:** `test_output`

```bash
MD_OUTPUT_FOLDER=output/documents
```

## Example Configurations

### Example 1: HuggingFace with sentence-transformers (Default, Free)
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```

**Pros:**
- Completely free
- Runs locally, no API calls
- Fast processing
- No rate limits

**Cons:**
- Requires local compute resources
- Lower quality than larger models

### Example 2: OpenAI Embeddings (Paid)
```bash
MODEL_SOURCE=OpenAI
TOKENIZER_MODEL=cl100k_base
EMBEDDING_MODEL=text-embedding-3-small
MAX_CHUNK_TOKENS=8191
OPENAI_API_KEY=sk-...
```

**Pros:**
- High quality embeddings
- No local compute required
- Fast API response

**Cons:**
- Costs money ($0.02 per 1M tokens)
- Requires API key
- Subject to rate limits

### Example 3: HuggingFace with Larger Model (Better Quality)
```bash
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
MAX_CHUNK_TOKENS=512
```

**Pros:**
- Better quality than small models
- Still free and local
- Good for production use

**Cons:**
- Slower than small models
- Requires more memory
- Larger download size

## How to Set Environment Variables

### Option 1: .env File (Recommended)
Create a `.env` file in the project root:

```bash
# Copy and paste your chosen configuration
MODEL_SOURCE=HuggingFace
TOKENIZER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_CHUNK_TOKENS=512
```

### Option 2: System Environment Variables

**Windows (PowerShell):**
```powershell
$env:MODEL_SOURCE = "HuggingFace"
$env:TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
$env:EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
$env:MAX_CHUNK_TOKENS = "512"
```

**Linux/Mac (Bash):**
```bash
export MODEL_SOURCE="HuggingFace"
export TOKENIZER_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export MAX_CHUNK_TOKENS="512"
```

## Tool-Specific Overrides

Some tools allow you to override the environment variables with tool parameters:

```python
# CrawlAndProcessUrl
tool = CrawlAndProcessUrl(
    url="https://example.com",
    embedding_model="BAAI/bge-small-en-v1.5",  # Override
    max_tokens=256  # Override
)

# ExtractAndChunkWebsite
tool = ExtractAndChunkWebsite(
    url="https://example.com",
    tokenizer_model="BAAI/bge-small-en-v1.5",  # Override
    max_tokens=256  # Override
)
```

Note: Tool-specific overrides will use the same `MODEL_SOURCE` from the environment.

## Troubleshooting

### "Model not found" error
- Check that the model name is correct
- For HuggingFace models, verify the model exists on https://huggingface.co
- For OpenAI models, check the encoding name is valid

### "Invalid MODEL_SOURCE" warning
- Ensure `MODEL_SOURCE` is set to either `HuggingFace` or `OpenAI`
- Check for typos or extra spaces

### Out of memory errors
- Reduce `MAX_CHUNK_TOKENS`
- Use a smaller embedding model
- Consider using OpenAI API instead

### Slow performance
- Use a smaller model (e.g., `all-MiniLM-L6-v2`)
- Reduce `MAX_CHUNK_TOKENS`
- Enable GPU if available for HuggingFace models

