# Sage Oracle Agent - Advanced Document Processing and Knowledge Extraction

## Overview

The Sage Oracle Agent is a sophisticated document processing and knowledge extraction system designed to handle large-scale document conversion, chunking, embedding, and storage operations. Built on the Agency Swarm framework, it leverages Docling's advanced document understanding capabilities to process various document formats from multiple sources including URLs, sitemaps, and local folders.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Tool Reference](#tool-reference)
- [Examples](#examples)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)

## Features

### 🚀 **Core Capabilities**
- **Multi-Format Support**: Process PDFs, HTML, DOCX, XLSX, PPTX, and images
- **Concurrent Processing**: Handle up to 50 documents simultaneously
- **AI-Powered Image Annotation**: Generate descriptions for images using OpenAI's vision models
- **Intelligent Chunking**: Break documents into semantically meaningful chunks
- **Vector Embeddings**: Create embeddings for semantic search capabilities
- **Flexible Input Sources**: Support for folders, URLs, sitemaps, and mixed sources

### 🛠 **Advanced Features**
- **Batch Processing**: Process multiple documents with retry logic and progress tracking
- **Real-time Monitoring**: Track processing status and performance metrics
- **Dynamic Configuration**: Customize processing parameters at runtime
- **Multiple Export Formats**: Export results as JSON, CSV, Markdown, or HTML
- **Error Handling**: Comprehensive error handling with detailed reporting
- **Resource Management**: Controlled concurrency to prevent system overload

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API Key (for image annotation and embeddings)
- PostgreSQL with pgvector extension (for vector storage)

### Dependencies

The Sage Oracle agent requires the following packages (already included in `requirements.txt`):

```bash
# Core framework
agency-swarm[fastapi]>=1.0.2

# Document processing
docling>=2.0.0
docling-core>=2.0.0

# Web crawling
crawl4ai>=0.7.0
beautifulsoup4>=4.12.0

# Database and embeddings
asyncpg>=0.29.0
pgvector>=0.2.4
sentence-transformers>=2.2.0

# Utilities
python-dotenv>=1.0.0
aiohttp>=3.9.0
pydantic>=2.5.0
```

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   # Required for image annotation
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional configuration
   IMAGE_MODEL=gpt-4o-mini
   ANNOTATE_IMAGES=true
   IMAGE_SCALE=2
   SAVE_IMAGES_AS_FILES=true
   MD_OUTPUT_FOLDER=test_output
   
   # Database configuration (for future vector storage)
   POSTGRES_CONNECTION_STRING=postgresql://user:password@localhost:5432/dbname
   ```

3. **Verify installation**:
   ```bash
   python agency.py
   ```
   You should see: `Sage Oracle agent is ready for document processing!`

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for image annotation | - | Yes |
| `IMAGE_MODEL` | OpenAI model for image description | `gpt-4o-mini` | No |
| `ANNOTATE_IMAGES` | Enable AI image annotation | `false` | No |
| `IMAGE_SCALE` | Scale factor for generated images (1-3) | `2` | No |
| `SAVE_IMAGES_AS_FILES` | Save images as external files | `false` | No |
| `MD_OUTPUT_FOLDER` | Output folder for processed documents | `test_output` | No |

### Processing Parameters

- **Max Concurrent**: 1-50 (default: 10)
- **Max Workers**: 1-20 (default: 4)
- **Batch Size**: 1-100 (default: 10)
- **Image Scale**: 1-3 (higher = better quality, slower processing)

## Usage Guide

### Basic Usage

The Sage Oracle agent is integrated into the Agency Swarm framework. You can interact with it through natural language commands:

```python
# Example: Process a single document
response = await agency.get_response("Convert this PDF to markdown: /path/to/document.pdf")

# Example: Process a folder
response = await agency.get_response("Process all PDFs in the /documents folder")

# Example: Process a website
response = await agency.get_response("Process all documents from https://example.com/sitemap.xml")
```

### Direct Tool Usage

You can also use the tools directly for more control:

```python
from sage_oracle.tools.ConvertSingleDocument import ConvertSingleDocument

tool = ConvertSingleDocument(
    input_source="https://example.com/document.pdf",
    input_type="url",
    annotate_images=True,
    save_images_as_files=True
)

result = tool.run()
print(result)
```

## Tool Reference

### 1. ProcessFolderPipeline

Process all documents in a specified folder with concurrent execution.

**Parameters:**
- `folder_path` (str): Path to folder containing documents
- `file_patterns` (List[str]): File patterns to process (default: ["*.pdf", "*.html", "*.docx", "*.md"])
- `max_concurrent` (int): Number of concurrent pipelines (1-50, default: 10)
- `annotate_images` (bool): Enable AI image annotation (default: True)
- `save_images_as_files` (bool): Save images as external files (default: True)
- `images_scale` (int): Scale factor for generated images (1-3, default: 2)

**Example:**
```python
tool = ProcessFolderPipeline(
    folder_path="/path/to/documents",
    file_patterns=["*.pdf", "*.docx"],
    max_concurrent=5,
    annotate_images=True
)
result = tool.run()
```

### 2. ProcessSitemapPipeline

Process all documents from a website sitemap with full pipeline execution.

**Parameters:**
- `sitemap_url` (str): URL of the website sitemap
- `max_concurrent` (int): Number of concurrent pipelines (1-20, default: 10)
- `enable_chunking` (bool): Enable document chunking (default: True)
- `enable_embeddings` (bool): Enable vector embeddings (default: True)
- `annotate_images` (bool): Enable AI image annotation (default: True)
- `max_urls` (int): Maximum number of URLs to process (default: 100)

**Example:**
```python
tool = ProcessSitemapPipeline(
    sitemap_url="https://docs.example.com/sitemap.xml",
    max_concurrent=5,
    max_urls=50,
    annotate_images=True
)
result = tool.run()
```

### 3. ProcessMixedSources

Process documents from multiple sources (folders, URLs, sitemaps) in a single operation.

**Parameters:**
- `folder_paths` (List[str]): List of folder paths to process
- `urls` (List[str]): List of URLs to process
- `sitemap_urls` (List[str]): List of sitemap URLs to process
- `file_patterns` (List[str]): File patterns for folder processing
- `max_concurrent` (int): Number of concurrent pipelines (1-50, default: 10)
- `output_format` (str): Output format preference (default: "markdown")

**Example:**
```python
tool = ProcessMixedSources(
    folder_paths=["/local/docs", "/research/papers"],
    urls=["https://example.com/doc1.pdf"],
    sitemap_urls=["https://docs.example.com/sitemap.xml"],
    max_concurrent=8
)
result = tool.run()
```

### 4. ConvertSingleDocument

Process a single document through the complete pipeline.

**Parameters:**
- `input_source` (str): File path, URL, or base64 content
- `input_type` (str): Type of input ('file', 'url', 'base64', 'auto')
- `annotate_images` (bool): Enable AI image annotation (default: True)
- `save_images_as_files` (bool): Save images as external files (default: True)
- `enable_chunking` (bool): Enable document chunking (default: True)
- `enable_embeddings` (bool): Enable vector embeddings (default: True)
- `output_filename` (str): Custom output filename (optional)

**Example:**
```python
tool = ConvertSingleDocument(
    input_source="https://arxiv.org/pdf/2401.12345.pdf",
    input_type="url",
    annotate_images=True,
    save_images_as_files=True
)
result = tool.run()
```

### 5. BatchProcessDocuments

Process multiple documents with advanced batch management.

**Parameters:**
- `input_sources` (List[str]): List of file paths, URLs, or base64 content
- `max_workers` (int): Number of concurrent threads (1-20, default: 4)
- `batch_size` (int): Number of documents per batch (1-100, default: 10)
- `retry_failed` (bool): Retry failed documents (default: True)
- `max_retries` (int): Maximum number of retries (default: 2)
- `progress_callback` (str): Progress tracking method (default: "console")

**Example:**
```python
tool = BatchProcessDocuments(
    input_sources=[
        "/path/to/doc1.pdf",
        "https://example.com/doc2.html",
        "/path/to/doc3.docx"
    ],
    max_workers=6,
    batch_size=5,
    retry_failed=True
)
result = tool.run()
```

### 6. MonitorProcessingStatus

Monitor and report on active document processing operations.

**Parameters:**
- `operation_id` (str): ID of the processing operation to monitor (optional)
- `include_details` (bool): Include detailed progress information (default: False)
- `refresh_interval` (int): Refresh interval in seconds (1-60, default: 5)

**Example:**
```python
tool = MonitorProcessingStatus(
    operation_id="batch_001",
    include_details=True,
    refresh_interval=10
)
result = tool.run()
```

### 7. ConfigureProcessingPipeline

Configure and customize the document processing pipeline.

**Parameters:**
- `pipeline_config` (dict): Pipeline configuration parameters
- `stage_settings` (dict): Individual stage configuration
- `concurrency_settings` (dict): Concurrency and resource settings
- `output_settings` (dict): Output format and storage settings

**Example:**
```python
tool = ConfigureProcessingPipeline(
    pipeline_config={
        "enable_chunking": True,
        "chunk_size": 1500,
        "chunk_overlap": 300
    },
    concurrency_settings={
        "max_concurrent": 15,
        "max_workers": 6
    },
    output_settings={
        "format": "markdown",
        "save_images_as_files": False
    }
)
result = tool.run()
```

### 8. ExportProcessingResults

Export processed document results in various formats.

**Parameters:**
- `operation_id` (str): ID of the processing operation
- `export_format` (str): Export format ('json', 'csv', 'markdown', 'html')
- `include_embeddings` (bool): Include vector embeddings (default: False)
- `include_images` (bool): Include image references (default: True)
- `output_path` (str): Path for exported files (optional)
- `include_metadata` (bool): Include processing metadata (default: True)

**Example:**
```python
tool = ExportProcessingResults(
    operation_id="batch_001",
    export_format="json",
    include_embeddings=False,
    include_images=True,
    include_metadata=True
)
result = tool.run()
```

## Examples

### Example 1: Process a Research Paper Collection

```python
# Process all PDFs in a research papers folder
tool = ProcessFolderPipeline(
    folder_path="/research/papers",
    file_patterns=["*.pdf"],
    max_concurrent=5,
    annotate_images=True,
    save_images_as_files=True,
    images_scale=2
)

result = tool.run()
print(f"Processed {result['successful_documents']}/{result['total_documents']} papers")
```

### Example 2: Process a Documentation Website

```python
# Process all pages from a documentation sitemap
tool = ProcessSitemapPipeline(
    sitemap_url="https://docs.example.com/sitemap.xml",
    max_concurrent=8,
    max_urls=100,
    annotate_images=True,
    enable_chunking=True,
    enable_embeddings=True
)

result = tool.run()
print(f"Successfully processed {result['successful_documents']} documentation pages")
```

### Example 3: Mixed Source Processing

```python
# Process documents from multiple sources
tool = ProcessMixedSources(
    folder_paths=["/local/docs", "/downloads"],
    urls=["https://example.com/important.pdf"],
    sitemap_urls=["https://docs.example.com/sitemap.xml"],
    file_patterns=["*.pdf", "*.html", "*.docx"],
    max_concurrent=10,
    annotate_images=True
)

result = tool.run()
print(f"Mixed processing completed: {result['successful_documents']} documents processed")
```

### Example 4: Batch Processing with Monitoring

```python
# Process multiple documents with monitoring
tool = BatchProcessDocuments(
    input_sources=[
        "/docs/doc1.pdf",
        "/docs/doc2.html",
        "https://example.com/doc3.pdf"
    ],
    max_workers=4,
    batch_size=3,
    retry_failed=True,
    progress_callback="detailed"
)

result = tool.run()

# Monitor the processing
monitor = MonitorProcessingStatus(
    operation_id=result.get("batch_id"),
    include_details=True
)
status = monitor.run()
print(f"Processing status: {status['summary']['overall_success_rate']}% success rate")
```

## Architecture

### Pipeline Stages

The Sage Oracle agent uses a multi-stage pipeline architecture:

1. **Input Acquisition**: Identify documents from specified sources
2. **Document Conversion**: Convert documents to structured markdown using Docling
3. **Image Processing**: Extract and optionally annotate images
4. **Document Chunking**: Break documents into semantically meaningful chunks
5. **Vector Embedding**: Generate embeddings for semantic search
6. **Data Storage**: Store processed content and metadata

### Concurrency Management

- **Controlled Concurrency**: Uses semaphore-based limiting to prevent resource exhaustion
- **Error Isolation**: Individual document failures don't affect batch processing
- **Progress Tracking**: Real-time monitoring of pipeline execution
- **Resource Management**: Optimized thread usage based on system capabilities

### Input Source Abstraction

- **BaseInputSource**: Abstract interface for different input types
- **FolderInputSource**: Process documents from local folders
- **URLInputSource**: Process documents from URLs and sitemaps
- **MixedInputSource**: Combine multiple input sources in single batch

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ImportError: attempted relative import with no known parent package
```
**Solution**: The tools are designed to work within the Agency Swarm framework. Use them through the agent interface rather than running them directly.

#### 2. OpenAI API Errors
```
Error: OPENAI_API_KEY environment variable is required
```
**Solution**: Ensure your OpenAI API key is set in the `.env` file:
```env
OPENAI_API_KEY=your_api_key_here
```

#### 3. Unicode Encoding Errors
```
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution**: This is a Windows console issue. The tools handle Unicode internally, but console output may have issues. Use the agent interface for better Unicode support.

#### 4. Memory Issues
```
OutOfMemoryError: CUDA out of memory
```
**Solution**: Reduce `max_concurrent` and `max_workers` parameters, or process documents in smaller batches.

#### 5. Network Timeouts
```
Error: Network timeout during processing
```
**Solution**: Increase timeout values in the configuration or reduce `max_concurrent` for web-based processing.

### Debug Mode

Enable detailed logging by setting environment variables:
```env
PYTHONPATH=.
PYTHONUNBUFFERED=1
```

### Performance Monitoring

Use the MonitorProcessingStatus tool to track performance:
```python
monitor = MonitorProcessingStatus(include_details=True)
status = monitor.run()
print(f"System metrics: {status['system_metrics']}")
```

## Performance Tips

### Optimization Strategies

1. **Concurrency Tuning**:
   - Start with `max_concurrent=4-8` and adjust based on system performance
   - Monitor CPU and memory usage during processing
   - Reduce concurrency if system becomes unresponsive

2. **Batch Size Optimization**:
   - Use smaller batch sizes (5-10) for large documents
   - Use larger batch sizes (20-50) for small documents
   - Monitor processing time per document

3. **Image Processing**:
   - Set `images_scale=1` for faster processing
   - Set `images_scale=3` for higher quality (slower)
   - Disable image annotation if not needed

4. **Memory Management**:
   - Process documents in smaller batches for large collections
   - Use `save_images_as_files=True` to reduce memory usage
   - Monitor memory usage with system tools

### Recommended Settings

#### For High-Volume Processing
```python
tool = ProcessFolderPipeline(
    max_concurrent=8,
    annotate_images=False,  # Disable for speed
    save_images_as_files=True,
    images_scale=1
)
```

#### For High-Quality Processing
```python
tool = ProcessFolderPipeline(
    max_concurrent=4,
    annotate_images=True,
    save_images_as_files=True,
    images_scale=3
)
```

#### For Web Processing
```python
tool = ProcessSitemapPipeline(
    max_concurrent=5,  # Lower for web sources
    max_urls=50,       # Limit for testing
    annotate_images=True
)
```

## Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review the tool reference for parameter details
3. Test with smaller datasets first
4. Monitor system resources during processing
5. Use the monitoring tools to identify bottlenecks

The Sage Oracle agent is designed to be robust and handle various edge cases, but proper configuration and monitoring are essential for optimal performance.
