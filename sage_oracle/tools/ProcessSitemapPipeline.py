"""
Process all documents from a website sitemap with full pipeline execution.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import json
import asyncio
from urllib.parse import urlparse

# Import our shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.docling_processor import DoclingProcessor
from utils.input_sources.url_input_source import URLInputSource
from utils.concurrency.batch_processor import BatchProcessor

class ProcessSitemapPipeline(BaseTool):
    """
    Process all documents from a website sitemap with full pipeline execution, 
    including URL extraction, concurrent processing, and comprehensive storage.
    """
    
    sitemap_url: str = Field(
        ..., 
        description="URL of the website sitemap to process"
    )
    
    max_concurrent: int = Field(
        default=10,
        description="Number of concurrent pipelines (1-20 for web processing)"
    )
    
    enable_chunking: bool = Field(
        default=True,
        description="Enable document chunking for optimal retrieval"
    )
    
    enable_embeddings: bool = Field(
        default=True,
        description="Enable vector embeddings for semantic search"
    )
    
    annotate_images: bool = Field(
        default=True,
        description="Enable AI image annotation using OpenAI API"
    )
    
    save_images_as_files: bool = Field(
        default=True,
        description="Save images as external files instead of embedding inline"
    )
    
    images_scale: int = Field(
        default=2,
        description="Scale factor for generated images (1-3, higher = better quality)"
    )
    
    max_urls: int = Field(
        default=100,
        description="Maximum number of URLs to process from sitemap"
    )

    def run(self):
        """
        Execute sitemap-based document processing pipeline.
        """
        try:
            # Step 1: Validate inputs
            if not self.sitemap_url.startswith(('http://', 'https://')):
                return json.dumps({
                    "success": False,
                    "error": f"Invalid sitemap URL: {self.sitemap_url}"
                }, indent=2)
            
            if not (1 <= self.max_concurrent <= 20):
                return json.dumps({
                    "success": False,
                    "error": "max_concurrent must be between 1 and 20 for web processing"
                }, indent=2)
            
            # Step 2: Run async processing
            result = asyncio.run(self._process_sitemap_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    async def _process_sitemap_async(self) -> Dict[str, Any]:
        """Asynchronous sitemap processing implementation"""
        
        # Step 1: Create input source
        input_source = URLInputSource(sitemap_url=self.sitemap_url)
        
        # Step 2: Get documents to process
        documents = await input_source.get_documents()
        
        if not documents:
            return {
                "success": False,
                "error": f"No URLs found in sitemap: {self.sitemap_url}"
            }
        
        # Step 3: Limit URLs if specified
        if self.max_urls and len(documents) > self.max_urls:
            documents = documents[:self.max_urls]
        
        # Step 4: Create processor and batch processor
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files,
            max_workers=self.max_concurrent
        )
        
        batch_processor = BatchProcessor(max_concurrent=self.max_concurrent)
        
        # Step 5: Process documents
        batch_result = await batch_processor.process_documents(
            documents=documents,
            processor_func=self._process_single_document,
            batch_id=f"sitemap_{urlparse(self.sitemap_url).netloc}"
        )
        
        # Step 6: Prepare results
        results = []
        for result in batch_result.results:
            if result.success:
                # Save the markdown output
                doc_result = result.result
                if doc_result.get("success"):
                    save_result = processor.save_markdown(
                        document=doc_result["document"],
                        output_path="",  # Will be determined by save_markdown
                        base_filename=self._get_filename_from_url(result.source)
                    )
                    
                    results.append({
                        "source": result.source,
                        "success": True,
                        "markdown_path": save_result.get("output_path"),
                        "content_length": doc_result.get("content_length"),
                        "processing_time": result.processing_time
                    })
                else:
                    results.append({
                        "source": result.source,
                        "success": False,
                        "error": doc_result.get("error"),
                        "processing_time": result.processing_time
                    })
            else:
                results.append({
                    "source": result.source,
                    "success": False,
                    "error": result.error,
                    "processing_time": result.processing_time
                })
        
        # Step 7: Return comprehensive results
        return {
            "success": True,
            "sitemap_url": self.sitemap_url,
            "total_documents": batch_result.total_documents,
            "successful_documents": batch_result.successful_documents,
            "failed_documents": batch_result.failed_documents,
            "total_processing_time": batch_result.processing_time,
            "enable_chunking": self.enable_chunking,
            "enable_embeddings": self.enable_embeddings,
            "annotate_images": self.annotate_images,
            "save_images_as_files": self.save_images_as_files,
            "max_concurrent": self.max_concurrent,
            "results": results,
            "message": f"Processed {batch_result.successful_documents}/{batch_result.total_documents} documents from sitemap successfully"
        }
    
    async def _process_single_document(self, document) -> Dict[str, Any]:
        """Process a single document"""
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files
        )
        
        return await processor.convert_document(
            input_source=document.source,
            input_type=document.source_type
        )
    
    def _get_filename_from_url(self, url: str) -> str:
        """Extract a filename from a URL"""
        from urllib.parse import urlparse
        import re
        
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove leading slash and get the last part
        if path:
            filename = path.split('/')[-1]
            if filename:
                # Remove file extension and clean up
                filename = filename.split('.')[0]
                # Remove non-alphanumeric characters
                filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
                return filename
        
        # Fallback to domain name
        domain = parsed.netloc.replace('www.', '')
        return re.sub(r'[^a-zA-Z0-9_-]', '_', domain)


if __name__ == "__main__":
    # Test the tool
    print("Testing ProcessSitemapPipeline...")
    
    tool = ProcessSitemapPipeline(
        sitemap_url="https://docs.crawl4ai.com",
        max_concurrent=2,
        max_urls=5,  # Limit for testing
        annotate_images=False,
        save_images_as_files=False
    )
    
    result = tool.run()
    print("Result:")
    print(result)
