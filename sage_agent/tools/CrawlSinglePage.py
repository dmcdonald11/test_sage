from agency_swarm.tools import BaseTool
from pydantic import Field
import os
import asyncio
import traceback
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

class CrawlSinglePage(BaseTool):
    """
    A tool that crawls a single web page and extracts its content as markdown.
    This tool uses Crawl4AI to intelligently handle different types of websites,
    including documentation sites (Docusaurus, VitePress, GitBook, etc.) and regular web pages.
    It includes retry logic with exponential backoff and content validation.
    """

    url: str = Field(
        ...,
        description="The URL of the web page to crawl. Can be any valid HTTP/HTTPS URL.",
    )
    
    is_documentation_site: bool = Field(
        default=False,
        description="Whether this URL is a documentation site. If True, uses specialized configuration for docs sites like Docusaurus, VitePress, GitBook, etc.",
    )
    
    retry_count: int = Field(
        default=3,
        description="Number of retry attempts if crawling fails. Uses exponential backoff between retries.",
    )

    def _get_wait_selector_for_docs(self, url: str) -> str:
        """
        Identifies the type of documentation framework based on URL patterns
        and returns appropriate CSS selectors to wait for content to load.
        """
        url_lower = url.lower()
        
        # Map of documentation frameworks to their CSS selectors
        doc_frameworks = {
            'docusaurus': '.markdown, .theme-doc-markdown, article',
            'vitepress': '.VPDoc, .vp-doc, .content',
            'gitbook': '.markdown-section, .page-wrapper',
            'mkdocs': '.md-content, article',
            'docsify': '#main, .markdown-section',
            'copilotkit': 'div[class*="content"], div[class*="doc"], #__next',
            'milkdown': 'main, article, .prose, [class*="content"]',
        }
        
        # Check for framework-specific patterns in URL
        for framework, selector in doc_frameworks.items():
            if framework in url_lower:
                return selector
        
        # Generic fallback for documentation sites
        return 'body'

    def _transform_url(self, url: str) -> str:
        """
        Transforms URLs to their raw content versions when needed.
        For example, converts GitHub blob URLs to raw content URLs.
        """
        # Transform GitHub URLs to raw content
        if 'github.com' in url and '/blob/' in url:
            return url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        return url

    async def _crawl_page(self) -> Dict[str, Any]:
        """
        Internal async method that performs the actual crawling with retry logic.
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except ImportError as e:
            return {
                "success": False,
                "error": f"Failed to import Crawl4AI. Please ensure crawl4ai>=0.7.0 is installed. Error: {str(e)}"
            }

        # Step 1: Transform URL if needed (e.g., GitHub URLs)
        transformed_url = self._transform_url(self.url)
        original_url = self.url
        
        # Step 2: Initialize crawler components
        markdown_generator = DefaultMarkdownGenerator()
        
        # Step 3: Attempt crawling with retry logic
        for attempt in range(self.retry_count):
            try:
                async with AsyncWebCrawler(verbose=False) as crawler:
                    # Step 4: Configure cache mode - first attempt uses cache, subsequent attempts bypass it
                    cache_mode = CacheMode.ENABLED if attempt == 0 else CacheMode.BYPASS
                    
                    # Step 5: Build crawler configuration based on site type
                    if self.is_documentation_site:
                        # Documentation site configuration
                        wait_selector = self._get_wait_selector_for_docs(transformed_url)
                        
                        config = CrawlerRunConfig(
                            cache_mode=cache_mode,
                            stream=True,
                            markdown_generator=markdown_generator,
                            wait_for=wait_selector,
                            wait_until='domcontentloaded',
                            page_timeout=30000,  # 30 seconds
                            delay_before_return_html=0.5,  # 500ms for JS rendering
                            wait_for_images=False,
                            scan_full_page=True,
                            exclude_all_images=False,
                            remove_overlay_elements=True,
                            process_iframes=True
                        )
                    else:
                        # Regular site configuration
                        config = CrawlerRunConfig(
                            cache_mode=cache_mode,
                            stream=True,
                            markdown_generator=markdown_generator,
                            wait_until='domcontentloaded',
                            page_timeout=45000,  # 45 seconds
                            delay_before_return_html=0.3,  # 300ms delay
                            scan_full_page=True
                        )
                    
                    # Step 6: Execute the crawl
                    result = await crawler.arun(
                        url=transformed_url,
                        config=config
                    )
                    
                    # Step 7: Validate the result
                    if result.success and result.markdown and len(result.markdown.strip()) >= 50:
                        # Successfully crawled with valid content
                        return {
                            "success": True,
                            "url": original_url,
                            "markdown": result.markdown,
                            "html": result.html if hasattr(result, 'html') else "",
                            "title": result.title if hasattr(result, 'title') and result.title else "Untitled",
                            "links": result.links.get('internal', []) + result.links.get('external', []) if hasattr(result, 'links') and result.links else [],
                            "content_length": len(result.markdown)
                        }
                    else:
                        # Content validation failed
                        error_msg = "Content validation failed"
                        if not result.success:
                            error_msg = "Crawl was not successful"
                        elif not result.markdown:
                            error_msg = "No markdown content extracted"
                        elif len(result.markdown.strip()) < 50:
                            error_msg = f"Content too short ({len(result.markdown.strip())} chars)"
                        
                        # Retry with exponential backoff
                        if attempt < self.retry_count - 1:
                            wait_time = 2 ** attempt
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": f"{error_msg} after {self.retry_count} attempts"
                            }
                            
            except Exception as e:
                # Handle error message encoding safely
                try:
                    error_msg = str(e)
                    error_trace = traceback.format_exc()
                except UnicodeEncodeError:
                    error_msg = repr(e)
                    error_trace = "Error trace contains non-ASCII characters"
                
                # Retry with exponential backoff
                if attempt < self.retry_count - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"Failed to crawl {original_url} after {self.retry_count} attempts. Error: {error_msg}"
                    }
        
        # Should not reach here, but just in case
        return {
            "success": False,
            "error": f"Failed to crawl {original_url} after all retry attempts"
        }

    def run(self):
        """
        Crawls a single web page and returns the extracted content.
        
        Returns:
            A JSON string containing the crawl result with the following structure:
            - On success: {"success": true, "url": "...", "markdown": "...", "html": "...", "title": "...", "links": [...], "content_length": 123}
            - On failure: {"success": false, "error": "error message"}
        """
        import json
        
        # Step 1: Run the async crawling method
        result = asyncio.run(self._crawl_page())
        
        # Step 2: Return the result as a JSON string (ensure_ascii=True for Windows compatibility)
        return json.dumps(result, indent=2, ensure_ascii=True)


if __name__ == "__main__":
    import json
    
    # Test 1: Crawl a simple example website
    print("Test 1: Crawling example.com (simple website)...")
    tool1 = CrawlSinglePage(
        url="https://example.com/",
        is_documentation_site=False,
        retry_count=2
    )
    result1_str = tool1.run()
    result1 = json.loads(result1_str)
    
    if result1.get("success"):
        print(f"[SUCCESS] Crawled {result1.get('url')}")
        print(f"  Title: {result1.get('title')}")
        print(f"  Content length: {result1.get('content_length')} characters")
        print(f"  Links found: {len(result1.get('links', []))}")
    else:
        print(f"[FAILED] {result1.get('error', 'Unknown error')[:100]}")
    print()
    
    # Test 2: Test URL transformation (GitHub)
    print("Test 2: Testing URL transformation with GitHub...")
    tool2 = CrawlSinglePage(
        url="https://github.com/VRSEN/agency-swarm/blob/main/README.md",
        is_documentation_site=False,
        retry_count=1
    )
    result2_str = tool2.run()
    result2 = json.loads(result2_str)
    
    if result2.get("success"):
        print(f"[SUCCESS] Crawled GitHub file")
        print(f"  Title: {result2.get('title')}")
        print(f"  Content length: {result2.get('content_length')} characters")
    else:
        print(f"[FAILED] {result2.get('error', 'Unknown error')[:100]}")
    print()
    
    print("Tests completed! The tool is ready to use.")

