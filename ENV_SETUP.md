# Environment Variables Setup

This document describes the environment variables needed for the Sage Agent tools.

## Required Variables

### OPENAI_API_KEY
- **Required for**: ConvertPdfToMarkdown tool (when image annotation is enabled)
- **Description**: Your OpenAI API key for accessing vision models
- **Example**: `sk-proj-...`

### IMAGE_MODEL
- **Required for**: ConvertPdfToMarkdown tool (when image annotation is enabled)
- **Description**: The OpenAI vision model to use for image annotation
- **Default**: `gpt-4o-mini` (if not set)
- **Recommended values**: 
  - `gpt-4o-mini` - Fast and cost-effective for most use cases
  - `gpt-4o` - More capable, higher quality descriptions
  - `gpt-4-turbo` - High quality with vision capabilities
- **Example**: `IMAGE_MODEL=gpt-4o-mini`

## Optional Configuration Variables

### ANNOTATE_IMAGES
- **Used by**: ConvertPdfToMarkdown tool
- **Description**: Enables or disables AI-powered image annotation by default
- **Default**: `false` (if not set)
- **Accepted values**: `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off` (case-insensitive)
- **Example**: `ANNOTATE_IMAGES=true`
- **Note**: Can be overridden by explicitly setting the `annotate_images` parameter when calling the tool

### IMAGE_SCALE
- **Used by**: ConvertPdfToMarkdown tool
- **Description**: Default scale factor for generated images when annotation is enabled
- **Default**: `2` (if not set)
- **Accepted values**: `1`, `2`, or `3` (higher = better quality, longer processing)
- **Example**: `IMAGE_SCALE=2`
- **Note**: Can be overridden by explicitly setting the `images_scale` parameter when calling the tool

### MD_OUTPUT_FOLDER
- **Used by**: ConvertPdfToMarkdown tool
- **Description**: Specifies the output folder where converted markdown files and images are saved
- **Default**: `test_output` (if not set)
- **Accepted values**: Any valid folder path (absolute or relative)
- **Example**: `MD_OUTPUT_FOLDER=output/documents` or `MD_OUTPUT_FOLDER=C:/my_documents`
- **Note**: The folder will be created automatically if it doesn't exist (including parent directories)

## Setup Instructions

1. Create a `.env` file in the root directory of the project
2. Add your environment variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Image Model for PDF Image Annotation
IMAGE_MODEL=gpt-4o-mini

# Enable image annotation by default (optional)
ANNOTATE_IMAGES=true

# Image quality scale (optional, 1-3)
IMAGE_SCALE=2

# Output folder for converted documents (optional)
MD_OUTPUT_FOLDER=test_output
```

3. The `.env` file will be automatically loaded by the tools using `python-dotenv`

## Configuration Priority

The tool follows this priority order for configuration:

1. **Explicit parameters** - Values passed directly to the tool (highest priority)
2. **Environment variables** - Values from `.env` file or system environment
3. **Default values** - Built-in defaults (`ANNOTATE_IMAGES=false`, `IMAGE_SCALE=2`)

**Example:**
```python
# Uses environment variable ANNOTATE_IMAGES
tool = ConvertPdfToMarkdown(file_path="doc.pdf")

# Overrides environment variable with explicit parameter
tool = ConvertPdfToMarkdown(file_path="doc.pdf", annotate_images=True)
```

## Optional Variables

You can add other environment variables as needed for your specific use case:

```bash
# Database Configuration (example)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Custom API endpoints
# CUSTOM_API_URL=https://your-api.com
```

## Security Note

⚠️ **Never commit your `.env` file to version control!**

The `.env` file should be added to `.gitignore` to prevent accidentally exposing your API keys.

