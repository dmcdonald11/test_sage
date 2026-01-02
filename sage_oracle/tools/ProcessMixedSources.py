"""
Process documents from multiple sources (folders, URLs, sitemaps) in a single operation.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import json
import asyncio
from pathlib import Path

# Import our shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.docling_processor import DoclingProcessor
from utils.input_sources.folder_input_source import FolderInputSource
from utils.input_sources.url_input_source import URLInputSource
from utils.concurrency.batch_processor import BatchProcessor

class ProcessMixedSources(BaseTool):
    """
    Process documents from multiple sources (folders, URLs, sitemaps) in a single operation, 
    providing unified processing capabilities for diverse input types.
    """
    
    folder_paths: List[str] = Field(
        default=[],
        description="List of folder paths to process"
    )
    
    urls: List[str] = Field(
        default=[],
        description="List of URLs to process"
    )
    
    sitemap_urls: List[str] = Field(
        default=[],
        description="List of sitemap URLs to process"
    )
    
    file_patterns: List[str] = Field(
        default=["*.pdf", "*.html", "*.docx", "*.md"],
        description="File patterns for folder processing"
    )
    
    max_concurrent: int = Field(
        default=10,
        description="Number of concurrent pipelines (1-50)"
    )
    
    output_format: str = Field(
        default="markdown",
        description="Output format preference (markdown, json, html)"
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

    def run(self):
        """
        Execute mixed-source document processing pipeline.
        """
        try:
            # Step 1: Validate inputs
            if not any([self.folder_paths, self.urls, self.sitemap_urls]):
                return json.dumps({
                    "success": False,
                    "error": "At least one input source must be provided (folder_paths, urls, or sitemap_urls)"
                }, indent=2)
            
            if not (1 <= self.max_concurrent <= 50):
                return json.dumps({
                    "success": False,
                    "error": "max_concurrent must be between 1 and 50"
                }, indent=2)
            
            # Step 2: Run async processing
            result = asyncio.run(self._process_mixed_sources_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    async def _process_mixed_sources_async(self) -> Dict[str, Any]:
        """Asynchronous mixed-source processing implementation"""
        
        all_documents = []
        source_info = {
            "folders": [],
            "urls": [],
            "sitemaps": []
        }
        
        # Step 1: Process folder sources
        for folder_path in self.folder_paths:
            try:
                input_source = FolderInputSource(
                    folder_path=folder_path,
                    file_patterns=self.file_patterns
                )
                documents = await input_source.get_documents()
                all_documents.extend(documents)
                
                source_info["folders"].append({
                    "path": folder_path,
                    "document_count": len(documents),
                    "patterns": self.file_patterns
                })
            except Exception as e:
                source_info["folders"].append({
                    "path": folder_path,
                    "error": str(e),
                    "document_count": 0
                })
        
        # Step 2: Process URL sources
        if self.urls:
            try:
                input_source = URLInputSource(urls=self.urls)
                documents = await input_source.get_documents()
                all_documents.extend(documents)
                
                source_info["urls"].append({
                    "urls": self.urls,
                    "document_count": len(documents)
                })
            except Exception as e:
                source_info["urls"].append({
                    "urls": self.urls,
                    "error": str(e),
                    "document_count": 0
                })
        
        # Step 3: Process sitemap sources
        for sitemap_url in self.sitemap_urls:
            try:
                input_source = URLInputSource(sitemap_url=sitemap_url)
                documents = await input_source.get_documents()
                all_documents.extend(documents)
                
                source_info["sitemaps"].append({
                    "url": sitemap_url,
                    "document_count": len(documents)
                })
            except Exception as e:
                source_info["sitemaps"].append({
                    "url": sitemap_url,
                    "error": str(e),
                    "document_count": 0
                })
        
        if not all_documents:
            return {
                "success": False,
                "error": "No documents found in any of the provided sources",
                "source_info": source_info
            }
        
        # Step 4: Create processor and batch processor
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files,
            max_workers=self.max_concurrent
        )
        
        batch_processor = BatchProcessor(max_concurrent=self.max_concurrent)
        
        # Step 5: Process all documents
        batch_result = await batch_processor.process_documents(
            documents=all_documents,
            processor_func=self._process_single_document,
            batch_id="mixed_sources"
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
                        base_filename=self._get_base_filename(result.source)
                    )
                    
                    results.append({
                        "source": result.source,
                        "source_type": doc_result.get("input_type", "unknown"),
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
            "source_info": source_info,
            "total_documents": batch_result.total_documents,
            "successful_documents": batch_result.successful_documents,
            "failed_documents": batch_result.failed_documents,
            "total_processing_time": batch_result.processing_time,
            "output_format": self.output_format,
            "annotate_images": self.annotate_images,
            "save_images_as_files": self.save_images_as_files,
            "max_concurrent": self.max_concurrent,
            "results": results,
            "message": f"Processed {batch_result.successful_documents}/{batch_result.total_documents} documents from mixed sources successfully"
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
    
    def _get_base_filename(self, source: str) -> str:
        """Get a base filename from a source path or URL"""
        from urllib.parse import urlparse
        import re
        
        # If it's a file path
        if source.startswith('/') or '\\' in source or Path(source).exists():
            return Path(source).stem
        
        # If it's a URL
        if source.startswith(('http://', 'https://')):
            parsed = urlparse(source)
            path = parsed.path
            
            if path:
                filename = path.split('/')[-1]
                if filename:
                    filename = filename.split('.')[0]
                    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
            
            # Fallback to domain name
            domain = parsed.netloc.replace('www.', '')
            return re.sub(r'[^a-zA-Z0-9_-]', '_', domain)
        
        # Fallback
        return re.sub(r'[^a-zA-Z0-9_-]', '_', source)


if __name__ == "__main__":
    # Test the tool
    print("Testing ProcessMixedSources...")
    
    tool = ProcessMixedSources(
        folder_paths=["."],
        file_patterns=["*.md"],
        max_concurrent=2,
        annotate_images=False,
        save_images_as_files=False
    )
    
    result = tool.run()
    print("Result:")
    print(result)
