# Changelog

All notable changes to the Document Processing Agency will be documented in this file.

## [Unreleased] - 2025-10-07

### Fixed
- **Chunking Error**: Fixed `'DocMeta' object has no attribute 'num_tokens'` error
  - Updated `CrawlAndProcessUrl` tool to use Docling v2 API for `HybridChunker`
  - Implemented manual token counting using `transformers.AutoTokenizer` instead of accessing `chunk.meta.num_tokens`
  - Removed deprecated `tokenizer` and `max_tokens` parameters from `HybridChunker` initialization
  - Fixed import error: `cannot import name 'Tokenizer' from 'docling_core.transforms.chunker.tokenizer'`
    - Switched to using `AutoTokenizer.from_pretrained()` from the `transformers` library
    - This provides accurate token counts compatible with sentence-transformers models
  - Fixed "Token indices sequence length is longer than the specified maximum" warning
    - Added `MAX_CHUNK_TOKENS` environment variable (default: 400)
    - Implemented explicit tokenization and truncation using the embedding model's own tokenizer
    - All text is now truncated to `MAX_CHUNK_TOKENS` BEFORE being passed to the embedding model
    - This completely eliminates token length warnings and prevents indexing errors

- **Crawl4AI Integration**: Resolved data type handling issues
  - Fixed `'dict' object has no attribute 'decode'` errors when processing HTML content
  - Added type checking for different content formats (string, bytes, dict)
  - Implemented proper URL extraction from Crawl4AI link objects

- **Document Format Support**: Improved compatibility across Docling versions
  - Dynamically add `InputFormat` types based on availability (PDF, DOCX, HTML, IMAGE, etc.)
  - Skip unsupported document types gracefully instead of failing
  - Handle version-specific format attributes (CSV, XML, VTT, JSON, etc.)

### Known Issues
- **Windows Console Encoding**: Crawl4AI may display Unicode characters incorrectly in Windows PowerShell
  - This is a cosmetic issue from Crawl4AI's debug output
  - Does not affect functionality or data processing
  - Will not occur when running through the Agency Swarm interface

## [1.0.0] - Initial Release

### Added
- Initial implementation of Document Processing Agency
- Three core tools:
  - `CrawlAndProcessUrl`: Web crawling and document processing
  - `SearchSimilarChunks`: Semantic similarity search
  - `ListCollections`: Database collection management
- Support for 12+ document formats via Docling
- PostgreSQL vector storage with pgvector
- Docker containerization
- Comprehensive documentation and setup guides

