from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import json
import re
import requests
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, ClassVar
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

class ExtractAndChunkWebsite(BaseTool):
    """
    A tool that extracts website content using Docling and chunks it using the HybridChunker.
    Supports automatic conversion of .txt files to .md format before processing.
    The chunked results are saved to the tst_output folder, and a markdown document
    is created with the URL as the filename.
    
    Supported formats: PDF, DOCX, XLSX, PPTX, CSV, Markdown, AsciiDoc, HTML, XHTML, 
    Image formats (PNG, JPEG, TIFF, BMP, WEBP), WebVTT, and TXT (auto-converted to MD).
    """

    url: str = Field(
        ...,
        description="The URL of the website/document to extract and chunk. Must be a valid HTTP/HTTPS URL. Supports .txt files (auto-converted to .md).",
    )
    
    max_tokens: int = Field(
        default=512,
        description="Maximum number of tokens per chunk. Default is 512 tokens for optimal chunking.",
    )
    
    tokenizer_model: str = Field(
        default=None,
        description="HuggingFace model ID to use for tokenization. If None, uses TOKENIZER_MODEL environment variable. Default is sentence-transformers/all-MiniLM-L6-v2.",
    )
    
    merge_peers: bool = Field(
        default=True,
        description="Whether to merge peer chunks in the hybrid chunker. Default is True.",
    )

    # Docling supported formats - ClassVar so Pydantic doesn't treat it as a field
    SUPPORTED_FORMATS: ClassVar[Dict[str, str]] = {
        '.pdf': 'PDF',
        '.docx': 'DOCX',
        '.xlsx': 'XLSX',
        '.pptx': 'PPTX',
        '.csv': 'CSV',
        '.md': 'MARKDOWN',
        '.asciidoc': 'ASCIIDOC',
        '.adoc': 'ASCIIDOC',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.xhtml': 'XHTML',
        '.png': 'IMAGE',
        '.jpeg': 'IMAGE',
        '.jpg': 'IMAGE',
        '.tiff': 'IMAGE',
        '.bmp': 'IMAGE',
        '.webp': 'IMAGE',
        '.vtt': 'WEBVTT',
        '.txt': 'TEXT'  # Will be converted to MD before processing
    }
    
    def _sanitize_filename(self, url: str) -> str:
        """
        Converts a URL to a safe filename by removing protocol and replacing special characters.
        
        Args:
            url: The URL to convert
            
        Returns:
            A sanitized filename string
        """
        # Step 1: Remove protocol (http://, https://)
        filename = re.sub(r'^https?://', '', url)
        
        # Step 2: Replace special characters with underscores
        filename = re.sub(r'[^\w\-.]', '_', filename)
        
        # Step 3: Remove consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Step 4: Remove trailing underscores and dots
        filename = filename.strip('_.')
        
        return filename
    
    def _check_url_and_format(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Checks if the URL is accessible and determines its format.
        
        Args:
            url: The URL to check
            
        Returns:
            A tuple of (is_valid, format_type, error_message)
            - is_valid: True if URL is accessible and format is supported
            - format_type: The detected format (e.g., 'PDF', 'HTML', 'TEXT')
            - error_message: Error message if validation fails, None otherwise
        """
        try:
            # Step 1: Parse URL to get file extension
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # Get file extension from URL path
            _, ext = os.path.splitext(path)
            ext = ext.lower()
            
            # Step 2: Make a HEAD request to check if URL is accessible
            print(f"Checking URL accessibility: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                
                # If HEAD fails, try GET with small range
                if response.status_code >= 400:
                    response = requests.get(url, headers=headers, timeout=10, stream=True)
                    
            except requests.exceptions.RequestException as e:
                # Try GET if HEAD fails completely
                try:
                    response = requests.get(url, headers=headers, timeout=10, stream=True)
                except Exception as get_error:
                    return False, None, f"URL is not accessible: {str(get_error)}"
            
            # Step 3: Check if request was successful
            if response.status_code >= 400:
                return False, None, f"URL returned error status code: {response.status_code}"
            
            # Step 4: Determine format from extension or content-type
            content_type = response.headers.get('Content-Type', '').lower()
            
            # If we have an extension, use it
            if ext in self.SUPPORTED_FORMATS:
                format_type = self.SUPPORTED_FORMATS[ext]
                print(f"Detected format from extension: {format_type} ({ext})")
                return True, format_type, None
            
            # Try to determine from content-type
            if 'pdf' in content_type:
                return True, 'PDF', None
            elif 'html' in content_type:
                return True, 'HTML', None
            elif 'word' in content_type or 'docx' in content_type:
                return True, 'DOCX', None
            elif 'powerpoint' in content_type or 'pptx' in content_type:
                return True, 'PPTX', None
            elif 'excel' in content_type or 'xlsx' in content_type:
                return True, 'XLSX', None
            elif 'markdown' in content_type:
                return True, 'MD', None
            elif 'text/plain' in content_type:
                return True, 'TEXT', None
            
            # If no extension and content-type doesn't help, assume HTML for web pages
            if not ext or ext == '/':
                print("No file extension detected, assuming HTML web page")
                return True, 'HTML', None
            
            # Unknown format
            supported_list = ', '.join(self.SUPPORTED_FORMATS.keys())
            return False, None, f"Unsupported format '{ext}'. Supported formats: {supported_list}"
            
        except Exception as e:
            return False, None, f"Error checking URL: {str(e)}"
    
    def _download_and_convert_txt_to_md(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Downloads a .txt file and converts it to .md format.
        
        Args:
            url: The URL of the .txt file
            
        Returns:
            A tuple of (success, md_file_path, error_message)
        """
        try:
            print(f"Downloading .txt file from: {url}")
            
            # Step 1: Download the .txt file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Step 2: Create a temporary .md file
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as tmp_file:
                # Write the content as markdown
                # Add a header with the source URL
                tmp_file.write(f"# Content from {url}\n\n")
                tmp_file.write("---\n\n")
                
                # Write the actual content
                content = response.text
                tmp_file.write(content)
                
                tmp_file_path = tmp_file.name
            
            print(f"Converted .txt to .md: {tmp_file_path}")
            return True, tmp_file_path, None
            
        except Exception as e:
            return False, None, f"Failed to download and convert .txt file: {str(e)}"

    def run(self):
        """
        Extracts website content using Docling, chunks it with HybridChunker,
        and saves the results to the tst_output folder.
        
        Automatically detects .txt files and converts them to .md before processing.
        
        Returns:
            A JSON string containing the operation result with the following structure:
            - On success: {"success": true, "url": "...", "chunks_count": N, "output_dir": "...", "markdown_file": "..."}
            - On failure: {"success": false, "error": "error message"}
        """
        temp_file_to_cleanup = None
        
        try:
            # Step 1: Import required libraries
            from docling.document_converter import DocumentConverter
            from docling.chunking import HybridChunker
            
        except ImportError as e:
            return json.dumps({
                "success": False,
                "error": f"Failed to import required libraries. Please ensure docling>=2.0.0 is installed. Error: {str(e)}"
            }, indent=2)

        try:
            # Step 2: Validate URL and check format
            is_valid, format_type, error_msg = self._check_url_and_format(self.url)
            
            if not is_valid:
                return json.dumps({
                    "success": False,
                    "error": error_msg,
                    "supported_formats": list(self.SUPPORTED_FORMATS.keys())
                }, indent=2)
            
            print(f"[OK] URL is valid. Detected format: {format_type}")
            
            # Step 3: Handle .txt files - convert to .md
            source_to_process = self.url
            is_converted_txt = False
            
            if format_type == 'TEXT':
                print("Converting .txt file to .md format...")
                success, md_file_path, error_msg = self._download_and_convert_txt_to_md(self.url)
                
                if not success:
                    return json.dumps({
                        "success": False,
                        "error": error_msg
                    }, indent=2)
                
                source_to_process = md_file_path
                temp_file_to_cleanup = md_file_path
                is_converted_txt = True
                print(f"[OK] Converted .txt to .md: {md_file_path}")
            
            # Step 4: Create output directory if it doesn't exist
            # Get the project root directory (2 levels up from this file)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_file_dir))
            output_dir = os.path.join(project_root, "tst_output")
            os.makedirs(output_dir, exist_ok=True)
            print(f"[DEBUG] Output directory: {output_dir}")
            print(f"[DEBUG] Current working directory: {os.getcwd()}")
            
            # Step 5: Initialize DocumentConverter
            converter = DocumentConverter()
            
            # Step 6: Extract content
            print(f"Extracting content from: {source_to_process}")
            result = converter.convert(source_to_process)
            
            if not result.document:
                return json.dumps({
                    "success": False,
                    "error": "Failed to extract content from the website. No document was returned."
                }, indent=2)
            
            document = result.document
            
            # Step 7: Export full markdown and HTML
            full_markdown = document.export_to_markdown()
            
            # Export HTML - try to get it from the result or export from document
            try:
                if hasattr(result, 'html') and result.html:
                    full_html = result.html
                else:
                    # Try to export HTML from document
                    full_html = document.export_to_html()
            except Exception as e:
                # If HTML export fails, create a basic HTML wrapper with markdown
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.url}</title>
</head>
<body>
    <h1>Content from: {self.url}</h1>
    <p><em>Note: HTML export not available, showing markdown content</em></p>
    <pre>{full_markdown}</pre>
