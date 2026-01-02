"""
Process a single document through the complete pipeline.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any
import json
import asyncio
import os
from pathlib import Path

# Import our shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.docling_processor import DoclingProcessor

class ConvertSingleDocument(BaseTool):
    """
    Process a single document through the complete pipeline, supporting various input types 
    and providing comprehensive processing capabilities.
    """
    
    input_source: str = Field(
        ..., 
        description="File path, URL, or base64 content to process"
    )
    
    input_type: str = Field(
        default="auto",
        description="Type of input: 'file', 'url', 'base64', or 'auto'"
    )
    
    annotate_images: bool = Field(
        default=True,
        description="Enable AI image annotation using OpenAI API"
    )
    
    save_images_as_files: bool = Field(
        default=True,
        description="Save images as external files instead of embedding inline"
    )
    
    enable_chunking: bool = Field(
        default=True,
        description="Enable document chunking for optimal retrieval"
    )
    
    enable_embeddings: bool = Field(
        default=True,
        description="Enable vector embeddings for semantic search"
    )
    
    images_scale: int = Field(
        default=2,
        description="Scale factor for generated images (1-3, higher = better quality)"
    )
    
    output_filename: str = Field(
        default="",
        description="Custom output filename (without extension). If not provided, will be auto-generated."
    )

    def run(self):
        """
        Execute single document processing pipeline.
        """
        try:
            # Step 1: Validate inputs
            if not self.input_source:
                return json.dumps({
                    "success": False,
                    "error": "input_source must be provided"
                }, indent=2)
            
            # Step 2: Run async processing
            result = asyncio.run(self._process_single_document_async())
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    async def _process_single_document_async(self) -> Dict[str, Any]:
        """Asynchronous single document processing implementation"""
        
        # Step 1: Auto-detect input type if needed
        input_type = self.input_type
        if input_type == "auto":
            if self.input_source.startswith(("http://", "https://")):
                input_type = "url"
            elif os.path.exists(self.input_source):
                input_type = "file"
            else:
                input_type = "base64"
        
        # Step 2: Validate input based on type
        if input_type == "file" and not os.path.exists(self.input_source):
            return {
                "success": False,
                "error": f"File not found: {self.input_source}"
            }
        
        if input_type == "url" and not self.input_source.startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": f"Invalid URL: {self.input_source}"
            }
        
        # Step 3: Create processor
        processor = DoclingProcessor(
            annotate_images=self.annotate_images,
            images_scale=self.images_scale,
            save_images_as_files=self.save_images_as_files,
            max_workers=1  # Single document processing
        )
        
        # Step 4: Process the document
        conversion_result = await processor.convert_document(
            input_source=self.input_source,
            input_type=input_type
        )
        
        if not conversion_result.get("success"):
            return conversion_result
        
        # Step 5: Save the markdown output
        base_filename = self.output_filename
        if not base_filename:
            base_filename = self._get_base_filename(self.input_source, input_type)
        
        save_result = processor.save_markdown(
            document=conversion_result["document"],
            output_path="",  # Will be determined by save_markdown
            base_filename=base_filename
        )
        
        if not save_result.get("success"):
            return {
                "success": False,
                "error": f"Failed to save document: {save_result.get('error')}",
                "conversion_result": conversion_result
            }
        
        # Step 6: Prepare comprehensive results
        result = {
            "success": True,
            "input_source": self.input_source,
            "input_type": input_type,
            "output_path": save_result.get("output_path"),
            "output_directory": save_result.get("output_directory"),
            "content_length": conversion_result.get("content_length"),
            "annotate_images": self.annotate_images,
            "save_images_as_files": self.save_images_as_files,
            "enable_chunking": self.enable_chunking,
            "enable_embeddings": self.enable_embeddings,
            "images_scale": self.images_scale,
            "message": f"Successfully processed document and saved to {save_result.get('output_path')}"
        }
        
        # Add preview of content
        if conversion_result.get("markdown_content"):
            content = conversion_result["markdown_content"]
            preview_length = min(500, len(content))
            result["preview"] = content[:preview_length]
            if len(content) > preview_length:
                result["preview"] += "..."
        
        return result
    
    def _get_base_filename(self, input_source: str, input_type: str) -> str:
        """Get a base filename from the input source"""
        from urllib.parse import urlparse
        import re
        from datetime import datetime
        
        if input_type == "file":
            return Path(input_source).stem
        elif input_type == "url":
            parsed = urlparse(input_source)
            path = parsed.path
            
            if path:
                filename = path.split('/')[-1]
                if filename:
                    filename = filename.split('.')[0]
                    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
            
            # Fallback to domain name
            domain = parsed.netloc.replace('www.', '')
            return re.sub(r'[^a-zA-Z0-9_-]', '_', domain)
        else:
            # For base64 or unknown types, use timestamp
            return f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


if __name__ == "__main__":
    # Test the tool
    print("Testing ConvertSingleDocument...")
    
    # Test with a URL
    tool = ConvertSingleDocument(
        input_source="https://docs.crawl4ai.com",
        input_type="url",
        annotate_images=False,
        save_images_as_files=False
    )
    
    result = tool.run()
    print("Result:")
    print(result.encode('utf-8', errors='ignore').decode('utf-8'))
