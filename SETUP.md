# Setup Guide for Document Processing Agency

This guide will help you set up and test the Document Processing Agency.

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12+ with pgvector extension
- OpenAI API key

---

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Agency Swarm framework
- Docling for document parsing
- Crawl4AI for web crawling
- sentence-transformers for embeddings
- asyncpg and pgvector for database
- All other required dependencies

---

## Step 2: Set Up PostgreSQL with pgvector

### Option A: Using Docker (Recommended for Development)

```bash
docker run -d \
  --name postgres-vector \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=vector_store \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Option B: Local Installation

1. Install PostgreSQL 12 or higher
2. Install pgvector extension:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install postgresql-16-pgvector
   
   # On macOS with Homebrew
   brew install pgvector
   ```
3. Create database:
   ```sql
   CREATE DATABASE vector_store;
   ```

---

## Step 3: Configure Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vector_store
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword

# Embedding Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_MAX_TOKENS=512
```

**Important:** Replace `sk-your-actual-openai-api-key-here` with your actual OpenAI API key from https://platform.openai.com/api-keys

---

## Step 4: Verify Installation

Run the structure validation test:

```bash
python test_structure.py
```

This verifies that all files are in place and have valid syntax.

---

## Step 5: Test the Agency

Run the agency in terminal mode:

```bash
python agency.py
```

You should see the agency initialize and present a chat interface.

### Example Interactions

Try these commands with the agency:

1. **Process a URL:**
   ```
   Process this URL: https://docling-project.github.io/docling/
   ```

2. **Search for content:**
   ```
   Search for information about document parsing
   ```

3. **List collections:**
   ```
   List all collections in the database
   ```

---

## Troubleshooting

### OpenAI API Key Issues

**Error:** `OpenAIError: The api_key client option must be set`

**Solution:** Ensure your `.env` file exists and contains a valid `OPENAI_API_KEY`

### Database Connection Issues

**Error:** `Could not connect to PostgreSQL`

**Solution:** 
1. Verify PostgreSQL is running: `pg_isready`
2. Check connection details in `.env` file match your PostgreSQL configuration
3. Ensure pgvector extension is installed

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'docling'`

**Solution:** Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Crawling Issues

**Error:** `Error crawling URL`

**Solution:**
1. Verify the URL is accessible
2. Check for network connectivity
3. Some sites may block automated crawling - try a different URL

---

## Testing Individual Tools

While the tools are designed to work within the Agency Swarm framework, you can test basic functionality:

### Test CrawlAndProcessUrl

```python
from document_processor.tools.CrawlAndProcessUrl import CrawlAndProcessUrl

tool = CrawlAndProcessUrl(
    url="https://example.com",
    collection_name="test_collection",
    max_tokens=512
)

# Note: This requires valid OPENAI_API_KEY and PostgreSQL connection
result = tool.run()
print(result)
```

### Test SearchSimilarChunks

```python
from document_processor.tools.SearchSimilarChunks import SearchSimilarChunks

tool = SearchSimilarChunks(
    query="document processing",
    collection_name="test_collection",
    top_k=5
)

# Note: This requires PostgreSQL with existing data
result = tool.run()
print(result)
```

### Test ListCollections

```python
from document_processor.tools.ListCollections import ListCollections

tool = ListCollections()

# Note: This requires PostgreSQL connection
result = tool.run()
print(result)
```

---

## Production Deployment

### Using Docker

Build the Docker image:

```bash
docker build -t document-processing-agency .
```

Run with environment variables:

```bash
docker run -d \
  -e OPENAI_API_KEY=your_key \
  -e POSTGRES_HOST=your_host \
  -e POSTGRES_DB=vector_store \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 8000:8000 \
  document-processing-agency
```

### Using Agencii Platform

1. Sign up at [agencii.ai](https://agencii.ai/)
2. Install the [Agencii GitHub App](https://github.com/apps/agencii)
3. Connect your repository
4. Configure environment variables in the Agencii dashboard
5. Push to main branch for automatic deployment

---

## Advanced Configuration

### Custom Embedding Models

You can use different embedding models by setting the `EMBEDDING_MODEL` environment variable or specifying it in tool calls:

```python
# In .env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Or per tool call
tool = CrawlAndProcessUrl(
    url="https://example.com",
    embedding_model="sentence-transformers/all-mpnet-base-v2"
)
```

**Supported Models:**
- `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) - Fast, good quality
- `sentence-transformers/all-mpnet-base-v2` (768 dimensions) - Higher quality
- `BAAI/bge-small-en-v1.5` (384 dimensions) - Excellent for retrieval
- Any sentence-transformers compatible model

### Custom Chunk Sizes

Adjust chunk sizes based on your use case:

```python
tool = CrawlAndProcessUrl(
    url="https://example.com",
    max_tokens=1024  # Larger chunks for more context
)
```

**Guidelines:**
- 256-512: Good for question answering
- 512-1024: Better for summarization
- 1024+: For maintaining more context

### Document Type Filtering

Process only specific document types:

```python
tool = CrawlAndProcessUrl(
    url="https://example.com",
    include_types=["pdf", "html", "markdown"]
)
```

---

## Database Management

### View Stored Chunks

```sql
SELECT 
    collection_name,
    COUNT(*) as chunk_count,
    COUNT(DISTINCT source_url) as unique_sources
FROM document_chunks
GROUP BY collection_name;
```

### Delete a Collection

```sql
DELETE FROM document_chunks 
WHERE collection_name = 'collection_to_delete';
```

### Check Database Size

```sql
SELECT 
    pg_size_pretty(pg_database_size('vector_store')) as db_size,
    COUNT(*) as total_chunks
FROM document_chunks;
```

---

## Support and Resources

- **Agency Swarm Documentation:** https://agency-swarm.ai
- **Docling Documentation:** https://docling-project.github.io/docling/
- **pgvector GitHub:** https://github.com/pgvector/pgvector
- **Crawl4AI Documentation:** https://github.com/unclecode/crawl4ai

---

## Next Steps

1. ✅ Complete the setup steps above
2. ✅ Test the agency with sample URLs
3. ✅ Build your document collection
4. ✅ Experiment with semantic search
5. ✅ Deploy to production when ready

Enjoy building intelligent document processing workflows!
