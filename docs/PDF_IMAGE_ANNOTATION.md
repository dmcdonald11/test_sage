# PDF Image Annotation Feature

## Overview

The `ConvertPdfToMarkdown` tool now supports AI-powered image annotation using OpenAI's vision models. This feature allows you to automatically generate descriptive text for images, diagrams, charts, and figures found in PDF documents.

## How It Works

When enabled, the tool uses Docling's picture description pipeline integrated with OpenAI's vision API to:

1. Extract images from the PDF document
2. Send each image to OpenAI's vision model
3. Generate detailed descriptions of the visual content
4. Embed these descriptions as inline annotations in the markdown output

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Required for image annotation
OPENAI_API_KEY=your_openai_api_key_here

# Optional - defaults to gpt-4o-mini if not set
IMAGE_MODEL=gpt-4o-mini
```

### Recommended Models

- **gpt-4o-mini** (default): Fast and cost-effective, good for most use cases
- **gpt-4o**: More capable, produces higher quality descriptions
- **gpt-4-turbo**: Excellent quality with vision capabilities

## Usage

### Basic Usage (No Image Annotation)

```python
from sage_agent.tools.ConvertPdfToMarkdown import ConvertPdfToMarkdown

tool = ConvertPdfToMarkdown(
    file_path="path/to/document.pdf",
    output_filename="my_document"
)
result = tool.run()
```

### With Image Annotation

```python
from sage_agent.tools.ConvertPdfToMarkdown import ConvertPdfToMarkdown

tool = ConvertPdfToMarkdown(
    file_path="path/to/document.pdf",
    output_filename="my_document_annotated",
    annotate_images=True,      # Enable image annotation
    images_scale=2             # Image quality (1-3, higher = better quality)
)
result = tool.run()
```

### Parameters

- **file_path** (str): Path to the PDF file to convert
- **file_content** (str): Base64-encoded PDF content for file uploads
- **output_filename** (str): Custom name for output markdown file (optional)
- **annotate_images** (bool): Enable AI-powered image annotation (default: False)
- **images_scale** (int): Scale factor for images (1-3, default: 2)

## Output Format

When image annotation is enabled, the markdown output includes inline annotations:

```markdown
## Example Section

This section discusses the architecture diagram shown below.

<!--<annotation kind="description">-->
The image illustrates a three-tier architecture with a frontend layer 
consisting of web and mobile clients, a middle application layer with 
microservices including authentication, data processing, and API gateway, 
and a backend layer with databases and caching systems. Arrows show the 
flow of requests through the system.
<!--<annotation/>-->

<!-- image -->
```

## Use Cases

Image annotation is particularly useful for:

- **Technical Documentation**: Understanding architecture diagrams and system flows
- **Research Papers**: Extracting information from charts, graphs, and experimental results
- **Business Reports**: Describing data visualizations and infographics
- **Educational Materials**: Making diagrams and illustrations accessible
- **Knowledge Extraction**: Making visual content searchable and retrievable

## Performance Considerations

- **Processing Time**: Each image adds 2-5 seconds to processing time due to API calls
- **Cost**: Each image description costs tokens based on image size and model used
- **Quality vs Speed**: Higher `images_scale` values produce better quality but take longer
- **Rate Limits**: Be aware of OpenAI API rate limits when processing documents with many images

## Example Test Results

### Test Document: Docling Technical Report (uploads/docling.pdf)

**Without Image Annotation:**
- Processing time: ~241 seconds
- Output size: 29,380 characters
- Images: Marked as `<!-- image -->` placeholders

**With Image Annotation:**
- Processing time: ~241 seconds + API calls
- Output size: 32,716 characters (+11% content)
- Images: Include detailed AI-generated descriptions
- Model used: gpt-4o-mini

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable is required"

**Solution**: Add your OpenAI API key to the `.env` file:
```bash
OPENAI_API_KEY=sk-proj-...
```

### Error: "Failed to import Docling pipeline options"

**Solution**: Ensure docling>=2.0.0 is installed:
```bash
pip install docling>=2.0.0
```

### Poor Image Descriptions

**Solution**: 
- Try using a more capable model (gpt-4o instead of gpt-4o-mini)
- Increase `images_scale` parameter (2 or 3)
- Check that your PDF images are high quality

### Rate Limit Errors

**Solution**:
- Add delays between processing multiple documents
- Use a lower-tier model (gpt-4o-mini)
- Check your OpenAI API usage limits

## Code Reference

The implementation uses Docling's advanced document processing pipeline:

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions
)
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure OpenAI API for image description
picture_desc_api_option = PictureDescriptionApiOptions(
    url="https://api.openai.com/v1/chat/completions",
    prompt="Describe this image in sentences in a single paragraph...",
    params={"model": "gpt-4o-mini"},
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=60,
)

# Configure PDF pipeline
pipeline_options = PdfPipelineOptions(
    do_picture_description=True,
    picture_description_options=picture_desc_api_option,
    enable_remote_services=True,
    generate_picture_images=True,
    images_scale=2,
)

# Create converter with options
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)
```

## References

- [Docling Documentation](https://docling-project.github.io/docling/)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Docling Picture Description Example](../examples/docling-images/00_docling-basic.ipynb)

