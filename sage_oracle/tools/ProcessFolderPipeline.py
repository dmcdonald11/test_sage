"""
Process all documents in a specified folder with concurrent execution.
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
from utils.concurrency.batch_processor import BatchProcessor

class ProcessFolderPipeline(BaseTool):
    """
    Process all documents in a specified folder with concurrent execution, supporting 
    multiple file formats and providing comprehensive document processing capabilities.
    """
    
    folder_path: str = Field(
        ..., 
        description="Path to folder containing documents to process"
    )
    
    file_patterns: List[str] = Field(
        default=["*.pdf", "*.html", "*.docx", "*.md"],
        description="File patterns to process (e.g., ['*.pdf', '*.html', '*.docx'])"
    )
    
    max_concurrent: int = Field(
        default=10,
        description="Number of concurrent pipelines (1-50)"
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
        Execute folder-based document processing pipeline.
        """
        try:
            # Step 1: Validate inputs
            if not Path(self.folder_path).exists():
                return json.dumps({
                    "success": False,
                    "error": f"Folder not found: {self.folder_path}"
                }, indent=2)
            
            if not Path(self.folder_path).is_dir():
                return json.dumps({
                    "success": False,
                    "error": f"Path is not a directory: {self.folder_path}"
                }, indent=2)
            
            if not (1 <= self.max_concurrent <= 50):
                return json.dumps({
                    "success": False,
                    "error": "max_concurrent must be between 1 and 50"
                }, indent=2)
            
            # Step 2: Run async processing
            result = asyncio.run(self._process_folder_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    async def _process_folder_async(self) -> Dict[str, Any]:
        """Asynchronous folder processing implementation"""
        
        # Step 1: Create input source
        input_source = FolderInputSource(
            folder_path=self.folder_path,
            file_patterns=self.file_patterns
        )
        
        # Step 2: Get documents to process
        documents = await input_source.get_documents()
        
        if not documents:
            return {
                "success": False,
                "error": f"No documents found in folder {self.folder_path} matching patterns {self.file_patterns}"
            }
        
        # Step 3: Create processor and batch processor
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files,
            max_workers=self.max_concurrent
        )
        
        batch_processor = BatchProcessor(max_concurrent=self.max_concurrent)
        
        # Step 4: Process documents
        batch_result = await batch_processor.process_documents(
            documents=documents,
            processor_func=self._process_single_document,
            batch_id=f"folder_{Path(self.folder_path).name}"
        )
        
        # Step 5: Prepare results
        results = []
        for result in batch_result.results:
            if result.success:
                # Save the markdown output
                doc_result = result.result
                if doc_result.get("success"):
                    save_result = processor.save_markdown(
                        document=doc_result["document"],
                        output_path="",  # Will be determined by save_markdown
                        base_filename=Path(result.source).stem
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
        
        # Step 6: Return comprehensive results
        return {
            "success": True,
            "folder_path": self.folder_path,
            "file_patterns": self.file_patterns,
            "total_documents": batch_result.total_documents,
            "successful_documents": batch_result.successful_documents,
            "failed_documents": batch_result.failed_documents,
            "total_processing_time": batch_result.processing_time,
            "annotate_images": self.annotate_images,
            "save_images_as_files": self.save_images_as_files,
            "max_concurrent": self.max_concurrent,
            "results": results,
            "message": f"Processed {batch_result.successful_documents}/{batch_result.total_documents} documents successfully"
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


if __name__ == "__main__":
    # Test the tool
    print("Testing ProcessFolderPipeline...")
    
    # Create a test folder if it doesn't exist
    test_folder = Path("test_documents")
    test_folder.mkdir(exist_ok=True)
    
    # Test with the current directory
    tool = ProcessFolderPipeline(
        folder_path=".",
        file_patterns=["*.md", "*.txt"],
        max_concurrent=2,
        annotate_images=False,
        save_images_as_files=False
    )
    
    result = tool.run()
    print("Result:")
    print(result)
