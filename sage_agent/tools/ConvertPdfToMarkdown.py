from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ConvertPdfToMarkdown(BaseTool):
    """
    A tool that uploads a PDF file, converts it to markdown using Docling, and saves the output.
    This tool can handle both file paths and base64-encoded file uploads.
    It uses Docling's DocumentConverter to intelligently extract and convert PDF content to markdown format.
    Optionally supports AI-powered image annotation using OpenAI's vision models.
    """

    file_path: str = Field(
        default="",
        description="Path to an existing PDF file to convert. If provided, this takes precedence over file_content.",
    )
    
    file_content: str = Field(
        default="",
        description="Base64-encoded PDF file content for upload. Used when uploading a new file. The file will be saved to the uploads folder.",
    )
    
    output_filename: str = Field(
        default="",
        description="Name for the output markdown file (without extension). If not provided, a timestamp-based name will be generated.",
    )
    
    annotate_images: bool = Field(
        default=None,
        description="Whether to use OpenAI API to generate descriptions for images found in the PDF. If not specified, reads from ANNOTATE_IMAGES environment variable (defaults to False). Requires OPENAI_API_KEY and IMAGE_MODEL environment variables to be set.",
    )
    
    images_scale: int = Field(
        default=None,
        description="Scale factor for generated images when annotate_images is True. If not specified, reads from IMAGE_SCALE environment variable (defaults to 2). Higher values produce better quality images but increase processing time. Typical values: 1-3.",
    )
    
    save_images_as_files: bool = Field(
        default=None,
        description="Whether to save images as separate external files referenced in the markdown. If True, images are saved in a subfolder alongside the markdown file. If False, images are embedded inline in the markdown. If not specified, reads from SAVE_IMAGES_AS_FILES environment variable (defaults to False).",
    )

    def run(self):
        """
        Converts a PDF file to markdown and saves it to the test_output folder.
        
        Process:
        1. Check environment variables for default settings
        2. If file_content is provided, decode and save to uploads folder
        3. If file_path is provided, use that file directly
        4. Use Docling to convert PDF to markdown (with optional image annotation)
        5. Save the markdown output to test_output folder
        
        Returns:
            A JSON string with the conversion result including success status, 
            file paths, and markdown content preview.
        """
        import json
        
        try:
            # Step 1: Read configuration from environment variables if not explicitly set
            if self.annotate_images is None:
                # Read from ANNOTATE_IMAGES env var, default to False
                annotate_images_env = os.getenv("ANNOTATE_IMAGES", "false").lower()
                self.annotate_images = annotate_images_env in ("true", "1", "yes", "on")
            
            if self.images_scale is None:
                # Read from IMAGE_SCALE env var, default to 2
                try:
                    self.images_scale = int(os.getenv("IMAGE_SCALE", "2"))
                except ValueError:
                    self.images_scale = 2
            
            if self.save_images_as_files is None:
                # Read from SAVE_IMAGES_AS_FILES env var, default to False
                save_images_env = os.getenv("SAVE_IMAGES_AS_FILES", "false").lower()
                self.save_images_as_files = save_images_env in ("true", "1", "yes", "on")
            
            # Step 2: Import Docling
            try:
                from docling.document_converter import DocumentConverter
            except ImportError as e:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to import Docling. Please ensure docling>=2.0.0 is installed. Error: {str(e)}"
                }, indent=2)
            
            # Step 3: Determine the PDF file path
            pdf_path = None
            
            if self.file_content:
                # Handle file upload via base64 content
                try:
                    # Decode base64 content
                    file_bytes = base64.b64decode(self.file_content)
                    
                    # Create uploads folder if it doesn't exist
                    uploads_dir = Path("uploads")
                    uploads_dir.mkdir(exist_ok=True)
                    
                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    uploaded_filename = f"uploaded_{timestamp}.pdf"
                    pdf_path = uploads_dir / uploaded_filename
                    
                    # Save the PDF file
                    with open(pdf_path, "wb") as f:
                        f.write(file_bytes)
                    
                    pdf_path = str(pdf_path)
                    
                except Exception as e:
                    return json.dumps({
                        "success": False,
                        "error": f"Failed to decode and save uploaded file: {str(e)}"
                    }, indent=2)
                    
            elif self.file_path:
                # Use provided file path
                pdf_path = self.file_path
                
                # Validate the file exists
                if not os.path.exists(pdf_path):
                    return json.dumps({
                        "success": False,
                        "error": f"File not found: {pdf_path}"
                    }, indent=2)
                    
            else:
                return json.dumps({
                    "success": False,
                    "error": "Either file_path or file_content must be provided"
                }, indent=2)
            
            # Step 4: Convert PDF to markdown using Docling
            try:
                # Import additional Docling classes for image annotation if needed
                if self.annotate_images:
                    try:
                        from docling.datamodel.base_models import InputFormat
                        from docling.datamodel.pipeline_options import (
                            PdfPipelineOptions,
                            PictureDescriptionApiOptions
                        )
                        from docling.document_converter import PdfFormatOption
                    except ImportError as e:
                        return json.dumps({
                            "success": False,
                            "error": f"Failed to import Docling pipeline options for image annotation. Please ensure docling>=2.0.0 is installed. Error: {str(e)}"
                        }, indent=2)
                    
                    # Get API key and model from environment
                    api_key = os.getenv("OPENAI_API_KEY")
                    image_model = os.getenv("IMAGE_MODEL", "gpt-4o-mini")  # Default to gpt-4o-mini if not set
                    
                    if not api_key:
                        return json.dumps({
                            "success": False,
                            "error": "OPENAI_API_KEY environment variable is required for image annotation but is not set"
                        }, indent=2)
                    
                    # Configure picture description options for OpenAI API
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
                
                # Convert the PDF
                conv_result = converter.convert(pdf_path)
                document = conv_result.document
                
                # Validate document was created
                if not document:
                    return json.dumps({
                        "success": False,
                        "error": "Docling conversion produced no document"
                    }, indent=2)
                
                # Store conversion result for later use (needed for external image references)
                conversion_result = conv_result
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Docling conversion failed: {str(e)}"
                }, indent=2)
            
            # Step 5: Save markdown to output folder
            try:
                # Get output folder from environment variable or use default
                output_folder_name = os.getenv("MD_OUTPUT_FOLDER", "test_output")
                base_output_dir = Path(output_folder_name)
                base_output_dir.mkdir(exist_ok=True, parents=True)
                
                # Determine base filename
                if self.output_filename:
                    base_filename = self.output_filename
                else:
                    # Use the PDF filename without extension
                    base_filename = Path(pdf_path).stem
                
                # If saving images as files, create a dedicated folder for the document
                if self.save_images_as_files:
                    # Create document-specific folder: test_output/document_name/
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
                    # Import ImageRefMode for external image references
                    try:
                        from docling_core.types.doc.document import ImageRefMode
                    except ImportError as e:
                        return json.dumps({
                            "success": False,
                            "error": f"Failed to import ImageRefMode. Please ensure docling-core>=2.0.0 is installed. Error: {str(e)}"
                        }, indent=2)
                    
                    # Save markdown with externally referenced images
                    # Change to the document folder to avoid nested paths
                    original_cwd = os.getcwd()
                    try:
                        # Change to the document's output directory
                        os.chdir(output_dir)
                        
                        # Save with just the filename (not full path)
                        # This will create artifacts folder in the same directory
                        document.save_as_markdown(
                            output_filename,
                            image_mode=ImageRefMode.REFERENCED,
                            include_annotations=self.annotate_images
                        )
                        
                        # Move images from artifacts folder to images subfolder
                        # for better organization (supports future video/audio expansion)
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
                            # Use forward slashes for cross-platform compatibility
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
                else:
                    # Export to markdown with inline/embedded images
                    if self.annotate_images:
                        markdown_output = document.export_to_markdown(
                            mark_annotations=True,
                            include_annotations=True
                        )
                    else:
                        markdown_output = document.export_to_markdown()
                    
                    # Validate we got content
                    if not markdown_output or len(markdown_output.strip()) < 10:
                        return json.dumps({
                            "success": False,
                            "error": "Docling conversion produced empty or invalid markdown content"
                        }, indent=2)
                    
                    # Write markdown to file
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(markdown_output)
                
                output_path = str(output_path)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to save markdown output: {str(e)}"
                }, indent=2)
            
            # Step 6: Return success result with preview
            preview_length = min(500, len(markdown_output))
            preview = markdown_output[:preview_length]
            if len(markdown_output) > preview_length:
                preview += "..."
            
            # Build result message
            message = f"Successfully converted PDF to markdown and saved to {output_path}"
            if self.annotate_images:
                message += " (with AI-powered image annotations)"
            if self.save_images_as_files:
                message += f" (images saved in {output_dir})"
            
            result_data = {
                "success": True,
                "pdf_path": pdf_path,
                "markdown_path": str(output_path),
                "content_length": len(markdown_output),
                "annotated_images": self.annotate_images,
                "external_images": self.save_images_as_files,
                "preview": preview,
                "message": message
            }
            
            # Add output directory info for external images
            if self.save_images_as_files:
                result_data["output_directory"] = str(output_dir)
            
            return json.dumps(result_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)


