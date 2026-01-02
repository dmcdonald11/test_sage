# MCP Server for Web Document Processing and Vector Storage

## Overview
Build a Model Context Protocol (MCP) server that crawls websites, extracts and parses various document formats using Docling, performs hybrid chunking, generates embeddings, and stores the results in a PostgreSQL vector database.

## Architecture Summary

```
URL Input → Web Crawler → Document Parser (Docling) → Hybrid Chunker → 
Embedding Generator → PostgreSQL (pgvector) Storage
```

## Core Requirements

### 1. MCP Server Setup

**Framework**: Use Agency Swarm and this code base as a template, PostgreSQL with pgvector addon, and docker deployment.  You should be able to only have to create the agent and the tools as indicated in the example_agent folder.

**Server Configuration**:
- Transport: HTTP, SSE and Stdio for network and local usage
- Async operations for better performance
- Error handling and logging
- Environment variables for sensitive data

**Required Environment Variables**:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=vector_store
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_MAX_TOKENS=512
```

---

## 2. Tool 1: `crawl_and_process_url`

### Description
Accepts a URL, crawls the page, identifies parseable documents, processes them through Docling, chunks the content, generates embeddings, and stores in PostgreSQL.

### Input Parameters

```python
{
    "url": str,  # Required: URL to crawl
    "embedding_model": str,  # Optional: Override default embedding model
    "max_tokens": int,  # Optional: Max tokens per chunk (default: 512)
    "include_types": List[str],  # Optional: Filter document types to process
    "collection_name": str,  # Optional: Vector DB collection/table name
    "metadata": dict  # Optional: Additional metadata to store with chunks
}
```

### Process Flow

#### Step 1: URL Crawling
Use **Crawl4AI** or **BeautifulSoup + requests** to:
- Download the HTML page
- Parse the HTML content
- Extract all links and embedded resources
- Identify downloadable documents

```python
# Pseudo-code
async def crawl_url(url: str) -> CrawlResult:
    """
    Crawl URL and extract:
    - HTML content
    - All document links (PDFs, DOCX, etc.)
    - Embedded images
    - Audio/video references
    """
    pass
```

#### Step 2: Document Discovery and Classification

Parse the crawled content and identify all Docling-supported formats:

**Document Types to Identify**:
- **PDF**: Links ending in `.pdf`
- **MS Office**: `.docx`, `.xlsx`, `.pptx`
- **Text Formats**: `.md`, `.asciidoc`, `.html`, `.xhtml`
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- **Data**: `.csv`, `.xml` (JATS, USPTO, METS)
- **Audio**: `.mp3`, `.wav`, `.ogg`, `.m4a`
- **Subtitles**: `.vtt`
- **Docling Native**: `.json` (with docling format)

**Discovery Strategy**:
```python
def discover_documents(html_content: str, base_url: str) -> List[Document]:
    """
    Extract all links and resources from HTML:
    1. Parse <a> tags with href attributes
    2. Parse <img> tags for images
    3. Parse <audio>/<video> tags
    4. Parse embedded documents (<embed>, <object>, <iframe>)
    5. Classify by file extension
    6. Return list of Document objects with metadata
    """
    documents = []
    
    # For each discovered resource:
    # - Determine format
    # - Resolve relative URLs to absolute
    # - Add to documents list with metadata
    
    return documents
```

#### Step 3: Document Download and Parsing with Docling

For each discovered document:

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat

async def parse_document(doc_url: str, doc_type: str) -> DoclingDocument:
    """
    Download and parse document using Docling
    
    Handles:
    - PDF, DOCX, XLSX, PPTX
    - Markdown, AsciiDoc
    - HTML, XHTML
    - Images (PNG, JPG, etc.)
    - CSV
    - Audio (via Whisper ASR)
    - VTT subtitles
    - XML (JATS, USPTO, METS)
    - JSON_DOCLING
    """
    
    # Download document
    document_bytes = await download_document(doc_url)
    
    # Configure Docling converter
    converter = DocumentConverter(
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.IMAGE,
            InputFormat.AUDIO,
            # ... all supported formats
        ]
    )
    
    # Convert document
    result = converter.convert(document_bytes)
    return result.document
```

