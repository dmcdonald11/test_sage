# Multi-Level URL Discovery with Crawl4AI

## Overview

The `DiscoverUrlsMultiLevel` tool uses Crawl4AI to recursively discover and extract URLs from a website up to a specified depth level (e.g., 3 levels deep).

## How It Works

The tool implements a **breadth-first crawling strategy**:

1. **Level 0**: Crawls the starting URL and extracts all internal links
2. **Level 1**: Crawls links discovered at Level 0
3. **Level 2**: Crawls links discovered at Level 1
4. **Level N**: Continues until `max_depth` is reached

At each level, the tool:
- Extracts internal links using Crawl4AI's built-in `result.links.get("internal", [])`
- Normalizes URLs (removes duplicates, fragments, trailing slashes)
- Respects rate limits (`max_urls_per_level`)
- Tracks visited vs discovered URLs

## Features

### Crawl4AI Integration

The tool leverages Crawl4AI's powerful features:

```python
# Automatic internal link extraction
result = await crawler.arun(url=url, config=crawler_config)
internal_links = result.links.get("internal", [])

# Configuration options
crawler_config = CrawlerRunConfig(
    exclude_external_links=True,      # Only internal links
    exclude_social_media_links=True,  # Skip social media
    cache_mode=CacheMode.BYPASS,      # Fresh results
    page_timeout=30000,               # 30 second timeout
)
```

### Parameters

- **start_url** (required): The starting URL to begin crawling
- **max_depth** (default: 3): Maximum depth to crawl
  - `1` = start URL only
  - `2` = start + linked pages
  - `3` = start + 2 levels of links
- **max_urls_per_level** (default: 50): Rate limiting per level
- **exclude_patterns** (optional): URL patterns to skip (e.g., `['/login', '/admin', '.pdf']`)

## Usage Examples

### Basic 3-Level Crawl

```python
from document_processor.tools.DiscoverUrlsMultiLevel import DiscoverUrlsMultiLevel

tool = DiscoverUrlsMultiLevel(
    start_url="https://docs.crawl4ai.com",
    max_depth=3,
    max_urls_per_level=50
)

result = tool.run()
print(result)
```

**Output:**
```
Multi-Level URL Discovery Complete!
=====================================

Starting URL: https://docs.crawl4ai.com
Max Depth: 3

Deduplication Statistics:
  Total Links Found: 487
  Unique URLs Discovered: 55
  Duplicates Prevented: 433
  Deduplication Rate: 88.9%

Crawl Statistics:
  URLs Visited: 11
  URLs Remaining: 44

URLs by Level:
  Level 0: 1 URLs
  Level 1: 54 URLs
  Level 2: 0 URLs
  Level 3: 0 URLs

Full URL List (55 URLs):
============================================================
[Level 0] [V] Visited: https://docs.crawl4ai.com
[Level 1] [D] Discovered: https://docs.crawl4ai.com/
[Level 1] [D] Discovered: https://docs.crawl4ai.com/advanced/adaptive-strategies
...
```

Note the **88.9% deduplication rate** - the tool prevented 433 duplicate URLs from appearing in the results!

### With Exclusion Patterns

```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://example.com",
    max_depth=3,
    max_urls_per_level=50,
    exclude_patterns=[
        "/login",           # Skip login pages
        "/admin",           # Skip admin pages
        ".pdf",             # Skip PDFs
        "/blog/archive",    # Skip blog archives
        "/api/",            # Skip API docs
    ]
)

result = tool.run()
```

### Shallow Crawl (2 levels)

```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://example.com",
    max_depth=2,
    max_urls_per_level=20  # Lower limit for faster results
)

result = tool.run()
```

### Deep Crawl (5 levels)

```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://example.com",
    max_depth=5,
    max_urls_per_level=100  # Higher limit for comprehensive discovery
)

result = tool.run()
```

## Real-World Example: Crawl4AI Documentation

When crawling `https://docs.crawl4ai.com` with 3 levels and 10 URLs per level:

```
--- Crawling Level 0 ---
  Crawling: https://docs.crawl4ai.com
  Found 55 internal links

--- Crawling Level 1 ---
  Crawling: https://docs.crawl4ai.com/api/arun_many
  Crawling: https://docs.crawl4ai.com/core/markdown-generation
  Crawling: https://docs.crawl4ai.com/core/crawler-result
  ...
  (10 URLs total)

--- Crawling Level 2 ---
  Crawling: https://docs.crawl4ai.com/blog/release-v0.7.4.md
  Crawling: https://docs.crawl4ai.com/core/quickstart
  ...
  (10 URLs total)

Result: 155 total URLs discovered across 3 levels
```

## Automatic Deduplication

The tool uses **three layers of deduplication** to ensure no duplicate URLs in the final list:

### 1. Global URL Tracking
Each URL is tracked globally and only added to ONE level (the first time it's discovered):
```python
all_discovered_urls: Set[str] = set()  # Tracks every discovered URL
```

### 2. Set-Based Storage
Python Sets automatically prevent duplicates:
```python
discovered_urls: Dict[int, Set[str]]  # Sets at each level
```

### 3. URL Normalization
URLs are normalized before comparison to catch variations:
- Converts relative URLs to absolute: `/docs` → `https://example.com/docs`
- Removes fragments: `https://example.com/page#section` → `https://example.com/page`
- Removes trailing slashes (except root): `https://example.com/docs/` → `https://example.com/docs`
- Preserves query strings: `https://example.com/search?q=test` (kept as-is)

### Real-World Example
When crawling `https://docs.crawl4ai.com`:
```
Deduplication Statistics:
  Total Links Found: 487
  Unique URLs Discovered: 55
  Duplicates Prevented: 433
  Deduplication Rate: 88.9%
```
Out of 487 total links found, **433 were duplicates** and automatically prevented!

### Common Duplicate Scenarios

Duplicates commonly occur due to:

1. **Navigation Menus**: Every page links back to home, about, contact, etc.
   ```
   Page A → Home, About, Contact
   Page B → Home, About, Contact  (duplicates!)
   Page C → Home, About, Contact  (duplicates!)
   ```

2. **Breadcrumbs**: Pages link to parent pages
   ```
   /blog/2024/post → /blog/2024 → /blog → /
   /blog/2023/post → /blog/2023 → /blog → /  (/ is duplicate)
   ```

3. **Related Content**: Articles link to each other
   ```
   Article A → Article B, Article C
   Article B → Article A, Article C  (all duplicates!)
   ```

4. **URL Variations**: Same page, different URLs
   ```
   https://example.com/page
   https://example.com/page/
   https://example.com/page#section
   https://example.com/page?utm_source=twitter
   ```
   ✅ The tool normalizes these to: `https://example.com/page`

Without deduplication, a typical 3-level crawl could have **70-90% duplicate URLs**!

## Use Cases

### 1. Sitemap Generation
Discover all pages on a website for creating a comprehensive sitemap:
```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://mywebsite.com",
    max_depth=4,
    max_urls_per_level=100
)
```

### 2. Documentation Indexing
Index all documentation pages for search or analysis:
```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://docs.example.com",
    max_depth=3,
    exclude_patterns=["/api/", "/changelog/"]
)
```

### 3. Content Auditing
Find all content pages excluding system/admin pages:
```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://myblog.com",
    max_depth=3,
    exclude_patterns=["/admin", "/login", "/wp-admin", "/feed"]
)
```

### 4. Competitive Analysis
Map out competitor website structure:
```python
tool = DiscoverUrlsMultiLevel(
    start_url="https://competitor.com",
    max_depth=3,
    max_urls_per_level=30
)
```

## Performance Considerations

### Crawl Time
- Each page typically takes 1-5 seconds to crawl
- Total time = (number of URLs visited) × (avg time per URL)
- Example: 20 URLs × 2 seconds = ~40 seconds

### Memory Usage
- URLs are stored in memory during crawling
- Each URL ~100-200 bytes
- 1000 URLs ≈ 100-200 KB (very lightweight)

### Rate Limiting
Use `max_urls_per_level` to control:
- **Server load**: Don't overwhelm target servers
- **Crawl duration**: Limit time for faster results
- **Resource usage**: Prevent excessive browser instances

## Limitations

1. **Same Domain Only**: Only crawls internal links (same domain)
2. **No JavaScript Navigation**: May miss dynamically loaded links
3. **Sequential Crawling**: Crawls one URL at a time (can be extended for parallel)
4. **No Authentication**: Doesn't handle login-protected pages

## Integration with Agents

This tool is already integrated into the `document_processor` agent and can be used for:

1. **Discovering documentation pages** before processing
2. **Building site maps** for targeted crawling
3. **Finding related content** for comprehensive analysis

## Advanced: Extending the Tool

### Add Parallel Crawling
```python
# Crawl multiple URLs simultaneously
tasks = [crawler.arun(url=url, config=config) for url in urls]
results = await asyncio.gather(*tasks)
```

### Export to JSON
```python
import json

# After running the tool, export discovered URLs
urls_by_level = {
    level: list(discovered_urls[level])
    for level in discovered_urls
}

with open("discovered_urls.json", "w") as f:
    json.dump(urls_by_level, f, indent=2)
```

### Filter by URL Pattern
```python
# Only include certain URL patterns
include_patterns = ["/docs/", "/guides/", "/tutorials/"]

if any(pattern in normalized_url for pattern in include_patterns):
    discovered_urls[current_depth + 1].add(normalized_url)
```

## Troubleshooting

### Issue: Too Many URLs Discovered
**Solution**: Reduce `max_urls_per_level` or `max_depth`

### Issue: Missing Some Pages
**Solution**: Increase `max_urls_per_level` or check `exclude_patterns`

### Issue: Crawl Taking Too Long
**Solution**: Reduce `max_depth` or `max_urls_per_level`

### Issue: Encoding Errors on Windows
**Solution**: Already handled with UTF-8 encoding fix in the code

## References

- [Crawl4AI Documentation](https://docs.crawl4ai.com)
- [Crawl4AI Link & Media Guide](https://docs.crawl4ai.com/core/link-media)
- [Crawl4AI Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling)

