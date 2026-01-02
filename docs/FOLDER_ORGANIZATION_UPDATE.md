# Folder Organization and Customization Update

## Summary

Successfully implemented two major improvements to the `ConvertPdfToMarkdown` tool:

1. **Document-Specific Folders**: Each converted document with external images gets its own dedicated folder
2. **Customizable Output Location**: The base output folder can be configured via `MD_OUTPUT_FOLDER` environment variable

## New Features

### 1. Document-Specific Folder Structure

When `save_images_as_files=True`, documents are now organized in dedicated folders:

```
{output_folder}/
└── {document_name}/
    ├── {document_name}.md
    └── {document_name}_artifacts/
        ├── image_000000_[hash].png
        ├── image_000001_[hash].png
        └── ...
```

**Example:**
```
tst_output/
└── my_report/
    ├── my_report.md
    └── my_report_artifacts/
        └── images...
```

### 2. Customizable Output Folder

**New Environment Variable:** `MD_OUTPUT_FOLDER`
- **Default**: `test_output`
- **Purpose**: Specify where converted documents are saved
- **Supports**: Relative and absolute paths
- **Auto-creates**: Parent directories if they don't exist

## Benefits

### Document-Specific Folders
✅ **Self-Contained**: Each document with all its assets in one place  
✅ **Easy to Move**: Copy one folder to move everything  
✅ **Clear Organization**: No mixed documents in the same folder  
✅ **Version Control**: Track each document independently  
✅ **Sharing**: Share complete document packages easily  

### Customizable Output Location
✅ **Flexibility**: Output to any desired location  
✅ **Project-Specific**: Different projects can use different folders  
✅ **CI/CD**: Easy integration with build pipelines  
✅ **Network Drives**: Can output directly to shared locations  
✅ **Environment-Specific**: Dev/staging/prod use different folders  

## Usage Examples

### Basic Usage with Default Location

```python
# Uses default test_output folder
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True
)
```

**Output:**
```
test_output/
└── document/
    ├── document.md
    └── document_artifacts/...
```

### Custom Output Folder via Environment Variable

**.env file:**
```bash
MD_OUTPUT_FOLDER=converted_documents
```

**Code:**
```python
tool = ConvertPdfToMarkdown(
    file_path="report.pdf",
    save_images_as_files=True
)
```

**Output:**
```
converted_documents/
└── report/
    ├── report.md
    └── report_artifacts/...
```

### Nested Custom Output

**.env file:**
```bash
MD_OUTPUT_FOLDER=output/documents/pdfs
```

**Code:**
```python
tool = ConvertPdfToMarkdown(
    file_path="manual.pdf",
    output_filename="user_manual_v2",
    save_images_as_files=True
)
```

**Output:**
```
output/
└── documents/
    └── pdfs/
        └── user_manual_v2/
            ├── user_manual_v2.md
            └── user_manual_v2_artifacts/...
```

### Without External Images (No Subfolder)

```python
# When save_images_as_files=False (default)
tool = ConvertPdfToMarkdown(file_path="document.pdf")
```

**Output:**
```
test_output/
└── document.md  # Single file, no subfolder
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Customize output location
MD_OUTPUT_FOLDER=my_documents

# Can use absolute paths
MD_OUTPUT_FOLDER=C:/Documents/Converted

# Can use relative paths with nesting
MD_OUTPUT_FOLDER=output/markdown/docs

# Optional: Enable external images by default
ANNOTATE_IMAGES=true
IMAGE_SCALE=2
```

### Folder Creation

The tool automatically creates:
- Base output folder (from `MD_OUTPUT_FOLDER`)
- Parent directories if they don't exist (`parents=True`)
- Document-specific subfolder (when `save_images_as_files=True`)
- Image artifacts folder (created by docling)

## Use Cases

### Use Case 1: Project Documentation

**.env:**
```bash
MD_OUTPUT_FOLDER=docs/converted
```

**Code:**
```python
for pdf_file in pdf_files:
    tool = ConvertPdfToMarkdown(
        file_path=pdf_file,
        save_images_as_files=True,
        annotate_images=True
    )
    tool.run()
```

**Result:**
```
docs/
└── converted/
    ├── api_guide/
    │   ├── api_guide.md
    │   └── api_guide_artifacts/
    ├── user_manual/
    │   ├── user_manual.md
    │   └── user_manual_artifacts/
    └── reference/
        ├── reference.md
        └── reference_artifacts/
```

### Use Case 2: Multi-Environment Setup

**Development (.env.development):**
```bash
MD_OUTPUT_FOLDER=dev_output
```

**Production (.env.production):**
```bash
MD_OUTPUT_FOLDER=/var/www/docs/converted
```

**Code** (same in both environments):
```python
tool = ConvertPdfToMarkdown(
    file_path="document.pdf",
    save_images_as_files=True
)
```

### Use Case 3: Batch Processing

