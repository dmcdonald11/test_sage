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


class CrawlWebsiteForSitemap(BaseTool):
    """
    Crawls a website to discover all URLs by following links recursively up to 5 levels deep.
    This tool uses crawl4ai to systematically explore a website, extract all URLs from each page,
    and build a comprehensive sitemap showing the website's structure and all referenced URLs.
    """

    website_url: str = Field(
        ..., 
        description="The starting URL of the website to crawl (e.g., 'https://example.com')"
    )
    
    max_depth: int = Field(
        default=5,
        description="Maximum depth to crawl (1 = start URL only, 2 = start + linked pages, etc.). Default is 5 levels deep as specified."
    )
    
    max_urls_per_level: int = Field(
        default=100,
        description="Maximum number of URLs to crawl per depth level (prevents infinite crawling on very large sites)"
    )
    
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [],
        description="URL patterns to exclude from crawling (e.g., ['/login', '/admin', '.pdf', '/api/']). Useful for skipping authentication pages or file downloads."
    )
    
    include_external: bool = Field(
        default=False,
        description="Whether to include external links (links to other domains) in the sitemap. Default is False to focus on internal site structure."
    )

    def run(self):
        """
        Executes the website crawling process and returns a comprehensive sitemap with all discovered URLs.
        """
        try:
            # Run the async crawling function
            result = asyncio.run(self._crawl_website_async())
            return result
        except Exception as e:
            return f"Error during website crawling: {str(e)}"

    async def _crawl_website_async(self):
        """
        Asynchronous implementation of website crawling for sitemap generation.
        """
        # Step 1: Initialize tracking structures
        discovered_urls: Dict[int, Set[str]] = {i: set() for i in range(self.max_depth + 1)}
        visited_urls: Set[str] = set()
        all_discovered_urls: Set[str] = set()  # Global deduplication tracker
        url_references: Dict[str, List[str]] = {}  # Track which URLs reference which other URLs
        total_links_found: int = 0
        duplicates_skipped: int = 0
        base_domain = urlparse(self.website_url).netloc
        
        # Step 2: Normalize and add starting URL to level 0
        normalized_start_url = self._normalize_url(self.website_url, self.website_url)
        discovered_urls[0].add(normalized_start_url)
        all_discovered_urls.add(normalized_start_url)
        url_references[normalized_start_url] = []
        
        print(f"Starting website crawl for sitemap generation")
        print(f"Starting URL: {self.website_url}")
        print(f"Max depth: {self.max_depth}, Max URLs per level: {self.max_urls_per_level}")
        print(f"Include external links: {self.include_external}")
        
        # Step 3: Create crawler configuration
        browser_config = BrowserConfig(
            headless=True,  # Run in headless mode
            verbose=False,
        )
        
        crawler_config = CrawlerRunConfig(
            exclude_external_links=not self.include_external,  # Control external link inclusion
            exclude_social_media_links=True,  # Skip social media links
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
                            url_references[url] = []  # Mark as having no references due to error
                            continue
                        
                        # Mark as visited
                        visited_urls.add(url)
                        
                        # Extract links based on include_external setting
                        if self.include_external:
                            all_links = result.links.get("internal", []) + result.links.get("external", [])
                        else:
                            all_links = result.links.get("internal", [])
                        
                        # Track references from this URL
                        referenced_urls = []
                        
                        # Process and normalize links
                        for link_data in all_links:
                            # Handle both dict and string formats
                            if isinstance(link_data, dict):
                                link_url = link_data.get("href", "")
                            else:
                                link_url = str(link_data)
                            
                            # Normalize the URL
                            normalized_url = self._normalize_url(link_url, url)
                            
                            # Check if it's the same domain (or include external if requested)
                            link_domain = urlparse(normalized_url).netloc
                            if self.include_external or link_domain == base_domain:
                                total_links_found += 1
                                referenced_urls.append(normalized_url)
                                
                                # Add to next level if not already discovered at ANY level
                                if normalized_url not in all_discovered_urls:
                                    if current_depth < self.max_depth:
                                        discovered_urls[current_depth + 1].add(normalized_url)
                                    all_discovered_urls.add(normalized_url)
                                    url_references[normalized_url] = []  # Initialize references list
                                else:
                                    duplicates_skipped += 1
                        
                        # Store references for this URL
                        url_references[url] = referenced_urls
                        
                        print(f"  Found {len(referenced_urls)} links (total discovered: {len(all_discovered_urls)})")
                        
                    except Exception as e:
                        print(f"  Error crawling {url}: {str(e)}")
                        visited_urls.add(url)
                        url_references[url] = []  # Mark as having no references due to error
                        continue
        
        # Step 5: Generate comprehensive sitemap results
        total_urls = len(all_discovered_urls)
        
        result_summary = f"""
Website Sitemap Generation Complete!
=====================================

Starting URL: {self.website_url}
Base Domain: {base_domain}
Max Depth: {self.max_depth}
Include External Links: {self.include_external}

Crawl Statistics:
  Total Links Found: {total_links_found}
  Unique URLs Discovered: {total_urls}
  URLs Successfully Visited: {len(visited_urls)}
  Duplicates Prevented: {duplicates_skipped}
  Deduplication Rate: {(duplicates_skipped / total_links_found * 100) if total_links_found > 0 else 0:.1f}%

URLs by Depth Level:
"""
        
        # Add URLs by level with reference information
        all_urls_list = []
        for level in range(self.max_depth + 1):
            urls_at_level = discovered_urls[level]
            result_summary += f"\n  Level {level}: {len(urls_at_level)} URLs"
            
            # Add to comprehensive list
            for url in sorted(urls_at_level):
                references = url_references.get(url, [])
                all_urls_list.append({
                    "url": url,
                    "level": level,
                    "visited": url in visited_urls,
                    "references_count": len(references),
                    "references": references[:10]  # Show first 10 references
                })
        
        result_summary += f"\n\nDetailed URL List ({len(all_urls_list)} URLs):\n"
        result_summary += "=" * 80 + "\n"
        
        for url_info in all_urls_list:
            status = "[✓] Visited" if url_info["visited"] else "[○] Discovered"
            ref_count = url_info["references_count"]
            result_summary += f"[Level {url_info['level']}] {status} | {ref_count} links → {url_info['url']}\n"
            
            # Show first few references if any
            if url_info["references"]:
                for ref in url_info["references"][:3]:  # Show first 3 references
                    result_summary += f"    └─→ {ref}\n"
                if ref_count > 3:
                    result_summary += f"    └─→ ... and {ref_count - 3} more\n"
        
        # Add summary of URL relationships
        result_summary += f"\n\nURL Reference Relationships:\n"
        result_summary += "=" * 80 + "\n"
        result_summary += "This shows which URLs reference which other URLs:\n\n"
        
        for url, refs in sorted(url_references.items()):
            if refs:  # Only show URLs that have references
                result_summary += f"{url}\n"
                for ref in refs[:5]:  # Show first 5 references
                    result_summary += f"  → {ref}\n"
                if len(refs) > 5:
                    result_summary += f"  → ... and {len(refs) - 5} more\n"
                result_summary += "\n"
        
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
    # Test case 1: Basic 5-level crawl
    print("Test 1: Basic 5-level website crawl for sitemap")
    print("=" * 80)
    tool = CrawlWebsiteForSitemap(
        website_url="https://docs.crawl4ai.com",
        max_depth=5,
        max_urls_per_level=20  # Limit for testing
    )
    result = tool.run()
    print(result)
    
    print("\n\n")
    
    # Test case 2: With exclude patterns
    print("Test 2: Website crawl with exclusions")
    print("=" * 80)
    tool2 = CrawlWebsiteForSitemap(
        website_url="https://example.com",
        max_depth=3,
        max_urls_per_level=10,
        exclude_patterns=["/login", "/admin", ".pdf"]
    )
    result2 = tool2.run()
    print(result2)