**Special Handling**:

- **HTML Content**: Parse main page HTML directly
- **Images**: Enable picture description with VLM if configured
- **Audio**: Configure Whisper ASR pipeline options
- **Large Documents**: Stream processing if needed

#### Step 4: Hybrid Chunking

Apply Docling's Hybrid Chunker to each parsed document:

```python
from docling.chunking import HybridChunker

async def chunk_document(
    docling_doc: DoclingDocument,
    tokenizer: str,
    max_tokens: int = 512
) -> List[Chunk]:
    """
    Apply hybrid chunking to DoclingDocument
    
    Features:
    - Tokenization-aware splitting
    - Preserves document structure
    - Adds contextual headings/captions
    - Maintains grounding to source elements
    """
    
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
    )
    
    chunks = []
    for chunk in chunker.chunk(dl_doc=docling_doc):
        chunks.append({
            "text": chunk.text,
            "num_tokens": chunk.meta.num_tokens,
            "doc_items_refs": chunk.meta.doc_items_refs,
            "headings": chunk.meta.headings,  # Contextual headings
            "source_document": docling_doc.origin.filename,
        })
    
    return chunks
```

#### Step 5: Embedding Generation

Generate vector embeddings for each chunk:

```python
from sentence_transformers import SentenceTransformer

async def generate_embeddings(
    chunks: List[Chunk],
    model_name: str
) -> List[ChunkWithEmbedding]:
    """
    Generate embeddings for all chunks
    
    Supports:
    - sentence-transformers models
    - OpenAI embeddings (with API key)
    - Cohere embeddings
    - Custom embedding models
    """
    
    # Load embedding model
    model = SentenceTransformer(model_name)
    
    # Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Combine chunks with embeddings
    chunks_with_embeddings = []
    for chunk, embedding in zip(chunks, embeddings):
        chunks_with_embeddings.append({
            **chunk,
            "embedding": embedding.tolist(),
            "embedding_model": model_name,
        })
    
    return chunks_with_embeddings
```

**Supported Embedding Models**:
- `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- `sentence-transformers/all-mpnet-base-v2` (768 dimensions)
- `BAAI/bge-small-en-v1.5` (384 dimensions)
- `openai/text-embedding-3-small` (via API)
- User-specified custom models

#### Step 6: PostgreSQL Vector Storage

Store chunks with embeddings in PostgreSQL using pgvector:

```python
import asyncpg
from pgvector.asyncpg import register_vector

