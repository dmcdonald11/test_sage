from agency_swarm.tools import BaseTool
from pydantic import Field
import asyncio
from typing import Set, Dict, List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig
from urllib.parse import urlparse, urljoin
import os
import sys
from dotenv import load_dotenv

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()


class DiscoverUrlsMultiLevel(BaseTool):
    """
    Discovers and extracts URLs from a website recursively up to a specified depth level.
    This tool crawls a starting URL, extracts all internal links, and recursively follows them
    to the specified depth (e.g., 3 levels deep), building a comprehensive list of URLs.
    """

    start_url: str = Field(
        ..., 
        description="The starting URL to begin crawling from (e.g., 'https://example.com')"
    )
    
    max_depth: int = Field(
        default=3,
        description="Maximum depth to crawl (1 = start URL only, 2 = start + linked pages, 3 = start + 2 levels of links, etc.)"
    )
    
    max_urls_per_level: int = Field(
        default=50,
        description="Maximum number of URLs to crawl per depth level (prevents infinite crawling)"
    )
    
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [],
        description="URL patterns to exclude (e.g., ['/login', '/admin', '.pdf'])"
    )

    def run(self):
        """
        Executes multi-level URL discovery and returns a structured list of discovered URLs.
        """
        try:
            # Run the async crawling function
            result = asyncio.run(self._discover_urls_async())
            return result
        except Exception as e:
            return f"Error during multi-level URL discovery: {str(e)}"

    async def _discover_urls_async(self):
        """
        Asynchronous implementation of multi-level URL discovery.
        """
        # Step 1: Initialize tracking structures
        discovered_urls: Dict[int, Set[str]] = {i: set() for i in range(self.max_depth + 1)}
        visited_urls: Set[str] = set()
        all_discovered_urls: Set[str] = set()  # Global deduplication tracker
        total_links_found: int = 0  # Track raw link count before deduplication
        duplicates_skipped: int = 0  # Track how many duplicates we prevented
        base_domain = urlparse(self.start_url).netloc
        
        # Step 2: Normalize and add starting URL to level 0
        normalized_start_url = self._normalize_url(self.start_url, self.start_url)
        discovered_urls[0].add(normalized_start_url)
        all_discovered_urls.add(normalized_start_url)
        
        print(f"Starting multi-level URL discovery from: {self.start_url}")
        print(f"Max depth: {self.max_depth}, Max URLs per level: {self.max_urls_per_level}")
        
        # Step 3: Create crawler configuration
        browser_config = BrowserConfig(
            headless=True,  # Run in headless mode
            verbose=False,
        )
        
        crawler_config = CrawlerRunConfig(
            exclude_external_links=True,  # Only follow internal links
            exclude_social_media_links=True,  # Skip social media
            cache_mode=CacheMode.BYPASS,  # Don't use cache for fresh results
            page_timeout=30000,  # 30 second timeout per page
        )
        
        # Step 4: Crawl each level
        async with AsyncWebCrawler(config=browser_config, verbose=False) as crawler:
            for current_depth in range(self.max_depth):
                print(f"\n--- Crawling Level {current_depth} ---")
                
                # Get URLs to crawl at this level
                urls_to_crawl = list(discovered_urls[current_depth] - visited_urls)
                
                # Limit URLs per level
                urls_to_crawl = urls_to_crawl[:self.max_urls_per_level]
                
                if not urls_to_crawl:
                    print(f"No new URLs to crawl at level {current_depth}")
                    break
                
                print(f"Crawling {len(urls_to_crawl)} URLs at level {current_depth}")
                
                # Crawl each URL at this level
                for url in urls_to_crawl:
                    if url in visited_urls:
                        continue
                    
                    # Check if URL matches exclude patterns
                    if self._should_exclude(url):
                        print(f"Skipping excluded URL: {url}")
                        visited_urls.add(url)
                        continue
                    
                    try:
                        print(f"  Crawling: {url}")
                        
                        # Execute the crawl
                        result = await crawler.arun(url=url, config=crawler_config)
                        
                        if not result.success:
                            print(f"  Failed to crawl {url}: {result.error_message}")
                            visited_urls.add(url)
                            continue
                        
                        # Mark as visited
                        visited_urls.add(url)
                        
                        # Extract internal links
                        internal_links = result.links.get("internal", [])
                        
                        # Process and normalize links
                        for link_data in internal_links:
                            # Handle both dict and string formats
                            if isinstance(link_data, dict):
                                link_url = link_data.get("href", "")
                            else:
                                link_url = str(link_data)
                            
                            # Normalize the URL
                            normalized_url = self._normalize_url(link_url, url)
                            
                            # Check if it's the same domain
                            if urlparse(normalized_url).netloc == base_domain:
                                total_links_found += 1
                                
                                # Add to next level if not already discovered at ANY level
                                if normalized_url not in all_discovered_urls:
                                    discovered_urls[current_depth + 1].add(normalized_url)
                                    all_discovered_urls.add(normalized_url)
                                else:
                                    duplicates_skipped += 1
                        
                        print(f"  Found {len(internal_links)} internal links")
                        
                    except Exception as e:
                        print(f"  Error crawling {url}: {str(e)}")
                        visited_urls.add(url)
                        continue
        
        # Step 5: Generate results summary
        total_urls = len(all_discovered_urls)  # Use global tracker for accurate count
        
        result_summary = f"""
Multi-Level URL Discovery Complete!
=====================================

Starting URL: {self.start_url}
Max Depth: {self.max_depth}

Deduplication Statistics:
  Total Links Found: {total_links_found}
  Unique URLs Discovered: {total_urls}
  Duplicates Prevented: {duplicates_skipped}
  Deduplication Rate: {(duplicates_skipped / total_links_found * 100) if total_links_found > 0 else 0:.1f}%

Crawl Statistics:
  URLs Visited: {len(visited_urls)}
  URLs Remaining: {total_urls - len(visited_urls)}

URLs by Level:
"""
        
        # Add URLs by level
        all_urls_list = []
        for level in range(self.max_depth + 1):
            urls_at_level = discovered_urls[level]
            result_summary += f"\n  Level {level}: {len(urls_at_level)} URLs"
            
            # Add to comprehensive list
            for url in sorted(urls_at_level):
                all_urls_list.append({
                    "url": url,
                    "level": level,
                    "visited": url in visited_urls
                })
        
        result_summary += f"\n\nFull URL List ({len(all_urls_list)} URLs):\n"
        result_summary += "=" * 60 + "\n"
        
        for url_info in all_urls_list:
            status = "[V] Visited" if url_info["visited"] else "[D] Discovered"
            result_summary += f"[Level {url_info['level']}] {status}: {url_info['url']}\n"
        
        return result_summary
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize a URL by resolving relative paths and removing fragments.
        """
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # Remove URL fragments (e.g., #section)
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Add query string if present
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        # Remove trailing slash for consistency
        # Special case: treat domain-only and domain-with-root-path as the same
        if normalized.endswith('/') and parsed.path == '/':
            normalized = normalized[:-1]
        elif normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized
    
    def _should_exclude(self, url: str) -> bool:
        """
        Check if a URL should be excluded based on exclude patterns.
        """
        for pattern in self.exclude_patterns:
            if pattern in url:
                return True
        return False


if __name__ == "__main__":
    # Test case 1: Basic 3-level crawl
    print("Test 1: Basic 3-level URL discovery")
    print("=" * 60)
    tool = DiscoverUrlsMultiLevel(
        start_url="https://docs.crawl4ai.com",
        max_depth=3,
        max_urls_per_level=10  # Limit for testing
    )
    result = tool.run()
    print(result)
    
    print("\n\n")
    
    # Test case 2: With exclude patterns
    print("Test 2: URL discovery with exclusions")
    print("=" * 60)
    tool2 = DiscoverUrlsMultiLevel(
        start_url="https://example.com",
        max_depth=2,
        max_urls_per_level=5,
        exclude_patterns=["/blog/", "/archive/", ".pdf"]
    )
    result2 = tool2.run()
    print(result2)

