# External Image References Update

## Summary

Successfully implemented external image reference support for the `ConvertPdfToMarkdown` tool, following the pattern shown in the docling example notebook `00_docling-basic.ipynb`.

## What Was Added

### New Parameter: `save_images_as_files`

```python
save_images_as_files: bool = Field(
    default=False,
    description="Whether to save images as separate external files referenced in the markdown."
)
```

### Implementation

The tool now uses Docling's `save_as_markdown()` method with `ImageRefMode.REFERENCED` when external images are requested:

```python
from docling_core.types.doc.document import ImageRefMode

document.save_as_markdown(
    output_path,
    image_mode=ImageRefMode.REFERENCED,
    include_annotations=self.annotate_images
)
```

## Usage Examples

### Basic Usage

```python
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True
)
```

### With All Features

```python
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True,
    annotate_images=True,
    images_scale=3,
    output_filename="my_document"
)
```

### Output Format

**Markdown file references images:**
```markdown
![Image](document_artifacts/image_000000_[hash].png)
```

**Directory structure:**
```
test_output/
├── document.md
└── document_artifacts/
    ├── image_000000_[hash].png
    ├── image_000001_[hash].png
    └── ...
```

## Test Results

✅ **Test 1**: Basic PDF conversion (29,380 chars)  
✅ **Test 2**: With image annotation (33,173 chars)  
✅ **Test 3**: With external image references (33,423 chars) - Images referenced as external files  
✅ **Test 4**: Usage examples displayed  

## Key Features

1. **Standard Markdown Format**: Uses `![Image](path)` syntax
2. **Compatible with Image Annotation**: Works seamlessly with AI descriptions
3. **Organized Structure**: Images saved in separate folder
4. **Flexible**: Can be combined with all other tool features
5. **Follows Docling Best Practices**: Uses official `ImageRefMode.REFERENCED` API

## Benefits

### For Documentation Sites
- Perfect for static site generators (Hugo, Jekyll, MkDocs, Docusaurus)
- Images in standard format recognized by all generators
- Easy to manage and optimize images separately

### For Version Control
- Clean text diffs in markdown
- Image changes tracked separately
- Better for team collaboration

### For Image Management
- Can optimize images post-processing
- Can replace images without changing markdown
- Can reuse images across documents

### For Portability
- Standard markdown format
- Compatible with all markdown viewers
- Easy to migrate to different systems

## Updated Files

1. ✅ **sage_agent/tools/ConvertPdfToMarkdown.py**
   - Added `save_images_as_files` parameter
   - Added `ImageRefMode` import
   - Updated save logic to handle both inline and external images
   - Added Test 3 for external image references
   - Updated usage examples

2. ✅ **sage_agent/instructions.md**
   - Documented new external image references feature
   - Added usage guidance

3. ✅ **docs/EXTERNAL_IMAGE_REFERENCES.md**
   - Complete feature documentation
   - Usage examples
   - Best practices
   - Troubleshooting guide

4. ✅ **EXTERNAL_IMAGES_UPDATE.md**
   - This summary document

## Comparison with Previous Versions

| Feature | Before | After |
|---------|--------|-------|
| Image handling | Inline only | Inline or External |
| Markdown compatibility | Limited | Standard format |
| Image management | Within markdown | Separate files |
| Documentation site support | Manual | Native support |
| Version control | Mixed text/binary | Separated |

## Code Changes

### Before
```python
# Only inline images
markdown_output = document.export_to_markdown()
```

### After
```python
# Flexible: inline or external
if self.save_images_as_files:
    document.save_as_markdown(
        output_path,
        image_mode=ImageRefMode.REFERENCED,
        include_annotations=self.annotate_images
    )
else:
    markdown_output = document.export_to_markdown()
```

## Backward Compatibility

✅ **100% Backward Compatible**
- Default behavior unchanged (`save_images_as_files=False`)
- Existing code works without modifications
- New feature is opt-in

## Testing Commands

```bash
# Test basic conversion
python sage_agent/tools/ConvertPdfToMarkdown.py

# Test with external images
tool = ConvertPdfToMarkdown(
    file_path="uploads/docling.pdf",
    save_images_as_files=True
)
```

## Environment Variables

No new environment variables required. The feature works with existing configuration:
- `OPENAI_API_KEY` (for image annotation)
- `IMAGE_MODEL` (for image annotation)
- `ANNOTATE_IMAGES` (for default annotation behavior)
- `IMAGE_SCALE` (for default image quality)

## Dependencies

No new dependencies required:
- ✅ `docling>=2.0.0` (already required)
- ✅ `docling-core>=2.0.0` (already required)
- ✅ `ImageRefMode` from `docling_core.types.doc.document` (built-in)

## Use Cases

### 1. Documentation Generation
```python
# Generate docs for a static site
tool = ConvertPdfToMarkdown(
    file_path="api_docs.pdf",
    save_images_as_files=True,
    annotate_images=True
)
```

### 2. Knowledge Base Building
```python
# Create searchable knowledge base
tool = ConvertPdfToMarkdown(
    file_path="manual.pdf",
    save_images_as_files=True,
    annotate_images=True,  # Makes images searchable
    images_scale=3
)
```

### 3. Report Conversion
```python
# Convert reports with reusable images
tool = ConvertPdfToMarkdown(
    file_path="quarterly_report.pdf",
    save_images_as_files=True
)
```

## Example Output

**JSON Response:**
```json
{
  "success": true,
  "pdf_path": "uploads/document.pdf",
  "markdown_path": "test_output/document.md",
  "content_length": 33423,
  "annotated_images": true,
  "external_images": true,
  "message": "Successfully converted PDF to markdown and saved to test_output/document.md (with AI-powered image annotations) (images saved as external files)"
}
```

## Next Steps for Users

1. **Update your code** to use `save_images_as_files=True` when needed
2. **Test with your PDFs** to see how images are extracted
3. **Optimize images** post-processing if needed for web use
4. **Combine features** for maximum benefit (annotation + external images)

## Related Documentation

- [PDF_IMAGE_ANNOTATION.md](docs/PDF_IMAGE_ANNOTATION.md) - Image annotation feature
- [ENV_VAR_CONFIG_UPDATE.md](docs/ENV_VAR_CONFIG_UPDATE.md) - Environment variable configuration
- [EXTERNAL_IMAGE_REFERENCES.md](docs/EXTERNAL_IMAGE_REFERENCES.md) - Complete feature guide
- [00_docling-basic.ipynb](examples/docling-images/00_docling-basic.ipynb) - Original docling example

## Conclusion

The external image references feature is now fully implemented and tested. It follows docling's best practices and provides users with flexibility in how they handle images in their PDF to markdown conversions.

---

**Status**: ✅ COMPLETE  
**Date**: October 17, 2025  
**Version**: 1.2  
**Tool**: ConvertPdfToMarkdown

