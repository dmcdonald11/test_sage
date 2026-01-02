"""
Process multiple documents with advanced batch management.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

# Import our shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.docling_processor import DoclingProcessor
from utils.concurrency.batch_processor import BatchProcessor

class BatchProcessDocuments(BaseTool):
    """
    Process multiple documents with advanced batch management, including retry logic, 
    progress tracking, and comprehensive error handling.
    """
    
    input_sources: List[str] = Field(
        ..., 
        description="List of file paths, URLs, or base64 content to process"
    )
    
    max_workers: int = Field(
        default=4,
        description="Number of concurrent threads (1-20)"
    )
    
    batch_size: int = Field(
        default=10,
        description="Number of documents per batch (1-100)"
    )
    
    retry_failed: bool = Field(
        default=True,
        description="Retry failed documents"
    )
    
    max_retries: int = Field(
        default=2,
        description="Maximum number of retries for failed documents"
    )
    
    progress_callback: str = Field(
        default="console",
        description="Progress tracking method (console, silent, detailed)"
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
        Execute batch document processing with advanced management.
        """
        try:
            # Step 1: Validate inputs
            if not self.input_sources:
                return json.dumps({
                    "success": False,
                    "error": "input_sources list must not be empty"
                }, indent=2)
            
            if not (1 <= self.max_workers <= 20):
                return json.dumps({
                    "success": False,
                    "error": "max_workers must be between 1 and 20"
                }, indent=2)
            
            if not (1 <= self.batch_size <= 100):
                return json.dumps({
                    "success": False,
                    "error": "batch_size must be between 1 and 100"
                }, indent=2)
            
            # Step 2: Run async processing
            result = asyncio.run(self._process_batch_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    async def _process_batch_async(self) -> Dict[str, Any]:
        """Asynchronous batch processing implementation"""
        
        start_time = datetime.now()
        total_documents = len(self.input_sources)
        
        # Step 1: Create processor and batch processor
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files,
            max_workers=self.max_workers
        )
        
        batch_processor = BatchProcessor(max_concurrent=self.max_workers)
        
        # Step 2: Process documents in batches
        all_results = []
        failed_documents = []
        
        for i in range(0, total_documents, self.batch_size):
            batch_sources = self.input_sources[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_documents + self.batch_size - 1) // self.batch_size
            
            if self.progress_callback in ["console", "detailed"]:
                print(f"Processing batch {batch_num}/{total_batches} ({len(batch_sources)} documents)")
            
            # Process batch
            batch_result = await batch_processor.process_documents(
                documents=batch_sources,
                processor_func=self._process_single_document,
                batch_id=f"batch_{batch_num}"
            )
            
            # Collect results
            for result in batch_result.results:
                if result.success:
                    all_results.append(result)
                else:
                    failed_documents.append(result)
            
            if self.progress_callback == "detailed":
                print(f"  Batch {batch_num} completed: {batch_result.successful_documents}/{batch_result.total_documents} successful")
        
        # Step 3: Retry failed documents if enabled
        if self.retry_failed and failed_documents:
            if self.progress_callback in ["console", "detailed"]:
                print(f"Retrying {len(failed_documents)} failed documents...")
            
            for retry_attempt in range(self.max_retries):
                if not failed_documents:
                    break
                
                retry_sources = [doc.source for doc in failed_documents]
                retry_result = await batch_processor.process_documents(
                    documents=retry_sources,
                    processor_func=self._process_single_document,
                    batch_id=f"retry_{retry_attempt + 1}"
                )
                
                # Update results
                new_failed = []
                for result in retry_result.results:
                    if result.success:
                        all_results.append(result)
                    else:
                        new_failed.append(result)
                
                failed_documents = new_failed
                
                if self.progress_callback == "detailed":
                    print(f"  Retry {retry_attempt + 1}: {retry_result.successful_documents}/{retry_result.total_documents} successful")
        
        # Step 4: Prepare final results
        end_time = datetime.now()
        total_processing_time = (end_time - start_time).total_seconds()
        
        successful_count = len(all_results)
        failed_count = len(failed_documents)
        
        # Step 5: Format results
        formatted_results = []
        for result in all_results:
            if result.success:
                doc_result = result.result
                if doc_result.get("success"):
                    formatted_results.append({
                        "source": result.source,
                        "success": True,
                        "content_length": doc_result.get("content_length"),
                        "processing_time": result.processing_time,
                        "input_type": doc_result.get("input_type", "unknown")
                    })
                else:
                    formatted_results.append({
                        "source": result.source,
                        "success": False,
                        "error": doc_result.get("error"),
                        "processing_time": result.processing_time
                    })
            else:
                formatted_results.append({
                    "source": result.source,
                    "success": False,
                    "error": result.error,
                    "processing_time": result.processing_time
                })
        
        # Add failed documents to results
        for result in failed_documents:
            formatted_results.append({
                "source": result.source,
                "success": False,
                "error": result.error,
                "processing_time": result.processing_time,
                "retry_failed": True
            })
        
        return {
            "success": True,
            "total_documents": total_documents,
            "successful_documents": successful_count,
            "failed_documents": failed_count,
            "total_processing_time": total_processing_time,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "retry_failed": self.retry_failed,
            "max_retries": self.max_retries,
            "annotate_images": self.annotate_images,
            "save_images_as_files": self.save_images_as_files,
            "results": formatted_results,
            "message": f"Batch processing completed: {successful_count}/{total_documents} documents successful"
        }
    
    async def _process_single_document(self, input_source: str) -> Dict[str, Any]:
        """Process a single document"""
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files
        )
        
        # Auto-detect input type
        if input_source.startswith(("http://", "https://")):
            input_type = "url"
        elif os.path.exists(input_source):
            input_type = "file"
        else:
            input_type = "base64"
        
        return await processor.convert_document(
            input_source=input_source,
            input_type=input_type
        )


if __name__ == "__main__":
    # Test the tool
    print("Testing BatchProcessDocuments...")
    
    tool = BatchProcessDocuments(
        input_sources=[
            "https://docs.crawl4ai.com",
            "https://example.com"
        ],
        max_workers=2,
        batch_size=2,
        annotate_images=False,
        save_images_as_files=False
    )
    
    result = tool.run()
    print("Result:")
    print(result)
