# Document Processing Agency - Shared Instructions

## Agency Overview

This agency provides intelligent document processing capabilities using state-of-the-art AI technologies. It specializes in web crawling, multi-format document parsing, semantic chunking, embedding generation, and vector-based retrieval for RAG (Retrieval-Augmented Generation) applications.

## Core Technologies

- **Docling**: Advanced document parsing library supporting 12+ formats (PDF, DOCX, XLSX, PPTX, HTML, Markdown, Images, Audio, CSV, XML, VTT, JSON)
- **Crawl4AI**: Intelligent web crawling with document discovery
- **Hybrid Chunking**: Structure-aware, token-limited chunking that preserves document context
- **Vector Embeddings**: Semantic embeddings using sentence-transformers
- **PostgreSQL + pgvector**: High-performance vector database for similarity search

## Infrastructure Requirements

### Database
- PostgreSQL 12+ with pgvector extension
- Configured for vector similarity operations (cosine distance)
- Environment variables must be set in `.env` file

### Embedding Models
- Default: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Alternatives: `all-mpnet-base-v2` (768d), `BAAI/bge-small-en-v1.5` (384d)
- Custom models can be specified per operation

## Document Processing Pipeline

1. **Web Crawling**: Extract HTML content and discover linked documents
2. **Document Discovery**: Classify documents by format (12+ supported types)
3. **Parsing**: Use Docling to extract structured content with metadata
4. **Chunking**: Apply hybrid chunking with token limits and structure preservation
5. **Embedding**: Generate semantic vectors for each chunk
6. **Storage**: Store chunks with embeddings in PostgreSQL/pgvector
7. **Retrieval**: Enable semantic search across document corpus

## Supported Document Formats

- **Office**: PDF, DOCX, XLSX, PPTX
- **Web**: HTML, XHTML
- **Text**: Markdown, AsciiDoc
- **Images**: PNG, JPG, GIF, WEBP (with OCR)
- **Audio**: MP3, WAV, OGG, M4A (with transcription)
- **Data**: CSV, JSON
- **Specialized**: XML (JATS, USPTO, METS), VTT subtitles

## Best Practices

- Use meaningful collection names to organize document corpus
- Adjust chunk size (max_tokens) based on document type and use case
- Set appropriate similarity thresholds for search (0.5-0.8 typical range)
- Monitor database size and create indexes for optimal performance
- Process documents in batches when handling multiple URLs
- Preserve document metadata for better retrieval context

## Error Handling

- All tools include comprehensive error handling
- Database connection issues are reported clearly
- Individual document failures don't stop batch processing
- Failed documents are logged with error details

## Security Notes

- Database credentials must be stored in environment variables
- Never expose API keys or passwords in code
- Use read-only database connections for search operations when possible
- Validate and sanitize URLs before processing

