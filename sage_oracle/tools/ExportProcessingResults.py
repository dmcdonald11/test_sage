"""
Export processed document results in various formats.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any, List
import json
import csv
import os
from pathlib import Path
from datetime import datetime

class ExportProcessingResults(BaseTool):
    """
    Export processed document results in various formats, providing flexible 
    output options for different use cases.
    """
    
    operation_id: str = Field(
        ..., 
        description="ID of the processing operation to export"
    )
    
    export_format: str = Field(
        default="json",
        description="Export format: 'json', 'csv', 'markdown', 'html'"
    )
    
    include_embeddings: bool = Field(
        default=False,
        description="Include vector embeddings in export (large files)"
    )
    
    include_images: bool = Field(
        default=True,
        description="Include image references in export"
    )
    
    output_path: str = Field(
        default="",
        description="Path for exported files. If not provided, will use default export directory."
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Include processing metadata in export"
    )

    def run(self):
        """
        Export processing results in the specified format.
        """
        try:
            # Step 1: Validate inputs
            valid_formats = ["json", "csv", "markdown", "html"]
            if self.export_format not in valid_formats:
                return json.dumps({
                    "success": False,
                    "error": f"Invalid export format. Must be one of: {valid_formats}"
                }, indent=2)
            
            # Step 2: Get processing results
            results_data = self._get_processing_results()
            if not results_data:
                return json.dumps({
                    "success": False,
                    "error": f"No results found for operation ID: {self.operation_id}"
                }, indent=2)
            
            # Step 3: Export in requested format
            export_result = self._export_results(results_data)
            return json.dumps(export_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    def _get_processing_results(self) -> Dict[str, Any]:
        """Get processing results for the operation"""
        
        # Simulate getting results from a database or storage system
        # In a real implementation, this would query the actual results
        
        sample_results = {
            "operation_id": self.operation_id,
            "operation_info": {
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T10:15:00Z",
                "total_documents": 10,
                "successful_documents": 9,
                "failed_documents": 1,
                "total_processing_time": 900.5
            },
            "documents": [
                {
                    "source": "document1.pdf",
                    "status": "success",
                    "output_path": "/output/document1.md",
                    "content_length": 2500,
                    "processing_time": 45.2,
                    "metadata": {
                        "file_size": 1024000,
                        "pages": 5,
                        "images_extracted": 3,
                        "chunks_created": 8
                    },
                    "chunks": [
                        {
                            "chunk_id": "chunk_1",
                            "content": "This is the first chunk of content...",
                            "start_position": 0,
                            "end_position": 500,
                            "embedding": [0.1, 0.2, 0.3] if self.include_embeddings else None
                        }
                    ] if self.include_embeddings else [],
                    "images": [
                        {
                            "image_path": "/output/images/image1.png",
                            "description": "A chart showing data trends",
                            "position": 100
                        }
                    ] if self.include_images else []
                },
                {
                    "source": "document2.html",
                    "status": "failed",
                    "error": "Network timeout",
                    "processing_time": 30.0,
                    "metadata": {
                        "file_size": 512000,
                        "attempts": 3
                    }
                }
            ]
        }
        
        return sample_results
    
    def _export_results(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export results in the specified format"""
        
        # Determine output path
        if not self.output_path:
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.operation_id}_{self.export_format}_{timestamp}"
            self.output_path = str(export_dir / f"{filename}.{self.export_format}")
        
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.export_format == "json":
                return self._export_json(results_data, output_path)
            elif self.export_format == "csv":
                return self._export_csv(results_data, output_path)
            elif self.export_format == "markdown":
                return self._export_markdown(results_data, output_path)
            elif self.export_format == "html":
                return self._export_html(results_data, output_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {self.export_format}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to export results: {str(e)}"
            }
    
    def _export_json(self, results_data: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
        """Export results as JSON"""
        
        # Filter data based on options
        export_data = self._filter_export_data(results_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "export_format": "json",
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "document_count": len(export_data.get("documents", [])),
            "message": f"Results exported to {output_path}"
        }
    
    def _export_csv(self, results_data: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
        """Export results as CSV"""
        
        documents = results_data.get("documents", [])
        if not documents:
            return {
                "success": False,
                "error": "No documents to export"
            }
        
        # Prepare CSV data
        csv_data = []
        for doc in documents:
            row = {
                "source": doc.get("source", ""),
                "status": doc.get("status", ""),
                "output_path": doc.get("output_path", ""),
                "content_length": doc.get("content_length", 0),
                "processing_time": doc.get("processing_time", 0),
                "error": doc.get("error", "")
            }
            
            # Add metadata if requested
            if self.include_metadata and "metadata" in doc:
                metadata = doc["metadata"]
                row.update({
                    "file_size": metadata.get("file_size", 0),
                    "pages": metadata.get("pages", 0),
                    "images_extracted": metadata.get("images_extracted", 0),
                    "chunks_created": metadata.get("chunks_created", 0)
                })
            
            csv_data.append(row)
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if csv_data:
                writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                writer.writeheader()
                writer.writerows(csv_data)
        
        return {
            "success": True,
            "export_format": "csv",
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "document_count": len(csv_data),
            "message": f"Results exported to {output_path}"
        }
    
    def _export_markdown(self, results_data: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
        """Export results as Markdown"""
        
        documents = results_data.get("documents", [])
        operation_info = results_data.get("operation_info", {})
        
        markdown_content = f"""# Processing Results Export

## Operation Information
- **Operation ID**: {self.operation_id}
- **Start Time**: {operation_info.get('start_time', 'N/A')}
- **End Time**: {operation_info.get('end_time', 'N/A')}
- **Total Documents**: {operation_info.get('total_documents', 0)}
- **Successful Documents**: {operation_info.get('successful_documents', 0)}
- **Failed Documents**: {operation_info.get('failed_documents', 0)}
- **Total Processing Time**: {operation_info.get('total_processing_time', 0)} seconds

## Document Results

"""
        
        for i, doc in enumerate(documents, 1):
            markdown_content += f"""### Document {i}: {doc.get('source', 'Unknown')}

- **Status**: {doc.get('status', 'Unknown')}
- **Output Path**: {doc.get('output_path', 'N/A')}
- **Content Length**: {doc.get('content_length', 0)} characters
- **Processing Time**: {doc.get('processing_time', 0)} seconds

"""
            
            if doc.get('error'):
                markdown_content += f"- **Error**: {doc['error']}\n\n"
            
            if self.include_metadata and "metadata" in doc:
                metadata = doc["metadata"]
                markdown_content += f"""#### Metadata
- **File Size**: {metadata.get('file_size', 0)} bytes
- **Pages**: {metadata.get('pages', 0)}
- **Images Extracted**: {metadata.get('images_extracted', 0)}
- **Chunks Created**: {metadata.get('chunks_created', 0)}

"""
            
            if self.include_images and "images" in doc:
                images = doc["images"]
                if images:
                    markdown_content += "#### Images\n"
                    for img in images:
                        markdown_content += f"- **{img.get('image_path', 'Unknown')}**: {img.get('description', 'No description')}\n"
                    markdown_content += "\n"
        
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return {
            "success": True,
            "export_format": "markdown",
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "document_count": len(documents),
            "message": f"Results exported to {output_path}"
        }
    
    def _export_html(self, results_data: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
        """Export results as HTML"""
        
        documents = results_data.get("documents", [])
        operation_info = results_data.get("operation_info", {})
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Processing Results - {self.operation_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .document {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; }}
        .failed {{ background-color: #f8d7da; }}
        .metadata {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Processing Results Export</h1>
        <h2>Operation Information</h2>
        <ul>
            <li><strong>Operation ID</strong>: {self.operation_id}</li>
            <li><strong>Start Time</strong>: {operation_info.get('start_time', 'N/A')}</li>
            <li><strong>End Time</strong>: {operation_info.get('end_time', 'N/A')}</li>
            <li><strong>Total Documents</strong>: {operation_info.get('total_documents', 0)}</li>
            <li><strong>Successful Documents</strong>: {operation_info.get('successful_documents', 0)}</li>
            <li><strong>Failed Documents</strong>: {operation_info.get('failed_documents', 0)}</li>
            <li><strong>Total Processing Time</strong>: {operation_info.get('total_processing_time', 0)} seconds</li>
        </ul>
    </div>
    
    <h2>Document Results</h2>
"""
        
        for i, doc in enumerate(documents, 1):
            status_class = "success" if doc.get('status') == 'success' else "failed"
            html_content += f"""
    <div class="document {status_class}">
        <h3>Document {i}: {doc.get('source', 'Unknown')}</h3>
        <ul>
            <li><strong>Status</strong>: {doc.get('status', 'Unknown')}</li>
            <li><strong>Output Path</strong>: {doc.get('output_path', 'N/A')}</li>
            <li><strong>Content Length</strong>: {doc.get('content_length', 0)} characters</li>
            <li><strong>Processing Time</strong>: {doc.get('processing_time', 0)} seconds</li>
"""
            
            if doc.get('error'):
                html_content += f"            <li><strong>Error</strong>: {doc['error']}</li>\n"
            
            html_content += "        </ul>\n"
            
            if self.include_metadata and "metadata" in doc:
                metadata = doc["metadata"]
                html_content += f"""
        <div class="metadata">
            <h4>Metadata</h4>
            <ul>
                <li><strong>File Size</strong>: {metadata.get('file_size', 0)} bytes</li>
                <li><strong>Pages</strong>: {metadata.get('pages', 0)}</li>
                <li><strong>Images Extracted</strong>: {metadata.get('images_extracted', 0)}</li>
                <li><strong>Chunks Created</strong>: {metadata.get('chunks_created', 0)}</li>
            </ul>
        </div>
"""
            
            if self.include_images and "images" in doc:
                images = doc["images"]
                if images:
                    html_content += """
        <h4>Images</h4>
        <ul>
"""
                    for img in images:
                        html_content += f"            <li><strong>{img.get('image_path', 'Unknown')}</strong>: {img.get('description', 'No description')}</li>\n"
                    html_content += "        </ul>\n"
            
            html_content += "    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            "success": True,
            "export_format": "html",
            "output_path": str(output_path),
            "file_size": output_path.stat().st_size,
            "document_count": len(documents),
            "message": f"Results exported to {output_path}"
        }
    
    def _filter_export_data(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter export data based on options"""
        
        filtered_data = results_data.copy()
        
        # Filter documents
        if "documents" in filtered_data:
            filtered_docs = []
            for doc in filtered_data["documents"]:
                filtered_doc = doc.copy()
                
                # Remove embeddings if not requested
                if not self.include_embeddings and "chunks" in filtered_doc:
                    for chunk in filtered_doc["chunks"]:
                        if "embedding" in chunk:
                            del chunk["embedding"]
                
                # Remove images if not requested
                if not self.include_images and "images" in filtered_doc:
                    del filtered_doc["images"]
                
                # Remove metadata if not requested
                if not self.include_metadata and "metadata" in filtered_doc:
                    del filtered_doc["metadata"]
                
                filtered_docs.append(filtered_doc)
            
            filtered_data["documents"] = filtered_docs
        
        return filtered_data


if __name__ == "__main__":
    # Test the tool
    print("Testing ExportProcessingResults...")
    
    tool = ExportProcessingResults(
        operation_id="test_operation_001",
        export_format="json",
        include_embeddings=False,
        include_images=True,
        include_metadata=True
    )
    
    result = tool.run()
    print("Export Result:")
    print(result)
