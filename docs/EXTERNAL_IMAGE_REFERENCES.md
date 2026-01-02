# External Image References Feature

## Overview

The `ConvertPdfToMarkdown` tool now supports saving images as external files referenced in the markdown output, similar to the example shown in the docling documentation. This feature provides better separation between text content and image assets.

## How It Works

When `save_images_as_files=True` is set, the tool uses Docling's `save_as_markdown()` method with `ImageRefMode.REFERENCED` to:

1. Extract images from the PDF
2. Save them as separate PNG files in a subfolder
3. Reference them in the markdown using standard markdown image syntax: `![Image](path/to/image.png)`

## Usage

### Basic Example

```python
from sage_agent.tools.ConvertPdfToMarkdown import ConvertPdfToMarkdown

tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True
)
result = tool.run()
```

### With Image Annotation

```python
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True,
    annotate_images=True,  # Add AI descriptions to images
    images_scale=2
)
result = tool.run()
```

### Output Structure

When images are saved externally:

```
test_output/
├── document.md                          # Main markdown file
└── document_artifacts/                  # Image folder (created by docling)
    ├── image_000000_[hash].png
    ├── image_000001_[hash].png
    └── ...
```

The markdown file will contain references like:

```markdown
## Section Title

![Image](document_artifacts/image_000000_4f05ea6de89ce20493a5d9cc2305a4feb948c7bb.png)

Some text content...

![Image](document_artifacts/image_000001_0b6a3cd25d375e942c65d4ff1ccf1bb92491db45.png)
```

## Parameters

### save_images_as_files
- **Type**: `bool`
- **Default**: `False`
- **Description**: Whether to save images as separate external files referenced in the markdown
- **When to use**: 
  - You want to manage images separately from the markdown
  - You need to edit or optimize images independently
  - You're building a documentation system that needs separate asset folders
  - You want standard markdown image references for better compatibility

## Comparison: Inline vs External

### Inline Images (Default: `save_images_as_files=False`)

**Advantages:**
- Single file output
- No missing image files
- Easy to share and move
- Self-contained document

**Disadvantages:**
- Larger markdown file
- Can't edit images separately
- May not be compatible with all markdown viewers

### External Images (`save_images_as_files=True`)

**Advantages:**
- Separate, manageable image files
- Smaller markdown file
- Can optimize/replace images
- Standard markdown format
- Better for version control
- Better for documentation sites

**Disadvantages:**
- Multiple files to manage
- Image files can be separated from markdown
- Requires proper path handling

## Use Cases

### 1. Documentation Sites

```python
# Generate docs with external images for a static site generator
tool = ConvertPdfToMarkdown(
    file_path="api_documentation.pdf",
    output_filename="api_docs",
    save_images_as_files=True,
    annotate_images=True
)
```

Perfect for systems like:
- Jekyll
- Hugo
- MkDocs
- Docusaurus
- GitBook

### 2. Version Control

External images make it easier to track changes in version control:
- Text changes in markdown show clearly in diffs
- Image changes are separate binary file updates
- Can optimize images without changing markdown

### 3. Image Optimization

```python
# Extract images separately for optimization
tool = ConvertPdfToMarkdown(
    file_path="large_report.pdf",
    save_images_as_files=True
)

# Then optimize images with tools like:
# - imagemin
# - pngquant
# - webp conversion
```

### 4. Multi-Format Publishing

```python
# Use same images across different formats
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True
)

# Images can now be:
# - Referenced in HTML
# - Used in presentations
# - Included in other documents
```

## Combined with Image Annotation

The external image feature works seamlessly with AI-powered image annotation:

```python
tool = ConvertPdfToMarkdown(
    file_path="technical_doc.pdf",
    save_images_as_files=True,       # Images saved separately
    annotate_images=True,             # AI descriptions added
    images_scale=3                    # High quality for analysis
)
```

**Output:**
```markdown
![Image](doc_artifacts/image_000000.png)

<!--<annotation kind="description">-->
The diagram shows a three-tier architecture with frontend, 
application layer, and database components...
<!--<annotation/>-->
```

## Implementation Details

### From Docling's API

The feature uses Docling's official API:

```python
from docling_core.types.doc.document import ImageRefMode

document.save_as_markdown(
    output_path,
    image_mode=ImageRefMode.REFERENCED,
    include_annotations=annotate_images
)
```

### Image Naming Convention

Docling automatically generates image filenames with:
- Sequential numbering: `image_000000`, `image_000001`, etc.
- Content hash: Prevents duplicate images
- PNG format: Universal compatibility

### Path Handling

Image paths in markdown are relative to the markdown file location, making the document portable when moved with its image folder.

## Troubleshooting

### Issue: No Images Extracted

**Possible Causes:**
1. PDF has vector graphics instead of raster images
2. Images are embedded in a way docling doesn't extract
3. PDF has no images, only text

**Solution:** Check the PDF in a viewer to confirm it has extractable images.

### Issue: Broken Image Links

**Possible Cause:** Markdown file moved without image folder

**Solution:** Keep markdown and image folder together, or use absolute paths.

### Issue: Image Quality Poor

**Solution:** Increase `images_scale` parameter:
```python
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True,
    images_scale=3  # Higher quality
)
```

## Example: Complete Workflow

```python
import json
from sage_agent.tools.ConvertPdfToMarkdown import ConvertPdfToMarkdown
from pathlib import Path

# Convert with external images
tool = ConvertPdfToMarkdown(
    file_path="reports/annual_report.pdf",
    output_filename="annual_report_2024",
    save_images_as_files=True,
    annotate_images=True,
    images_scale=2
)

result_str = tool.run()
result = json.loads(result_str)

if result["success"]:
    print(f"✓ Markdown saved: {result['markdown_path']}")
    print(f"✓ Content length: {result['content_length']} chars")
    print(f"✓ External images: {result['external_images']}")
    
    # Check for image folder
    md_path = Path(result['markdown_path'])
    image_folder = md_path.parent / f"{md_path.stem}_artifacts"
    
    if image_folder.exists():
        images = list(image_folder.glob("*.png"))
        print(f"✓ Extracted {len(images)} images")
    else:
        print("  No separate images (embedded or vector graphics)")
else:
    print(f"✗ Error: {result['error']}")
```

## Best Practices

1. **Use for Documentation**: External images work best for documentation projects
2. **Keep Together**: Always move markdown and image folder together
3. **Version Control**: Commit both markdown and image files
4. **Optimize Images**: Post-process images for web use if needed
5. **Combine Features**: Use with image annotation for best results

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling Example Notebook](../../examples/docling-images/00_docling-basic.ipynb)
- [PDF_IMAGE_ANNOTATION.md](PDF_IMAGE_ANNOTATION.md)
- [ENV_VAR_CONFIG_UPDATE.md](ENV_VAR_CONFIG_UPDATE.md)

---

**Version:** 1.0  
**Date:** October 17, 2025  
**Feature:** External Image References