if __name__ == "__main__":
    import json
    
    # Test 1: Convert a PDF from URL without image annotation
    print("Test 1: Converting a PDF from a URL (without image annotation)...")
    print("-" * 80)
    
    try:
        from docling.document_converter import DocumentConverter
        
        # Create test_output folder
        Path("test_output").mkdir(exist_ok=True)
        
        # Test with a sample PDF URL
        test_url = "https://arxiv.org/pdf/2408.09869"
        
        converter = DocumentConverter()
        result = converter.convert(test_url)
        document = result.document
        markdown_output = document.export_to_markdown()
        
        # Save to test_output
        output_path = Path("test_output") / "test_arxiv_paper.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_output)
        
        print(f"[SUCCESS] Converted PDF from URL")
        print(f"  Output saved to: {output_path}")
        print(f"  Content length: {len(markdown_output)} characters")
        print(f"  Preview (first 300 chars):")
        print(f"  {markdown_output[:300]}...")
        
    except Exception as e:
        print(f"[FAILED] Could not complete test: {str(e)}")
        print("Note: This is expected if you don't have internet access or Docling is not properly installed.")
    
    print()
    print("-" * 80)
    print("Test 2: Test with image annotation (requires OPENAI_API_KEY and IMAGE_MODEL)...")
    print("-" * 80)
    
    # Check if we have the necessary environment variables
    if os.getenv("OPENAI_API_KEY"):
        print("[INFO] OPENAI_API_KEY found. Testing image annotation feature...")
        
        # For this test, you need an existing PDF file with images
        # Example using the uploaded docling.pdf if it exists
        test_pdf = "uploads/docling.pdf"
        
        if os.path.exists(test_pdf):
            tool = ConvertPdfToMarkdown(
                file_path=test_pdf,
                output_filename="test_with_annotations",
                annotate_images=True,
                images_scale=2
            )
            result_str = tool.run()
            result = json.loads(result_str)
            
            if result.get("success"):
                print(f"[SUCCESS] {result.get('message')}")
                print(f"  PDF path: {result.get('pdf_path')}")
                print(f"  Markdown path: {result.get('markdown_path')}")
                print(f"  Content length: {result.get('content_length')} characters")
                print(f"  Images annotated: {result.get('annotated_images')}")
                print(f"  Preview:")
                print(f"  {result.get('preview')[:300]}...")
            else:
                print(f"[FAILED] {result.get('error')}")
        else:
            print(f"[INFO] Test PDF not found at {test_pdf}")
            print("       To test image annotation, place a PDF with images in the uploads folder")
    else:
        print("[INFO] OPENAI_API_KEY not found in environment variables")
        print("       Set OPENAI_API_KEY and IMAGE_MODEL to test image annotation")
    
    print()
    print("-" * 80)
    print("Test 3: Test with external image references...")
    print("-" * 80)
    
    test_pdf = "uploads/docling.pdf"
    if os.path.exists(test_pdf):
        print("[INFO] Testing external image references feature...")
        tool = ConvertPdfToMarkdown(
            file_path=test_pdf,
            output_filename="test_with_external_images",
            save_images_as_files=True,
            annotate_images=bool(os.getenv("OPENAI_API_KEY")),
            images_scale=2
        )
        result_str = tool.run()
        result = json.loads(result_str)
        
        if result.get("success"):
            print(f"[SUCCESS] {result.get('message')}")
            print(f"  PDF path: {result.get('pdf_path')}")
            print(f"  Markdown path: {result.get('markdown_path')}")
            print(f"  Content length: {result.get('content_length')} characters")
            print(f"  External images: {result.get('external_images')}")
            
            # Check if image folder was created
            md_path = Path(result.get('markdown_path'))
            image_folder = md_path.parent / md_path.stem
            if image_folder.exists():
                image_files = list(image_folder.glob("*"))
                print(f"  Image folder created: {image_folder}")
                print(f"  Number of image files: {len(image_files)}")
            else:
                print(f"  Note: No separate image folder created")
        else:
            print(f"[FAILED] {result.get('error')}")
    else:
        print(f"[INFO] Test PDF not found at {test_pdf}")
        print("       To test external image references, place a PDF with images in the uploads folder")
    
    print()
    print("-" * 80)
    print("Test 4: Usage examples...")
    print("-" * 80)
    
    print("[INFO] To fully test this tool, provide a PDF file path or upload base64-encoded content.")
    print()
    print("Example usage:")
    print("  # Basic conversion:")
    print("  tool = ConvertPdfToMarkdown(file_path='path/to/file.pdf')")
    print()
    print("  # With image annotation:")
    print("  tool = ConvertPdfToMarkdown(")
    print("      file_path='path/to/file.pdf',")
    print("      annotate_images=True,")
    print("      images_scale=2")
    print("  )")
    print()
    print("  # With external image files:")
    print("  tool = ConvertPdfToMarkdown(")
    print("      file_path='path/to/file.pdf',")
    print("      save_images_as_files=True")
    print("  )")
    print()
    print("  # All features combined:")
    print("  tool = ConvertPdfToMarkdown(")
    print("      file_path='path/to/file.pdf',")
    print("      annotate_images=True,")
    print("      images_scale=3,")
    print("      save_images_as_files=True")
    print("  )")
    print()
    print("Tool is ready to use!")

