"""
Base input source abstraction for different document input types.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class DocumentInput:
    """Represents a document input with metadata"""
    source: str
    source_type: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseInputSource(ABC):
    """Abstract base for different input sources"""
    
    @abstractmethod
    async def get_documents(self) -> List[DocumentInput]:
        """Get list of documents to process"""
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Return source type identifier"""
        pass
    
    @abstractmethod
    def get_source_count(self) -> int:
        """Return estimated number of documents"""
        pass