async def store_in_postgres(
    chunks_with_embeddings: List[ChunkWithEmbedding],
    collection_name: str,
    metadata: dict
):
    """
    Store chunks in PostgreSQL with pgvector
    
    Schema:
    - id: UUID primary key
    - collection_name: Text (for grouping)
    - chunk_text: Text (the actual chunk content)
    - num_tokens: Integer
    - doc_items_refs: JSONB (references to source doc items)
    - headings: JSONB (contextual headings)
    - source_url: Text (original URL)
    - source_document: Text (document filename/URL)
    - embedding: vector(dimension) (pgvector type)
    - embedding_model: Text
    - metadata: JSONB (custom metadata)
    - created_at: Timestamp
    """
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=int(os.getenv("POSTGRES_PORT")),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    
    # Register pgvector type
    await register_vector(conn)
    
    # Insert chunks
    for chunk in chunks_with_embeddings:
        await conn.execute(
            """
            INSERT INTO document_chunks (
                collection_name, chunk_text, num_tokens, 
                doc_items_refs, headings, source_url, 
                source_document, embedding, embedding_model, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            collection_name,
            chunk["text"],
            chunk["num_tokens"],
            json.dumps(chunk["doc_items_refs"]),
            json.dumps(chunk.get("headings", [])),
            metadata.get("source_url"),
            chunk["source_document"],
            chunk["embedding"],
            chunk["embedding_model"],
            json.dumps(metadata),
        )
    
    await conn.close()
```

**Database Schema**:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    num_tokens INTEGER NOT NULL,
    doc_items_refs JSONB,
    headings JSONB,
    source_url TEXT,
    source_document TEXT,
    embedding vector(384),  -- Adjust dimension based on model
    embedding_model TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Create index for collection queries
CREATE INDEX ON document_chunks (collection_name);
```

---

## 3. Tool 2: `search_similar_chunks`

### Description
Search for similar chunks using vector similarity

### Input Parameters

```python
{
    "query": str,  # Required: Search query
    "collection_name": str,  # Optional: Filter by collection
    "top_k": int,  # Optional: Number of results (default: 5)
    "similarity_threshold": float,  # Optional: Min similarity score
    "embedding_model": str,  # Optional: Model to use for query embedding
}
```

### Implementation

```python
async def search_similar_chunks(
    query: str,
    collection_name: str = None,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
    embedding_model: str = None
) -> List[SearchResult]:
    """
    Perform vector similarity search
    """
    
    # Generate query embedding
    model = SentenceTransformer(embedding_model or os.getenv("EMBEDDING_MODEL"))
    query_embedding = model.encode(query).tolist()
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(...)
    await register_vector(conn)
    
    # Perform similarity search
    if collection_name:
        results = await conn.fetch(
            """
            SELECT 
                chunk_text, 
                num_tokens, 
                source_url, 
                source_document,
                headings,
                metadata,
                1 - (embedding <=> $1) as similarity
            FROM document_chunks
            WHERE collection_name = $2
            AND 1 - (embedding <=> $1) > $3
            ORDER BY embedding <=> $1
            LIMIT $4
            """,
            query_embedding,
            collection_name,
            similarity_threshold,
            top_k,
        )
    else:
        results = await conn.fetch(
            """
            SELECT 
                chunk_text, 
                num_tokens, 
                source_url, 
                source_document,
                headings,
                metadata,
                1 - (embedding <=> $1) as similarity
            FROM document_chunks
            WHERE 1 - (embedding <=> $1) > $2
            ORDER BY embedding <=> $1
            LIMIT $3
            """,
            query_embedding,
            similarity_threshold,
            top_k,
        )
    
    await conn.close()
    
    return [dict(r) for r in results]
```

---

## 4. Tool 3: `list_collections`

### Description
List all available collections in the vector database

### Implementation

```python
async def list_collections() -> List[str]:
    """List unique collection names"""
    conn = await asyncpg.connect(...)
    
    collections = await conn.fetch(
        """
        SELECT DISTINCT collection_name, COUNT(*) as chunk_count
        FROM document_chunks
        GROUP BY collection_name
        ORDER BY collection_name
        """
    )
    
    await conn.close()
    
    return [{"name": r["collection_name"], "count": r["chunk_count"]} for r in collections]
```

---

## 5. Error Handling

```python
class URLCrawlError(Exception):
    """Raised when URL cannot be crawled"""
    pass

class DocumentParseError(Exception):
    """Raised when document cannot be parsed"""
    pass

class EmbeddingError(Exception):
    """Raised when embedding generation fails"""
    pass

class DatabaseError(Exception):
    """Raised when database operation fails"""
    pass
```

**Error Response Format**:
```json
{
    "success": false,
    "error": "Error type",
    "message": "Detailed error message",
    "url": "original_url",
    "failed_documents": ["list", "of", "failed", "docs"]
}
```

---

## 6. Success Response Format

```json
{
    "success": true,
    "url": "https://example.com",
    "documents_processed": 5,
    "documents_list": [
        {
            "url": "https://example.com/doc.pdf",
            "type": "PDF",
            "chunks": 12,
            "tokens": 5847
        }
    ],
    "total_chunks": 45,
    "total_tokens": 23456,
    "collection_name": "example_collection",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "storage": {
        "database": "postgresql",
        "table": "document_chunks",
        "records_inserted": 45
    }
}
```

---

## 7. Dependencies

**requirements.txt**:
```txt
# MCP Server
mcp>=1.0.0

# Document Processing
docling>=2.0.0
docling-core>=2.0.0

# Web Crawling
crawl4ai>=0.7.0
beautifulsoup4>=4.12.0
requests>=2.31.0

# Embeddings
sentence-transformers>=2.2.0
transformers>=4.35.0
torch>=2.1.0

# Database
asyncpg>=0.29.0
pgvector>=0.2.4

# Utilities
python-dotenv>=1.0.0
aiohttp>=3.9.0
pydantic>=2.5.0
```

---

## 8. Usage Example

**Starting the MCP Server**:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_DB=vector_store
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword

# Run the server
python mcp_server.py
```

**Using the Tool from MCP Client**:
```python
# Example Claude Desktop config or MCP client usage
{
    "mcpServers": {
        "document-processor": {
            "command": "python",
            "args": ["/path/to/mcp_server.py"]
        }
    }
}
```

**Tool Call Example**:
```json
{
    "tool": "crawl_and_process_url",
    "arguments": {
        "url": "https://docling-project.github.io/docling/",
        "collection_name": "docling_docs",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "max_tokens": 512,
        "include_types": ["html", "pdf", "markdown"],
        "metadata": {
            "source": "docling_documentation",
            "date_crawled": "2025-10-07"
        }
    }
}
```

---

## 9. Advanced Features (Optional)

### 9.1 Incremental Updates
- Check if URL has been crawled before
- Compare document hashes
- Only process changed/new documents

### 9.2 Batch Processing
- Support multiple URLs in one call
- Parallel processing of documents
- Progress tracking

### 9.3 Content Filtering
- Filter by document size
- Filter by language
- Filter by content type

### 9.4 Custom Chunking Strategies
- Allow users to specify chunking parameters
- Support for HierarchicalChunker vs HybridChunker
- Custom serialization for tables

### 9.5 Metadata Enrichment
- Extract metadata from documents
- Add timestamp information
- Tag documents automatically

---

## 10. Testing Strategy

### Unit Tests
- Test URL crawling
- Test document discovery
- Test Docling parsing for each format
- Test chunking logic
- Test embedding generation
- Test database operations

### Integration Tests
- End-to-end test with real URLs
- Test with various document types
- Test error handling
- Test large documents

### Performance Tests
- Benchmark crawling speed
- Benchmark embedding generation
- Benchmark database insertion
- Memory usage profiling

---

## 11. Security Considerations

1. **URL Validation**: Prevent SSRF attacks
2. **Rate Limiting**: Respect robots.txt and rate limits
3. **Resource Limits**: Max document size, max documents per URL
4. **API Keys**: Secure storage of embedding API keys
5. **Database Security**: Use prepared statements, connection pooling
6. **Content Validation**: Sanitize extracted content

---

## 12. Monitoring and Logging

- Log all URL crawl attempts
- Log document processing success/failure
- Track embedding generation time
- Monitor database performance
- Alert on errors or failures

---

## Summary

This MCP server provides a comprehensive solution for:
- 🌐 **Web crawling** with intelligent document discovery
- 📄 **Multi-format parsing** using Docling (12+ formats)
- 🧩 **Smart chunking** with Hybrid Chunker (structure + token-aware)
- 🔢 **Flexible embeddings** with choice of models
- 💾 **Vector storage** in PostgreSQL with pgvector
- 🔍 **Similarity search** for retrieval

The architecture is production-ready, scalable, and designed for RAG applications.

