# Sage Agent - Web Crawling Specialist

## Overview

The Sage Agent has been successfully configured as a specialized web crawling and knowledge extraction agent. It uses the `CrawlSinglePage` tool, which is based on the Single Page Crawling Strategy from Crawl4AI.

## What Was Created

### 1. CrawlSinglePage Tool
**Location**: `sage_agent/tools/CrawlSinglePage.py`

A production-ready tool that crawls individual web pages and extracts structured content. 

**Key Features**:
- ✅ Intelligent documentation site detection (Docusaurus, VitePress, GitBook, MkDocs, etc.)
- ✅ Retry logic with exponential backoff (default: 3 attempts)
- ✅ URL transformation for GitHub files (converts blob URLs to raw content)
- ✅ Content validation (ensures minimum 50 characters)
- ✅ Supports streaming for parallel processing
- ✅ Customizable page timeouts and wait conditions
- ✅ Returns structured JSON with markdown, HTML, title, links, and metadata

**Tool Parameters**:
```python
CrawlSinglePage(
    url="https://example.com",           # Required: URL to crawl
    is_documentation_site=False,         # Optional: Special handling for docs sites
    retry_count=3                        # Optional: Number of retry attempts
)
```

**Return Format**:
```json
{
  "success": true,
  "url": "https://example.com",
  "markdown": "# Content...",
  "html": "<html>...</html>",
  "title": "Page Title",
  "links": ["url1", "url2"],
  "content_length": 1234
}
```

### 2. Sage Agent Configuration
**Location**: `sage_agent/sage_agent.py`

The agent has been configured with:
- **Name**: SageAgent
- **Model**: gpt-5 with reasoning enabled
- **Description**: Web crawling and knowledge extraction specialist
- **Tools**: CrawlSinglePage
- **Max Tokens**: 25,000

### 3. Agent Instructions
**Location**: `sage_agent/instructions.md`

Comprehensive instructions for the agent including:
- How to identify documentation sites vs regular sites
- When to use the CrawlSinglePage tool
- How to process and present results
- URL pattern recognition
- Error handling guidance

## How to Use

### Option 1: Add to Existing Agency

Add the Sage Agent to your agency in `agency.py`:

```python
from sage_agent import sage_agent

def create_agency(load_threads_callback=None):
    agency = Agency(
        document_processor,
        communication_flows=[
            (document_processor, sage_agent),  # Allow document_processor to use sage_agent
        ],
        shared_instructions="shared_instructions.md",
        load_threads_callback=load_threads_callback,
    )
    return agency
```

### Option 2: Use Standalone

Test the agent standalone:

```python
from sage_agent import sage_agent

# Send a message to the agent
response = sage_agent.get_response("Crawl this URL: https://docs.python.org/3/")
print(response)
```

### Option 3: Use Tool Directly

Import and use the tool directly in your code:

```python
from sage_agent.tools.CrawlSinglePage import CrawlSinglePage
import json

# Crawl a documentation site
tool = CrawlSinglePage(
    url="https://docs.pydantic.dev/latest/",
    is_documentation_site=True,
    retry_count=3
)

result_json = tool.run()
result = json.loads(result_json)

if result['success']:
    print(f"Title: {result['title']}")
    print(f"Content: {result['markdown'][:200]}...")
    print(f"Links found: {len(result['links'])}")
else:
    print(f"Error: {result['error']}")
```

## Tool Implementation Details

### Documentation Site Detection

The tool automatically detects and configures crawling for these documentation frameworks:

| Framework | URL Pattern | Wait Selector |
|-----------|-------------|---------------|
| Docusaurus | `docusaurus` | `.markdown, .theme-doc-markdown, article` |
| VitePress | `vitepress` | `.VPDoc, .vp-doc, .content` |
| GitBook | `gitbook` | `.markdown-section, .page-wrapper` |
| MkDocs | `mkdocs` | `.md-content, article` |
| Docsify | `docsify` | `#main, .markdown-section` |
| CopilotKit | `copilotkit` | `div[class*="content"], div[class*="doc"]` |
| Milkdown | `milkdown` | `main, article, .prose` |

### GitHub URL Transformation

The tool automatically transforms GitHub blob URLs to raw content URLs:

```
Before: https://github.com/user/repo/blob/main/README.md
After:  https://raw.githubusercontent.com/user/repo/main/README.md
```

### Retry Strategy

- **Attempt 1**: Uses cached content (if available), waits 1 second before retry
- **Attempt 2**: Bypasses cache for fresh content, waits 2 seconds before retry  
- **Attempt 3**: Bypasses cache, waits 4 seconds before retry
- **After all attempts**: Returns error with detailed message

### Content Validation

The tool validates crawled content before returning:
1. ✅ Crawl must be successful (`result.success == True`)
2. ✅ Markdown content must exist
3. ✅ Content must be at least 50 characters long

## Known Limitations

1. **Windows Unicode Handling**: The test cases may show encoding warnings on Windows due to Crawl4AI's internal Unicode handling. This doesn't affect the tool's functionality when used by the agent, as JSON output uses `ensure_ascii=True`.

2. **Asyncio Cleanup Warnings**: You may see warnings about "unclosed transport" on Windows. These are harmless cleanup warnings from asyncio and don't affect functionality.

3. **Authentication**: The tool cannot crawl pages that require authentication or login.

4. **Rate Limiting**: The tool doesn't include rate limiting. For crawling many pages, implement delays between calls.

## Dependencies

All required dependencies are already in `requirements.txt`:
- `crawl4ai>=0.7.0` - Web crawling engine
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=4.9.0` - XML/HTML processing
- `aiohttp>=3.9.0` - Async HTTP client

## Next Steps

1. **Add to Agency**: Integrate the Sage Agent into your agency's communication flows
2. **Test Crawling**: Test with various URLs to ensure it works for your use cases
3. **Extend Tools**: Add more crawling tools (sitemap crawling, recursive crawling, etc.)
4. **Connect to Knowledge Base**: Integrate with your knowledge base for storing crawled content

## Example Use Cases

1. **Documentation Scraping**: Crawl official documentation sites for RAG systems
2. **Content Extraction**: Extract clean markdown from web pages
3. **Link Discovery**: Find all links on a page for further processing
4. **GitHub File Access**: Read README files and documentation from GitHub repositories
5. **Knowledge Base Population**: Feed crawled content into vector databases

## Support

For issues or questions:
- Check the SINGLE_PAGE_CRAWLING.md documentation for technical details
- Review the tool's logging output for debugging
- Test with simpler URLs (like example.com) to isolate issues
- Ensure all dependencies are correctly installed

---

**Status**: ✅ Production Ready  
**Created**: 2025-10-08  
**Version**: 1.0.0

