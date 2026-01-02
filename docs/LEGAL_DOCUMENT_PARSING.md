# Legal Document Parsing and Chunking Strategy

## Overview

This document outlines best practices for parsing, chunking, embedding, and storing legal documents for semantic search and retrieval applications.

## Key Considerations for Legal Document Chunking

### Structural Hierarchy
Legal documents have inherent structure (sections, articles, clauses, sub-clauses) that should be preserved. Breaking mid-section can destroy critical context.

### Citation Integrity
Legal text heavily references other sections ("as defined in Section 3.2"). Your chunks need enough context to maintain these relationships.

### Semantic Density
A single sentence in legal text can carry enormous weight. Unlike casual prose, you can't assume adjacent sentences are redundant.

## Recommended Chunking Strategy

### 1. Hierarchical/Semantic Chunking (Preferred)
- Parse the document structure first (headings, numbered sections, etc.)
- Create chunks that respect document boundaries
- Keep related clauses together
- Typical size: 500-1000 tokens per chunk with 100-200 token overlap

### 2. Implementation Approach

**Structure Detection:**
- Use regex or NLP to identify section headers, numbered lists, articles
- Tools like `unstructured.io` or custom parsers work well
- Preserve metadata (section numbers, titles, hierarchy level)

**Smart Splitting:**
- Split at natural boundaries (between sections, not mid-paragraph)
- For long sections, split at sub-section boundaries
- Add contextual metadata to each chunk (document name, section hierarchy, date)

### 3. Critical: Maintain Context Windows
- Include parent section titles in metadata
- Add overlapping content (last paragraph of previous chunk)
- Store cross-references as structured metadata

### 4. Metadata to Capture

```
- document_title
- document_type (contract, brief, statute, etc.)
- section_number
- section_title
- parent_sections (full hierarchy)
- page_number
- effective_date
- parties_involved
```

## Document-Type Specific Techniques

### For Contracts
- Chunk by clause/article
- Keep definitions section intact or cross-reference it
- Preserve exhibit references

### For Case Law
- Chunk by holding, facts, reasoning sections
- Keep citations with their context
- Preserve judge opinions separately

### For Statutes
- Chunk by section/subsection
- Maintain statutory hierarchy
- Include amendment history in metadata

## Using Docling for Legal Document Processing

### Why Docling Works Well

**Structure Preservation**
Docling excels at understanding document structure:
- Headings and hierarchies
- Tables (common in contracts, exhibits)
- Lists and numbered sections
- Page layouts and columns

**Multi-Format Support**
Legal documents come in various formats (PDF, DOCX, HTML), and Docling handles these robustly, which is crucial since legal PDFs are often scanned or poorly formatted.

**Rich Metadata Extraction**
Docling extracts document structure as a hierarchy:
- Section relationships
- Document object model (DOM)
- Bounding boxes and page numbers
- Table structures

### Basic Implementation

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Configure for legal docs (prioritize accuracy)
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True  # Important for scanned legal docs
pipeline_options.do_table_structure = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: pipeline_options
    }
)

# Convert document
result = converter.convert("contract.pdf")

# Access structured content
doc = result.document

# Iterate through document structure
for element in doc.iterate_items():
    if element.label == "section-header":
        # Track section hierarchy
        section_title = element.text
    elif element.label == "text":
        # Chunk based on structure
        chunk_text = element.text
        # Preserve metadata
        metadata = {
            "page": element.page_no,
            "section": section_title,
            "bbox": element.bbox
        }
```

### Recommended Workflow

**1. Parse with Docling**
```python
# Extract structured document with hierarchy
# Preserve tables, lists, headers separately
result = converter.convert("legal_document.pdf")
doc = result.document
```

**2. Smart Chunking**
```python
# Group by logical sections
chunks = []
current_section = []
current_metadata = {}

for item in doc.iterate_items():
    if item.label in ["section-header", "title"]:
        # Save previous chunk
        if current_section:
            chunks.append({
                "text": "\n".join(current_section),
                "metadata": current_metadata
            })
        # Start new chunk
        current_section = [item.text]
        current_metadata = {"section": item.text, "page": item.page_no}
    else:
        current_section.append(item.text)
```

**3. Post-Processing**
- Check chunk sizes (split large sections if needed)
- Add overlap between chunks
- Enrich with document-level metadata

### Advantages for Legal Documents

- **Table handling**: Critical for schedules, exhibits, fee structures
- **OCR support**: Many legal PDFs are scanned
- **Layout understanding**: Preserves multi-column layouts, footnotes
- **Markdown export**: Clean, structured output
- **Bounding boxes**: Can reference specific locations in source document

### Considerations

Docling might need supplementing for:
- Very domain-specific legal formatting (custom section numbering schemes)
- Complex cross-references between documents
- Citation extraction (you might add a separate citation parser)

## Additional Tools Worth Considering

- **LangChain**: Has legal-specific text splitters
- **LlamaIndex**: Good hierarchical chunking
- **Unstructured.io**: Excellent at parsing various legal doc formats
- **Custom solution**: Often best for specialized legal doc types

## Conclusion

For most legal document parsing and chunking needs, Docling provides an excellent foundation with its robust structure preservation, multi-format support, and rich metadata extraction capabilities. Combined with thoughtful chunking strategies that respect document hierarchy and maintain context, it forms a solid basis for legal document processing pipelines.