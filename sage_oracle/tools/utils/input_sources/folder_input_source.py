"""
Folder-based input source for processing documents from local directories.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from .base_input_source import BaseInputSource, DocumentInput

class FolderInputSource(BaseInputSource):
    """Process documents from a folder"""
    
    def __init__(self, folder_path: str, file_patterns: List[str] = None):
        """
        Initialize folder input source.
        
        Args:
            folder_path: Path to folder containing documents
            file_patterns: List of file patterns to process (e.g., ["*.pdf", "*.html"])
        """
        self.folder_path = Path(folder_path)
        self.file_patterns = file_patterns or ["*.pdf", "*.html", "*.docx", "*.md"]
        self._documents_cache = None
    
    async def get_documents(self) -> List[DocumentInput]:
        """Scan folder and return document list"""
        if self._documents_cache is not None:
            return self._documents_cache
        
        documents = []
        
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")
        
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self.folder_path}")
        
        for pattern in self.file_patterns:
            for file_path in self.folder_path.glob(pattern):
                if file_path.is_file():
                    documents.append(DocumentInput(
                        source=str(file_path),
                        source_type="file",
                        metadata={
                            "filename": file_path.name,
                            "file_extension": file_path.suffix,
                            "file_size": file_path.stat().st_size,
                            "modified_time": file_path.stat().st_mtime
                        }
                    ))
        
        # Cache the results
        self._documents_cache = documents
        return documents
    
    def get_source_type(self) -> str:
        return "folder"
    
    def get_source_count(self) -> int:
        """Return estimated number of documents"""
        if self._documents_cache is not None:
            return len(self._documents_cache)
        
        count = 0
        for pattern in self.file_patterns:
            count += len(list(self.folder_path.glob(pattern)))
        return count
    
    def get_folder_info(self) -> Dict[str, Any]:
        """Get information about the folder"""
        return {
            "folder_path": str(self.folder_path),
            "file_patterns": self.file_patterns,
            "exists": self.folder_path.exists(),
            "is_directory": self.folder_path.is_dir() if self.folder_path.exists() else False,
            "estimated_document_count": self.get_source_count()
        }
