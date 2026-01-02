"""
Shared Docling processing logic for Sage Oracle Agent.
Handles document conversion, chunking, and embedding operations.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DoclingProcessor:
    """Thread-safe Docling processing with batch capabilities"""
    
    def __init__(self, 
                 annotate_images: bool = False,
                 images_scale: int = 2,
                 save_images_as_files: bool = False,
                 max_workers: int = 4):
        """
        Initialize the Docling processor with configuration options.
        
        Args:
            annotate_images: Whether to use AI for image annotation
            images_scale: Scale factor for generated images
            save_images_as_files: Whether to save images as external files
            max_workers: Maximum number of concurrent workers
        """
        self.annotate_images = annotate_images
        self.images_scale = images_scale
        self.save_images_as_files = save_images_as_files
        self.max_workers = max_workers
        self.executor = None
        
    async def convert_document(self, input_source: str, input_type: str = "auto") -> Dict[str, Any]:
        """
        Convert a single document using Docling.
        
        Args:
            input_source: File path, URL, or base64 content
            input_type: Type of input ('file', 'url', 'base64', 'auto')
            
        Returns:
            Dictionary with conversion results
        """
        try:
            # Step 1: Import Docling
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions
            from docling.document_converter import PdfFormatOption
            
            # Step 2: Auto-detect input type if needed
            if input_type == "auto":
                if input_source.startswith(("http://", "https://")):
                    input_type = "url"
                elif os.path.exists(input_source):
                    input_type = "file"
                else:
                    input_type = "base64"
            
            # Step 3: Configure converter based on options
            if self.annotate_images:
                # Get API key and model from environment
                api_key = os.getenv("OPENAI_API_KEY")
                image_model = os.getenv("IMAGE_MODEL", "gpt-4o-mini")
                
                if not api_key:
                    return {
                        "success": False,
                        "error": "OPENAI_API_KEY environment variable is required for image annotation but is not set"
                    }
                
                # Configure picture description options
                picture_desc_api_option = PictureDescriptionApiOptions(
                    url="https://api.openai.com/v1/chat/completions",
                    prompt="Describe this image in sentences in a single paragraph. Focus on key visual elements, data, diagrams, charts, or important details that would be useful for understanding the document.",
                    params={
                        "model": image_model,
                    },
                    headers={
                        "Authorization": f"Bearer {api_key}",
                    },
                    timeout=60,
                )
                
                # Configure PDF pipeline with image annotation
                pipeline_options = PdfPipelineOptions(
                    do_picture_description=True,
                    picture_description_options=picture_desc_api_option,
                    enable_remote_services=True,
                    generate_picture_images=True,
                    images_scale=self.images_scale,
                )
                
                # Create converter with custom pipeline options
                converter = DocumentConverter(
                    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
                )
            else:
                # Standard converter without image annotation
                converter = DocumentConverter()
            
            # Step 4: Convert the document
            conv_result = converter.convert(input_source)
            document = conv_result.document
            
            if not document:
                return {
                    "success": False,
                    "error": "Docling conversion produced no document"
                }
            
            # Step 5: Export to markdown
            if self.annotate_images:
                markdown_output = document.export_to_markdown(
                    mark_annotations=True,
                    include_annotations=True
                )
            else:
                markdown_output = document.export_to_markdown()
            
            # Step 6: Prepare result
            result = {
                "success": True,
                "input_source": input_source,
                "input_type": input_type,
                "markdown_content": markdown_output,
                "content_length": len(markdown_output),
                "annotated_images": self.annotate_images,
                "external_images": self.save_images_as_files,
                "conversion_result": conv_result,
                "document": document
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Docling conversion failed: {str(e)}"
            }
    
    async def convert_batch(self, input_sources: List[str]) -> List[Dict[str, Any]]:
        """
        Convert multiple documents concurrently.
        
        Args:
            input_sources: List of file paths, URLs, or base64 content
            
        Returns:
            List of conversion results
        """
        if not self.executor:
            self.executor = asyncio.get_event_loop().run_in_executor(None, lambda: None)
        
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, self._convert_single_sync, source)
            for source in input_sources
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _convert_single_sync(self, input_source: str) -> Dict[str, Any]:
        """Synchronous wrapper for single document conversion"""
        return asyncio.run(self.convert_document(input_source))
    
    def save_markdown(self, document, output_path: str, base_filename: str = None) -> Dict[str, Any]:
        """
        Save markdown output to file system.
        
        Args:
            document: Docling document object
            output_path: Path to save the markdown file
            base_filename: Base filename for the output
            
        Returns:
            Dictionary with save results
        """
        try:
            # Get output folder from environment variable or use default
            output_folder_name = os.getenv("MD_OUTPUT_FOLDER", "test_output")
            base_output_dir = Path(output_folder_name)
            base_output_dir.mkdir(exist_ok=True, parents=True)
            
            # Determine base filename
            if not base_filename:
                base_filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # If saving images as files, create a dedicated folder for the document
            if self.save_images_as_files:
                # Create document-specific folder
                output_dir = base_output_dir / base_filename
                output_dir.mkdir(exist_ok=True)
                output_filename = f"{base_filename}.md"
                output_path = output_dir / output_filename
            else:
                # For inline images, save directly in test_output
                output_dir = base_output_dir
                output_filename = f"{base_filename}.md"
                output_path = output_dir / output_filename
            
            # Save markdown based on image reference mode
            if self.save_images_as_files:
                try:
                    from docling_core.types.doc.document import ImageRefMode
                    
                    # Change to the document folder to avoid nested paths
                    original_cwd = os.getcwd()
                    try:
                        # Change to the document's output directory
                        os.chdir(output_dir)
                        
                        # Save with just the filename (not full path)
                        document.save_as_markdown(
                            output_filename,
                            image_mode=ImageRefMode.REFERENCED,
                            include_annotations=self.annotate_images
                        )
                        
                        # Move images from artifacts folder to images subfolder
                        artifacts_folder = Path(f"{base_filename}_artifacts")
                        if artifacts_folder.exists() and artifacts_folder.is_dir():
                            # Create images subfolder
                            images_folder = Path("images")
                            images_folder.mkdir(exist_ok=True)
                            
                            # Move all images to the images folder
                            for image_file in artifacts_folder.glob("*"):
                                if image_file.is_file():
                                    image_file.rename(images_folder / image_file.name)
                            
                            # Remove the now-empty artifacts folder
                            artifacts_folder.rmdir()
                            
                            # Update markdown to use images/ folder path
                            with open(output_filename, "r", encoding="utf-8") as f:
                                markdown_content = f.read()
                            
                            # Replace references from "folder_artifacts/image.png" to "images/image.png"
                            markdown_content = markdown_content.replace(
                                f"{base_filename}_artifacts\\",
                                "images/"
                            ).replace(
                                f"{base_filename}_artifacts/",
                                "images/"
                            )
                            
                            # Write updated markdown
                            with open(output_filename, "w", encoding="utf-8") as f:
                                f.write(markdown_content)
                    finally:
                        # Always restore original working directory
                        os.chdir(original_cwd)
                    
                    # Read the saved markdown for preview
                    with open(output_path, "r", encoding="utf-8") as f:
                        markdown_output = f.read()
                except ImportError as e:
                    return {
                        "success": False,
                        "error": f"Failed to import ImageRefMode. Please ensure docling-core>=2.0.0 is installed. Error: {str(e)}"
                    }
            else:
                # Export to markdown with inline/embedded images
                if self.annotate_images:
                    markdown_output = document.export_to_markdown(
                        mark_annotations=True,
                        include_annotations=True
                    )
                else:
                    markdown_output = document.export_to_markdown()
                
                # Write markdown to file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_output)
            
            return {
                "success": True,
                "output_path": str(output_path),
                "output_directory": str(output_dir),
                "content_length": len(markdown_output),
                "message": f"Successfully saved markdown to {output_path}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save markdown output: {str(e)}"
            }
