"""
URL-based input source for processing documents from web URLs and sitemaps.
"""

import asyncio
from typing import List, Dict, Any
from urllib.parse import urlparse
from .base_input_source import BaseInputSource, DocumentInput

class URLInputSource(BaseInputSource):
    """Process documents from URLs and sitemaps"""
    
    def __init__(self, urls: List[str] = None, sitemap_url: str = None):
        """
        Initialize URL input source.
        
        Args:
            urls: List of direct URLs to process
            sitemap_url: URL of a sitemap to extract URLs from
        """
        self.urls = urls or []
        self.sitemap_url = sitemap_url
        self._documents_cache = None
    
    async def get_documents(self) -> List[DocumentInput]:
        """Return URL documents, optionally extracting from sitemap"""
        if self._documents_cache is not None:
            return self._documents_cache
        
        documents = []
        
        # Add direct URLs
        for url in self.urls:
            documents.append(DocumentInput(
                source=url,
                source_type="url",
                metadata={
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "scheme": urlparse(url).scheme
                }
            ))
        
        # Extract URLs from sitemap if provided
        if self.sitemap_url:
            sitemap_urls = await self._extract_sitemap_urls()
            for url in sitemap_urls:
                documents.append(DocumentInput(
                    source=url,
                    source_type="url",
                    metadata={
                        "url": url,
                        "domain": urlparse(url).netloc,
                        "scheme": urlparse(url).scheme,
                        "source": "sitemap",
                        "sitemap_url": self.sitemap_url
                    }
                ))
        
        # Cache the results
        self._documents_cache = documents
        return documents
    
    def get_source_type(self) -> str:
        return "url"
    
    def get_source_count(self) -> int:
        """Return estimated number of documents"""
        if self._documents_cache is not None:
            return len(self._documents_cache)
        
        count = len(self.urls)
        if self.sitemap_url:
            # Estimate sitemap URLs (will be updated after actual extraction)
            count += 50  # Conservative estimate
        return count
    
    async def _extract_sitemap_urls(self) -> List[str]:
        """Extract URLs from sitemap using the existing DiscoverUrlsMultiLevel tool"""
        try:
            # Import the existing tool
            import sys
            from pathlib import Path
            
            # Add the document_processor tools to the path
            doc_processor_path = Path(__file__).parent.parent.parent.parent.parent / "document_processor" / "tools"
            sys.path.append(str(doc_processor_path))
            
            from DiscoverUrlsMultiLevel import DiscoverUrlsMultiLevel
            
            # Use the existing tool to discover URLs
            discoverer = DiscoverUrlsMultiLevel(
                start_url=self.sitemap_url,
                max_depth=1,  # Just get the sitemap URLs
                max_urls_per_level=1000,  # Get all URLs from sitemap
                exclude_patterns=[]  # No exclusions for sitemap
            )
            
            result = discoverer.run()
            
            # Parse the result to extract URLs
            urls = []
            if isinstance(result, str):
                # Parse the text output to extract URLs
                lines = result.split('\n')
                for line in lines:
                    if '[Level 0]' in line and 'http' in line:
                        # Extract URL from line like "[Level 0] [V] Visited: https://example.com"
                        url_part = line.split(': ', 1)
                        if len(url_part) > 1:
                            url = url_part[1].strip()
                            if url.startswith('http'):
                                urls.append(url)
            
            return urls
            
        except Exception as e:
            print(f"Warning: Failed to extract URLs from sitemap {self.sitemap_url}: {str(e)}")
            return []
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the URL source"""
        return {
            "direct_urls": self.urls,
            "sitemap_url": self.sitemap_url,
            "estimated_document_count": self.get_source_count(),
            "has_sitemap": self.sitemap_url is not None
        }