```python
import json
from pathlib import Path

# Set custom output via code
os.environ["MD_OUTPUT_FOLDER"] = "batch_output"

pdf_files = Path("input_pdfs").glob("*.pdf")

for pdf_file in pdf_files:
    tool = ConvertPdfToMarkdown(
        file_path=str(pdf_file),
        output_filename=pdf_file.stem,
        save_images_as_files=True,
        annotate_images=True
    )
    
    result = json.loads(tool.run())
    if result["success"]:
        print(f"✓ {pdf_file.name} → {result['output_directory']}")
```

**Result:**
```
batch_output/
├── doc1/
├── doc2/
└── doc3/
```

### Use Case 4: CI/CD Integration

```yaml
# GitHub Actions example
- name: Convert PDFs
  env:
    MD_OUTPUT_FOLDER: ${{ github.workspace }}/docs/converted
    ANNOTATE_IMAGES: true
  run: |
    python convert_docs.py
```

## Comparison: Before vs After

### Before (Old Behavior)

```
test_output/
├── document1.md
├── document1_artifacts/...
├── document2.md
├── document2_artifacts/...
└── document3.md
```

**Issues:**
- Mixed documents in one folder
- Hard to identify which artifacts belong to which document
- Difficult to move/share individual documents

### After (New Behavior)

```
{custom_folder}/
├── document1/
│   ├── document1.md
│   └── document1_artifacts/...
├── document2/
│   ├── document2.md
│   └── document2_artifacts/...
└── document3/
    ├── document3.md
    └── document3_artifacts/...
```

**Benefits:**
- Clear organization
- Self-contained document packages
- Easy to manage and share

## Implementation Details

### Code Changes

```python
# Get output folder from environment variable
output_folder_name = os.getenv("MD_OUTPUT_FOLDER", "test_output")
base_output_dir = Path(output_folder_name)
base_output_dir.mkdir(exist_ok=True, parents=True)

# Create document-specific folder for external images
if self.save_images_as_files:
    output_dir = base_output_dir / base_filename
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{base_filename}.md"
else:
    # Inline images: save directly in base folder
    output_dir = base_output_dir
    output_path = output_dir / f"{base_filename}.md"
```

### JSON Response

The tool now returns the output directory:

```json
{
  "success": true,
  "pdf_path": "uploads/document.pdf",
  "markdown_path": "custom_output/document/document.md",
  "output_directory": "custom_output/document",
  "external_images": true,
  "annotated_images": true,
  "content_length": 34255,
  "message": "Successfully converted PDF to markdown and saved to custom_output/document/document.md (with AI-powered image annotations) (images saved in custom_output/document)"
}
```

## Backward Compatibility

✅ **100% Backward Compatible**
- Default folder is still `test_output`
- Inline images (default) still save in base folder
- No breaking changes to existing workflows
- New features are opt-in

## Best Practices

1. **Use Document Folders for External Images**: Always use `save_images_as_files=True` to get organized structure
2. **Set MD_OUTPUT_FOLDER Globally**: Configure once in `.env` for consistent behavior
3. **Use Descriptive Names**: Provide meaningful `output_filename` values
4. **Keep Documents Together**: Don't separate markdown from its artifacts folder
5. **Version Control**: Commit entire document folders
6. **Absolute Paths for Production**: Use absolute paths in production environments

## Troubleshooting

### Issue: Folder Not Created

**Cause:** Insufficient permissions or invalid path

**Solution:**
```bash
# Check path permissions
# Use absolute path
MD_OUTPUT_FOLDER=/full/path/to/output
```

### Issue: Nested Path Issues

**Cause:** Docling may create paths with full output folder in image references

**Solution:** This is expected behavior - keep the entire document folder together

### Issue: Can't Find Output Files

**Cause:** Forgot which folder name was used

**Solution:** Check the JSON response `output_directory` field:
```python
result = json.loads(tool.run())
print(f"Files saved to: {result['output_directory']}")
```

## Testing

```bash
# Test with default folder
python sage_agent/tools/ConvertPdfToMarkdown.py

# Test with custom folder
MD_OUTPUT_FOLDER=test_converted python sage_agent/tools/ConvertPdfToMarkdown.py

# Test via .env
echo "MD_OUTPUT_FOLDER=my_output" >> .env
python sage_agent/tools/ConvertPdfToMarkdown.py
```

## Related Documentation

- [ENV_SETUP.md](../ENV_SETUP.md) - Environment variable configuration
- [EXTERNAL_IMAGE_REFERENCES.md](EXTERNAL_IMAGE_REFERENCES.md) - External images feature
- [PDF_IMAGE_ANNOTATION.md](PDF_IMAGE_ANNOTATION.md) - Image annotation feature
- [ENV_VAR_CONFIG_UPDATE.md](ENV_VAR_CONFIG_UPDATE.md) - Environment variable configuration

---

**Version:** 1.3  
**Date:** October 17, 2025  
**Features:** Document-Specific Folders + Customizable Output Location

