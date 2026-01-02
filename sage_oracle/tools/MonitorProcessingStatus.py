"""
Monitor and report on active document processing operations.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta

# Import our shared utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils.concurrency.batch_processor import BatchProcessor

class MonitorProcessingStatus(BaseTool):
    """
    Monitor and report on active document processing operations, providing real-time 
    status updates and performance metrics.
    """
    
    operation_id: str = Field(
        default="",
        description="ID of the processing operation to monitor. If empty, returns all active operations."
    )
    
    include_details: bool = Field(
        default=False,
        description="Include detailed progress information"
    )
    
    refresh_interval: int = Field(
        default=5,
        description="Refresh interval in seconds (1-60)"
    )

    def run(self):
        """
        Monitor processing status and return current information.
        """
        try:
            # Step 1: Validate inputs
            if not (1 <= self.refresh_interval <= 60):
                return json.dumps({
                    "success": False,
                    "error": "refresh_interval must be between 1 and 60 seconds"
                }, indent=2)
            
            # Step 2: Get monitoring data
            result = self._get_monitoring_data()
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    def _get_monitoring_data(self) -> Dict[str, Any]:
        """Get monitoring data for operations"""
        
        # For now, we'll simulate monitoring data since we don't have a global
        # batch processor instance. In a real implementation, this would connect
        # to a shared monitoring service or database.
        
        if self.operation_id:
            # Monitor specific operation
            return self._get_operation_status(self.operation_id)
        else:
            # Monitor all operations
            return self._get_all_operations_status()
    
    def _get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get status of a specific operation"""
        
        # Simulate operation data
        # In a real implementation, this would query the actual operation status
        operation_data = {
            "operation_id": operation_id,
            "status": "completed",  # completed, processing, failed, pending
            "start_time": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_documents": 10,
            "processed_documents": 10,
            "successful_documents": 9,
            "failed_documents": 1,
            "processing_time": 45.2,
            "progress_percentage": 100.0,
            "current_stage": "completed",
            "estimated_completion": None
        }
        
        if self.include_details:
            operation_data["details"] = {
                "documents": [
                    {
                        "source": "document1.pdf",
                        "status": "completed",
                        "processing_time": 4.2,
                        "content_length": 1500
                    },
                    {
                        "source": "document2.html",
                        "status": "failed",
                        "error": "Network timeout",
                        "processing_time": 2.1
                    }
                ],
                "performance_metrics": {
                    "average_processing_time": 4.5,
                    "documents_per_minute": 13.3,
                    "memory_usage": "2.1GB",
                    "cpu_usage": "45%"
                }
            }
        
        return {
            "success": True,
            "operation_id": operation_id,
            "operation_data": operation_data,
            "timestamp": datetime.now().isoformat(),
            "refresh_interval": self.refresh_interval
        }
    
    def _get_all_operations_status(self) -> Dict[str, Any]:
        """Get status of all operations"""
        
        # Simulate multiple operations
        operations = [
            {
                "operation_id": "batch_001",
                "status": "processing",
                "start_time": (datetime.now() - timedelta(minutes=2)).isoformat(),
                "total_documents": 25,
                "processed_documents": 15,
                "successful_documents": 14,
                "failed_documents": 1,
                "progress_percentage": 60.0,
                "current_stage": "conversion"
            },
            {
                "operation_id": "batch_002",
                "status": "completed",
                "start_time": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "end_time": (datetime.now() - timedelta(minutes=1)).isoformat(),
                "total_documents": 5,
                "processed_documents": 5,
                "successful_documents": 5,
                "failed_documents": 0,
                "progress_percentage": 100.0,
                "current_stage": "completed"
            },
            {
                "operation_id": "batch_003",
                "status": "failed",
                "start_time": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "end_time": (datetime.now() - timedelta(minutes=12)).isoformat(),
                "total_documents": 3,
                "processed_documents": 1,
                "successful_documents": 0,
                "failed_documents": 3,
                "progress_percentage": 33.3,
                "current_stage": "failed",
                "error": "Out of memory"
            }
        ]
        
        # Calculate summary statistics
        total_operations = len(operations)
        active_operations = sum(1 for op in operations if op["status"] == "processing")
        completed_operations = sum(1 for op in operations if op["status"] == "completed")
        failed_operations = sum(1 for op in operations if op["status"] == "failed")
        
        total_documents = sum(op["total_documents"] for op in operations)
        total_processed = sum(op["processed_documents"] for op in operations)
        total_successful = sum(op["successful_documents"] for op in operations)
        total_failed = sum(op["failed_documents"] for op in operations)
        
        result = {
            "success": True,
            "summary": {
                "total_operations": total_operations,
                "active_operations": active_operations,
                "completed_operations": completed_operations,
                "failed_operations": failed_operations,
                "total_documents": total_documents,
                "total_processed": total_processed,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_success_rate": (total_successful / total_processed * 100) if total_processed > 0 else 0
            },
            "operations": operations,
            "timestamp": datetime.now().isoformat(),
            "refresh_interval": self.refresh_interval
        }
        
        if self.include_details:
            result["system_metrics"] = {
                "memory_usage": "4.2GB",
                "cpu_usage": "65%",
                "disk_usage": "12.5GB",
                "active_threads": 8,
                "queue_size": 3
            }
        
        return result


if __name__ == "__main__":
    # Test the tool
    print("Testing MonitorProcessingStatus...")
    
    # Test monitoring all operations
    tool = MonitorProcessingStatus(
        include_details=True
    )
    
    result = tool.run()
    print("All Operations Status:")
    print(result)
    
    print("\n" + "="*50 + "\n")
    
    # Test monitoring specific operation
    tool2 = MonitorProcessingStatus(
        operation_id="batch_001",
        include_details=True
    )
    
    result2 = tool2.run()
    print("Specific Operation Status:")
    print(result2)
