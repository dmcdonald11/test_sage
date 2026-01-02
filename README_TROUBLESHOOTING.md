# Troubleshooting Guide

## Current Issue: Windows Console Encoding with Crawl4AI

If you're on Windows and seeing Unicode encoding errors from Crawl4AI, here are the solutions:

### Quick Test

Try running the agency again with the latest updates:

```bash
python agency.py
```

Then try:
```
Please process https://example.com
```

### If Issues Persist

The tool now has extensive debug output. When you run it, check for console output showing:
- `DEBUG: crawl_result['html'] type:`
- `DEBUG _parse_document: doc['content'] type =`
- Full traceback in error output

### Alternative: Use Simple Web Scraping

If Crawl4AI continues to have issues on Windows, the tool automatically falls back to requests+BeautifulSoup, which is more stable on Windows.

### Database Requirement

Remember, you still need:
1. **PostgreSQL with pgvector** running
2. **`.env` file** with credentials

Quick setup:
```bash
# Start PostgreSQL with Docker
docker run -d --name postgres-vector \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=vector_store \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

Create `.env`:
```env
OPENAI_API_KEY=your_key_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vector_store
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Expected Debug Output

With the latest fixes, you should see:
1. Crawl4AI fetching the URL
2. DEBUG output showing data types
3. Either success with chunks stored, or detailed error traceback

### Contact

If you continue to see the `'dict' object has no attribute 'decode'` error after these updates, please share the full debug output from the console.

