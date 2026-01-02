from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Optional, Any
import os
import json
import asyncio
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()


class CrawlAndProcessUrl(BaseTool):
    """
    Crawls a URL, discovers and parses documents using Docling, applies hybrid chunking,
    generates embeddings, and stores the results in PostgreSQL with pgvector.
    
    This tool supports multiple document formats including PDF, DOCX, XLSX, PPTX, HTML,
    Markdown, Images, Audio, CSV, XML, VTT, and JSON documents.
    """
    
    url: str = Field(
        ..., 
        description="The URL to crawl and process. Must be a valid HTTP/HTTPS URL."
    )
    
    embedding_model: Optional[str] = Field(
        default=None,
        description="Override the default embedding model. Examples: 'sentence-transformers/all-MiniLM-L6-v2', 'BAAI/bge-small-en-v1.5'"
    )
    
    max_tokens: Optional[int] = Field(
        default=512,
        description="Maximum tokens per chunk for the hybrid chunker (default: 512)"
    )
    
    include_types: Optional[List[str]] = Field(
        default=None,
        description="Filter document types to process. E.g., ['pdf', 'html', 'markdown']. If None, processes all types."
    )
    
    collection_name: Optional[str] = Field(
        default="default_collection",
        description="Collection/table name for organizing chunks in the vector database"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata to store with chunks"
    )
    
    def run(self):
        """
        Execute the full document processing pipeline.
        """
        try:
            # Run the async processing pipeline
            result = asyncio.run(self._process_url())
            return json.dumps(result, indent=2)
        except Exception as e:
            error_result = {
                "success": False,
                "error": type(e).__name__,
                "message": str(e),
                "url": self.url
            }
            return json.dumps(error_result, indent=2)
    
    async def _process_url(self):
        """
        Main async processing pipeline.
        """
        # Step 1: Crawl URL and extract content
        crawl_result = await self._crawl_url()
        
        # Step 2: Discover documents
        documents = await self._discover_documents(crawl_result)
        
        # Step 3: Process each document
        all_chunks = []
        processed_docs = []
        
        for doc in documents:
            try:
                # Parse document with Docling
                parsed_doc = await self._parse_document(doc)
                
                # Chunk the document
                chunks = await self._chunk_document(parsed_doc)
                
                # Generate embeddings
                chunks_with_embeddings = await self._generate_embeddings(chunks)
                
                all_chunks.extend(chunks_with_embeddings)
                
                processed_docs.append({
                    "url": doc["url"],
                    "type": doc["type"],
                    "chunks": len(chunks),
                    "tokens": sum(c["num_tokens"] for c in chunks)
                })
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Error processing {doc['url']}: {str(e)}")
                continue
        
        # Step 4: Store in PostgreSQL
        if all_chunks:
            storage_result = await self._store_in_postgres(all_chunks)
        else:
            storage_result = {"records_inserted": 0}
        
        # Step 5: Return success response
        from .utils.model_loader import get_model_config
        _, embedding_model_name, model_source, _ = get_model_config()
        
        return {
            "success": True,
            "url": self.url,
            "documents_processed": len(processed_docs),
            "documents_list": processed_docs,
            "total_chunks": len(all_chunks),
            "total_tokens": sum(c["num_tokens"] for c in all_chunks),
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model or embedding_model_name,
            "model_source": model_source,
            "storage": {
                "database": "postgresql",
                "table": "document_chunks",
                **storage_result
            }
        }
    
    async def _crawl_url(self):
        """
        Crawl the URL and extract HTML content using crawl4ai or requests+BeautifulSoup.
        """
        try:
            from crawl4ai import AsyncWebCrawler
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=self.url)
                return {
                    "html": result.html,
                    "markdown": result.markdown,
                    "links": result.links.get("external", []) + result.links.get("internal", []) if hasattr(result, 'links') and result.links else [],
                    "success": result.success
                }
        except ImportError:
            # Fallback to requests + BeautifulSoup
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract all links
            links = []
            for a_tag in soup.find_all('a', href=True):
                absolute_url = urljoin(self.url, a_tag['href'])
                links.append(absolute_url)
            
            return {
                "html": str(soup),
                "markdown": soup.get_text(),
                "links": links,
                "success": True
            }
    
    async def _discover_documents(self, crawl_result):
        """
        Discover and classify documents from crawled content.
        """
        from bs4 import BeautifulSoup
        
        documents = []
        
        # Document type extensions mapping
        doc_types = {
            "pdf": [".pdf"],
            "docx": [".docx", ".doc"],
            "xlsx": [".xlsx", ".xls"],
            "pptx": [".pptx", ".ppt"],
            "markdown": [".md", ".markdown"],
            "html": [".html", ".htm", ".xhtml"],
            "image": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"],
            "audio": [".mp3", ".wav", ".ogg", ".m4a", ".flac"],
            "csv": [".csv"],
            "xml": [".xml"],
            "vtt": [".vtt"],
            "json": [".json"]
        }
        
        # Add main page HTML as first document
        documents.append({
            "url": self.url,
            "type": "html",
            "content": crawl_result["html"]
        })
        
        # Parse HTML to find document links
        # Handle different HTML formats from crawler
        html_for_parsing = crawl_result["html"]
        if isinstance(html_for_parsing, dict):
            # If it's a dict, try to extract HTML string
            html_for_parsing = html_for_parsing.get("html") or html_for_parsing.get("content") or str(html_for_parsing)
        soup = BeautifulSoup(html_for_parsing, 'html.parser')
        
        # Find all links
        for link in crawl_result.get("links", []):
            # Handle different link formats from Crawl4AI
            if isinstance(link, dict):
                # Extract URL from dict (could be 'href', 'url', or other keys)
                link_url = link.get("href") or link.get("url") or link.get("link") or str(link)
            elif isinstance(link, str):
                link_url = link
            else:
                # Skip invalid link formats
                continue
            
            parsed = urlparse(link_url)
            path = parsed.path.lower()
            
            # Classify by extension
            for doc_type, extensions in doc_types.items():
                if any(path.endswith(ext) for ext in extensions):
                    # Filter by include_types if specified
                    if self.include_types and doc_type not in self.include_types:
                        continue
                    
                    documents.append({
                        "url": link_url,
                        "type": doc_type,
                        "content": None  # Will be downloaded later
                    })
                    break
        
        # Find embedded images
        for img in soup.find_all('img', src=True):
            img_url = urljoin(self.url, img['src'])
            if self.include_types is None or "image" in self.include_types:
                documents.append({
                    "url": img_url,
                    "type": "image",
                    "content": None
                })
        
        return documents
    
    async def _parse_document(self, doc):
        """
        Parse document using Docling.
        """
        from docling.document_converter import DocumentConverter
        from docling.datamodel.base_models import InputFormat
        import aiohttp
        import tempfile
        
        # Map document types to Docling InputFormat
        # Note: Only include formats that exist in the installed Docling version
        format_mapping = {
            "pdf": InputFormat.PDF,
            "docx": InputFormat.DOCX,
            "html": InputFormat.HTML,
            "image": InputFormat.IMAGE,
        }
        
        # Add optional formats if they exist (version-dependent)
        try:
            format_mapping["xlsx"] = InputFormat.XLSX
            format_mapping["pptx"] = InputFormat.PPTX
        except AttributeError:
            pass
        
        try:
            format_mapping["markdown"] = InputFormat.MD
        except AttributeError:
            pass
        
        try:
            format_mapping["audio"] = InputFormat.AUDIO
        except AttributeError:
            pass
        
        try:
            format_mapping["csv"] = InputFormat.CSV
        except AttributeError:
            pass
        
        try:
            format_mapping["xml"] = InputFormat.XML
        except AttributeError:
            pass
        
        try:
            format_mapping["vtt"] = InputFormat.VTT
        except AttributeError:
            pass
        
        try:
            format_mapping["json"] = InputFormat.JSON_DOCLING
        except AttributeError:
            pass
        
        # Skip unsupported document types
        if doc["type"] not in format_mapping:
            raise ValueError(f"Document type '{doc['type']}' not supported by installed Docling version")
        
        # Get content if not already available
        if doc["content"] is None and doc["type"] != "html":
            async with aiohttp.ClientSession() as session:
                async with session.get(doc["url"]) as response:
                    doc["content"] = await response.read()
        
        # Create converter
        converter = DocumentConverter()
        
        # For HTML with existing content, save to temp file
        if doc["type"] == "html" and doc["content"]:
            # Handle different content types from crawler
            if isinstance(doc["content"], str):
                html_content = doc["content"]
            elif isinstance(doc["content"], bytes):
                html_content = doc["content"].decode('utf-8')
            elif isinstance(doc["content"], dict):
                # If Crawl4AI returns a dict, it might have an 'html' or 'content' key
                html_content = doc["content"].get("html") or doc["content"].get("content") or str(doc["content"])
            else:
                # Fallback: convert to string
                html_content = str(doc["content"])
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode='w', encoding='utf-8') as tmp:
                tmp.write(html_content)
                tmp_path = tmp.name
            
            # Convert document
            result = converter.convert(tmp_path)
            os.unlink(tmp_path)  # Clean up temp file
        
        # For other document types with binary content
        elif doc["content"] and isinstance(doc["content"], bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc['type']}") as tmp:
                tmp.write(doc["content"])
                tmp_path = tmp.name
            
            # Convert document
            result = converter.convert(tmp_path)
            os.unlink(tmp_path)  # Clean up temp file
        
        # For URLs without content (download on the fly)
        else:
            result = converter.convert(doc["url"])
        
        return {
            "docling_doc": result.document,
            "source_url": doc["url"],
            "doc_type": doc["type"]
        }
    
    async def _chunk_document(self, parsed_doc):
        """
        Apply hybrid chunking to the parsed document.
        """
        from docling.chunking import HybridChunker
        from .utils.model_loader import get_tokenizer, get_model_config
        
        # Get model configuration from environment
        tokenizer_model, embedding_model, model_source, max_chunk_tokens = get_model_config()
        
        # Use override if provided, otherwise use env config
        if self.embedding_model:
            tokenizer_model = self.embedding_model
        else:
            tokenizer_model = tokenizer_model
        
        # Create chunker (v2 API uses default initialization)
        chunker = HybridChunker()
        
        # Load tokenizer based on MODEL_SOURCE
        tokenizer = get_tokenizer(model_name=tokenizer_model, model_source=model_source)
        
        chunks = []
        for chunk in chunker.chunk(dl_doc=parsed_doc["docling_doc"]):
            # Tokenize the chunk text
            tokens = tokenizer.encode(chunk.text, add_special_tokens=False, truncation=True, max_length=max_chunk_tokens)
            num_tokens = len(tokens)
            
            # Decode back to text if we truncated
            if num_tokens >= max_chunk_tokens:
                chunk_text = tokenizer.decode(tokens, skip_special_tokens=True)
            else:
                chunk_text = chunk.text
            
            chunks.append({
                "text": chunk_text,
                "num_tokens": num_tokens,
                "doc_items_refs": [str(item) for item in chunk.meta.doc_items] if hasattr(chunk.meta, 'doc_items') else [],
                "headings": chunk.meta.headings if hasattr(chunk.meta, 'headings') else [],
                "source_url": parsed_doc["source_url"],
                "source_document": parsed_doc["docling_doc"].name if hasattr(parsed_doc["docling_doc"], 'name') else parsed_doc["source_url"],
                "doc_type": parsed_doc["doc_type"]
            })
        
        return chunks
    
    async def _generate_embeddings(self, chunks):
        """
        Generate embeddings for chunks.
        """
        from .utils.model_loader import get_embedding_model, get_tokenizer, get_model_config
        
        # Get model configuration from environment
        tokenizer_model, embedding_model_name, model_source, max_chunk_tokens = get_model_config()
        
        # Use override if provided, otherwise use env config
        if self.embedding_model:
            embedding_model_name = self.embedding_model
        
        # Load embedding model based on MODEL_SOURCE
        model = get_embedding_model(model_name=embedding_model_name, model_source=model_source)
        
        # Get the tokenizer for proper truncation (use the same model source)
        tokenizer = get_tokenizer(model_name=embedding_model_name, model_source=model_source)
        
        # Truncate all texts to max_chunk_tokens BEFORE encoding
        truncated_texts = []
        for chunk in chunks:
            # Tokenize with truncation
            tokens = tokenizer.encode(
                chunk["text"], 
                add_special_tokens=True,  # Add special tokens for embedding
                truncation=True, 
                max_length=max_chunk_tokens
            )
            # Decode back to text
            truncated_text = tokenizer.decode(tokens, skip_special_tokens=True)
            truncated_texts.append(truncated_text)
        
        # Generate embeddings with properly truncated texts
        embeddings = model.encode(
            truncated_texts, 
            show_progress_bar=False,
            batch_size=32,
            normalize_embeddings=True,  # Normalize for cosine similarity
            convert_to_numpy=True
        )
        
        # Combine chunks with embeddings
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            chunks_with_embeddings.append({
                **chunk,
                "embedding": embedding.tolist(),
                "embedding_model": embedding_model_name,
                "embedding_dimension": len(embedding)
            })
        
        return chunks_with_embeddings
    
    async def _store_in_postgres(self, chunks_with_embeddings):
        """
        Store chunks with embeddings in PostgreSQL.
        """
        import asyncpg
        from pgvector.asyncpg import register_vector
        
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "vector_store"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        
        try:
            # Register pgvector type
            await register_vector(conn)
            
            # Create table if not exists
            embedding_dim = chunks_with_embeddings[0]["embedding_dimension"]
            await conn.execute(f"""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    collection_name TEXT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    num_tokens INTEGER NOT NULL,
                    doc_items_refs JSONB,
                    headings JSONB,
                    source_url TEXT,
                    source_document TEXT,
                    doc_type TEXT,
                    embedding vector({embedding_dim}),
                    embedding_model TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
                ON document_chunks USING ivfflat (embedding vector_cosine_ops);
                
                CREATE INDEX IF NOT EXISTS idx_document_chunks_collection 
                ON document_chunks (collection_name);
            """)
            
            # Insert chunks
            records_inserted = 0
            for chunk in chunks_with_embeddings:
                await conn.execute(
                    """
                    INSERT INTO document_chunks (
                        collection_name, chunk_text, num_tokens, 
                        doc_items_refs, headings, source_url, 
                        source_document, doc_type, embedding, 
                        embedding_model, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    self.collection_name,
                    chunk["text"],
                    chunk["num_tokens"],
                    json.dumps(chunk.get("doc_items_refs", [])),
                    json.dumps(chunk.get("headings", [])),
                    chunk["source_url"],
                    chunk["source_document"],
                    chunk.get("doc_type", "unknown"),
                    chunk["embedding"],
                    chunk["embedding_model"],
                    json.dumps({**self.metadata, "original_url": self.url}),
                )
                records_inserted += 1
            
            return {"records_inserted": records_inserted}
        
        finally:
            await conn.close()


if __name__ == "__main__":
    # Test the tool
    # Note: Requires PostgreSQL with pgvector to be running
    tool = CrawlAndProcessUrl(
        url="https://docling-project.github.io/docling/",
        collection_name="test_collection",
        max_tokens=512,
        metadata={"test": True}
    )
    
    print("Testing CrawlAndProcessUrl tool...")
    print("Note: This requires PostgreSQL with pgvector extension to be running.")
    print(tool.run())

