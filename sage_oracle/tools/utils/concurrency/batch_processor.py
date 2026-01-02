"""
Batch processing with concurrency management for Sage Oracle Agent.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class ProcessingResult:
    """Result of a document processing operation"""
    operation_id: str
    source: str
    success: bool
    result: Dict[str, Any] = None
    error: str = None
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class BatchResult:
    """Result of a batch processing operation"""
    batch_id: str
    total_documents: int
    successful_documents: int
    failed_documents: int
    processing_time: float
    results: List[ProcessingResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class BatchProcessor:
    """Manages concurrent document processing with controlled concurrency"""
    
    def __init__(self, max_concurrent: int = 10):
        """
        Initialize batch processor.
        
        Args:
            max_concurrent: Maximum number of concurrent processing operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_operations: Dict[str, Dict[str, Any]] = {}
    
    async def process_documents(self, 
                              documents: List[Any], 
                              processor_func,
                              batch_id: str = None) -> BatchResult:
        """
        Process multiple documents with controlled concurrency.
        
        Args:
            documents: List of documents to process
            processor_func: Function to process each document
            batch_id: Optional batch identifier
            
        Returns:
            BatchResult with processing statistics
        """
        if batch_id is None:
            batch_id = str(uuid.uuid4())
        
        start_time = datetime.now()
        results = []
        
        # Create tasks for concurrent processing
        tasks = []
        for doc in documents:
            task = self._process_with_semaphore(doc, processor_func, batch_id)
            tasks.append(task)
        
        # Wait for all tasks to complete
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                results.append(ProcessingResult(
                    operation_id=f"{batch_id}_{i}",
                    source=str(documents[i]) if i < len(documents) else "unknown",
                    success=False,
                    error=str(result)
                ))
            else:
                results.append(result)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return BatchResult(
            batch_id=batch_id,
            total_documents=len(documents),
            successful_documents=successful,
            failed_documents=failed,
            processing_time=processing_time,
            results=results
        )
    
    async def _process_with_semaphore(self, 
                                    document: Any, 
                                    processor_func,
                                    batch_id: str) -> ProcessingResult:
        """Process a single document with semaphore control"""
        operation_id = f"{batch_id}_{uuid.uuid4().hex[:8]}"
        
        async with self.semaphore:
            start_time = datetime.now()
            
            try:
                # Track active operation
                self.active_operations[operation_id] = {
                    "start_time": start_time,
                    "document": str(document),
                    "status": "processing"
                }
                
                # Process the document
                result = await processor_func(document)
                
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Update operation status
                self.active_operations[operation_id]["status"] = "completed"
                self.active_operations[operation_id]["end_time"] = end_time
                
                return ProcessingResult(
                    operation_id=operation_id,
                    source=str(document),
                    success=True,
                    result=result,
                    processing_time=processing_time
                )
                
            except Exception as e:
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # Update operation status
                self.active_operations[operation_id]["status"] = "failed"
                self.active_operations[operation_id]["end_time"] = end_time
                self.active_operations[operation_id]["error"] = str(e)
                
                return ProcessingResult(
                    operation_id=operation_id,
                    source=str(document),
                    success=False,
                    error=str(e),
                    processing_time=processing_time
                )
            
            finally:
                # Clean up completed operations (keep last 100)
                if len(self.active_operations) > 100:
                    # Remove oldest operations
                    oldest_ops = sorted(
                        self.active_operations.items(),
                        key=lambda x: x[1].get("start_time", datetime.min)
                    )[:len(self.active_operations) - 100]
                    
                    for op_id, _ in oldest_ops:
                        del self.active_operations[op_id]
    
    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active operations"""
        return self.active_operations.copy()
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific operation"""
        return self.active_operations.get(operation_id)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics"""
        active_count = len(self.active_operations)
        completed_count = sum(1 for op in self.active_operations.values() 
                            if op.get("status") == "completed")
        failed_count = sum(1 for op in self.active_operations.values() 
                         if op.get("status") == "failed")
        processing_count = sum(1 for op in self.active_operations.values() 
                             if op.get("status") == "processing")
        
        return {
            "max_concurrent": self.max_concurrent,
            "active_operations": active_count,
            "completed_operations": completed_count,
            "failed_operations": failed_count,
            "processing_operations": processing_count,
            "available_slots": self.max_concurrent - processing_count
        }