</body>
</html>"""
            
            # Step 8: Get model configuration and initialize tokenizer
            # Import model loader utilities
            import sys
            from pathlib import Path
            # Add document_processor utils path for accessing shared utilities
            doc_processor_utils_path = Path(__file__).parent.parent.parent / "document_processor" / "tools" / "utils"
            if str(doc_processor_utils_path) not in sys.path:
                sys.path.insert(0, str(doc_processor_utils_path))
            
            from model_loader import get_tokenizer, get_model_config
            
            # Get model configuration from environment
            tokenizer_model_env, _, model_source, max_chunk_tokens_env = get_model_config()
            
            # Use tool parameter if provided, otherwise use env config
            tokenizer_model_to_use = self.tokenizer_model or tokenizer_model_env
            max_tokens_to_use = self.max_tokens if self.max_tokens != 512 else max_chunk_tokens_env
            
            # Debug output
            print(f"[DEBUG] Tool parameters: max_tokens={self.max_tokens}, tokenizer_model={self.tokenizer_model}")
            print(f"[DEBUG] Resolved values: max_tokens_to_use={max_tokens_to_use}, tokenizer_model_to_use={tokenizer_model_to_use}")
            print(f"[DEBUG] Model source: {model_source}")
            
            # Load tokenizer based on MODEL_SOURCE
            tokenizer = get_tokenizer(model_name=tokenizer_model_to_use, model_source=model_source)
            
            # Step 9: Initialize HybridChunker with tokenizer instance
            chunker = HybridChunker(
                tokenizer=tokenizer,
                max_tokens=max_tokens_to_use,
                merge_peers=self.merge_peers,
            )
            
            # Step 10: Chunk the document
            print(f"Chunking document with tokenizer={tokenizer_model_to_use} (source: {model_source}), max_tokens={max_tokens_to_use}")
            chunk_iter = chunker.chunk(dl_doc=document)
            chunks = list(chunk_iter)
            print(f"[DEBUG] Created {len(chunks)} chunks")
            
            # Step 10: Save individual chunks to separate files
            sanitized_url = self._sanitize_filename(self.url)
            chunk_files = []
            
            for i, chunk in enumerate(chunks):
                chunk_filename = os.path.join(output_dir, f"{sanitized_url}_chunk_{i+1}.txt")
                print(f"Saved chunk {i+1}/{len(chunks)} to: {chunk_filename}")
                with open(chunk_filename, 'w', encoding='utf-8') as f:
                    # Write chunk metadata
                    f.write(f"# Chunk {i+1} of {len(chunks)}\n")
                    f.write(f"# Source URL: {self.url}\n")
                    f.write(f"# Chunk Index: {i+1}\n")
                    
                    # Write chunk headings if available
                    if hasattr(chunk.meta, 'headings') and chunk.meta.headings:
                        f.write(f"# Headings: {' > '.join(chunk.meta.headings)}\n")
                    
                    # Write page numbers if available
                    if hasattr(chunk.meta, 'doc_items') and chunk.meta.doc_items:
                        page_numbers = sorted(set(
                            prov.page_no
                            for item in chunk.meta.doc_items
                            for prov in item.prov
                            if hasattr(prov, 'page_no')
                        ))
                        if page_numbers:
                            f.write(f"# Page Numbers: {', '.join(map(str, page_numbers))}\n")
                    
                    f.write("\n---\n\n")
                    
                    # Write the actual chunk text
                    f.write(chunk.text)
                
                chunk_files.append(chunk_filename)
                print(f"Saved chunk {i+1}/{len(chunks)} to: {chunk_filename}")
            
            # Step 11: Save full markdown document
            markdown_filename = os.path.join(output_dir, f"{sanitized_url}.md")
            with open(markdown_filename, 'w', encoding='utf-8') as f:
                f.write(f"# Website Content: {self.url}\n\n")
                f.write(f"Extracted on: {result.document.export_to_dict().get('created', 'N/A')}\n\n")
                f.write("---\n\n")
                f.write(full_markdown)
            
            print(f"Saved full markdown to: {markdown_filename}")
            
            # Step 12: Save full HTML document
            html_filename = os.path.join(output_dir, f"{sanitized_url}.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            print(f"Saved full HTML to: {html_filename}")
            
            # Step 13: Create a summary file with chunk information
            summary_filename = os.path.join(output_dir, f"{sanitized_url}_summary.json")
            summary = {
                "url": self.url,
                "detected_format": format_type,
                "was_converted_from_txt": is_converted_txt,
                "chunks_count": len(chunks),
                "max_tokens_per_chunk": max_tokens_to_use,
                "tokenizer_model": tokenizer_model_to_use,
                "model_source": model_source,
                "merge_peers": self.merge_peers,
                "chunk_files": chunk_files,
                "markdown_file": markdown_filename,
                "html_file": html_filename,
                "chunks_metadata": [
                    {
                        "chunk_index": i + 1,
                        "text_length": len(chunk.text),
                        "headings": chunk.meta.headings if hasattr(chunk.meta, 'headings') else [],
                        "page_numbers": sorted(set(
                            prov.page_no
                            for item in chunk.meta.doc_items
                            for prov in item.prov
                            if hasattr(prov, 'page_no')
                        )) if hasattr(chunk.meta, 'doc_items') else []
                    }
                    for i, chunk in enumerate(chunks)
                ]
            }
            
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            print(f"Saved summary to: {summary_filename}")
            
            # Step 14: Clean up temporary file if created
            if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
                try:
                    os.unlink(temp_file_to_cleanup)
                    print(f"Cleaned up temporary file: {temp_file_to_cleanup}")
                except Exception as cleanup_error:
                    print(f"Warning: Failed to cleanup temp file: {cleanup_error}")
            
            # Step 15: Return success result
            return json.dumps({
                "success": True,
                "url": self.url,
                "detected_format": format_type,
                "was_converted_from_txt": is_converted_txt,
                "chunks_count": len(chunks),
                "tokenizer_model": tokenizer_model_to_use,
                "model_source": model_source,
                "max_tokens": max_tokens_to_use,
                "output_dir": output_dir,
                "markdown_file": markdown_filename,
                "html_file": html_filename,
                "summary_file": summary_filename,
                "chunk_files": chunk_files
            }, indent=2)
            
        except Exception as e:
            # Handle any errors during processing
            import traceback
            error_trace = traceback.format_exc()
            
            # Clean up temporary file if it was created
            if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
                try:
                    os.unlink(temp_file_to_cleanup)
                except:
                    pass
            
            return json.dumps({
                "success": False,
                "error": f"Failed to extract and chunk website. Error: {str(e)}",
                "traceback": error_trace
            }, indent=2)


if __name__ == "__main__":
    # Add parent directory to path for standalone testing
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Test 1: Extract and chunk a .txt file (with auto-conversion to .md)
    print("Test 1: Extracting and chunking a .txt file (auto-converted to .md)...")
    print("=" * 80)
    
    tool1 = ExtractAndChunkWebsite(
        url="https://agentclientprotocol.com/llms-full.txt",
        max_tokens=512,
        tokenizer_model="sentence-transformers/all-MiniLM-L6-v2",
        merge_peers=True
    )
    
    result_str1 = tool1.run()
    result1 = json.loads(result_str1)
    
    if result1.get("success"):
        print(f"\n[SUCCESS] Extracted and chunked: {result1.get('url')}")
        print(f"  Detected format: {result1.get('detected_format')}")
        print(f"  Converted from .txt: {result1.get('was_converted_from_txt')}")
        print(f"  Chunks created: {result1.get('chunks_count')}")
        print(f"  Output directory: {result1.get('output_dir')}")
        print(f"  Markdown file: {result1.get('markdown_file')}")
        print(f"  HTML file: {result1.get('html_file')}")
        print(f"  Summary file: {result1.get('summary_file')}")
        print(f"  Chunk files: {len(result1.get('chunk_files', []))} files")
    else:
        print(f"\n[FAILED] {result1.get('error')}")
        if result1.get('traceback'):
            print(f"\nTraceback:\n{result1.get('traceback')}")
    
    print("\n" + "=" * 80)
    
    # Test 2: Extract and chunk a PDF document
    print("\nTest 2: Extracting and chunking a PDF document...")
    print("=" * 80)
    
    tool2 = ExtractAndChunkWebsite(
        url="https://arxiv.org/pdf/2408.09869",
        max_tokens=512,
        tokenizer_model="sentence-transformers/all-MiniLM-L6-v2",
        merge_peers=True
    )
    
    result_str2 = tool2.run()
    result2 = json.loads(result_str2)
    
    if result2.get("success"):
        print(f"\n[SUCCESS] Extracted and chunked: {result2.get('url')}")
        print(f"  Detected format: {result2.get('detected_format')}")
        print(f"  Chunks created: {result2.get('chunks_count')}")
        print(f"  Output directory: {result2.get('output_dir')}")
        print(f"  Markdown file: {result2.get('markdown_file')}")
        print(f"  HTML file: {result2.get('html_file')}")
        print(f"  Summary file: {result2.get('summary_file')}")
        print(f"  Chunk files: {len(result2.get('chunk_files', []))} files")
    else:
        print(f"\n[FAILED] {result2.get('error')}")
        if result2.get('traceback'):
            print(f"\nTraceback:\n{result2.get('traceback')}")
    
    print("\n" + "=" * 80)
    print("All tests completed! Check the tst_output folder for results.")

