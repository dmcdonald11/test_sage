# Environment Variable Configuration Update

## Overview

The `ConvertPdfToMarkdown` tool now supports configuration via environment variables, allowing you to set default behavior globally without specifying parameters on every call.

## New Environment Variables

### ANNOTATE_IMAGES
Controls whether image annotation is enabled by default.

**Values:**
- `true`, `1`, `yes`, `on` - Enable image annotation
- `false`, `0`, `no`, `off` - Disable image annotation (default)

**Example:**
```bash
ANNOTATE_IMAGES=true
```

### IMAGE_SCALE
Sets the default image quality scale when annotation is enabled.

**Values:**
- `1` - Lower quality, faster processing
- `2` - Balanced quality and speed (default)
- `3` - Higher quality, slower processing

**Example:**
```bash
IMAGE_SCALE=2
```

## Configuration Priority

The tool uses a three-tier priority system:

1. **Explicit Parameters** (Highest Priority)
   - Values passed directly when creating the tool
   
2. **Environment Variables** (Medium Priority)
   - Values from `.env` file or system environment
   
3. **Default Values** (Lowest Priority)
   - Built-in defaults: `ANNOTATE_IMAGES=false`, `IMAGE_SCALE=2`

## Usage Examples

### Example 1: Use Environment Variable Defaults

**.env file:**
```bash
OPENAI_API_KEY=sk-proj-...
IMAGE_MODEL=gpt-4o-mini
ANNOTATE_IMAGES=true
IMAGE_SCALE=2
```

**Code:**
```python
# Uses ANNOTATE_IMAGES=true from environment
tool = ConvertPdfToMarkdown(file_path="document.pdf")
result = tool.run()
```

### Example 2: Override Environment Variables

**.env file:**
```bash
ANNOTATE_IMAGES=true  # Set globally
IMAGE_SCALE=2
```

**Code:**
```python
# Override: disable annotation for this specific call
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    annotate_images=False  # Overrides environment variable
)
result = tool.run()
```

### Example 3: Partial Override

**.env file:**
```bash
ANNOTATE_IMAGES=true
IMAGE_SCALE=2
```

**Code:**
```python
# Keep annotation enabled from env, but use higher quality
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    images_scale=3  # Override only scale, annotation stays True from env
)
result = tool.run()
```

### Example 4: No Environment Variables

**Code:**
```python
# No .env configuration - uses defaults (annotation off, scale 2)
tool = ConvertPdfToMarkdown(file_path="document.pdf")
# This will NOT annotate images (default behavior)
```

## Complete .env Example

```bash
# OpenAI Configuration (required for image annotation)
OPENAI_API_KEY=sk-proj-your-api-key-here
IMAGE_MODEL=gpt-4o-mini

# Image Annotation Defaults (optional)
ANNOTATE_IMAGES=true
IMAGE_SCALE=2

# Other optional settings
# DATABASE_URL=postgresql://...
```

## Benefits

1. **Consistency**: Set default behavior once for all conversions
2. **Flexibility**: Override defaults when needed for specific documents
3. **Convenience**: No need to specify the same parameters repeatedly
4. **Environment-Specific**: Different settings for dev/staging/production
5. **Cost Control**: Disable annotation globally to avoid API costs, enable selectively

## Migration from Previous Version

### Before (Always Required Parameters)
```python
# Had to specify every time
tool = ConvertPdfToMarkdown(
    file_path="doc.pdf",
    annotate_images=True,
    images_scale=2
)
```

### After (Environment Variables)
```python
# Set once in .env:
# ANNOTATE_IMAGES=true
# IMAGE_SCALE=2

# Use everywhere without repetition
tool = ConvertPdfToMarkdown(file_path="doc.pdf")
```

## Use Cases

### Use Case 1: Development Environment
```bash
# .env.development
ANNOTATE_IMAGES=false  # Save costs during development
```

### Use Case 2: Production Environment
```bash
# .env.production
ANNOTATE_IMAGES=true   # Full features in production
IMAGE_SCALE=3          # Highest quality
```

### Use Case 3: Batch Processing
```bash
# .env
ANNOTATE_IMAGES=true   # Enable for all documents in batch
IMAGE_SCALE=1          # Fast processing for large batches
```

### Use Case 4: Selective Processing
```bash
# .env
ANNOTATE_IMAGES=false  # Disabled by default
```

```python
# Enable only for specific important documents
important_doc = ConvertPdfToMarkdown(
    file_path="annual_report.pdf",
    annotate_images=True  # Override for this document
)

# Regular documents use default (no annotation)
regular_doc = ConvertPdfToMarkdown(file_path="invoice.pdf")
```

## Implementation Details

### How It Works

The tool checks for environment variables at runtime:

```python
# Pseudocode of the logic
if annotate_images parameter is None:
    read from ANNOTATE_IMAGES environment variable
    if not set, default to False

if images_scale parameter is None:
    read from IMAGE_SCALE environment variable
    if not set, default to 2
```

### Accepted Boolean Values

The `ANNOTATE_IMAGES` variable accepts multiple formats (case-insensitive):

- **Enable**: `true`, `True`, `TRUE`, `1`, `yes`, `Yes`, `YES`, `on`, `On`, `ON`
- **Disable**: `false`, `False`, `FALSE`, `0`, `no`, `No`, `NO`, `off`, `Off`, `OFF`

## Testing

### Test Environment Variable Reading
```python
import os
os.environ["ANNOTATE_IMAGES"] = "true"
os.environ["IMAGE_SCALE"] = "3"

tool = ConvertPdfToMarkdown(file_path="test.pdf")
# Will use: annotate_images=True, images_scale=3
```

### Test Parameter Override
```python
os.environ["ANNOTATE_IMAGES"] = "true"

tool = ConvertPdfToMarkdown(
    file_path="test.pdf",
    annotate_images=False  # Overrides environment
)
# Will use: annotate_images=False
```

## Troubleshooting

### Issue: Environment Variable Not Working

**Problem:** Setting `ANNOTATE_IMAGES=true` but images aren't being annotated.

**Solutions:**
1. Check `.env` file is in the project root
2. Verify no typos in variable names (case-sensitive)
3. Ensure `python-dotenv` is installed and loading `.env`
4. Check if parameter is being explicitly set (overriding env var)
5. Restart your application after changing `.env`

### Issue: Invalid IMAGE_SCALE Value

**Problem:** Set `IMAGE_SCALE=5` but getting default value.

**Solution:** IMAGE_SCALE only accepts 1, 2, or 3. Invalid values fall back to default (2).

### Issue: ANNOTATE_IMAGES Not Recognized

**Problem:** Set `ANNOTATE_IMAGES=enabled` but annotation is disabled.

**Solution:** Use accepted values: `true`, `1`, `yes`, or `on` (not `enabled`).

## Related Documentation

- [ENV_SETUP.md](../ENV_SETUP.md) - Complete environment setup guide
- [PDF_IMAGE_ANNOTATION.md](PDF_IMAGE_ANNOTATION.md) - Image annotation feature guide
- [FEATURE_UPDATE_SUMMARY.md](../FEATURE_UPDATE_SUMMARY.md) - Original feature implementation

---

**Version:** 1.1  
**Date:** October 17, 2025  
**Tool:** ConvertPdfToMarkdown

