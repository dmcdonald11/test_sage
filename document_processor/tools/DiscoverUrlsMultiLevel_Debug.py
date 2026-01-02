"""
Debug version of DiscoverUrlsMultiLevel that shows raw URLs before deduplication.
This helps understand why deduplication is necessary.
"""
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
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()


class DiscoverUrlsMultiLevelDebug(BaseTool):
    """
    DEBUG VERSION: Shows raw URLs before deduplication to understand duplicate patterns.
    """

    start_url: str = Field(
        ..., 
        description="The starting URL to begin crawling from"
    )
    
    max_depth: int = Field(
        default=2,
        description="Maximum depth to crawl (lower for debug)"
    )
    
    max_urls_per_level: int = Field(
        default=5,
        description="Maximum number of URLs to crawl per depth level"
    )

    def run(self):
        """
        Executes multi-level URL discovery with detailed duplicate tracking.
        """
        try:
            result = asyncio.run(self._discover_urls_async())
            return result
        except Exception as e:
            return f"Error during multi-level URL discovery: {str(e)}"

    async def _discover_urls_async(self):
        """
        Asynchronous implementation with detailed logging.
        """
        # Tracking structures
        discovered_urls: Dict[int, Set[str]] = {i: set() for i in range(self.max_depth + 1)}
        visited_urls: Set[str] = set()
        all_discovered_urls: Set[str] = set()
        
        # Raw link tracking for each page
        raw_links_by_page: Dict[str, List[str]] = {}
        
        base_domain = urlparse(self.start_url).netloc
        
        # Add starting URL
        discovered_urls[0].add(self.start_url)
        all_discovered_urls.add(self.start_url)
        
        print(f"\n{'='*80}")
        print(f"DEBUG: Multi-Level URL Discovery")
        print(f"{'='*80}")
        print(f"Starting URL: {self.start_url}")
        print(f"Max depth: {self.max_depth}, Max URLs per level: {self.max_urls_per_level}")
        print(f"{'='*80}\n")
        
        # Browser configuration
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )
        
        crawler_config = CrawlerRunConfig(
            exclude_external_links=True,
            exclude_social_media_links=True,
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
        )
        
        # Crawl each level
        async with AsyncWebCrawler(config=browser_config, verbose=False) as crawler:
            for current_depth in range(self.max_depth):
                print(f"\n{'='*80}")
                print(f"LEVEL {current_depth}")
                print(f"{'='*80}\n")
                
                urls_to_crawl = list(discovered_urls[current_depth] - visited_urls)
                urls_to_crawl = urls_to_crawl[:self.max_urls_per_level]
                
                if not urls_to_crawl:
                    print(f"No new URLs to crawl at level {current_depth}\n")
                    break
                
                print(f"Crawling {len(urls_to_crawl)} URLs at this level:\n")
                
                for idx, url in enumerate(urls_to_crawl, 1):
                    if url in visited_urls:
                        continue
                    
                    try:
                        print(f"[{idx}/{len(urls_to_crawl)}] Crawling: {url}")
                        
                        result = await crawler.arun(url=url, config=crawler_config)
                        
                        if not result.success:
                            print(f"    ❌ Failed: {result.error_message}\n")
                            visited_urls.add(url)
                            continue
                        
                        visited_urls.add(url)
                        
                        # Extract internal links
                        internal_links = result.links.get("internal", [])
                        
                        # Store raw links for this page
                        raw_links_by_page[url] = []
                        
                        print(f"    ✅ Success! Found {len(internal_links)} internal links")
                        
                        # Track: new vs duplicate
                        new_urls = []
                        duplicate_urls = []
                        
                        # Process each link
                        for link_data in internal_links:
                            if isinstance(link_data, dict):
                                link_url = link_data.get("href", "")
                            else:
                                link_url = str(link_data)
                            
                            # Normalize the URL
                            normalized_url = self._normalize_url(link_url, url)
                            
                            # Track raw link
                            raw_links_by_page[url].append(normalized_url)
                            
                            # Check if it's the same domain
                            if urlparse(normalized_url).netloc == base_domain:
                                if normalized_url not in all_discovered_urls:
                                    discovered_urls[current_depth + 1].add(normalized_url)
                                    all_discovered_urls.add(normalized_url)
                                    new_urls.append(normalized_url)
                                else:
                                    duplicate_urls.append(normalized_url)
                        
                        print(f"    📊 New URLs: {len(new_urls)}, Duplicates: {len(duplicate_urls)}")
                        
                        # Show some examples
                        if new_urls:
                            print(f"    🆕 New URLs (showing first 3):")
                            for new_url in new_urls[:3]:
                                print(f"       • {new_url}")
                            if len(new_urls) > 3:
                                print(f"       ... and {len(new_urls) - 3} more")
                        
                        if duplicate_urls:
                            print(f"    🔄 Duplicates (showing first 3):")
                            for dup_url in duplicate_urls[:3]:
                                print(f"       • {dup_url}")
                            if len(duplicate_urls) > 3:
                                print(f"       ... and {len(duplicate_urls) - 3} more")
                        
                        print()  # Blank line between pages
                        
                    except Exception as e:
                        print(f"    ❌ Error: {str(e)}\n")
                        visited_urls.add(url)
                        continue
        
        # Generate detailed report
        print(f"\n{'='*80}")
        print(f"DETAILED DEDUPLICATION REPORT")
        print(f"{'='*80}\n")
        
        report = ""
        
        # Show raw links for each crawled page
        report += "RAW LINKS FOUND ON EACH PAGE:\n"
        report += "=" * 80 + "\n\n"
        
        for page_url, links in raw_links_by_page.items():
            report += f"Page: {page_url}\n"
            report += f"Found {len(links)} internal links:\n"
            
            # Count duplicates within this page
            link_counts = {}
            for link in links:
                link_counts[link] = link_counts.get(link, 0) + 1
            
            # Show all links with counts
            for link, count in sorted(link_counts.items()):
                if count > 1:
                    report += f"  [{count}x] {link} (appears {count} times on this page)\n"
                else:
                    report += f"  [1x] {link}\n"
            
            report += "\n"
        
        # Summary statistics
        total_raw_links = sum(len(links) for links in raw_links_by_page.values())
        unique_urls = len(all_discovered_urls)
        duplicates = total_raw_links - unique_urls
        
        report += "\n" + "=" * 80 + "\n"
        report += "SUMMARY STATISTICS\n"
        report += "=" * 80 + "\n\n"
        report += f"Total Pages Crawled: {len(raw_links_by_page)}\n"
        report += f"Total Raw Links Found: {total_raw_links}\n"
        report += f"Unique URLs Discovered: {unique_urls}\n"
        report += f"Duplicates Prevented: {duplicates}\n"
        if total_raw_links > 0:
            report += f"Deduplication Rate: {(duplicates / total_raw_links * 100):.1f}%\n"
        
        report += "\n" + "=" * 80 + "\n"
        report += "ALL UNIQUE URLs (after deduplication):\n"
        report += "=" * 80 + "\n\n"
        
        for level in range(self.max_depth + 1):
            urls_at_level = discovered_urls[level]
            if urls_at_level:
                report += f"\nLevel {level} ({len(urls_at_level)} URLs):\n"
                for url in sorted(urls_at_level):
                    status = "[VISITED]" if url in visited_urls else "[DISCOVERED]"
                    report += f"  {status} {url}\n"
        
        print(report)
        return report
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize a URL."""
        if not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized


if __name__ == "__main__":
    print("\nDebug Tool: Multi-Level URL Discovery with Deduplication Analysis")
    print("=" * 80)
    
    tool = DiscoverUrlsMultiLevelDebug(
        start_url="https://docs.crawl4ai.com",
        max_depth=2,  # Lower depth for detailed analysis
        max_urls_per_level=5  # Fewer URLs for clearer output
    )
    
    result = tool.run()

